# query_manager.py
import sqlite3

class QueryManager:
    def __init__(self):
        self.db_path = 'mahjong.db'
    
    def get_season_filter(self):
        """获取用户选择的赛季ID，返回 (season_id, season_name) 或 (None, None)"""
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
                    print("无效选择，使用所有赛季")
                    return None, None
            except ValueError:
                print("无效输入，使用所有赛季")
                return None, None
        except:
            return None, None
    
    def user_stats(self):
        """查看单个用户战绩（可筛选赛季）"""
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
        
        # 获取用户信息
        c.execute('''
            SELECT username, created_at 
            FROM users WHERE id=?
        ''', (uid,))
        user = c.fetchone()
        
        if not user:
            print("用户不存在")
            conn.close()
            return
        
        print(f"\n=== {user[0]} 的战绩 {f'({season_name})' if season_name else ''} ===")
        print(f"注册时间: {user[1]}")
        
        # 查询总局数
        if season_id:
            c.execute('''
                SELECT COUNT(*) FROM games 
                WHERE (player1_id=? OR player2_id=? OR player3_id=? OR player4_id=?)
                AND season_id=? AND is_finished=1
            ''', (uid, uid, uid, uid, season_id))
        else:
            c.execute('''
                SELECT COUNT(*) FROM games 
                WHERE (player1_id=? OR player2_id=? OR player3_id=? OR player4_id=?)
                AND is_finished=1
            ''', (uid, uid, uid, uid))
        total_games = c.fetchone()[0]
        
        # 查询胜局数
        if season_id:
            c.execute('''
                SELECT COUNT(*) FROM actions a
                JOIN games g ON a.game_id = g.id
                WHERE a.action_type='hupai' AND a.player_id=?
                AND g.season_id=? AND g.is_finished=1
            ''', (uid, season_id))
        else:
            c.execute('''
                SELECT COUNT(*) FROM actions a
                JOIN games g ON a.game_id = g.id
                WHERE a.action_type='hupai' AND a.player_id=?
                AND g.is_finished=1
            ''', (uid,))
        total_wins = c.fetchone()[0]
        
        # 计算净胜分
        if season_id:
            c.execute('''
                SELECT 
                    SUM(CASE 
                        WHEN player1_id = ? THEN score1 - 1000
                        WHEN player2_id = ? THEN score2 - 1000
                        WHEN player3_id = ? THEN score3 - 1000
                        WHEN player4_id = ? THEN score4 - 1000
                        ELSE 0
                    END) as net_score
                FROM games
                WHERE (player1_id=? OR player2_id=? OR player3_id=? OR player4_id=?)
                AND season_id=? AND is_finished=1
            ''', (uid, uid, uid, uid, uid, uid, uid, uid, season_id))
        else:
            c.execute('''
                SELECT 
                    SUM(CASE 
                        WHEN player1_id = ? THEN score1 - 1000
                        WHEN player2_id = ? THEN score2 - 1000
                        WHEN player3_id = ? THEN score3 - 1000
                        WHEN player4_id = ? THEN score4 - 1000
                        ELSE 0
                    END) as net_score
                FROM games
                WHERE (player1_id=? OR player2_id=? OR player3_id=? OR player4_id=?)
                AND is_finished=1
            ''', (uid, uid, uid, uid, uid, uid, uid, uid))
        
        net_score = c.fetchone()[0]
        if net_score is None:
            net_score = 0
        
        print(f"总参与局数: {total_games}")
        print(f"总胡牌次数: {total_wins}")
        if total_games > 0:
            print(f"胜率: {total_wins/total_games*100:.1f}%")
        print(f"净胜分: {net_score:+d}")
        
        # 查询最近5局记录
        if season_id:
            c.execute('''
                SELECT g.id, g.created_at, 
                       u1.username, u2.username, u3.username, u4.username,
                       g.score1, g.score2, g.score3, g.score4
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
                SELECT g.id, g.created_at, 
                       u1.username, u2.username, u3.username, u4.username,
                       g.score1, g.score2, g.score3, g.score4
                FROM games g
                JOIN users u1 ON g.player1_id = u1.id
                JOIN users u2 ON g.player2_id = u2.id
                JOIN users u3 ON g.player3_id = u3.id
                JOIN users u4 ON g.player4_id = u4.id
                WHERE ? IN (g.player1_id, g.player2_id, g.player3_id, g.player4_id)
                AND g.is_finished=1
                ORDER BY g.created_at DESC LIMIT 5
            ''', (uid,))
        
        recent = c.fetchall()
        if recent:
            print("\n最近5局成绩:")
            for game in recent:
                print(f"  牌局{game[0]}: {game[2][:4]}{game[6]} {game[3][:4]}{game[7]} {game[4][:4]}{game[8]} {game[5][:4]}{game[9]}")
        else:
            print("\n暂无历史牌局记录")
        
        conn.close()
    
    def global_stats(self):
        """全局统计"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # 总牌局数
        c.execute("SELECT COUNT(*) FROM games WHERE is_finished=1")
        total_games = c.fetchone()[0]
        
        # 总操作数
        c.execute("SELECT COUNT(*) FROM actions")
        total_actions = c.fetchone()[0]
        
        # 杠总数
        c.execute("SELECT COUNT(*) FROM actions WHERE action_type='baiban'")
        total_baiban = c.fetchone()[0]
        
        # 胡牌总数
        c.execute("SELECT COUNT(*) FROM actions WHERE action_type='hupai'")
        total_hupai = c.fetchone()[0]
        
        print("\n=== 全局统计 ===")
        print(f"总牌局数: {total_games}")
        print(f"总操作记录: {total_actions}")
        print(f"杠总数: {total_baiban}")
        print(f"胡牌总数: {total_hupai}")
        
        # 赢家排行榜
        c.execute('''
            SELECT username, total_wins, net_score
            FROM users
            WHERE total_wins > 0
            ORDER BY total_wins DESC LIMIT 5
        ''')
        top_winners = c.fetchall()
        
        if top_winners:
            print("\n🏆 赢家榜 (胜局数):")
            for i, (name, wins, score) in enumerate(top_winners, 1):
                print(f"  {i}. {name} - {wins}胜 (净胜分:{score:+d})")
        
        # 净胜分排行榜
        c.execute('''
            SELECT username, net_score
            FROM users
            ORDER BY net_score DESC LIMIT 5
        ''')
        top_scores = c.fetchall()
        
        if top_scores:
            print("\n💰 富豪榜 (净胜分):")
            for i, (name, score) in enumerate(top_scores, 1):
                print(f"  {i}. {name} - {score:+d}分")
        
        conn.close()
    
    def recent_games(self):
        """查看最近牌局"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            SELECT g.id, g.created_at, 
                   u1.username, u2.username, u3.username, u4.username,
                   g.score1, g.score2, g.score3, g.score4,
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
            print("暂无牌局记录")
            conn.close()
            return
        
        print("\n=== 最近10局牌局 ===")
        for game in games:
            status = "✅" if game[10] else "⏳"
            print(f"\n牌局 #{game[0]} {status} ({game[1][:16]})")
            print(f"  {game[2]}: {game[6]}")
            print(f"  {game[3]}: {game[7]}")
            print(f"  {game[4]}: {game[8]}")
            print(f"  {game[5]}: {game[9]}")
        
        conn.close()

    def big_game_stats(self):
        """查看大局统计"""
        from big_game_manager import BigGameManager
        bgm = BigGameManager()
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # 列出最近的大局
        c.execute('''
            SELECT id, created_at, round_count, is_finished
            FROM big_games
            ORDER BY id DESC LIMIT 10
        ''')
        
        big_games = c.fetchall()
        
        if not big_games:
            print("暂无大局记录")
            conn.close()
            return
        
        print("\n=== 最近大局 ===")
        for bg in big_games:
            status = "✅" if bg[3] else "⏳"
            print(f"  #{bg[0]} {status} ({bg[1][:16]}) - {bg[2]}小局")
        
        try:
            bg_id = int(input("\n请输入要查看的大局ID: "))
            bgm.get_big_game_stats(bg_id)
        except ValueError:
            print("无效输入")
        
        conn.close()