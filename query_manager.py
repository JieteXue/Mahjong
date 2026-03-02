# query_manager.py (更新版 - 增加小局查询功能)
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
    
    def user_stats(self):
        """查看用户战绩"""
        season_id, season_name = self.get_season_filter()
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # 列出所有用户
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
        
        # 获取用户信息
        c.execute('''
            SELECT username, created_at, total_games, total_rounds, total_wins, net_score
            FROM users WHERE id=?
        ''', (uid,))
        user = c.fetchone()
        
        if not user:
            print("用户不存在")
            conn.close()
            return
        
        username, created_at, total_games, total_rounds, total_wins, net_score = user
        
        print(f"\n=== {username} 的战绩 {f'({season_name})' if season_name else ''} ===")
        print(f"注册时间: {created_at}")
        print(f"总大局数: {total_games}")
        print(f"总小局数: {total_rounds}")
        print(f"总胡牌次数: {total_wins}")
        if total_rounds > 0:
            print(f"小局胜率: {total_wins/total_rounds*100:.1f}%")
        print(f"净胜分: {net_score:+d}")
        
        # 查询最近5大局
        if season_id:
            c.execute('''
                SELECT g.id, g.created_at, g.finished_at, g.total_rounds,
                       u1.username, u2.username, u3.username, u4.username,
                       g.final_score1, g.final_score2, g.final_score3, g.final_score4
                FROM games g
                JOIN users u1 ON g.player1_id = u1.id
                JOIN users u2 ON g.player2_id = u2.id
                JOIN users u3 ON g.player3_id = u3.id
                JOIN users u4 ON g.player4_id = u4.id
                WHERE (? IN (g.player1_id, g.player2_id, g.player3_id, g.player4_id))
                AND g.season_id=? AND g.is_finished=1
                ORDER BY g.created_at DESC LIMIT 5
            ''', (uid, season_id))
        else:
            c.execute('''
                SELECT g.id, g.created_at, g.finished_at, g.total_rounds,
                       u1.username, u2.username, u3.username, u4.username,
                       g.final_score1, g.final_score2, g.final_score3, g.final_score4
                FROM games g
                JOIN users u1 ON g.player1_id = u1.id
                JOIN users u2 ON g.player2_id = u2.id
                JOIN users u3 ON g.player3_id = u3.id
                JOIN users u4 ON g.player4_id = u4.id
                WHERE ? IN (g.player1_id, g.player2_id, g.player3_id, g.player4_id)
                AND g.is_finished=1
                ORDER BY g.created_at DESC LIMIT 5
            ''', (uid,))
        
        recent_games = c.fetchall()
        if recent_games:
            print("\n最近5大局成绩:")
            for game in recent_games:
                game_id, start_time, finish_time, rounds, p1, p2, p3, p4, s1, s2, s3, s4 = game
                print(f"  大局 #{game_id} ({rounds}小局):")
                print(f"    {p1}: {s1:+d}  {p2}: {s2:+d}  {p3}: {s3:+d}  {p4}: {s4:+d}")
        
        # 查询该用户参与的最近小局
        print("\n最近5小局记录:")
        if season_id:
            c.execute('''
                SELECT r.round_number, r.created_at, r.tai, r.lianzhuang,
                       u1.username, r.winner_id,
                       r.score_change1, r.score_change2, r.score_change3, r.score_change4
                FROM rounds r
                JOIN games g ON r.game_id = g.id
                JOIN users u1 ON r.dealer_id = u1.id
                WHERE g.season_id=? AND 
                      (r.winner_id=? OR r.dealer_id=? OR 
                       EXISTS (SELECT 1 FROM baiban_records b WHERE b.round_id = r.id AND b.player_id = ?))
                ORDER BY r.created_at DESC LIMIT 5
            ''', (season_id, uid, uid, uid))
        else:
            c.execute('''
                SELECT r.round_number, r.created_at, r.tai, r.lianzhuang,
                       u1.username, r.winner_id,
                       r.score_change1, r.score_change2, r.score_change3, r.score_change4
                FROM rounds r
                JOIN users u1 ON r.dealer_id = u1.id
                WHERE r.winner_id=? OR r.dealer_id=?
                ORDER BY r.created_at DESC LIMIT 5
            ''', (uid, uid))
        
        recent_rounds = c.fetchall()
        if recent_rounds:
            for round_data in recent_rounds:
                rnum, rtime, tai, lian, dealer_name, winner_id, c1, c2, c3, c4 = round_data
                if winner_id == uid:
                    result = f"✅ 胡牌 {tai}台"
                elif winner_id is None:
                    result = "🔄 流局"
                else:
                    result = f"❌ 放枪"
                print(f"  第{rnum}小局 [{rtime[5:16]}] {result} (庄家:{dealer_name})")
        else:
            print("  暂无小局记录")
        
        conn.close()
    
    def global_stats(self):
        """全局统计"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # 总大局数
        c.execute("SELECT COUNT(*) FROM games WHERE is_finished=1")
        total_games = c.fetchone()[0]
        
        # 总小局数
        c.execute("SELECT COUNT(*) FROM rounds")
        total_rounds = c.fetchone()[0]
        
        # 总操作数
        c.execute("SELECT COUNT(*) FROM actions")
        total_actions = c.fetchone()[0]
        
        # 杠总数
        c.execute("SELECT SUM(count) FROM baiban_records")
        total_baiban = c.fetchone()[0] or 0
        
        # 胡牌总数
        c.execute("SELECT COUNT(*) FROM rounds WHERE winner_id IS NOT NULL")
        total_hupai = c.fetchone()[0]
        
        print("\n=== 全局统计 ===")
        print(f"总大局数: {total_games}")
        print(f"总小局数: {total_rounds}")
        print(f"平均每大局小局数: {total_rounds/total_games:.1f}" if total_games > 0 else "")
        print(f"总操作记录: {total_actions}")
        print(f"白板杠总数: {total_baiban}")
        print(f"胡牌总数: {total_hupai}")
        if total_rounds > 0:
            print(f"流局率: {(total_rounds - total_hupai)/total_rounds*100:.1f}%")
        
        # 赢家排行榜
        c.execute('''
            SELECT username, total_wins, total_rounds, net_score
            FROM users
            WHERE total_wins > 0
            ORDER BY total_wins DESC LIMIT 5
        ''')
        top_winners = c.fetchall()
        
        if top_winners:
            print("\n🏆 赢家榜 (胜局数):")
            for i, (name, wins, rounds, score) in enumerate(top_winners, 1):
                win_rate = wins/rounds*100 if rounds > 0 else 0
                print(f"  {i}. {name} - {wins}胜 (胜率{win_rate:.1f}%, 净胜分:{score:+d})")
        
        # 净胜分排行榜
        c.execute('''
            SELECT username, net_score, total_rounds
            FROM users
            ORDER BY net_score DESC LIMIT 5
        ''')
        top_scores = c.fetchall()
        
        if top_scores:
            print("\n💰 富豪榜 (净胜分):")
            for i, (name, score, rounds) in enumerate(top_scores, 1):
                avg_score = score/rounds if rounds > 0 else 0
                print(f"  {i}. {name} - {score:+d}分 (平均每局{avg_score:.1f}分)")
        
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
            print(f"\n大局 #{game_id} {status} ({start[:16]})")
            print(f"  小局数: {rounds}")
            print(f"  {p1}: {s1:+d}  {p2}: {s2:+d}")
            print(f"  {p3}: {s3:+d}  {p4}: {s4:+d}")
            
            # 显示该大局下的小局记录
            c.execute('''
                SELECT round_number, winner_id, tai, 
                       score_change1, score_change2, score_change3, score_change4
                FROM rounds
                WHERE game_id = ?
                ORDER BY round_number
            ''', (game_id,))
            rounds_detail = c.fetchall()
            if rounds_detail:
                print("  小局详情:")
                for rd in rounds_detail[:3]:  # 只显示前3局，避免太长
                    rnum, winner, tai, ch1, ch2, ch3, ch4 = rd
                    if winner:
                        print(f"    第{rnum}局: 胡牌{tai}台 [{ch1:+d},{ch2:+d},{ch3:+d},{ch4:+d}]")
                    else:
                        print(f"    第{rnum}局: 流局")
        
        conn.close()

    def recent_rounds(self):
        """查看最近小局记录"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        season_id, season_name = self.get_season_filter()

        if season_id:
            c.execute('''
                SELECT r.id, r.game_id, r.round_number, r.created_at, 
                       u1.username, r.winner_id, r.tai, r.lianzhuang,
                       r.score1, r.score2, r.score3, r.score4,
                       r.score_change1, r.score_change2, r.score_change3, r.score_change4
                FROM rounds r
                JOIN games g ON r.game_id = g.id
                JOIN users u1 ON r.dealer_id = u1.id
                WHERE g.season_id = ?
                ORDER BY r.created_at DESC LIMIT 20
            ''', (season_id,))
        else:
            c.execute('''
                SELECT r.id, r.game_id, r.round_number, r.created_at, 
                       u1.username, r.winner_id, r.tai, r.lianzhuang,
                       r.score1, r.score2, r.score3, r.score4,
                       r.score_change1, r.score_change2, r.score_change3, r.score_change4
                FROM rounds r
                JOIN users u1 ON r.dealer_id = u1.id
                ORDER BY r.created_at DESC LIMIT 20
            ''')

        rounds = c.fetchall()

        if not rounds:
            print("暂无小局记录")
            conn.close()
            return

        print(f"\n=== 最近20小局 {f'({season_name})' if season_name else ''} ===")

        for r in rounds:
            rid, gid, rnum, rtime, dealer, winner_id, tai, lian, s1, s2, s3, s4, c1, c2, c3, c4 = r

            if winner_id:
                # 获取赢家名字
                c2 = conn.cursor()
                c2.execute("SELECT username FROM users WHERE id=?", (winner_id,))
                winner = c2.fetchone()
                winner_name = winner[0] if winner else "未知"
                result = f"✅ {winner_name} 胡 {tai}台"
            else:
                result = "🔄 流局"

            print(f"\n小局 #{rid} (大局{gid}-第{rnum}局) [{rtime[5:16]}]")
            print(f"  庄家: {dealer} 连庄:{lian} | {result}")
            print(f"  分数变化: [{c1:+d}, {c2:+d}, {c3:+d}, {c4:+d}]")

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
                SELECT u.username, SUM(b.count) as total_baiban, COUNT(DISTINCT b.round_id) as rounds_with_baiban
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
                SELECT u.username, SUM(b.count) as total_baiban, COUNT(DISTINCT b.round_id) as rounds_with_baiban
                FROM baiban_records b
                JOIN users u ON b.player_id = u.id
                GROUP BY u.id
                ORDER BY total_baiban DESC
            ''')

        stats = c.fetchall()

        if stats:
            print("\n🏆 白板杠排行榜:")
            for i, (name, total, rounds) in enumerate(stats, 1):
                print(f"  {i}. {name}: 杠 {total} 张 (共{rounds}局有杠)")

            # 总计
            c.execute('SELECT SUM(count) FROM baiban_records')
            total = c.fetchone()[0] or 0
            print(f"\n总计白板杠次数: {total} 张")
        else:
            print("暂无白板杠记录")

        conn.close()