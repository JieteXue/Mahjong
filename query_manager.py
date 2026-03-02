# query_manager.py (更新版)
import sqlite3

class QueryManager:
    def __init__(self):
        self.db_path = 'mahjong.db'
    
    def get_season_filter(self):
        """获取用户选择的赛季ID"""
        try:
            from season_manager import SeasonManager
            season_mgr = SeasonManager()
            seasons = season_mgr.list_seasons()
            
            if not seasons:
                return None, None
            
            print("\n0. 所有赛季")
            for season in seasons:
                print(f"{season[0]}. {season[1]}")
            
            try:
                choice = int(input("请选择赛季 (输入0查看所有): "))
                if choice == 0:
                    return None, None
                else:
                    for season in seasons:
                        if season[0] == choice:
                            return choice, season[1]
                    return None, None
            except ValueError:
                return None, None
        except:
            return None, None
        
    def get_user_game_stats(self, user_id, season_id=None):
        """从牌局记录中获取用户的实际游戏统计"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # 构建查询条件
        if season_id:
            season_condition = "AND g.season_id = ?"
            # 参数列表：4个user_id用于player条件 + 1个season_id
            params = [user_id, user_id, user_id, user_id, season_id]
        else:
            season_condition = ""
            # 参数列表：4个user_id用于player条件
            params = [user_id, user_id, user_id, user_id]

        # 查询用户参与的大局数
        c.execute(f'''
            SELECT COUNT(DISTINCT g.id) 
            FROM games g
            WHERE (g.player1_id = ? OR g.player2_id = ? OR g.player3_id = ? OR g.player4_id = ?)
            AND g.is_finished = 1
            {season_condition}
        ''', params)
        total_games = c.fetchone()[0]

        # 查询用户参与的小局数
        c.execute(f'''
            SELECT COUNT(*) 
            FROM rounds r
            JOIN games g ON r.game_id = g.id
            WHERE g.is_finished = 1
            AND (g.player1_id = ? OR g.player2_id = ? OR g.player3_id = ? OR g.player4_id = ?)
            {season_condition}
        ''', params)
        total_rounds = c.fetchone()[0]

        # 查询用户胡牌次数
        if season_id:
            c.execute('''
                SELECT COUNT(*) 
                FROM rounds r
                JOIN games g ON r.game_id = g.id
                WHERE r.winner_id = ?
                AND g.is_finished = 1
                AND g.season_id = ?
            ''', (user_id, season_id))
        else:
            c.execute('''
                SELECT COUNT(*) 
                FROM rounds r
                JOIN games g ON r.game_id = g.id
                WHERE r.winner_id = ?
                AND g.is_finished = 1
            ''', (user_id,))
        total_wins = c.fetchone()[0]

        # 查询用户净胜分（从games表计算）
        if season_id:
            # 对于净胜分查询，需要重复参数：4个user_id用于CASE WHEN，4个user_id用于WHERE，1个season_id
            c.execute('''
                SELECT 
                    SUM(CASE 
                        WHEN g.player1_id = ? THEN g.final_score1 - 1000
                        WHEN g.player2_id = ? THEN g.final_score2 - 1000
                        WHEN g.player3_id = ? THEN g.final_score3 - 1000
                        WHEN g.player4_id = ? THEN g.final_score4 - 1000
                        ELSE 0
                    END) as net_score
                FROM games g
                WHERE (g.player1_id = ? OR g.player2_id = ? OR g.player3_id = ? OR g.player4_id = ?)
                AND g.is_finished = 1
                AND g.season_id = ?
            ''', (user_id, user_id, user_id, user_id, user_id, user_id, user_id, user_id, season_id))
        else:
            c.execute('''
                SELECT 
                    SUM(CASE 
                        WHEN g.player1_id = ? THEN g.final_score1 - 1000
                        WHEN g.player2_id = ? THEN g.final_score2 - 1000
                        WHEN g.player3_id = ? THEN g.final_score3 - 1000
                        WHEN g.player4_id = ? THEN g.final_score4 - 1000
                        ELSE 0
                    END) as net_score
                FROM games g
                WHERE (g.player1_id = ? OR g.player2_id = ? OR g.player3_id = ? OR g.player4_id = ?)
                AND g.is_finished = 1
            ''', (user_id, user_id, user_id, user_id, user_id, user_id, user_id, user_id))

        net_score = c.fetchone()[0]
        if net_score is None:
            net_score = 0

        conn.close()

        return {
            'total_games': total_games,
            'total_rounds': total_rounds,
            'total_wins': total_wins,
            'net_score': net_score
        }

    def user_stats(self):
        """查看单个用户战绩（基于实际牌局计算）"""
        # 获取赛季筛选
        season_id, season_name = self.get_season_filter()

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # 先列出所有用户
        c.execute("SELECT id, username FROM users ORDER BY username")
        users = c.fetchall()

        if not users:
            print("暂无用户")
            conn.close()
            return

        print("\n用户列表:")
        for user in users:
            print(f"{user[0]}. {user[1]}")

        try:
            uid = int(input("请输入用户ID: "))
        except ValueError:
            print("无效输入")
            conn.close()
            return

        # 获取用户基本信息
        c.execute('''
            SELECT username, created_at 
            FROM users WHERE id=?
        ''', (uid,))
        user = c.fetchone()

        if not user:
            print("用户不存在")
            conn.close()
            return

        # 从牌局记录获取实际统计
        stats = self.get_user_game_stats(uid, season_id)

        print(f"\n=== {user[0]} 的战绩 {f'({season_name})' if season_name else ''} ===")
        print(f"注册时间: {user[1]}")
        print(f"参与大局数: {stats['total_games']}")
        print(f"参与小局数: {stats['total_rounds']}")
        print(f"胡牌次数: {stats['total_wins']}")

        if stats['total_rounds'] > 0:
            win_rate = stats['total_wins'] / stats['total_rounds'] * 100
            print(f"小局胜率: {win_rate:.1f}%")

            avg_score_per_round = stats['net_score'] / stats['total_rounds']
            print(f"平均每局得分: {avg_score_per_round:.2f}")

        print(f"净胜分: {stats['net_score']:+d}")

        # 查询最近5大局 - 修复参数问题
        if season_id:
            # 有赛季筛选的情况
            c.execute('''
                SELECT g.id, g.created_at, g.finished_at, g.total_rounds,
                       u1.username, u2.username, u3.username, u4.username,
                       g.final_score1, g.final_score2, g.final_score3, g.final_score4
                FROM games g
                JOIN users u1 ON g.player1_id = u1.id
                JOIN users u2 ON g.player2_id = u2.id
                JOIN users u3 ON g.player3_id = u3.id
                JOIN users u4 ON g.player4_id = u4.id
                WHERE (g.player1_id = ? OR g.player2_id = ? OR g.player3_id = ? OR g.player4_id = ?)
                AND g.is_finished = 1
                AND g.season_id = ?
                ORDER BY g.created_at DESC LIMIT 5
            ''', (uid, uid, uid, uid, season_id))
        else:
            # 无赛季筛选的情况
            c.execute('''
                SELECT g.id, g.created_at, g.finished_at, g.total_rounds,
                       u1.username, u2.username, u3.username, u4.username,
                       g.final_score1, g.final_score2, g.final_score3, g.final_score4
                FROM games g
                JOIN users u1 ON g.player1_id = u1.id
                JOIN users u2 ON g.player2_id = u2.id
                JOIN users u3 ON g.player3_id = u3.id
                JOIN users u4 ON g.player4_id = u4.id
                WHERE (g.player1_id = ? OR g.player2_id = ? OR g.player3_id = ? OR g.player4_id = ?)
                AND g.is_finished = 1
                ORDER BY g.created_at DESC LIMIT 5
            ''', (uid, uid, uid, uid))

        recent_games = c.fetchall()
        if recent_games:
            print("\n最近5大局成绩:")
            for game in recent_games:
                game_id, start_time, finish_time, rounds, p1, p2, p3, p4, s1, s2, s3, s4 = game

                # 找出该用户在这局的得分
                user_score = None
                score_change = 0
                if p1 == user[0]:
                    user_score = s1
                    score_change = s1 - 1000
                elif p2 == user[0]:
                    user_score = s2
                    score_change = s2 - 1000
                elif p3 == user[0]:
                    user_score = s3
                    score_change = s3 - 1000
                elif p4 == user[0]:
                    user_score = s4
                    score_change = s4 - 1000

                # 找出这局的其他玩家分数用于显示
                print(f"  大局 #{game_id} ({rounds}小局) [{start_time[:10]}]: {score_change:+d}分")
                print(f"    {p1}: {s1}  {p2}: {s2}  {p3}: {s3}  {p4}: {s4}")
        else:
            print("\n暂无大局记录")

        # 查询最近小局记录
        if season_id:
            c.execute('''
                SELECT r.round_number, r.created_at, r.tai, 
                       u2.username as winner_name,
                       r.score_change1, r.score_change2, r.score_change3, r.score_change4
                FROM rounds r
                JOIN games g ON r.game_id = g.id
                LEFT JOIN users u2 ON r.winner_id = u2.id
                WHERE g.season_id = ?
                AND (g.player1_id = ? OR g.player2_id = ? OR g.player3_id = ? OR g.player4_id = ?)
                ORDER BY r.created_at DESC LIMIT 5
            ''', (season_id, uid, uid, uid, uid))
        else:
            c.execute('''
                SELECT r.round_number, r.created_at, r.tai, 
                       u2.username as winner_name,
                       r.score_change1, r.score_change2, r.score_change3, r.score_change4
                FROM rounds r
                JOIN games g ON r.game_id = g.id
                LEFT JOIN users u2 ON r.winner_id = u2.id
                WHERE (g.player1_id = ? OR g.player2_id = ? OR g.player3_id = ? OR g.player4_id = ?)
                ORDER BY r.created_at DESC LIMIT 5
            ''', (uid, uid, uid, uid))

        recent_rounds = c.fetchall()
        if recent_rounds:
            print("\n最近5小局记录:")
            for rnum, rtime, tai, winner, c1, c2, c3, c4 in recent_rounds:
                # 找出该用户的分数变化
                # 这里简化处理，实际应该根据玩家位置找出对应的分数变化
                changes = [c1, c2, c3, c4]
                if winner:
                    result = f"✅ {winner} 胡{tai}台"
                else:
                    result = "🔄 流局"
                print(f"  第{rnum}局 [{rtime[5:16]}] {result} 变化: [{c1:+d},{c2:+d},{c3:+d},{c4:+d}]")
        else:
            print("\n暂无小局记录")

        conn.close()
    
    def global_stats(self):
        """全局统计（基于实际牌局计算）"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # 大局统计
        c.execute("SELECT COUNT(*) FROM games WHERE is_finished=1")
        total_games = c.fetchone()[0]
        
        # 小局统计
        c.execute("SELECT COUNT(*) FROM rounds")
        total_rounds = c.fetchone()[0]
        
        # 操作统计
        c.execute("SELECT COUNT(*) FROM actions")
        total_actions = c.fetchone()[0]
        
        # 白板杠统计
        c.execute("SELECT COALESCE(SUM(count), 0) FROM baiban_records")
        total_baiban = c.fetchone()[0]
        
        # 胡牌统计
        c.execute("SELECT COUNT(*) FROM rounds WHERE winner_id IS NOT NULL")
        total_hupai = c.fetchone()[0]
        
        print("\n=== 全局统计 ===")
        print(f"总大局数: {total_games}")
        print(f"总小局数: {total_rounds}")
        if total_games > 0:
            print(f"平均每大局小局数: {total_rounds/total_games:.1f}")
        print(f"总操作记录: {total_actions}")
        print(f"白板杠总数: {total_baiban}")
        print(f"胡牌总数: {total_hupai}")
        if total_rounds > 0:
            print(f"胡牌率: {total_hupai/total_rounds*100:.1f}%")
            print(f"流局率: {(total_rounds - total_hupai)/total_rounds*100:.1f}%")
        
        # 赢家排行榜（基于实际胡牌次数）
        print("\n🏆 赢家榜 (按胡牌次数):")
        c.execute('''
            SELECT u.username, COUNT(r.winner_id) as wins, 
                   COUNT(DISTINCT r.game_id) as games,
                   COUNT(r.id) as rounds
            FROM users u
            LEFT JOIN rounds r ON u.id = r.winner_id
            GROUP BY u.id
            HAVING wins > 0
            ORDER BY wins DESC LIMIT 5
        ''')
        
        top_winners = c.fetchall()
        if top_winners:
            for i, (name, wins, games, rounds) in enumerate(top_winners, 1):
                win_rate = wins/rounds*100 if rounds > 0 else 0
                print(f"  {i}. {name}: {wins}胜 (参与{ games }大局{ rounds }小局, 胜率{win_rate:.1f}%)")
        
        # 净胜分排行榜（从games表计算）- 修复参数问题
        print("\n💰 富豪榜 (按净胜分):")
        c.execute('''
            SELECT u.username, 
                   SUM(CASE 
                       WHEN g.player1_id = u.id THEN g.final_score1 - 1000
                       WHEN g.player2_id = u.id THEN g.final_score2 - 1000
                       WHEN g.player3_id = u.id THEN g.final_score3 - 1000
                       WHEN g.player4_id = u.id THEN g.final_score4 - 1000
                       ELSE 0
                   END) as net_score,
                   COUNT(DISTINCT g.id) as games,
                   AVG(CASE 
                       WHEN g.player1_id = u.id THEN g.final_score1 - 1000
                       WHEN g.player2_id = u.id THEN g.final_score2 - 1000
                       WHEN g.player3_id = u.id THEN g.final_score3 - 1000
                       WHEN g.player4_id = u.id THEN g.final_score4 - 1000
                       ELSE NULL
                   END) as avg_score
            FROM users u
            LEFT JOIN games g ON (g.player1_id = u.id OR g.player2_id = u.id OR 
                                  g.player3_id = u.id OR g.player4_id = u.id)
                              AND g.is_finished = 1
            GROUP BY u.id
            HAVING games > 0
            ORDER BY net_score DESC LIMIT 5
        ''')

        top_scores = c.fetchall()
        if top_scores:
            for i, (name, score, games, avg) in enumerate(top_scores, 1):
                if avg is None:
                    avg_display = "N/A"
                else:
                    avg_display = f"{avg:.1f}"
                print(f"  {i}. {name}: {score:+d}分 (参与{games}大局, 平均{avg_display}分/大局)")
        else:
            print("  暂无数据")
        
        # 白板杠排行榜
        print("\n🀄️ 白板杠榜:")
        c.execute('''
            SELECT u.username, SUM(b.count) as total_baiban, COUNT(DISTINCT b.round_id) as rounds
            FROM baiban_records b
            JOIN users u ON b.player_id = u.id
            GROUP BY u.id
            ORDER BY total_baiban DESC LIMIT 5
        ''')
        
        top_baiban = c.fetchall()
        if top_baiban:
            for i, (name, total, rounds) in enumerate(top_baiban, 1):
                print(f"  {i}. {name}: 杠{total}张 (共{rounds}局有杠)")
        
        conn.close()
    
    def recent_games(self):
        """查看最近大局"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            SELECT g.id, g.created_at, g.finished_at, g.total_rounds,
                   u1.username, u2.username, u3.username, u4.username,
                   g.final_score1, g.final_score2, g.final_score3, g.final_score4,
                   g.is_finished
            FROM games g
            JOIN users u1 ON g.player1_id = u1.id
            JOIN users u2 ON g.player2_id = u2.id
            JOIN users u3 ON g.player3_id = u3.id
            JOIN users u4 ON g.player4_id = u4.id
            ORDER BY g.created_at DESC LIMIT 10
        ''')
        
        games = c.fetchall()
        
        if not games:
            print("暂无大局记录")
            conn.close()
            return
        
        print("\n=== 最近10大局 ===")
        for game in games:
            game_id, start, finish, rounds, p1, p2, p3, p4, s1, s2, s3, s4, finished = game
            status = "✅" if finished else "⏳"
            
            # 计算每人的净胜分
            net1 = s1 - 1000
            net2 = s2 - 1000
            net3 = s3 - 1000
            net4 = s4 - 1000
            
            print(f"\n大局 #{game_id} {status} ({start[:16]})")
            print(f"  小局数: {rounds}")
            print(f"  {p1}: {s1} ({net1:+d})")
            print(f"  {p2}: {s2} ({net2:+d})")
            print(f"  {p3}: {s3} ({net3:+d})")
            print(f"  {p4}: {s4} ({net4:+d})")
            
            # 显示该大局下的小局记录
            c.execute('''
                SELECT round_number, 
                       u.username as winner_name, 
                       tai, 
                       score_change1, score_change2, score_change3, score_change4
                FROM rounds r
                LEFT JOIN users u ON r.winner_id = u.id
                WHERE r.game_id = ?
                ORDER BY round_number
            ''', (game_id,))
            
            rounds_detail = c.fetchall()
            if rounds_detail:
                print("  小局详情:")
                for rd in rounds_detail[:5]:  # 最多显示5局
                    rnum, winner, tai, ch1, ch2, ch3, ch4 = rd
                    if winner:
                        print(f"    第{rnum}局: {winner} 胡牌{tai}台 [{ch1:+d},{ch2:+d},{ch3:+d},{ch4:+d}]")
                    else:
                        print(f"    第{rnum}局: 流局 [{ch1:+d},{ch2:+d},{ch3:+d},{ch4:+d}]")
                if len(rounds_detail) > 5:
                    print(f"    ... 还有 {len(rounds_detail)-5} 局")
        
        conn.close()

    def recent_rounds(self):
        """查看最近小局记录"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        season_id, season_name = self.get_season_filter()

        if season_id:
            c.execute('''
                SELECT r.id, r.game_id, r.round_number, r.created_at, 
                       u1.username as dealer_name,
                       u2.username as winner_name,
                       r.tai, r.lianzhuang,
                       r.score1, r.score2, r.score3, r.score4,
                       r.score_change1, r.score_change2, r.score_change3, r.score_change4
                FROM rounds r
                JOIN games g ON r.game_id = g.id
                JOIN users u1 ON r.dealer_id = u1.id
                LEFT JOIN users u2 ON r.winner_id = u2.id
                WHERE g.season_id = ?
                ORDER BY r.created_at DESC LIMIT 20
            ''', (season_id,))
        else:
            c.execute('''
                SELECT r.id, r.game_id, r.round_number, r.created_at, 
                       u1.username as dealer_name,
                       u2.username as winner_name,
                       r.tai, r.lianzhuang,
                       r.score1, r.score2, r.score3, r.score4,
                       r.score_change1, r.score_change2, r.score_change3, r.score_change4
                FROM rounds r
                JOIN users u1 ON r.dealer_id = u1.id
                LEFT JOIN users u2 ON r.winner_id = u2.id
                ORDER BY r.created_at DESC LIMIT 20
            ''')

        rounds = c.fetchall()

        if not rounds:
            print("暂无小局记录")
            conn.close()
            return

        print(f"\n=== 最近20小局 {f'({season_name})' if season_name else ''} ===")

        for r in rounds:
            rid, gid, rnum, rtime, dealer, winner, tai, lian, s1, s2, s3, s4, c1, c2, c3, c4 = r

            if winner:
                result = f"✅ {winner} 胡 {tai}台"
            else:
                result = "🔄 流局"

            print(f"\n小局 #{rid} (大局{gid}-第{rnum}局) [{rtime[5:16]}]")
            print(f"  庄家: {dealer} 连庄:{lian} | {result}")
            print(f"  分数变化: [{c1:+d}, {c2:+d}, {c3:+d}, {c4:+d}]")
            print(f"  最终分数: [{s1}, {s2}, {s3}, {s4}]")

            # 查询本局白板杠
            c.execute('''
                SELECT b.count, u.username
                FROM baiban_records b
                JOIN users u ON b.player_id = u.id
                WHERE b.round_id = ?
            ''', (rid,))
            baibans = c.fetchall()
            if baibans:
                for count, name in baibans:
                    print(f"  白板杠: {name} 杠{count}张")

        conn.close()
    
    def baiban_stats(self):
        """白板杠统计"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        season_id, season_name = self.get_season_filter()
        
        print(f"\n=== 白板杠统计 {f'({season_name})' if season_name else ''} ===")
        
        if season_id:
            c.execute('''
                SELECT u.username, SUM(b.count) as total_baiban, 
                       COUNT(DISTINCT b.round_id) as rounds_with_baiban,
                       COUNT(DISTINCT r.game_id) as games
                FROM baiban_records b
                JOIN rounds r ON b.round_id = r.id
                JOIN games g ON r.game_id = g.id
                JOIN users u ON b.player_id = u.id
                WHERE g.season_id = ?
                GROUP BY u.id
                ORDER BY total_baiban DESC
            ''', (season_id,))
        else:
            c.execute('''
                SELECT u.username, SUM(b.count) as total_baiban, 
                       COUNT(DISTINCT b.round_id) as rounds_with_baiban,
                       COUNT(DISTINCT r.game_id) as games
                FROM baiban_records b
                JOIN rounds r ON b.round_id = r.id
                JOIN users u ON b.player_id = u.id
                GROUP BY u.id
                ORDER BY total_baiban DESC
            ''')
        
        stats = c.fetchall()
        
        if stats:
            print("\n🏆 白板杠排行榜:")
            for i, (name, total, rounds, games) in enumerate(stats, 1):
                avg_per_round = total/rounds if rounds > 0 else 0
                print(f"  {i}. {name}: 杠 {total} 张 (参与{games}大局{rounds}小局, 平均{avg_per_round:.1f}张/有杠局)")
            
            # 总计
            if season_id:
                c.execute('''
                    SELECT SUM(count) FROM baiban_records b
                    JOIN rounds r ON b.round_id = r.id
                    JOIN games g ON r.game_id = g.id
                    WHERE g.season_id = ?
                ''', (season_id,))
            else:
                c.execute('SELECT SUM(count) FROM baiban_records')
            
            total = c.fetchone()[0] or 0
            print(f"\n总计白板杠次数: {total} 张")
        else:
            print("暂无白板杠记录")
        
        conn.close()