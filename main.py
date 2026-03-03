# main.py (更新版)
import os
import sys
import sqlite3
from database import init_db
from user_manager import UserManager
from season_manager import SeasonManager
from game_manager import GameManager
from query_manager import QueryManager

class MahjongSystem:
    def __init__(self):
        init_db()
        from maintenance_manager import MaintenanceManager
        maint_mgr = MaintenanceManager()
        maint_mgr.check_database_integrity()

        self.user_mgr = UserManager()
        self.season_mgr = SeasonManager()
        self.game_mgr = GameManager()
        self.query_mgr = QueryManager()
        self.current_game = None
    
    def clear_screen(self):
        """清屏"""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def main_menu(self):
        """主菜单"""
        while True:
            self.clear_screen()
            print("=" * 60)
            print("         麻将积分管理系统")
            print("=" * 60)
            print("1. 👤 用户管理")
            print("2. 📊 数据查询")
            print("3. 🀄️ 开始游戏")
            print("4. 🏆 赛季管理")
            print("5. 🧹 数据维护")
            print("0. 🚪 退出系统")
            print("=" * 60)
            
            # 显示当前活跃赛季
            active = self.season_mgr.get_active_season()
            if active:
                print(f"当前赛季: {active[1]} ({active[2]} 至 {active[3]})")
            else:
                print("当前赛季: 未设置")
            print("=" * 60)
            
            choice = input("请选择操作: ").strip()
            
            if choice == '1':
                self.user_menu()
            elif choice == '2':
                self.query_menu()
            elif choice == '3':
                self.game_menu()
            elif choice == '4':
                self.season_menu()
            elif choice == '5':
                self.maintenance_menu()
            elif choice == '0':
                print("感谢使用，再见！")
                sys.exit(0)
            else:
                input("无效选择，按回车继续...")
    
    def user_menu(self):
        """用户管理界面"""
        while True:
            self.clear_screen()
            print("\n--- 用户管理 ---")
            print("1. 注册新用户")
            print("2. 查看所有用户")
            print("3. 修改用户信息")
            print("4. 删除用户")
            print("5. 💰 手动调整积分")
            print("6. 💸 用户间转账")
            print("0. 返回主菜单")

            choice = input("请选择: ")

            if choice == '1':
                self.user_mgr.register()
            elif choice == '2':
                self.user_mgr.list_users(show_stats=False)
            elif choice == '3':
                self.user_mgr.update_user()
            elif choice == '4':
                self.user_mgr.delete_user()
            elif choice == '5':
                self.user_mgr.manual_adjust_score()
            elif choice == '6':
                self.user_mgr.transfer_score()
            elif choice == '0':
                break
            input("\n按回车继续...")
    
    def query_menu(self):
        """数据查询界面"""
        while True:
            self.clear_screen()
            print("\n--- 数据查询 ---")
            print("1. 查看用户战绩")
            print("2. 全局统计")
            print("3. 最近大局记录")
            print("4. 最近小局记录")
            print("5. 查看调整记录")
            print("6. 白板杠统计")
            print("7. 💰 总积分排行榜")      # 新增
            print("8. 📊 用户积分明细")       # 新增
            print("0. 返回主菜单")

            choice = input("请选择: ")

            if choice == '1':
                self.query_mgr.user_stats()
            elif choice == '2':
                self.query_mgr.global_stats()
            elif choice == '3':
                self.query_mgr.recent_games()
            elif choice == '4':
                self.query_mgr.recent_rounds()
            elif choice == '5':
                self.view_adjustment_logs()
            elif choice == '6':
                self.query_mgr.baiban_stats()
            elif choice == '7':
                self.query_mgr.total_score_stats()      # 新增
            elif choice == '8':
                self.query_mgr.user_total_score_detail() # 新增
            elif choice == '0':
                break
            input("\n按回车继续...")
    
    def season_menu(self):
        """赛季管理界面"""
        while True:
            self.clear_screen()
            print("\n--- 赛季管理 ---")
            print("1. 创建新赛季")
            print("2. 查看所有赛季")
            print("3. 设置当前活跃赛季")
            print("4. 查看赛季统计")
            print("0. 返回主菜单")
            
            choice = input("请选择: ")
            
            if choice == '1':
                self.season_mgr.create_season()
            elif choice == '2':
                self.season_mgr.list_seasons()
            elif choice == '3':
                self.season_mgr.set_active_season()
            elif choice == '4':
                self.season_mgr.season_stats()
            elif choice == '0':
                break
            input("\n按回车继续...")

    def maintenance_menu(self):
        """数据维护界面"""
        # 创建维护管理器实例
        from maintenance_manager import MaintenanceManager
        maint_mgr = MaintenanceManager()

        while True:
            self.clear_screen()
            print("\n" + "=" * 60)
            print("⚠️  数据维护")
            print("=" * 60)
            print("1. 💾 备份数据库")
            print("2. 🗑️ 清空所有数据")
            print("3. 🎮 只清空大局记录")
            print("4. 📋 只清空小局记录")
            print("5. 📝 只清空操作记录")
            print("6. 👤 重置用户积分")
            print("7. 🔧 压缩数据库")
            print("8. 🔍 检查数据库完整性")
            print("9. 📤 导出数据到CSV")
            print("0. ↩️ 返回主菜单")
            print("=" * 60)

            # 显示当前数据库状态
            try:
                conn = sqlite3.connect('mahjong.db')
                c = conn.cursor()
                c.execute("SELECT COUNT(*) FROM users")
                user_count = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM games")
                game_count = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM rounds")
                round_count = c.fetchone()[0]
                conn.close()
                print(f"当前状态: {user_count}用户 | {game_count}大局 | {round_count}小局")
            except:
                pass
            print("=" * 60)

            choice = input("请选择: ").strip()

            if choice == '1':
                maint_mgr.backup_database()
            elif choice == '2':
                maint_mgr.clear_all_data()
            elif choice == '3':
                maint_mgr.clear_games_only()
            elif choice == '4':
                maint_mgr.clear_rounds_only()
            elif choice == '5':
                maint_mgr.clear_actions_only()
            elif choice == '6':
                maint_mgr.reset_user_scores()
            elif choice == '7':
                maint_mgr.vacuum_database()
            elif choice == '8':
                maint_mgr.check_database_integrity()
            elif choice == '9':
                maint_mgr.export_to_csv()
            elif choice == '0':
                break
            
            input("\n按回车继续...")
    
    def game_menu(self):
        """开始新牌局（支持2/3/4人）"""
        self.clear_screen()
        print("\n--- 开始新牌局 ---")

        # 1. 选择人数
        print("请选择游戏人数：")
        print("1. 2人")
        print("2. 3人")
        print("3. 4人")
        choice = input("请选择 (1-3): ").strip()
        if choice == '1':
            num_players = 2
        elif choice == '2':
            num_players = 3
        else:
            num_players = 4

        # 2. 获取所有用户（带统计）
        users = self.user_mgr.get_all_users(with_stats=True)
        if len(users) < num_players:
            print(f"❌ 错误: 至少需要 {num_players} 个已注册用户才能开始游戏！")
            print(f"当前用户数: {len(users)}")
            input("按回车返回...")
            return

        selected = []  # 已选中的玩家列表，元素为 (id, name)

        # 3. 逐个选择玩家
        for i in range(num_players):
            while True:
                self.clear_screen()
                print(f"\n--- 选择第 {i+1} 个玩家 (共需 {num_players} 人) ---")

                # 显示所有用户列表（带统计）
                print("序号 | 用户名 | 大局数 | 小局数 | 胜局数 | 净胜分 | 状态")
                print("-" * 70)
                for idx, user in enumerate(users, 1):
                    if len(user) >= 6:  # 有统计信息
                        uid, name, total_games, total_rounds, total_wins, net_score = user[:6]
                    else:  # 只有基本信息（理论上不会发生，但保留兼容）
                        uid, name = user
                        total_games = total_rounds = total_wins = net_score = 0

                    selected_ids = [s[0] for s in selected]
                    selected_flag = "✅ 已选" if uid in selected_ids else "     "

                    print(f"{idx:2d}   | {name:8} | {total_games:5d} | {total_rounds:5d} | {total_wins:5d} | {net_score:+6d} | {selected_flag}")

                try:
                    idx = int(input(f"\n请选择第 {i+1} 个玩家 (输入序号): "))
                    if 1 <= idx <= len(users):
                        selected_user = users[idx-1]
                        user_id = selected_user[0] if isinstance(selected_user, tuple) else selected_user[0]

                        if user_id in [s[0] for s in selected]:
                            print("该玩家已被选中，请重新选择")
                            input("按回车继续...")
                        else:
                            # 保存 (id, name) 格式
                            selected.append((user_id, selected_user[1]))
                            break
                    else:
                        print("序号超出范围")
                        input("按回车继续...")
                except ValueError:
                    print("请输入有效数字")
                    input("按回车继续...")

        # 4. 确认玩家
        self.clear_screen()
        print("\n--- 确认玩家 ---")
        for i, (_, name) in enumerate(selected, 1):
            print(f"玩家{i}: {name}")

        print("\n游戏说明:")
        print("• 每局胡牌或流局都会自动保存为一个小局")
        print("• 结束整场游戏时保存为一个大局")
        print("• 可以随时查看当前小局状态")

        confirm = input("\n确认开始游戏？(y/n): ").lower()
        if confirm != 'y':
            print("已取消创建牌局")
            input("按回车返回...")
            return

        # 5. 创建游戏并进入游戏循环
        self.current_game = self.game_mgr.create_game(selected)
        self.game_play_loop()
    
    def game_play_loop(self):
        """游戏进行中的交互界面"""
        while not self.current_game.is_finished:
            self.clear_screen()
            print("\n" + "=" * 50)
            print(f"          大局 #{self.current_game.id}")
            print("=" * 50)

            # 显示当前状态
            self.current_game.show_status()

            # 显示本局信息
            if self.current_game.current_round:
                print(f"\n当前小局: 第 {self.current_game.current_round.round_number} 局")
                if self.current_game.current_round.baiban_records:
                    print(f"本局已杠白板: {len(self.current_game.current_round.baiban_records)} 次")

            print("\n操作菜单:")
            print("1. 🀄️ 白板杠")
            print("2. 🏆 胡牌结算")
            print("3. 🔄 流局")
            print("4. 📊 显示当前分数")
            print("5. 🔧 紧急调分")
            print("6. 📝 查看本小局记录")
            print("7. ⚡ 快捷结算（先统计杠，再胡牌）")  # 新增
            print("0. 🚪 结束整场游戏")

            choice = input("请选择: ")

            if choice == '1':
                self.current_game.baiban_input()
                input("按回车继续...")
            elif choice == '2':
                self.current_game.hupai_input()
            elif choice == '3':
                self.current_game.liuju()
            elif choice == '4':
                self.current_game.show_status()
                input("按回车继续...")
            elif choice == '5':
                self.current_game.emergency_adjust()
                input("按回车继续...")
            elif choice == '6':
                self.show_current_round_detail()
                input("按回车继续...")
            elif choice == '7':
                self.current_game.quick_settlement()
            elif choice == '0':
                self.confirm_end_game()
                break
    
    def show_current_round_detail(self):
        """显示当前小局详情"""
        if not self.current_game.current_round:
            print("还没有开始小局")
            return
        
        round_data = self.current_game.current_round
        print(f"\n=== 第 {round_data.round_number} 小局详情 ===")
        print(f"庄家: {self.current_game.players[round_data.dealer_idx][1]}")
        print(f"连庄: {round_data.lianzhuang}")
        print(f"开局分数: {round_data.initial_scores}")
        
        if round_data.baiban_records:
            print("\n本局白板杠:")
            for player_idx, count in round_data.baiban_records:
                player_name = self.current_game.players[player_idx][1]
                print(f"  {player_name}: 杠 {count} 张")
        else:
            print("\n本局暂无白板杠")
    
    def confirm_end_game(self):
        """确认结束游戏"""
        print("\n" + "=" * 50)
        print("⚠️  确认结束整场游戏")
        print("=" * 50)
        
        # 显示当前大局统计
        print(f"大局 #{self.current_game.id}")
        print(f"已进行小局数: {len(self.current_game.rounds)}")
        if self.current_game.current_round and self.current_game.current_round not in self.current_game.rounds:
            print(f"当前未完成小局: 第 {self.current_game.current_round.round_number} 局")
        
        print("\n当前分数:")
        for i, (pid, name) in enumerate(self.current_game.players):
            print(f"  {name}: {self.current_game.scores[i]} 分")
        
        confirm = input("\n确认结束整场游戏？(y/n): ").lower()
        if confirm == 'y':
            # 如果有未完成的小局，先结束它
            if self.current_game.current_round and self.current_game.current_round not in self.current_game.rounds:
                print("正在保存当前小局...")
                self.current_game.current_round.finish()
                self.current_game.rounds.append(self.current_game.current_round)
                self.current_game._save_round_to_db(
                    self.current_game.current_round, 
                    self.current_game.current_round.initial_scores
                )
            
            self.current_game.is_finished = True
        else:
            print("继续游戏")
    
    def finish_game(self):
        """游戏结束，更新统计"""
        print("\n" + "=" * 50)
        print("牌局结束，正在更新统计数据...")
        print("=" * 50)

        # 显示最终统计
        print(f"\n大局 #{self.current_game.id} 统计:")
        print(f"总小局数: {len(self.current_game.rounds)}")
        
        # 显示每局结果
        if self.current_game.rounds:
            print("\n小局结果:")
            for i, round_data in enumerate(self.current_game.rounds, 1):
                if round_data.winner_id:
                    winner_name = next(name for pid, name in self.current_game.players if pid == round_data.winner_id)
                    print(f"  第{i}局: {winner_name} 胡牌 {round_data.tai}台")
                else:
                    print(f"  第{i}局: 流局")
        
        # 显示最终分数
        print("\n最终分数:")
        for i, (pid, name) in enumerate(self.current_game.players):
            change = self.current_game.scores[i] - 1000
            print(f"  {name}: {self.current_game.scores[i]} 分 ({change:+d})")

        # 先结束大局（保存分数到数据库）
        self.current_game.end_game()

        # 更新用户统计
        self.game_mgr.update_user_stats(self.current_game)

        # 关闭连接
        self.current_game.close_connection()

        print("\n✅ 数据更新完成！")
        print(f"大局 #{self.current_game.id} 已保存，共 {len(self.current_game.rounds)} 小局")

        input("\n按回车返回主菜单...")
    
    
    def view_adjustment_logs(self):
        """查看调整记录"""
        try:
            with open('score_adjustments.log', 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if not lines:
                print("暂无调整记录")
                return
            
            print("\n=== 手动调分记录 ===")
            for line in lines[-20:]:
                print(line.strip())
                
        except FileNotFoundError:
            print("暂无调整记录")

    def get_total_score(self, user_id):
        """获取用户总积分（牌局净胜分 + 手动调整积分）

        总积分 = 牌局净胜分 + 手动调整积分
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # 1. 获取牌局净胜分（从games表计算）
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
        ''', (user_id, user_id, user_id, user_id, user_id, user_id, user_id, user_id))

        game_score = c.fetchone()[0]

        # 2. 获取手动调整积分（从users表的net_score减去牌局净胜分？）
        # 但users表的net_score已经是总积分了，所以我们可以直接使用users表的net_score
        # 或者从调整日志中计算手动调整积分

        conn.close()
        return game_score

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

            # 计算胜率
            win_rate = (wins / rounds * 100) if rounds > 0 else 0

            print(f"{i:4d} | {name:10} | {game_score:10+d} | {manual_adjust:10+d} | {total_score:10+d} | {games:6d} | {rounds:6d} | {wins:6d} ({win_rate:.1f}%)")

        # 显示总计
        print("-" * 85)
        total_players = len(results)
        total_game_score = sum(row[2] for row in results)
        total_manual = sum(row[3] for row in results)
        total_all = sum(row[4] for row in results)
        total_games = sum(row[5] for row in results)
        total_rounds = sum(row[6] for row in results)
        total_wins = sum(row[7] for row in results)

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

if __name__ == "__main__":
    system = MahjongSystem()
    system.main_menu()