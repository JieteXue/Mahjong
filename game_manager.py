# game_manager.py
import sqlite3
import random
import json
from datetime import datetime

class Game:
    def __init__(self, game_id, players, scores, dealer_id, lianzhuang, bao):
        self.id = game_id
        self.players = players  # [(id, name), ...]
        self.scores = scores    # [score1, score2, score3, score4]
        self.dealer_id = dealer_id
        self.dealer_idx = [p[0] for p in players].index(dealer_id)
        self.lianzhuang = lianzhuang
        self.bao = bao
        self.is_finished = False
        self.conn = sqlite3.connect('mahjong.db')
    
    def show_status(self):
        """显示当前牌局状态"""
        print(f"庄家: {self.players[self.dealer_idx][1]} (连庄 {self.lianzhuang})")
        print("\n当前分数:")
        for i, (pid, name) in enumerate(self.players):
            print(f"  {name}: {self.scores[i]} 分")
    
    def baiban_input(self):
        """处理白板杠输入 - 支持多张白板"""
        print("\n谁杠？")
        for i, (_, name) in enumerate(self.players):
            print(f"{i+1}. {name}")
        
        try:
            choice = int(input("请选择玩家(1-4): ")) - 1
            if not (0 <= choice < 4):
                print("无效选择")
                return
            
            # 询问杠几张白板
            print("\n杠几张？")
            print("1. 杠1张")
            print("2. 杠2张")
            print("3. 杠3张")
            print("4. 杠4张")
            
            gang_count = int(input("请选择(1-4): "))
            if gang_count not in [1, 2, 3, 4]:
                print("无效选择")
                return
            
            self.baiban(choice, gang_count)
            
        except ValueError:
            print("请输入数字")
        except Exception as e:
            print(f"发生错误: {e}")
    
    def baiban(self, player_idx, count=1):
        """执行白板杠结算 - 支持多张白板"""
        changes = [0, 0, 0, 0]
        changes[player_idx] = 3 * count
        for i in range(4):
            if i != player_idx:
                changes[i] = -1 * count
        
        # 更新分数
        for i in range(4):
            self.scores[i] += changes[i]
        
        # 记录操作
        self.record_action('baiban', self.players[player_idx][0], changes, {'count': count})
        
        print(f"\n✅ {self.players[player_idx][1]} 杠 {count} 张白板")
        print(f"   +{3*count} 分")
        for i in range(4):
            if i != player_idx:
                print(f"   {self.players[i][1]}: -{count} 分")
        
        print("\n更新后分数:")
        for i, (pid, name) in enumerate(self.players):
            print(f"  {name}: {self.scores[i]} 分")
    
    def hupai_input(self):
        """处理胡牌输入"""
        print("\n谁胡牌了？")
        for i, (_, name) in enumerate(self.players):
            print(f"{i+1}. {name}")
        
        try:
            winner = int(input("请选择(1-4): ")) - 1
            if not (0 <= winner < 4):
                print("无效选择")
                return
            
            tai = int(input("请输入总台数: "))
            self.hupai(winner, tai)
        except ValueError:
            print("请输入有效数字")
    
    def hupai(self, winner_idx, tai):
        """执行胡牌结算"""
        changes = [0, 0, 0, 0]
        winner_id = self.players[winner_idx][0]
        
        if winner_id == self.dealer_id:
            # 庄家胡
            base = tai + 2 + self.lianzhuang * 2
            changes[winner_idx] = base * 3
            for i in range(4):
                if i != winner_idx:
                    changes[i] = -base
            
            self.lianzhuang += 1
            print(f"\n✅ 庄家 {self.players[winner_idx][1]} 胡牌 {tai}台")
            print(f"每人付 {base}条")
        else:
            # 闲家胡
            zhuang_pay = tai + 2 + self.lianzhuang * 2
            xian_pay = tai + 1
            
            for i in range(4):
                if i == winner_idx:
                    continue
                if self.players[i][0] == self.dealer_id:
                    changes[i] = -zhuang_pay
                    changes[winner_idx] += zhuang_pay
                else:
                    changes[i] = -xian_pay
                    changes[winner_idx] += xian_pay
            
            print(f"\n✅ {self.players[winner_idx][1]} 胡牌 {tai}台")
            print(f"庄家 {self.players[self.dealer_idx][1]} 付 {zhuang_pay}条")
            print(f"其他闲家付 {xian_pay}条")
            
            # 更新庄家
            self.dealer_id = winner_id
            self.dealer_idx = winner_idx
            self.lianzhuang = 0
        
        # 更新分数
        for i in range(4):
            self.scores[i] += changes[i]
        
        # 显示更新后的分数
        print("\n更新后分数:")
        for i, (pid, name) in enumerate(self.players):
            print(f"  {name}: {self.scores[i]} 分")
        
        self.record_action('hupai', winner_id, changes, {'tai': tai})
        
        # 询问是否继续
        cont = input("\n是否继续下一局？(y/n): ").lower()
        if cont != 'y':
            self.is_finished = True
    
    def liuju(self):
        """流局处理"""
        self.record_action('liuju', None, [0,0,0,0])
        print("流局")
        self.is_finished = True
    
    def emergency_adjust(self):
        """牌局中紧急调分"""
        print("\n--- 紧急调分 ---")
        print("当前分数:")
        for i, (_, name) in enumerate(self.players):
            print(f"{i+1}. {name}: {self.scores[i]}")
        
        try:
            idx = int(input("请选择要调整的玩家 (1-4): ")) - 1
            if not (0 <= idx < 4):
                print("无效选择")
                return
            
            new_score = int(input(f"请输入 {self.players[idx][1]} 的新分数: "))
            old_score = self.scores[idx]
            
            print(f"{self.players[idx][1]}: {old_score} -> {new_score}")
            confirm = input("确认调整？(y/n): ").lower()
            
            if confirm == 'y':
                self.scores[idx] = new_score
                changes = [0, 0, 0, 0]
                changes[idx] = new_score - old_score
                self.record_action('emergency_adjust', self.players[idx][0], changes)
                print("分数已更新")
            else:
                print("已取消")
                
        except ValueError:
            print("请输入有效数字")
    
    def record_action(self, action_type, player_id, changes, detail=None):
        """记录操作到数据库"""
        try:
            c = self.conn.cursor()
            c.execute('''
                INSERT INTO actions (game_id, action_type, player_id, score_changes, tai_detail, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                self.id,
                action_type,
                player_id,
                json.dumps(changes, ensure_ascii=False),
                json.dumps(detail, ensure_ascii=False) if detail else None,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            self.conn.commit()
        except Exception as e:
            print(f"记录操作时出错: {e}")
    
    def end_game(self):
        """结束牌局 - 只保存数据，不关闭连接"""
        self.is_finished = True
        try:
            c = self.conn.cursor()

            print(f"\n💾 保存牌局 #{self.id} 最终分数:")
            for i, (pid, name) in enumerate(self.players):
                print(f"  {name}: {self.scores[i]}")

            # 更新游戏状态和分数
            c.execute("UPDATE games SET is_finished=1 WHERE id=?", (self.id,))
            c.execute('''
                UPDATE games SET 
                    score1=?, score2=?, score3=?, score4=?, 
                    dealer_id=?, lianzhuang=? 
                WHERE id=?
            ''', (
                self.scores[0], self.scores[1], self.scores[2], self.scores[3],
                self.dealer_id, self.lianzhuang, self.id
            ))

            self.conn.commit()
            print("✅ 牌局数据已保存到数据库")

        except Exception as e:
            print(f"❌ 结束牌局时出错: {e}")
            self.conn.rollback()

    def close_connection(self):
        """关闭数据库连接"""
        try:
            self.conn.close()
            print("✅ 游戏数据库连接已关闭")
        except Exception as e:
            print(f"关闭连接时出错: {e}")


class GameManager:
    def __init__(self):
        self.db_path = 'mahjong.db'
    
    def generate_bao(self):
        """随机生成财神（内部使用）"""
        suits = ['万', '筒', '条']
        numbers = ['一', '二', '三', '四', '五', '六', '七', '八', '九']
        
        suit = random.choice(suits)
        number = random.choice(numbers)
        
        if random.random() < 0.1:
            honors = ['东风', '南风', '西风', '北风', '红中', '发财', '白板']
            return random.choice(honors)
        
        return f"{number}{suit}"
    
    def create_game(self, selected_users):
        """创建新游戏"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # 获取当前活跃赛季
        try:
            from season_manager import SeasonManager
            season_mgr = SeasonManager()
            active_season = season_mgr.get_active_season()
            
            season_id = None
            if active_season:
                season_id = active_season[0]
                print(f"当前赛季: {active_season[1]}")
        except:
            season_id = None
            print("⚠️ 赛季功能未启用")
        
        # 随机生成财神
        bao = self.generate_bao()
        
        dealer_id = selected_users[0][0]
        
        # 检查games表是否有season_id列
        c.execute("PRAGMA table_info(games)")
        columns = [col[1] for col in c.fetchall()]
        
        if 'season_id' in columns:
            c.execute('''
                INSERT INTO games 
                (player1_id, player2_id, player3_id, player4_id, dealer_id, bao, season_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                selected_users[0][0], selected_users[1][0],
                selected_users[2][0], selected_users[3][0],
                dealer_id, bao, season_id
            ))
        else:
            c.execute('''
                INSERT INTO games 
                (player1_id, player2_id, player3_id, player4_id, dealer_id, bao)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                selected_users[0][0], selected_users[1][0],
                selected_users[2][0], selected_users[3][0],
                dealer_id, bao
            ))
        
        game_id = c.lastrowid
        conn.commit()
        conn.close()
        
        return Game(
            game_id=game_id,
            players=selected_users,
            scores=[1000, 1000, 1000, 1000],
            dealer_id=dealer_id,
            lianzhuang=0,
            bao=bao
        )
    
    def update_user_stats(self, game):
        """游戏结束后更新用户统计 - 使用独立连接"""
        print("\n📊 正在更新用户统计...")
        
        # 使用独立的数据库连接
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # 获取游戏结束时的最终分数
            final_scores = game.scores
            print(f"最终分数: {final_scores}")
            
            for i, (pid, name) in enumerate(game.players):
                # 计算该玩家的净胜分变化（最终分数 - 初始分数1000）
                score_change = final_scores[i] - 1000
                
                # 查询该玩家在本局中是否有胡牌操作
                c.execute('''
                    SELECT COUNT(*) FROM actions 
                    WHERE game_id=? AND action_type='hupai' AND player_id=?
                ''', (game.id, pid))
                has_win = c.fetchone()[0] > 0
                
                print(f"玩家 {name}: 分数变化 {score_change:+d}, 是否胡牌: {has_win}")
                
                # 更新用户统计
                c.execute('''
                    UPDATE users SET 
                        total_games = total_games + 1,
                        total_wins = total_wins + ?,
                        net_score = net_score + ?
                    WHERE id = ?
                ''', (1 if has_win else 0, score_change, pid))
            
            conn.commit()
            
            # 验证更新是否成功
            c.execute("SELECT id, username, total_games, total_wins, net_score FROM users")
            updated_users = c.fetchall()
            print("\n✅ 更新后的用户统计:")
            for user in updated_users:
                print(f"  {user[1]}: {user[2]}局 {user[3]}胜 净胜分:{user[4]:+d}")
                
        except Exception as e:
            print(f"❌ 更新用户统计时出错: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()