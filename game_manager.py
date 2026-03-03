# game_manager.py (支持2/3/4人)
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
        self.baiban_records.append((player_idx, count))

    def finish(self, winner_idx=None, tai=0):
        self.winner_id = self.game.players[winner_idx][0] if winner_idx is not None else None
        self.tai = tai
        self.final_scores = self.game.scores.copy()

    def get_score_changes(self):
        return [self.game.scores[i] - self.initial_scores[i] for i in range(self.game.num_players)]


class Game:
    def __init__(self, game_id, players, scores, bao):
        self.id = game_id
        self.players = players          # [(id, name), ...] 长度 = 玩家人数
        self.num_players = len(players)
        self.scores = scores             # 长度 = 玩家人数
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
        self._update_game_total_rounds()

    def _update_game_total_rounds(self):
        """更新游戏表中的总小局数"""
        try:
            c = self.conn.cursor()
            c.execute('UPDATE games SET total_rounds = ? WHERE id = ?', (len(self.rounds), self.id))
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
            choice = int(input("请选择玩家(1-{}): ".format(self.num_players))) - 1
            if not (0 <= choice < self.num_players):
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
        changes = [0] * self.num_players
        changes[player_idx] = (self.num_players - 1) * count
        for i in range(self.num_players):
            if i != player_idx:
                changes[i] = -1 * count

        # 更新分数
        for i in range(self.num_players):
            self.scores[i] += changes[i]

        # 记录到当前小局
        if self.current_round:
            self.current_round.add_baiban(player_idx, count)

        # 记录操作
        self.record_action('baiban', self.players[player_idx][0], changes, {'count': count})

        print(f"\n✅ {self.players[player_idx][1]} 杠 {count} 张白板")
        print(f"   +{(self.num_players-1)*count} 分")
        for i in range(self.num_players):
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
            winner = int(input("请选择(1-{}): ".format(self.num_players))) - 1
            if not (0 <= winner < self.num_players):
                print("无效选择")
                return
            tai = int(input("请输入总台数: "))
            self._hupai(winner, tai)
        except ValueError:
            print("请输入有效数字")

    def _hupai(self, winner_idx, tai):
        """执行胡牌结算"""
        changes = [0] * self.num_players
        winner_id = self.players[winner_idx][0]
        round_start_scores = self.scores.copy()

        zhuang_base = tai + 2 + self.lianzhuang * 2
        xian_base = tai + 1

        if winner_id == self.dealer_id:  # 庄家胡
            for i in range(self.num_players):
                if i != winner_idx:
                    changes[i] = -zhuang_base
                    changes[winner_idx] += zhuang_base
            print(f"\n✅ 庄家 {self.players[winner_idx][1]} 胡牌 {tai}台")
            print(f"其他玩家每人付 {zhuang_base}条")
            self.lianzhuang += 1
        else:  # 闲家胡
            changes[self.dealer_idx] = -zhuang_base
            changes[winner_idx] += zhuang_base
            for i in range(self.num_players):
                if i != winner_idx and i != self.dealer_idx:
                    changes[i] = -xian_base
                    changes[winner_idx] += xian_base
            print(f"\n✅ {self.players[winner_idx][1]} 胡牌 {tai}台")
            print(f"庄家 {self.players[self.dealer_idx][1]} 付 {zhuang_base}条")
            other_xian = self.num_players - 2
            if other_xian > 0:
                print(f"其他 {other_xian} 位闲家每人付 {xian_base}条")
            # 换庄
            self.dealer_id = winner_id
            self.dealer_idx = winner_idx
            self.lianzhuang = 0

        # 更新分数
        for i in range(self.num_players):
            self.scores[i] += changes[i]

        # 结束当前小局
        self.current_round.finish(winner_idx, tai)
        self.rounds.append(self.current_round)
        self._save_round_to_db(self.current_round, round_start_scores)

        print("\n更新后分数:")
        for i, (pid, name) in enumerate(self.players):
            print(f"  {name}: {self.scores[i]} 分")

        self.record_action('hupai', winner_id, changes, {'tai': tai, 'round': self.round_counter})

        # 询问是否继续
        cont = input("\n是否继续下一局？(y/n): ").lower()
        if cont == 'y':
            self.start_new_round()
        else:
            end_game = input("是否结束整场游戏？(y/n): ").lower()
            if end_game == 'y':
                self.is_finished = True
            else:
                self.start_new_round()

    def _save_round_to_db(self, round_obj, start_scores):
        """保存小局到数据库（支持不足4人时填充NULL）"""
        try:
            c = self.conn.cursor()
            changes = round_obj.get_score_changes()

            # 构建值列表（共14个）
            values = [
                self.id,
                round_obj.round_number,
                round_obj.dealer_id,
                round_obj.winner_id,
                round_obj.tai,
                round_obj.lianzhuang
            ]
            # 分数 (score1..score4)
            for i in range(4):
                if i < self.num_players:
                    values.append(self.scores[i])
                else:
                    values.append(None)
            # 分数变化 (change1..change4)
            for i in range(4):
                if i < self.num_players:
                    values.append(changes[i])
                else:
                    values.append(None)

            c.execute('''
                INSERT INTO rounds (
                    game_id, round_number, dealer_id, winner_id, tai, lianzhuang,
                    score1, score2, score3, score4,
                    score_change1, score_change2, score_change3, score_change4
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', values)

            round_db_id = c.lastrowid

            # 更新 actions 的 round_id
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
            self._update_game_total_rounds()
            print(f"✅ 第 {round_obj.round_number} 小局已保存到数据库")

        except Exception as e:
            print(f"保存小局时出错: {e}")
            self.conn.rollback()

    def liuju(self):
        """流局处理"""
        if not self.current_round:
            self.start_new_round()
        self.current_round.finish(None, 0)
        self.rounds.append(self.current_round)
        self._save_round_to_db(self.current_round, self.scores.copy())
        self.record_action('liuju', None, [0]*self.num_players)
        print("流局")
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
            idx = int(input("请选择要调整的玩家 (1-{}): ".format(self.num_players))) - 1
            if not (0 <= idx < self.num_players):
                print("无效选择")
                return
            new_score = int(input(f"请输入 {self.players[idx][1]} 的新分数: "))
            old_score = self.scores[idx]
            print(f"{self.players[idx][1]}: {old_score} -> {new_score}")
            confirm = input("确认调整？(y/n): ").lower()
            if confirm == 'y':
                self.scores[idx] = new_score
                changes = [0] * self.num_players
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
            # 获取当前round_id（如果存在）
            round_id = None
            if self.current_round:
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
        if self.current_round and self.current_round not in self.rounds:
            self.current_round.finish()
            self.rounds.append(self.current_round)
            self._save_round_to_db(self.current_round, self.current_round.initial_scores)

        try:
            c = self.conn.cursor()
            finished_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 计算最终分数（应该是当前分数，而不是初始分数）
            final_scores = self.scores.copy()

            print(f"\n💾 保存大局 #{self.id} 最终分数:")
            for i, (pid, name) in enumerate(self.players):
                print(f"  {name}: {final_scores[i]} 分")
            print(f"总小局数: {len(self.rounds)}")

            # 准备最终分数（不足4人时多余列填NULL）
            final_scores = [self.scores[i] if i < self.num_players else None for i in range(4)]

            c.execute('''
                UPDATE games SET 
                    is_finished=1,
                    finished_at=?,
                    final_score1=?, final_score2=?, final_score3=?, final_score4=?,
                    total_rounds=?
                WHERE id=?
            ''', (
                finished_at,
                final_scores[0], final_scores[1], final_scores[2], final_scores[3],
                len(self.rounds), self.id
            ))

            self.conn.commit()
            print("✅ 大局数据已保存到数据库")
        except Exception as e:
            print(f"❌ 结束游戏时出错: {e}")
            self.conn.rollback()

    def close_connection(self):
        try:
            self.conn.close()
            print("✅ 游戏数据库连接已关闭")
        except Exception as e:
            print(f"关闭连接时出错: {e}")

    def quick_settlement(self):
        """快捷结算"""
        if not self.current_round:
            self.start_new_round()
        print("\n" + "=" * 50)
        print("🎯 快捷结算模式")
        print("=" * 50)
        print("请依次输入各家白板杠数量（输入0表示没有，可多次输入）")

        gang_counts = [0] * self.num_players
        for i, (pid, name) in enumerate(self.players):
            print(f"\n--- {name} 的杠数量 ---")
            while True:
                try:
                    count = input("  杠几张白板 (直接回车结束): ").strip()
                    if count == "":
                        break
                    count = int(count)
                    if 1 <= count <= 4:
                        gang_counts[i] += count
                        print(f"    累计: {gang_counts[i]} 张")
                    else:
                        print("    请输入1-4的数字")
                except ValueError:
                    print("    请输入有效数字")

        print("\n" + "=" * 50)
        print("📊 杠统计结果:")
        for i, (pid, name) in enumerate(self.players):
            print(f"  {name}: {gang_counts[i]} 张")

        confirm = input("\n确认杠统计结果？(y/n): ").lower()
        if confirm != 'y':
            print("已取消快捷结算")
            return

        # 执行杠结算
        for i, count in enumerate(gang_counts):
            if count > 0:
                self._baiban(i, count)

        # 胡牌结算
        print("\n" + "=" * 50)
        print("🏆 胡牌结算")
        print("=" * 50)
        print("\n谁胡牌了？")
        for i, (_, name) in enumerate(self.players):
            print(f"{i+1}. {name}")
        print("0. 流局")
        try:
            winner_choice = input("请选择(0-{}): ".format(self.num_players)).strip()
            if winner_choice == "0":
                self.liuju()
                return
            winner = int(winner_choice) - 1
            if not (0 <= winner < self.num_players):
                print("无效选择")
                return
            tai = int(input("请输入总台数: "))
            self._hupai(winner, tai)
        except ValueError:
            print("请输入有效数字")
        except Exception as e:
            print(f"发生错误: {e}")


class GameManager:
    def __init__(self):
        self.db_path = 'mahjong.db'

    def generate_bao(self):
        suits = ['万', '筒', '条']
        numbers = ['一', '二', '三', '四', '五', '六', '七', '八', '九']
        suit = random.choice(suits)
        number = random.choice(numbers)
        if random.random() < 0.1:
            honors = ['东风', '南风', '西风', '北风', '红中', '发财', '白板']
            return random.choice(honors)
        return f"{number}{suit}"

    def create_game(self, selected_users):
        """创建新游戏（大局），selected_users 长度可为2/3/4"""
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

        bao = self.generate_bao()
        num_players = len(selected_users)

        # 准备玩家ID列表（长度4，不足补None）
        player_ids = [selected_users[i][0] if i < num_players else None for i in range(4)]
        # 初始分数（长度4，不足补None）
        init_scores = [1000 if i < num_players else None for i in range(4)]

        c.execute('''
            INSERT INTO games 
            (player1_id, player2_id, player3_id, player4_id, bao, season_id, dealer_id,
             final_score1, final_score2, final_score3, final_score4)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            player_ids[0], player_ids[1], player_ids[2], player_ids[3],
            bao, season_id, player_ids[0],
            init_scores[0], init_scores[1], init_scores[2], init_scores[3]
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
        game.start_new_round()
        return game

    def update_user_stats(self, game):
        """游戏结束后更新用户统计"""
        print("\n📊 正在更新用户统计...")
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            for i, (pid, name) in enumerate(game.players):
                score_change = game.scores[i] - 1000
                c.execute('''
                    SELECT COUNT(*) FROM rounds 
                    WHERE game_id=? AND winner_id=?
                ''', (game.id, pid))
                win_count = c.fetchone()[0]

                print(f"玩家 {name}: 分数变化 {score_change:+d}, 胡牌次数: {win_count}")

                c.execute('''
                    UPDATE users SET 
                        total_games = total_games + 1,
                        total_rounds = total_rounds + ?,
                        total_wins = total_wins + ?,
                        net_score = net_score + ?
                    WHERE id = ?
                ''', (len(game.rounds), win_count, score_change, pid))

            conn.commit()
            print("✅ 用户统计更新完成")
        except Exception as e:
            print(f"❌ 更新用户统计时出错: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()