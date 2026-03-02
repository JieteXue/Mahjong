# game_manager.py (更新版)
import sqlite3
import random
import json
from datetime import datetime

class Round:
    """小局类"""
    def __init__(self, game, round_number, dealer_id, dealer_idx, lianzhuang):
        self.game = game
        self.round_number = round_number
        self.dealer_id = dealer_id
        self.dealer_idx = dealer_idx
        self.lianzhuang = lianzhuang
        self.winner_id = None
        self.tai = 0
        self.baiban_records = []  # [(player_idx, count), ...]
        self.initial_scores = game.scores.copy()
        
    def add_baiban(self, player_idx, count):
        """添加白板杠记录"""
        self.baiban_records.append((player_idx, count))
        
    def finish(self, winner_idx=None, tai=0):
        """结束小局"""
        self.winner_id = self.game.players[winner_idx][0] if winner_idx is not None else None
        self.tai = tai
        self.final_scores = self.game.scores.copy()
        
    def get_score_changes(self):
        """获取本局分数变化"""
        return [self.game.scores[i] - self.initial_scores[i] for i in range(4)]


class Game:
    def __init__(self, game_id, players, scores, bao):
        self.id = game_id
        self.players = players  # [(id, name), ...]
        self.scores = scores    # [score1, score2, score3, score4]
        self.bao = bao
        self.is_finished = False
        
        # 庄家相关（初始随机选择第一个玩家为庄家）
        self.dealer_id = players[0][0]
        self.dealer_idx = 0
        self.lianzhuang = 0
        
        # 小局记录
        self.rounds = []
        self.current_round = None
        self.round_counter = 0
        
        self.conn = sqlite3.connect('mahjong.db')
        
        # 初始化游戏记录中的总小局数
        self._update_game_total_rounds()
    
    def _update_game_total_rounds(self):
        """更新游戏表中的总小局数"""
        try:
            c = self.conn.cursor()
            c.execute('''
                UPDATE games SET total_rounds = ? WHERE id = ?
            ''', (len(self.rounds), self.id))
            self.conn.commit()
        except Exception as e:
            print(f"更新小局数时出错: {e}")
    
    def start_new_round(self):
        """开始新的一局"""
        self.round_counter += 1
        self.current_round = Round(
            game=self,
            round_number=self.round_counter,
            dealer_id=self.dealer_id,
            dealer_idx=self.dealer_idx,
            lianzhuang=self.lianzhuang
        )
        print(f"\n=== 开始第 {self.round_counter} 小局 ===")
        print(f"庄家: {self.players[self.dealer_idx][1]} (连庄 {self.lianzhuang})")
        return self.current_round
    
    def show_status(self):
        """显示当前牌局状态"""
        print(f"当前小局: {self.round_counter + 1 if self.current_round else 1}")
        print(f"庄家: {self.players[self.dealer_idx][1]} (连庄 {self.lianzhuang})")
        print(f"财神: {self.bao}")
        print("\n当前分数:")
        for i, (pid, name) in enumerate(self.players):
            print(f"  {name}: {self.scores[i]} 分")
    
    def baiban_input(self):
        """处理白板杠输入"""
        if not self.current_round:
            self.start_new_round()
            
        print("\n谁杠白板？")
        for i, (_, name) in enumerate(self.players):
            print(f"{i+1}. {name}")
        
        try:
            choice = int(input("请选择玩家(1-4): ")) - 1
            if not (0 <= choice < 4):
                print("无效选择")
                return
            
            print("\n杠几张？")
            print("1. 杠1张")
            print("2. 杠2张")
            print("3. 杠3张")
            print("4. 杠4张")
            
            gang_count = int(input("请选择(1-4): "))
            if gang_count not in [1, 2, 3, 4]:
                print("无效选择")
                return
            
            self._baiban(choice, gang_count)
            
        except ValueError:
            print("请输入数字")
    
    def _baiban(self, player_idx, count):
        """执行白板杠结算"""
        changes = [0, 0, 0, 0]
        changes[player_idx] = 3 * count
        for i in range(4):
            if i != player_idx:
                changes[i] = -1 * count
        
        # 更新分数
        for i in range(4):
            self.scores[i] += changes[i]
        
        # 记录到当前小局
        if self.current_round:
            self.current_round.add_baiban(player_idx, count)
        
        # 记录操作
        self.record_action('baiban', self.players[player_idx][0], changes, {'count': count})
        
        print(f"\n✅ {self.players[player_idx][1]} 杠 {count} 张白板")
        print(f"   +{3*count} 分")
        for i in range(4):
            if i != player_idx:
                print(f"   {self.players[i][1]}: -{count} 分")
    
    def hupai_input(self):
        """处理胡牌输入"""
        if not self.current_round:
            self.start_new_round()
            
        print("\n谁胡牌了？")
        for i, (_, name) in enumerate(self.players):
            print(f"{i+1}. {name}")
        
        try:
            winner = int(input("请选择(1-4): ")) - 1
            if not (0 <= winner < 4):
                print("无效选择")
                return
            
            tai = int(input("请输入总台数: "))
            self._hupai(winner, tai)
        except ValueError:
            print("请输入有效数字")
    
    def _hupai(self, winner_idx, tai):
        """执行胡牌结算"""
        changes = [0, 0, 0, 0]
        winner_id = self.players[winner_idx][0]
        
        # 记录本局开始时的分数
        round_start_scores = self.scores.copy()
        
        if winner_id == self.dealer_id:
            # 庄家胡
            base = tai + 2 + self.lianzhuang * 2
            changes[winner_idx] = base * 3
            for i in range(4):
                if i != winner_idx:
                    changes[i] = -base
            
            print(f"\n✅ 庄家 {self.players[winner_idx][1]} 胡牌 {tai}台")
            print(f"每人付 {base}条")
            
            # 庄家连庄
            self.lianzhuang += 1
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
            
            # 换庄
            self.dealer_id = winner_id
            self.dealer_idx = winner_idx
            self.lianzhuang = 0
        
        # 更新分数
        for i in range(4):
            self.scores[i] += changes[i]
        
        # 结束当前小局
        self.current_round.finish(winner_idx, tai)
        self.rounds.append(self.current_round)
        
        # 保存小局到数据库
        self._save_round_to_db(self.current_round, round_start_scores)
        
        # 显示更新后的分数
        print("\n更新后分数:")
        for i, (pid, name) in enumerate(self.players):
            print(f"  {name}: {self.scores[i]} 分")
        
        self.record_action('hupai', winner_id, changes, {'tai': tai, 'round': self.round_counter})
        
        # 询问是否继续下一局
        cont = input("\n是否继续下一局？(y/n): ").lower()
        if cont == 'y':
            self.start_new_round()
        else:
            # 不继续下一局，询问是否结束整场游戏
            end_game = input("是否结束整场游戏？(y/n): ").lower()
            if end_game == 'y':
                self.is_finished = True
            else:
                # 如果不结束游戏，可以继续新的一局
                self.start_new_round()
    
    def _save_round_to_db(self, round_obj, start_scores):
        """保存小局到数据库"""
        try:
            c = self.conn.cursor()

            # 计算分数变化
            changes = round_obj.get_score_changes()

            # 插入小局记录
            c.execute('''
                INSERT INTO rounds (
                    game_id, round_number, dealer_id, winner_id, tai, lianzhuang,
                    score1, score2, score3, score4,
                    score_change1, score_change2, score_change3, score_change4
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.id, round_obj.round_number,
                round_obj.dealer_id,
                round_obj.winner_id,
                round_obj.tai,
                round_obj.lianzhuang,
                self.scores[0], self.scores[1], self.scores[2], self.scores[3],
                changes[0], changes[1], changes[2], changes[3]
            ))

            round_db_id = c.lastrowid

            # 更新刚插入的actions记录，设置round_id
            c.execute('''
                UPDATE actions SET round_id = ?
                WHERE game_id = ? AND round_id IS NULL
            ''', (round_db_id, self.id))

            # 保存白板杠记录
            for player_idx, count in round_obj.baiban_records:
                c.execute('''
                    INSERT INTO baiban_records (round_id, player_id, count)
                    VALUES (?, ?, ?)
                ''', (round_db_id, self.players[player_idx][0], count))

            self.conn.commit()

            # 更新游戏表中的总小局数
            self._update_game_total_rounds()

            print(f"✅ 第 {round_obj.round_number} 小局已保存到数据库")

        except Exception as e:
            print(f"保存小局时出错: {e}")
            self.conn.rollback()
    
    def liuju(self):
        """流局处理"""
        if not self.current_round:
            self.start_new_round()
        
        # 记录流局
        self.current_round.finish(None, 0)
        self.rounds.append(self.current_round)
        
        # 保存流局到数据库
        self._save_round_to_db(self.current_round, self.scores.copy())
        
        self.record_action('liuju', None, [0,0,0,0])
        print("流局")
        
        # 询问是否继续
        cont = input("\n是否继续下一局？(y/n): ").lower()
        if cont == 'y':
            self.start_new_round()
        else:
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

            # 获取当前round_id
            round_id = None
            if self.current_round:
                # 需要先获取刚插入的round记录的ID
                c.execute('''
                    SELECT id FROM rounds 
                    WHERE game_id = ? AND round_number = ?
                    ORDER BY created_at DESC LIMIT 1
                ''', (self.id, self.current_round.round_number))
                result = c.fetchone()
                if result:
                    round_id = result[0]

            c.execute('''
                INSERT INTO actions (game_id, round_id, action_type, player_id, score_changes, tai_detail, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.id,
                round_id,
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
        """结束整场游戏（大局）"""
        self.is_finished = True

        # 如果有未结束的小局，先结束它
        if self.current_round and self.current_round not in self.rounds:
            self.current_round.finish()
            self.rounds.append(self.current_round)
            self._save_round_to_db(self.current_round, self.current_round.initial_scores)

        try:
            c = self.conn.cursor()

            finished_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            print(f"\n💾 保存大局 #{self.id} 最终分数:")
            for i, (pid, name) in enumerate(self.players):
                print(f"  {name}: {self.scores[i]} 分")
            print(f"总小局数: {len(self.rounds)}")

            # 更新游戏状态和分数 - 使用 final_score 列名
            c.execute('''
                UPDATE games SET 
                    is_finished=1,
                    finished_at=?,
                    final_score1=?, final_score2=?, final_score3=?, final_score4=?,
                    total_rounds=?
                WHERE id=?
            ''', (
                finished_at,
                self.scores[0], self.scores[1], self.scores[2], self.scores[3],
                len(self.rounds), self.id
            ))

            self.conn.commit()
            print("✅ 大局数据已保存到数据库")

        except Exception as e:
            print(f"❌ 结束游戏时出错: {e}")
            self.conn.rollback()
    
    def close_connection(self):
        """关闭数据库连接"""
        try:
            self.conn.close()
            print("✅ 游戏数据库连接已关闭")
        except Exception as e:
            print(f"关闭连接时出错: {e}")
    
    def quick_settlement(self):
        """快捷结算：先统计各家杠数量，再统一胡牌结算"""
        if not self.current_round:
            self.start_new_round()
        
        print("\n" + "=" * 50)
        print("🎯 快捷结算模式")
        print("=" * 50)
        print("请依次输入各家白板杠数量")
        print("（输入0表示没有杠，可以多次输入多张杠）")
        
        # 统计各家杠数量
        gang_counts = [0, 0, 0, 0]
        
        for i, (pid, name) in enumerate(self.players):
            print(f"\n--- {name} 的杠数量 ---")
            while True:
                try:
                    count = input(f"  杠几张白板 (直接回车结束): ").strip()
                    if count == "":
                        break
                    count = int(count)
                    if count in [1, 2, 3, 4]:
                        gang_counts[i] += count
                        print(f"    累计: {gang_counts[i]} 张")
                    else:
                        print("    请输入1-4的数字")
                except ValueError:
                    print("    请输入有效数字")
        
        # 显示杠统计
        print("\n" + "=" * 50)
        print("📊 杠统计结果:")
        total_gang = 0
        for i, (pid, name) in enumerate(self.players):
            if gang_counts[i] > 0:
                print(f"  {name}: {gang_counts[i]} 张")
                total_gang += gang_counts[i]
            else:
                print(f"  {name}: 0 张")
        
        if total_gang == 0:
            print("本局无人杠白板")
        else:
            print(f"总计: {total_gang} 张")
        
        # 询问是否确认杠统计
        confirm = input("\n确认杠统计结果？(y/n): ").lower()
        if confirm != 'y':
            print("已取消快捷结算")
            return
        
        # 执行杠结算
        if total_gang > 0:
            for i, count in enumerate(gang_counts):
                if count > 0:
                    self._baiban(i, count)
        
        # 询问胡牌情况
        print("\n" + "=" * 50)
        print("🏆 胡牌结算")
        print("=" * 50)
        
        # 选择胡牌玩家
        print("\n谁胡牌了？")
        for i, (_, name) in enumerate(self.players):
            print(f"{i+1}. {name}")
        print("0. 流局")
        
        try:
            winner_choice = input("请选择(0-4): ").strip()
            if winner_choice == "0":
                # 流局
                self.liuju()
                return
            
            winner = int(winner_choice) - 1
            if not (0 <= winner < 4):
                print("无效选择")
                return
            
            # 输入台数
            tai = int(input("请输入总台数: "))
            
            # 执行胡牌结算
            self._hupai(winner, tai)
            
        except ValueError:
            print("请输入有效数字")
        except Exception as e:
            print(f"发生错误: {e}")


class GameManager:
    def __init__(self):
        self.db_path = 'mahjong.db'
    
    def generate_bao(self):
        """随机生成财神"""
        suits = ['万', '筒', '条']
        numbers = ['一', '二', '三', '四', '五', '六', '七', '八', '九']
        
        suit = random.choice(suits)
        number = random.choice(numbers)
        
        if random.random() < 0.1:
            honors = ['东风', '南风', '西风', '北风', '红中', '发财', '白板']
            return random.choice(honors)
        
        return f"{number}{suit}"
    
    def create_game(self, selected_users):
        """创建新游戏（大局）"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # 获取当前活跃赛季
        try:
            from season_manager import SeasonManager
            season_mgr = SeasonManager()
            active_season = season_mgr.get_active_season()
            season_id = active_season[0] if active_season else None
            if active_season:
                print(f"当前赛季: {active_season[1]}")
        except:
            season_id = None
            print("⚠️ 赛季功能未启用")
        
        # 随机生成财神
        bao = self.generate_bao()
        
        # 检查games表是否有season_id列
        c.execute("PRAGMA table_info(games)")
        columns = [col[1] for col in c.fetchall()]
        
        # 构建插入语句 - 使用正确的列名
        if 'season_id' in columns:
            c.execute('''
                INSERT INTO games 
                (player1_id, player2_id, player3_id, player4_id, bao, season_id, dealer_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                selected_users[0][0], selected_users[1][0],
                selected_users[2][0], selected_users[3][0],
                bao, season_id, selected_users[0][0]
            ))
        else:
            c.execute('''
                INSERT INTO games 
                (player1_id, player2_id, player3_id, player4_id, bao, dealer_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                selected_users[0][0], selected_users[1][0],
                selected_users[2][0], selected_users[3][0],
                bao, selected_users[0][0]
            ))
        
        game_id = c.lastrowid
        conn.commit()
        conn.close()
        
        game = Game(
            game_id=game_id,
            players=selected_users,
            scores=[1000, 1000, 1000, 1000],
            bao=bao
        )
        
        # 开始第一小局
        game.start_new_round()
        
        return game
    
    def update_user_stats(self, game):
        """游戏结束后更新用户统计"""
        print("\n📊 正在更新用户统计...")
        
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # 获取游戏结束时的最终分数
            final_scores = game.scores
            print(f"最终分数: {final_scores}")
            
            for i, (pid, name) in enumerate(game.players):
                # 计算该玩家的净胜分变化
                score_change = final_scores[i] - 1000
                
                # 查询该玩家在本局中的胡牌次数
                c.execute('''
                    SELECT COUNT(*) FROM rounds 
                    WHERE game_id=? AND winner_id=?
                ''', (game.id, pid))
                win_count = c.fetchone()[0]
                
                print(f"玩家 {name}: 分数变化 {score_change:+d}, 胡牌次数: {win_count}")
                
                # 更新用户统计
                c.execute('''
                    UPDATE users SET 
                        total_games = total_games + 1,
                        total_rounds = total_rounds + ?,
                        total_wins = total_wins + ?,
                        net_score = net_score + ?
                    WHERE id = ?
                ''', (len(game.rounds), win_count, score_change, pid))
            
            conn.commit()
            
            # 验证更新
            c.execute("SELECT id, username, total_games, total_rounds, total_wins, net_score FROM users")
            updated_users = c.fetchall()
            print("\n✅ 更新后的用户统计:")
            for user in updated_users:
                print(f"  {user[1]}: {user[2]}大局 {user[3]}小局 {user[4]}胜 净胜分:{user[5]:+d}")
                
        except Exception as e:
            print(f"❌ 更新用户统计时出错: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()