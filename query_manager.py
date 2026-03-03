# query_manager.py (更新版)
import sqlite3
from unicodedata import name

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
            # 参数列表
            params_game = [user_id, user_id, user_id, user_id, season_id]
            params_rounds = [user_id, user_id, user_id, user_id, season_id]
            params_wins = [user_id, season_id]
        else:
            season_condition = ""
            params_game = [user_id, user_id, user_id, user_id]
            params_rounds = [user_id, user_id, user_id, user_id]
            params_wins = [user_id]

        # 查询用户参与的大局数
        query_games = f'''
            SELECT COUNT(DISTINCT g.id) 
            FROM games g
            WHERE (g.player1_id = ? OR g.player2_id = ? OR g.player3_id = ? OR g.player4_id = ?)
            AND g.is_finished = 1
            {season_condition}
        '''
        c.execute(query_games, params_game)
        total_games = c.fetchone()[0]

        # 查询用户参与的小局数 - 修复：直接从rounds表通过game关联查询
        query_rounds = f'''
            SELECT COUNT(*) 
            FROM rounds r
            LEFT JOIN games g ON r.game_id = g.id
            WHERE g.is_finished = 1
            AND (g.player1_id = ? OR g.player2_id = ? OR g.player3_id = ? OR g.player4_id = ?)
            {season_condition}
        '''
        c.execute(query_rounds, params_rounds)
        total_rounds = c.fetchone()[0]

        # 查询用户胡牌次数
        if season_id:
            c.execute('''
                SELECT COUNT(*) 
                FROM rounds r
                LEFT JOIN games g ON r.game_id = g.id
                WHERE r.winner_id = ?
                AND g.is_finished = 1
                AND g.season_id = ?
            ''', (user_id, season_id))
        else:
            c.execute('''
                SELECT COUNT(*) 
                FROM rounds r
                LEFT JOIN games g ON r.game_id = g.id
                WHERE r.winner_id = ?
            ''', (user_id,))
        total_wins = c.fetchone()[0]

        # 查询用户净胜分（从games表计算）
        if season_id:
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

        print(f"DEBUG - 用户 {user_id} 统计: 大局={total_games}, 小局={total_rounds}, 胜局={total_wins}, 净胜分={net_score}")

        return {
            'total_games': total_games,
            'total_rounds': total_rounds,
            'total_wins': total_wins,
            'net_score': net_score
        }

    def user_stats(self):
        """查看单个用户战绩（基于实际牌局计算，兼容不足4人）"""
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
    
        # 获取用户基本信息
        c.execute('SELECT username, created_at FROM users WHERE id=?', (uid,))
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
    
        # 查询最近5大局
        if season_id:
            c.execute('''
                SELECT g.id, g.created_at, g.finished_at, g.total_rounds,
                    u1.username, u2.username, u3.username, u4.username,
                    COALESCE(g.final_score1, 1000) as s1,
                    COALESCE(g.final_score2, 1000) as s2,
                    COALESCE(g.final_score3, 1000) as s3,
                    COALESCE(g.final_score4, 1000) as s4
                FROM games g
                LEFT JOIN users u1 ON g.player1_id = u1.id
                LEFT JOIN users u2 ON g.player2_id = u2.id
                LEFT JOIN users u3 ON g.player3_id = u3.id
                LEFT JOIN users u4 ON g.player4_id = u4.id
                WHERE (g.player1_id = ? OR g.player2_id = ? OR g.player3_id = ? OR g.player4_id = ?)
                AND g.is_finished = 1
                AND g.season_id = ?
                ORDER BY g.created_at DESC LIMIT 5
            ''', (uid, uid, uid, uid, season_id))
        else:
            c.execute('''
                SELECT g.id, g.created_at, g.finished_at, g.total_rounds,
                    u1.username, u2.username, u3.username, u4.username,
                    COALESCE(g.final_score1, 1000) as s1,
                    COALESCE(g.final_score2, 1000) as s2,
                    COALESCE(g.final_score3, 1000) as s3,
                    COALESCE(g.final_score4, 1000) as s4
                FROM games g
                LEFT JOIN users u1 ON g.player1_id = u1.id
                LEFT JOIN users u2 ON g.player2_id = u2.id
                LEFT JOIN users u3 ON g.player3_id = u3.id
                LEFT JOIN users u4 ON g.player4_id = u4.id
                WHERE (g.player1_id = ? OR g.player2_id = ? OR g.player3_id = ? OR g.player4_id = ?)
                AND g.is_finished = 1
                ORDER BY g.created_at DESC LIMIT 5
            ''', (uid, uid, uid, uid))
    
        recent_games = c.fetchall()
        if recent_games:
            print("\n最近5大局成绩:")
            for game in recent_games:
                game_id, start_time, finish_time, rounds, p1, p2, p3, p4, s1, s2, s3, s4 = game
    
                # 构建玩家列表和分数列表（过滤 NULL）
                players = [p for p in [p1, p2, p3, p4] if p is not None]
                scores = [s for s in [s1, s2, s3, s4] if s is not None]
    
                # 找出该用户的得分变化
                user_score_change = None
                for i, name in enumerate(players):
                    if name == user[0]:
                        user_score_change = scores[i] - 1000
                        break
                    
                print(f"  大局 #{game_id} ({rounds if rounds else 0}小局) [{start_time[:10]}]: {user_score_change:+d}分")
                # 显示所有玩家
                display_line = "    " + "  ".join(f"{name}: {score}" for name, score in zip(players, scores))
                print(display_line)
        else:
            print("\n暂无大局记录")
    
        # 查询最近小局记录
        if season_id:
            c.execute('''
                SELECT r.round_number, r.created_at, r.tai, 
                       u2.username as winner_name,
                       r.score_change1, r.score_change2, r.score_change3, r.score_change4,
                       g.id as game_id
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
                       r.score_change1, r.score_change2, r.score_change3, r.score_change4,
                       g.id as game_id
                FROM rounds r
                JOIN games g ON r.game_id = g.id
                LEFT JOIN users u2 ON r.winner_id = u2.id
                WHERE (g.player1_id = ? OR g.player2_id = ? OR g.player3_id = ? OR g.player4_id = ?)
                ORDER BY r.created_at DESC LIMIT 5
            ''', (uid, uid, uid, uid))
    
        recent_rounds = c.fetchall()
        if recent_rounds:
            print("\n最近5小局记录:")
            for rnum, rtime, tai, winner, c1, c2, c3, c4, game_id_val in recent_rounds:
                # 过滤 NULL 变化值
                changes = []
                for ch in [c1, c2, c3, c4]:
                    if ch is not None:
                        changes.append(f"{ch:+d}")
                changes_str = ','.join(changes)
                if winner:
                    result = f"✅ {winner} 胡{tai}台"
                else:
                    result = "🔄 流局"
                print(f"  第{rnum}局 (大局{game_id_val}) [{rtime[5:16]}] {result} 变化: [{changes_str}]")
        else:
            print("\n暂无小局记录")
    
        conn.close()
    def global_stats(self):
        """全局统计（基于实际牌局计算，兼容不足4人）"""
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

        # 白板杠统计（COALESCE 处理 NULL）
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
                print(f"  {i}. {name}: {wins}胜 (参与{games}大局{rounds}小局, 胜率{win_rate:.1f}%)")

        # 净胜分排行榜（需处理 NULL 分数）
        print("\n💰 富豪榜 (按净胜分):")
        c.execute('''
            SELECT u.username, 
                COALESCE(SUM(
                    CASE 
                        WHEN g.player1_id = u.id THEN g.final_score1 - 1000
                        WHEN g.player2_id = u.id THEN g.final_score2 - 1000
                        WHEN g.player3_id = u.id THEN g.final_score3 - 1000
                        WHEN g.player4_id = u.id THEN g.final_score4 - 1000
                        ELSE 0
                    END
                ), 0) as net_score,
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
            SELECT u.username, COALESCE(SUM(b.count), 0) as total_baiban, COUNT(DISTINCT b.round_id) as rounds
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
        """查看最近大局（支持不足4人的游戏）"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # 先检查表结构
        c.execute("PRAGMA table_info(games)")
        columns = [col[1] for col in c.fetchall()]

        # 确定正确的列名
        if 'final_score1' in columns:
            score_cols = ['final_score1', 'final_score2', 'final_score3', 'final_score4']
        else:
            score_cols = ['score1', 'score2', 'score3', 'score4']

        # 修复：移除重复的列定义，确保SQL语法正确
        query = f'''
            SELECT g.id, g.created_at, g.finished_at, g.total_rounds,
                   u1.username, u2.username, u3.username, u4.username,
                   COALESCE(g.{score_cols[0]}, 1000) as s1,
                   COALESCE(g.{score_cols[1]}, 1000) as s2,
                   COALESCE(g.{score_cols[2]}, 1000) as s3,
                   COALESCE(g.{score_cols[3]}, 1000) as s4,
                   g.is_finished
            FROM games g
            LEFT JOIN users u1 ON g.player1_id = u1.id
            LEFT JOIN users u2 ON g.player2_id = u2.id
            LEFT JOIN users u3 ON g.player3_id = u3.id
            LEFT JOIN users u4 ON g.player4_id = u4.id
            ORDER BY g.created_at DESC LIMIT 10
        '''

        c.execute(query)
        games = c.fetchall()

        if not games:
            print("暂无大局记录")
            conn.close()
            return

        print("\n=== 最近10大局 ===")
        for game in games:
            game_id, start, finish, rounds, p1, p2, p3, p4, s1, s2, s3, s4, finished = game
            status = "✅" if finished else "⏳"

            # 构建玩家列表和分数列表（过滤掉 NULL 玩家）
            players = []
            scores = []
            for name, score in zip([p1, p2, p3, p4], [s1, s2, s3, s4]):
                if name is not None and score is not None:
                    players.append(name)
                    scores.append(score)

            # 计算净胜分（仅对非 NULL 分数）
            nets = [score - 1000 for score in scores]

            print(f"\n大局 #{game_id} {status} ({start[:16] if start else ''})")
            print(f"  小局数: {rounds if rounds is not None else 0}")
            for i, name in enumerate(players):
                print(f"  {name}: {scores[i]} ({nets[i]:+d})")

            # 显示该大局下的小局记录
            c.execute('''
                SELECT round_number, 
                       u.username as winner_name, 
                       tai, 
                       COALESCE(score_change1, 0) as ch1,
                       COALESCE(score_change2, 0) as ch2,
                       COALESCE(score_change3, 0) as ch3,
                       COALESCE(score_change4, 0) as ch4
                FROM rounds r
                LEFT JOIN users u ON r.winner_id = u.id
                WHERE r.game_id = ?
                ORDER BY round_number
            ''', (game_id,))

            rounds_detail = c.fetchall()
            if rounds_detail:
                print("  小局详情:")
                for rd in rounds_detail[:5]:
                    rnum, winner, tai, ch1, ch2, ch3, ch4 = rd
                    # 处理可能的 NULL 值
                    rnum = rnum if rnum is not None else 0
                    winner = winner if winner is not None else "未知"
                    tai = tai if tai is not None else 0
                    # 构建变化值列表
                    changes = []
                    for ch in [ch1, ch2, ch3, ch4]:
                        if ch is not None:
                            changes.append(f"{ch:+d}")
                    changes_str = ','.join(changes)
                    if winner != "未知":
                        print(f"    第{rnum}局: {winner} 胡牌{tai}台 [{changes_str}]")
                    else:
                        print(f"    第{rnum}局: 流局 [{changes_str}]")
                if len(rounds_detail) > 5:
                    print(f"    ... 还有 {len(rounds_detail)-5} 局")

        conn.close()
    
    def recent_rounds(self):
        """查看最近小局记录（支持不足4人）"""
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
                LEFT JOIN users u1 ON r.dealer_id = u1.id
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
                LEFT JOIN users u1 ON r.dealer_id = u1.id
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

            # 构建分数和变化列表，过滤 NULL
            scores = [s for s in [s1, s2, s3, s4] if s is not None]
            changes = [ch for ch in [c1, c2, c3, c4] if ch is not None]

            if winner:
                result = f"✅ {winner} 胡 {tai}台"
            else:
                result = "🔄 流局"

            print(f"\n小局 #{rid} (大局{gid}-第{rnum}局) [{rtime[5:16]}]")
            print(f"  庄家: {dealer if dealer else '未知'} 连庄:{lian if lian else 0} | {result}")
            print(f"  分数变化: {changes}")
            print(f"  最终分数: {scores}")

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
                LEFT JOIN rounds r ON b.round_id = r.id
                LEFT JOIN games g ON r.game_id = g.id
                LEFT JOIN users u ON b.player_id = u.id
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
                LEFT JOIN rounds r ON b.round_id = r.id
                LEFT JOIN users u ON b.player_id = u.id
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
                    LEFT JOIN rounds r ON b.round_id = r.id
                    LEFT JOIN games g ON r.game_id = g.id
                    WHERE g.season_id = ?
                ''', (season_id,))
            else:
                c.execute('SELECT SUM(count) FROM baiban_records')
            
            total = c.fetchone()[0] or 0
            print(f"\n总计白板杠次数: {total} 张")
        else:
            print("暂无白板杠记录")
        
        conn.close()
           
    def total_score_stats(self):
        """查看所有用户总积分排行榜"""
        print("\n" + "=" * 60)
        print("💰 总积分排行榜")
        print("=" * 60)

        season_id, season_name = self.get_season_filter()

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        if season_id:
            # 按赛季统计
            c.execute('''
                SELECT u.id, u.username,
                       COALESCE(SUM(
                           CASE 
                               WHEN g.player1_id = u.id THEN g.final_score1 - 1000
                               WHEN g.player2_id = u.id THEN g.final_score2 - 1000
                               WHEN g.player3_id = u.id THEN g.final_score3 - 1000
                               WHEN g.player4_id = u.id THEN g.final_score4 - 1000
                               ELSE 0
                           END
                       ), 0) as game_score,
                       u.net_score - COALESCE(SUM(
                           CASE 
                               WHEN g.player1_id = u.id THEN g.final_score1 - 1000
                               WHEN g.player2_id = u.id THEN g.final_score2 - 1000
                               WHEN g.player3_id = u.id THEN g.final_score3 - 1000
                               WHEN g.player4_id = u.id THEN g.final_score4 - 1000
                               ELSE 0
                           END
                       ), 0) as manual_adjust,
                       u.net_score as total_score,
                       COUNT(DISTINCT g.id) as games_played,
                       COUNT(r.id) as rounds_played,
                       COUNT(CASE WHEN r.winner_id = u.id THEN 1 END) as wins
                FROM users u
                LEFT JOIN games g ON (g.player1_id = u.id OR g.player2_id = u.id OR 
                                      g.player3_id = u.id OR g.player4_id = u.id)
                                  AND g.season_id = ? AND g.is_finished = 1
                LEFT JOIN rounds r ON r.game_id = g.id
                GROUP BY u.id
                ORDER BY total_score DESC
            ''', (season_id,))
        else:
            # 全局统计
            c.execute('''
                SELECT u.id, u.username,
                       COALESCE((
                           SELECT COALESCE(SUM(
                               CASE 
                                   WHEN g.player1_id = u.id THEN g.final_score1 - 1000
                                   WHEN g.player2_id = u.id THEN g.final_score2 - 1000
                                   WHEN g.player3_id = u.id THEN g.final_score3 - 1000
                                   WHEN g.player4_id = u.id THEN g.final_score4 - 1000
                                   ELSE 0
                               END
                           ), 0)
                           FROM games g
                           WHERE (g.player1_id = u.id OR g.player2_id = u.id OR 
                                  g.player3_id = u.id OR g.player4_id = u.id)
                           AND g.is_finished = 1
                       ), 0) as game_score,
                       u.net_score - COALESCE((
                           SELECT COALESCE(SUM(
                               CASE 
                                   WHEN g2.player1_id = u.id THEN g2.final_score1 - 1000
                                   WHEN g2.player2_id = u.id THEN g2.final_score2 - 1000
                                   WHEN g2.player3_id = u.id THEN g2.final_score3 - 1000
                                   WHEN g2.player4_id = u.id THEN g2.final_score4 - 1000
                                   ELSE 0
                               END
                           ), 0)
                           FROM games g2
                           WHERE (g2.player1_id = u.id OR g2.player2_id = u.id OR 
                                  g2.player3_id = u.id OR g2.player4_id = u.id)
                           AND g2.is_finished = 1
                       ), 0) as manual_adjust,
                       u.net_score as total_score,
                       COUNT(DISTINCT g3.id) as games_played,
                       COUNT(r.id) as rounds_played,
                       COUNT(CASE WHEN r.winner_id = u.id THEN 1 END) as wins
                FROM users u
                LEFT JOIN games g3 ON (g3.player1_id = u.id OR g3.player2_id = u.id OR 
                                       g3.player3_id = u.id OR g3.player4_id = u.id)
                                   AND g3.is_finished = 1
                LEFT JOIN rounds r ON r.game_id = g3.id
                GROUP BY u.id
                ORDER BY total_score DESC
            ''')

        results = c.fetchall()

        if not results:
            print("暂无用户数据")
            conn.close()
            return

        print(f"\n{'排名':^4} | {'用户名':^10} | {'牌局得分':^10} | {'手动调整':^10} | {'总积分':^10} | {'大局数':^6} | {'小局数':^6} | {'胜局数':^6}")
        print("-" * 85)

        for i, row in enumerate(results, 1):
            if season_id:
                uid, name, game_score, manual_adjust, total_score, games, rounds, wins = row
            else:
                uid, name, game_score, manual_adjust, total_score, games, rounds, wins = row

            # 确保所有值都不是None，如果是None则替换为0
            game_score = game_score if game_score is not None else 0
            manual_adjust = manual_adjust if manual_adjust is not None else 0
            total_score = total_score if total_score is not None else 0
            games = games if games is not None else 0
            rounds = rounds if rounds is not None else 0
            wins = wins if wins is not None else 0

            # 计算胜率
            win_rate = (wins / rounds * 100) if rounds > 0 else 0

            # 修复格式化输出 - 使用正确的格式说明符
            # {:10d} 是整数右对齐10位，{:10} 是字符串左对齐10位
            print(f"{i:4d} | {name:10} | {game_score:10d} | {manual_adjust:10d} | {total_score:10d} | {games:6d} | {rounds:6d} | {wins:6d} ({win_rate:.1f}%)")

        # 显示总计
        print("-" * 85)

        # 计算总计时也要处理None值
        total_players = len(results)
        total_game_score = sum(row[2] if row[2] is not None else 0 for row in results)
        total_manual = sum(row[3] if row[3] is not None else 0 for row in results)
        total_all = sum(row[4] if row[4] is not None else 0 for row in results)
        total_games = sum(row[5] if row[5] is not None else 0 for row in results)
        total_rounds = sum(row[6] if row[6] is not None else 0 for row in results)
        total_wins = sum(row[7] if row[7] is not None else 0 for row in results)

        print(f"总计: {total_players}人 | 牌局得分: {total_game_score:+d} | 手动调整: {total_manual:+d} | 总积分: {total_all:+d} | 大局: {total_games} | 小局: {total_rounds} | 胜局: {total_wins}")

        conn.close()

    def user_total_score_detail(self):
        """查看单个用户的总积分明细"""
        print("\n" + "=" * 60)
        print("📊 用户总积分明细")
        print("=" * 60)

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
            uid = int(input("\n请输入用户ID: "))
        except ValueError:
            print("无效输入")
            conn.close()
            return

        # 获取用户基本信息
        c.execute('''
            SELECT username, created_at, net_score
            FROM users WHERE id=?
        ''', (uid,))
        user = c.fetchone()

        if not user:
            print("用户不存在")
            conn.close()
            return

        username, created_at, total_score = user
        total_score = total_score if total_score is not None else 0

        # 计算牌局净胜分
        c.execute('''
            SELECT COALESCE(SUM(
                CASE 
                    WHEN g.player1_id = ? THEN g.final_score1 - 1000
                    WHEN g.player2_id = ? THEN g.final_score2 - 1000
                    WHEN g.player3_id = ? THEN g.final_score3 - 1000
                    WHEN g.player4_id = ? THEN g.final_score4 - 1000
                    ELSE 0
                END
            ), 0) as game_score
            FROM games g
            WHERE (g.player1_id = ? OR g.player2_id = ? OR g.player3_id = ? OR g.player4_id = ?)
            AND g.is_finished = 1
        ''', (uid, uid, uid, uid, uid, uid, uid, uid))

        game_score = c.fetchone()[0]
        game_score = game_score if game_score is not None else 0

        # 手动调整积分 = 总积分 - 牌局得分
        manual_score = total_score - game_score

        print(f"\n=== {username} 的积分明细 ===")
        print(f"注册时间: {created_at}")
        print(f"📊 牌局净胜分: {game_score:+d}")
        print(f"✏️  手动调整分: {manual_score:+d}")
        print(f"{'='*40}")
        print(f"💰 总积分: {total_score:+d}")

        # 显示各大局的得分明细
        print(f"\n📋 各大局得分明细:")
        c.execute('''
            SELECT g.id, g.created_at, g.total_rounds,
                   g.final_score1, g.final_score2, g.final_score3, g.final_score4,
                   u1.username, u2.username, u3.username, u4.username
            FROM games g
            LEFT JOIN users u1 ON g.player1_id = u1.id
            LEFT JOIN users u2 ON g.player2_id = u2.id
            LEFT JOIN users u3 ON g.player3_id = u3.id
            LEFT JOIN users u4 ON g.player4_id = u4.id
            WHERE (g.player1_id = ? OR g.player2_id = ? OR g.player3_id = ? OR g.player4_id = ?)
            AND g.is_finished = 1
            ORDER BY g.created_at DESC
        ''', (uid, uid, uid, uid))

        games = c.fetchall()

        if games:
            for game in games:
                gid, date, rounds, s1, s2, s3, s4, p1, p2, p3, p4 = game

                # 确保分数值不为None
                s1 = s1 if s1 is not None else 1000
                s2 = s2 if s2 is not None else 1000
                s3 = s3 if s3 is not None else 1000
                s4 = s4 if s4 is not None else 1000
                rounds = rounds if rounds is not None else 0

                # 找出该用户的得分
                user_score = None
                if p1 == username:
                    user_score = s1 - 1000
                elif p2 == username:
                    user_score = s2 - 1000
                elif p3 == username:
                    user_score = s3 - 1000
                elif p4 == username:
                    user_score = s4 - 1000

                print(f"\n  大局 #{gid} [{date[:10]}] ({rounds}小局)")
                print(f"    {p1}: {s1}  {p2}: {s2}  {p3}: {s3}  {p4}: {s4}")
                print(f"    该局得分: {user_score:+d}")
        else:
            print("  暂无大局记录")

        # 显示手动调整记录
        try:
            with open('score_adjustments.log', 'r', encoding='utf-8') as f:
                lines = f.readlines()

            user_adjustments = [line for line in lines if username in line]
            if user_adjustments:
                print(f"\n✏️  手动调整记录:")
                for line in user_adjustments[-5:]:  # 显示最近5条
                    print(f"  {line.strip()}")
        except FileNotFoundError:
            pass
        
        conn.close()