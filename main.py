# main.py
import os
import sys
import sqlite3
from database import init_db
from user_manager import UserManager
from season_manager import SeasonManager
from game_manager import GameManager
from query_manager import QueryManager
from big_game_manager import BigGameManager

class MahjongSystem:
    def __init__(self):
        init_db()
        self.user_mgr = UserManager()
        self.season_mgr = SeasonManager()
        self.game_mgr = GameManager()
        self.big_game_mgr = BigGameManager()
        self.query_mgr = QueryManager()
        self.current_game = None
        self.current_big_game = None
        self.current_round = 1
    
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
                self.user_mgr.list_users()
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
            print("3. 最近牌局记录")
            print("4. 查看调整记录")
            print("5. 查看大局统计")
            print("0. 返回主菜单")

            choice = input("请选择: ")

            if choice == '1':
                self.query_mgr.user_stats()
            elif choice == '2':
                self.query_mgr.global_stats()
            elif choice == '3':
                self.query_mgr.recent_games()
            elif choice == '4':
                self.view_adjustment_logs()
            elif choice == '5':
                self.query_mgr.big_game_stats()
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
        while True:
            self.clear_screen()
            print("\n" + "=" * 50)
            print("⚠️  数据维护")
            print("=" * 50)
            print("1. 备份数据库")
            print("2. 清空所有数据")
            print("3. 只清空牌局记录")
            print("4. 只清空操作记录")
            print("5. 重置用户积分")
            print("0. 返回主菜单")
            print("=" * 50)
            
            choice = input("请选择: ").strip()
            
            if choice == '1':
                self.backup_database()
            elif choice == '2':
                self.clear_all_data()
            elif choice == '3':
                self.clear_games_only()
            elif choice == '4':
                self.clear_actions_only()
            elif choice == '5':
                self.reset_user_scores()
            elif choice == '0':
                break
            input("\n按回车继续...")
    
    def game_menu(self):
        """开始游戏界面 - 支持大局"""
        self.clear_screen()
        print("\n--- 开始新牌局 ---")

        users = self.user_mgr.get_all_users()
        if len(users) < 4:
            print(f"❌ 错误: 至少需要4个已注册用户才能开始游戏！")
            print(f"当前用户数: {len(users)}")
            input("按回车返回...")
            return

        # 选择4个玩家
        selected = []
        for i in range(4):
            while True:
                self.clear_screen()
                print(f"\n--- 选择第 {i+1} 个玩家 ---")

                conn = sqlite3.connect('mahjong.db')
                c = conn.cursor()
                c.execute("SELECT id, username FROM users ORDER BY username")
                all_users = c.fetchall()
                conn.close()

                print("序号 | 用户名")
                print("-" * 20)
                for idx, (uid, name) in enumerate(all_users, 1):
                    selected_ids = [s[0] for s in selected]
                    selected_flag = " (已选)" if uid in selected_ids else ""
                    print(f"{idx:2d}   | {name}{selected_flag}")

                try:
                    idx = int(input(f"\n请选择第 {i+1} 个玩家 (输入序号): "))
                    if 1 <= idx <= len(all_users):
                        selected_user = all_users[idx-1]
                        if selected_user[0] in [s[0] for s in selected]:
                            print("该玩家已被选中，请重新选择")
                            input("按回车继续...")
                        else:
                            selected.append(selected_user)
                            break
                    else:
                        print("序号超出范围")
                        input("按回车继续...")
                except ValueError:
                    print("请输入有效数字")
                    input("按回车继续...")

        self.clear_screen()
        print("\n--- 确认玩家 ---")
        for i, (_, name) in enumerate(selected, 1):
            print(f"玩家{i}: {name}")

        # 询问是否开始新大局
        print("\n1. 开始新大局")
        print("2. 继续现有大局")
        print("3. 单局模式（不关联大局）")

        mode = input("请选择(1-3): ").strip()

        if mode == '1':
            # 创建新大局
            active_season = self.season_mgr.get_active_season()
            season_id = active_season[0] if active_season else None
            self.current_big_game = self.big_game_mgr.create_big_game(selected, season_id)
            self.current_round = 1
            print(f"开始新大局 #{self.current_big_game.id}")

        elif mode == '2':
            # 继续现有大局 - 这里简化处理，实际应该让用户选择
            print("功能开发中，使用单局模式")
            self.current_big_game = None
            self.current_round = 1

        else:
            # 单局模式
            self.current_big_game = None
            self.current_round = 1

        confirm = input("\n确认开始游戏？(y/n): ").lower()
        if confirm != 'y':
            print("已取消创建牌局")
            input("按回车返回...")
            return

        # 创建第一小局
        self.current_game = self.game_mgr.create_game(
            selected, 
            big_game=self.current_big_game,
            round_number=self.current_round
        )

        # 如果是在大局中，关联小局到大局
        if self.current_big_game:
            self.big_game_mgr.update_small_game_big_game(
                self.current_game.id,
                self.current_big_game.id,
                self.current_round
            )
            self.current_big_game.add_small_game(self.current_game.id)

        self.game_play_loop()
    
    def game_play_loop(self):
        """游戏进行中的交互界面 - 支持连续小局"""
        while True:
            while not self.current_game.is_finished:
                self.clear_screen()

                # 显示大局信息
                if self.current_big_game:
                    self.current_big_game.show_status()
                    print(f"当前小局: 第 {self.current_round} 局")
                    print("-" * 40)

                print("\n=== 当前小局 ===")
                self.current_game.show_status()
                print("\n操作菜单:")
                print("1. 白板杠")
                print("2. 胡牌结算")
                print("3. 流局")
                print("4. 显示当前分数")
                print("5. 🔧 紧急调分")
                print("0. 结束牌局")

                choice = input("请选择: ")

                if choice == '1':
                    self.current_game.baiban_input()
                    input("按回车继续...")
                elif choice == '2':
                    self.current_game.hupai_input()
                elif choice == '3':
                    self.current_game.liuju()
                    break
                elif choice == '4':
                    self.current_game.show_status()
                    input("按回车继续...")
                elif choice == '5':
                    self.current_game.emergency_adjust()
                    input("按回车继续...")
                elif choice == '0':
                    self.current_game.end_game()
                    break
                
            # 小局结束，更新统计
            if self.current_game:
                print("\n" + "=" * 50)
                print(f"第 {self.current_round} 小局结束")
                print("=" * 50)

                # 显示最终分数
                print("本局最终分数:")
                for i, (pid, name) in enumerate(self.current_game.players):
                    print(f"  {name}: {self.current_game.scores[i]}")

                # 保存小局数据
                self.current_game.end_game()

                # 更新大局分数
                if self.current_big_game:
                    self.current_big_game.update_scores(self.current_game.scores)

                # 更新用户统计（小局结束，不是大局结束）
                self.game_mgr.update_user_stats(self.current_game, is_big_game_end=False)

                # 关闭小局连接
                self.current_game.close_connection()

                # 询问是否继续下一小局
                if self.current_big_game:
                    print(f"\n大局 #{self.current_big_game.id} 当前分数:")
                    for i, (pid, name) in enumerate(self.current_big_game.players):
                        change = self.current_big_game.current_scores[i] - self.current_big_game.start_scores[i]
                        print(f"  {name}: {self.current_big_game.current_scores[i]} 分 ({change:+d})")

                    cont = input("\n是否继续下一小局？(y/n, 输入'end'结束大局): ").lower()

                    if cont == 'end':
                        # 结束大局
                        self.current_big_game.end_big_game()
                        # 大局结束，更新大局统计
                        self.game_mgr.update_user_stats(self.current_game, is_big_game_end=True)
                        break
                    elif cont == 'y':
                        # 继续下一小局
                        self.current_round += 1

                        # 庄家轮换：上一局的赢家是下一局的庄家
                        # 这里简化处理，实际应该从游戏状态获取
                        next_dealer = self.current_game.dealer_id

                        # 创建新小局，使用当前大局分数作为初始分数
                        self.current_game = self.game_mgr.create_game(
                            self.current_big_game.players,
                            big_game=self.current_big_game,
                            round_number=self.current_round
                        )

                        # 关联到大局
                        self.big_game_mgr.update_small_game_big_game(
                            self.current_game.id,
                            self.current_big_game.id,
                            self.current_round
                        )
                        self.current_big_game.add_small_game(self.current_game.id)

                        # 继续循环
                        continue
                    else:
                        # 不继续，结束大局
                        self.current_big_game.end_big_game()
                        break
                else:
                    # 单局模式，直接结束
                    break
                
            # 退出循环
            break
        
        print("\n✅ 牌局全部结束！")
        input("\n按回车返回主菜单...")
    
    def backup_database(self):
        """备份数据库"""
        import shutil
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"mahjong_backup_{timestamp}.db"
        
        try:
            shutil.copy2('mahjong.db', backup_file)
            print(f"✅ 数据库已备份到: {backup_file}")
        except Exception as e:
            print(f"❌ 备份失败: {e}")
    
    def clear_all_data(self):
        """清空所有数据"""
        print("\n⚠️  警告：这将删除所有用户、牌局、赛季数据！")
        
        self.backup_database()
        
        confirm1 = input("请输入 'DELETE' 确认: ").strip()
        if confirm1 != 'DELETE':
            print("操作已取消")
            return
        
        confirm2 = input("最后确认？(y/n): ").lower()
        if confirm2 != 'y':
            print("操作已取消")
            return
        
        conn = sqlite3.connect('mahjong.db')
        c = conn.cursor()
        
        c.execute("DELETE FROM actions")
        c.execute("DELETE FROM games")
        c.execute("DELETE FROM seasons")
        c.execute("DELETE FROM users")
        c.execute("DELETE FROM sqlite_sequence")
        
        conn.commit()
        conn.close()
        
        print("✅ 所有数据已清空！")
    
    def clear_games_only(self):
        """只清空牌局记录"""
        print("\n⚠️  警告：这将删除所有牌局和操作记录！")
        
        self.backup_database()
        
        confirm = input("确定清空？(y/n): ").lower()
        if confirm != 'y':
            print("操作已取消")
            return
        
        conn = sqlite3.connect('mahjong.db')
        c = conn.cursor()
        
        c.execute("DELETE FROM actions")
        c.execute("DELETE FROM games")
        
        conn.commit()
        conn.close()
        
        print("✅ 牌局记录已清空！")
    
    def clear_actions_only(self):
        """只清空操作记录"""
        print("\n⚠️  警告：这将删除所有操作记录！")
        
        self.backup_database()
        
        confirm = input("确定清空？(y/n): ").lower()
        if confirm != 'y':
            print("操作已取消")
            return
        
        conn = sqlite3.connect('mahjong.db')
        c = conn.cursor()
        
        c.execute("DELETE FROM actions")
        
        conn.commit()
        conn.close()
        
        print("✅ 操作记录已清空！")
    
    def reset_user_scores(self):
        """重置用户积分"""
        print("\n⚠️  警告：这将重置所有用户积分为0")
        
        self.backup_database()
        
        confirm = input("确定重置？(y/n): ").lower()
        if confirm != 'y':
            print("操作已取消")
            return
        
        conn = sqlite3.connect('mahjong.db')
        c = conn.cursor()
        
        c.execute('''
            UPDATE users SET 
                total_games = 0,
                total_wins = 0,
                net_score = 0
        ''')
        
        conn.commit()
        conn.close()
        
        print("✅ 用户积分已重置！")
    
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

if __name__ == "__main__":
    system = MahjongSystem()
    system.main_menu()