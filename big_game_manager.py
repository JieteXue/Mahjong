# big_game_manager.py
import sqlite3
import json
from datetime import datetime

class BigGame:
    def __init__(self, big_game_id, players, start_scores):
        self.id = big_game_id
        self.players = players  # [(id, name), ...]
        self.start_scores = start_scores
        self.current_scores = start_scores.copy()
        self.round_count = 0
        self.small_games = []  # 存储小局ID
        self.is_finished = False
        self.conn = sqlite3.connect('mahjong.db')
    
    def add_small_game(self, game_id):
        """添加小局"""
        self.small_games.append(game_id)
        self.round_count += 1
    
    def update_scores(self, new_scores):
        """更新当前分数"""
        self.current_scores = new_scores.copy()
    
    def end_big_game(self):
        """结束大局"""
        self.is_finished = True
        try:
            c = self.conn.cursor()
            
            # 更新大局表
            c.execute('''
                UPDATE big_games SET 
                    end_scores = ?,
                    round_count = ?,
                    is_finished = 1
                WHERE id = ?
            ''', (
                json.dumps(self.current_scores, ensure_ascii=False),
                self.round_count,
                self.id
            ))
            
            self.conn.commit()
            print(f"\n✅ 大局 #{self.id} 结束，共进行 {self.round_count} 小局")
            
        except Exception as e:
            print(f"❌ 结束大局时出错: {e}")
        finally:
            self.conn.close()
    
    def show_status(self):
        """显示大局状态"""
        print(f"\n=== 大局 #{self.id} ===")
        print(f"已进行小局数: {self.round_count}")
        print("当前分数:")
        for i, (pid, name) in enumerate(self.players):
            change = self.current_scores[i] - self.start_scores[i]
            print(f"  {name}: {self.current_scores[i]} 分 ({change:+d})")


class BigGameManager:
    def __init__(self):
        self.db_path = 'mahjong.db'
    
    def create_big_game(self, selected_users, season_id=None):
        """创建新大局"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # 初始分数都是1000
        start_scores = [1000, 1000, 1000, 1000]
        
        c.execute('''
            INSERT INTO big_games 
            (season_id, player1_id, player2_id, player3_id, player4_id, start_scores)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            season_id,
            selected_users[0][0], selected_users[1][0],
            selected_users[2][0], selected_users[3][0],
            json.dumps(start_scores, ensure_ascii=False)
        ))
        
        big_game_id = c.lastrowid
        conn.commit()
        conn.close()
        
        print(f"\n🎮 创建新大局 #{big_game_id}")
        
        return BigGame(
            big_game_id=big_game_id,
            players=selected_users,
            start_scores=start_scores
        )
    
    def update_small_game_big_game(self, game_id, big_game_id, round_number):
        """更新小局关联的大局ID"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            UPDATE games SET big_game_id=?, round_number=? WHERE id=?
        ''', (big_game_id, round_number, game_id))
        conn.commit()
        conn.close()
    
    def get_big_game_stats(self, big_game_id):
        """获取大局统计"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            SELECT id, created_at, player1_id, player2_id, player3_id, player4_id,
                   start_scores, end_scores, round_count, is_finished
            FROM big_games WHERE id=?
        ''', (big_game_id,))
        
        big_game = c.fetchone()
        if not big_game:
            print("大局不存在")
            conn.close()
            return
        
        print(f"\n=== 大局 #{big_game[0]} 统计 ===")
        print(f"创建时间: {big_game[1]}")
        print(f"小局数量: {big_game[8]}")
        print(f"状态: {'已完成' if big_game[9] else '进行中'}")
        
        # 获取玩家信息
        player_ids = [big_game[2], big_game[3], big_game[4], big_game[5]]
        players = []
        for pid in player_ids:
            c.execute("SELECT username FROM users WHERE id=?", (pid,))
            players.append(c.fetchone()[0])
        
        start_scores = json.loads(big_game[6])
        print("\n初始分数:")
        for i, name in enumerate(players):
            print(f"  {name}: {start_scores[i]}")
        
        if big_game[7]:
            end_scores = json.loads(big_game[7])
            print("\n最终分数:")
            for i, name in enumerate(players):
                change = end_scores[i] - start_scores[i]
                print(f"  {name}: {end_scores[i]} 分 ({change:+d})")
        
        # 查询所有小局
        c.execute('''
            SELECT id, round_number, created_at, score1, score2, score3, score4
            FROM games
            WHERE big_game_id=?
            ORDER BY round_number
        ''', (big_game_id,))
        
        small_games = c.fetchall()
        if small_games:
            print("\n小局记录:")
            for sg in small_games:
                print(f"  第{sg[1]}局 ({sg[2][:16]}): {sg[3]} {sg[4]} {sg[5]} {sg[6]}")
        
        conn.close()