# season_manager.py
import sqlite3
from datetime import datetime, timedelta

class SeasonManager:
    def __init__(self):
        self.db_path = 'mahjong.db'
    
    def create_season(self):
        """创建新赛季"""
        print("\n--- 创建新赛季 ---")
        name = input("赛季名称 (如: 2024年春季赛): ").strip()
        if not name:
            print("赛季名称不能为空")
            return
        
        print("\n日期设置:")
        print("1. 使用当前日期范围 (今天起3个月)")
        print("2. 自定义日期范围")
        
        choice = input("请选择 (1/2): ").strip()
        
        if choice == '1':
            start_date = datetime.now().strftime("%Y-%m-%d")
            end_date = (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")
        elif choice == '2':
            start_date = input("开始日期 (YYYY-MM-DD): ").strip()
            end_date = input("结束日期 (YYYY-MM-DD): ").strip()
            
            try:
                datetime.strptime(start_date, "%Y-%m-%d")
                datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                print("日期格式错误，请使用 YYYY-MM-DD 格式")
                return
        else:
            print("无效选择")
            return
        
        description = input("赛季描述 (可选): ").strip()
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute("SELECT id FROM seasons WHERE name=?", (name,))
        if c.fetchone():
            print(f"赛季 '{name}' 已存在")
            conn.close()
            return
        
        c.execute('''
            INSERT INTO seasons (name, start_date, end_date, description)
            VALUES (?, ?, ?, ?)
        ''', (name, start_date, end_date, description))
        
        season_id = c.lastrowid
        conn.commit()
        conn.close()
        
        print(f"✅ 赛季 '{name}' 创建成功！(ID: {season_id})")
    
    def list_seasons(self):
        """列出所有赛季"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            SELECT id, name, start_date, end_date, is_active, description,
                   (SELECT COUNT(*) FROM games WHERE season_id = seasons.id) as game_count
            FROM seasons
            ORDER BY start_date DESC
        ''')
        
        seasons = c.fetchall()
        conn.close()
        
        if not seasons:
            print("暂无赛季")
            return []
        
        print("\n=== 赛季列表 ===")
        print("ID | 赛季名称 | 日期范围 | 状态 | 牌局数 | 描述")
        print("-" * 70)
        
        for season in seasons:
            season_id, name, start, end, is_active, desc, game_count = season
            status = "✅ 当前赛季" if is_active else "  "
            short_name = name[:10] if len(name) > 10 else name
            short_desc = desc[:10] if desc and len(desc) > 10 else (desc or "")
            print(f"{season_id:2d} | {short_name:10} | {start} 至 {end} | {status} | {game_count:3d}局 | {short_desc}")
        
        return seasons
    
    def set_active_season(self):
        """设置当前活跃赛季"""
        seasons = self.list_seasons()
        if not seasons:
            return
        
        try:
            season_id = int(input("\n请输入要设为活跃的赛季ID: "))
        except ValueError:
            print("无效输入")
            return
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute("SELECT name FROM seasons WHERE id=?", (season_id,))
        season = c.fetchone()
        if not season:
            print("赛季不存在")
            conn.close()
            return
        
        c.execute("UPDATE seasons SET is_active = 0")
        c.execute("UPDATE seasons SET is_active = 1 WHERE id=?", (season_id,))
        conn.commit()
        conn.close()
        
        print(f"✅ 赛季 '{season[0]}' 已被设为当前活跃赛季")
    
    def get_active_season(self):
        """获取当前活跃赛季"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            SELECT id, name, start_date, end_date 
            FROM seasons 
            WHERE is_active = 1
            LIMIT 1
        ''')
        
        season = c.fetchone()
        conn.close()
        
        return season
    
    def season_stats(self):
        """查看赛季统计（基于实际牌局计算）"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        seasons = self.list_seasons()
        if not seasons:
            conn.close()
            return

        try:
            season_id = int(input("\n请输入要查看的赛季ID: "))
        except ValueError:
            print("无效输入")
            conn.close()
            return

        c.execute('''
            SELECT name, start_date, end_date 
            FROM seasons WHERE id=?
        ''', (season_id,))
        season_info = c.fetchone()

        if not season_info:
            print("赛季不存在")
            conn.close()
            return

        print(f"\n=== {season_info[0]} 统计 ({season_info[1]} 至 {season_info[2]}) ===")

        # 大局统计
        c.execute('''
            SELECT COUNT(*) FROM games 
            WHERE season_id=? AND is_finished=1
        ''', (season_id,))
        game_count = c.fetchone()[0]
        print(f"总大局数: {game_count}")

        # 小局统计
        c.execute('''
            SELECT COUNT(*) FROM rounds r
            LEFT JOIN games g ON r.game_id = g.id
            WHERE g.season_id=?
        ''', (season_id,))
        round_count = c.fetchone()[0]
        print(f"总小局数: {round_count}")

        if game_count > 0:
            print(f"平均每大局小局数: {round_count/game_count:.1f}")

        # 参与玩家
        c.execute('''
            SELECT DISTINCT u.id, u.username
            FROM users u
            LEFT JOIN games g ON 
                u.id IN (g.player1_id, g.player2_id, g.player3_id, g.player4_id)
            WHERE g.season_id=?
            ORDER BY u.username
        ''', (season_id,))
        players = c.fetchall()
        print(f"参与玩家: {len(players)} 人")

        # 赛季排行榜（按净胜分）
        print("\n🏆 赛季排行榜 (净胜分):")

        player_stats = []
        for player_id, player_name in players:
            # 计算净胜分
            c.execute('''
                SELECT 
                    SUM(CASE 
                        WHEN g.player1_id = ? THEN g.final_score1 - 1000
                        WHEN g.player2_id = ? THEN g.final_score2 - 1000
                        WHEN g.player3_id = ? THEN g.final_score3 - 1000
                        WHEN g.player4_id = ? THEN g.final_score4 - 1000
                        ELSE 0
                    END) as score_change
                FROM games g
                WHERE g.season_id=? AND g.is_finished=1
                AND (? IN (g.player1_id, g.player2_id, g.player3_id, g.player4_id))
            ''', (player_id, player_id, player_id, player_id, season_id, player_id))

            total_change = c.fetchone()[0]
            if total_change is None:
                total_change = 0

            # 计算胡牌次数
            c.execute('''
                SELECT COUNT(*) FROM rounds r
                LEFT JOIN games g ON r.game_id = g.id
                WHERE g.season_id=? AND r.winner_id=?
            ''', (season_id, player_id))
            wins = c.fetchone()[0]

            # 计算参与小局数
            c.execute('''
                SELECT COUNT(*) FROM rounds r
                LEFT JOIN games g ON r.game_id = g.id
                WHERE g.season_id=?
                AND (g.player1_id=? OR g.player2_id=? OR g.player3_id=? OR g.player4_id=?)
            ''', (season_id, player_id, player_id, player_id, player_id))
            rounds_played = c.fetchone()[0]

            player_stats.append((player_name, total_change, wins, rounds_played))

        # 按净胜分排序
        player_stats.sort(key=lambda x: x[1], reverse=True)

        for i, (name, score, wins, rounds) in enumerate(player_stats, 1):
            win_rate = wins/rounds*100 if rounds > 0 else 0
            print(f"{i:2d}. {name:10} | 净胜分: {score:+5d} | 胜局: {wins} | 参与小局: {rounds} | 胜率: {win_rate:.1f}%")

        # 显示赛季最佳
        if player_stats:
            best_player = max(player_stats, key=lambda x: x[1])
            print(f"\n✨ 赛季 MVP: {best_player[0]} (净胜分 {best_player[1]:+d})")

            most_wins = max(player_stats, key=lambda x: x[2])
            print(f"🏅 胡牌王: {most_wins[0]} ({most_wins[2]}胜)")

        conn.close()