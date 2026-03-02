# user_manager.py
import sqlite3
import datetime

class UserManager:
    def __init__(self):
        self.db_path = 'mahjong.db'
    
    def register(self):
        """注册新用户"""
        print("\n--- 注册新用户 ---")
        username = input("请输入用户名: ").strip()
        if not username:
            print("用户名不能为空")
            return
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username) VALUES (?)", (username,))
            conn.commit()
            print(f"✅ 用户 {username} 注册成功！")
        except sqlite3.IntegrityError:
            print("❌ 用户名已存在，请使用其他名称")
        finally:
            conn.close()
    
    def list_users(self, show_stats=False):
        """显示所有用户

        Args:
            show_stats: 是否显示详细统计（用于选择玩家时的界面）
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            SELECT id, username, total_games, total_rounds, total_wins, net_score 
            FROM users ORDER BY id
        ''')
        users = c.fetchall()
        conn.close()

        if not users:
            print("暂无用户")
            return users

        if show_stats:
            # 详细统计模式（用于选择玩家界面）
            print("\n用户列表 (带详细统计):")
            print("序号 | ID | 用户名 | 大局数 | 小局数 | 胜局数 | 净胜分")
            print("-" * 70)
            for i, user in enumerate(users, 1):
                print(f"{i:2d}   | {user[0]:2d} | {user[1]:8} | {user[2]:6d} | {user[3]:6d} | {user[4]:6d} | {user[5]:+6d}")
        else:
            # 简洁模式
            print("\n用户列表:")
            print("ID | 用户名 | 大局数 | 小局数 | 胜局数 | 净胜分")
            print("-" * 50)
            for user in users:
                print(f"{user[0]:2d} | {user[1]:8} | {user[2]:6d}局 | {user[3]:6d}局 | {user[4]:6d}胜 | {user[5]:+6d}分")

        return users

    def get_all_users(self, with_stats=False):
        """获取所有用户列表

        Args:
            with_stats: 是否包含统计信息
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        if with_stats:
            c.execute("SELECT id, username, total_games, total_rounds, total_wins, net_score FROM users ORDER BY username")
        else:
            c.execute("SELECT id, username FROM users ORDER BY username")

        users = c.fetchall()
        conn.close()
        return users
    
    def update_user(self):
        """修改用户信息"""
        users = self.list_users()
        if not users:
            return
        
        try:
            user_id = int(input("\n请输入要修改的用户ID: "))
        except ValueError:
            print("无效输入")
            return
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # 检查用户是否存在
        c.execute("SELECT username FROM users WHERE id=?", (user_id,))
        user = c.fetchone()
        if not user:
            print("用户不存在")
            conn.close()
            return
        
        print(f"当前用户名: {user[0]}")
        new_name = input("请输入新用户名 (直接回车保持不变): ").strip()
        
        if new_name:
            try:
                c.execute("UPDATE users SET username=? WHERE id=?", (new_name, user_id))
                conn.commit()
                print("✅ 用户名修改成功！")
            except sqlite3.IntegrityError:
                print("❌ 用户名已存在，修改失败")
        
        conn.close()
    
    def delete_user(self):
        """删除用户"""
        users = self.list_users()
        if not users:
            return
        
        try:
            user_id = int(input("\n请输入要删除的用户ID: "))
        except ValueError:
            print("无效输入")
            return
        
        # 确认删除
        confirm = input(f"确定要删除ID为 {user_id} 的用户吗？(y/n): ").lower()
        if confirm != 'y':
            print("已取消删除")
            return
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # 检查用户是否存在
        c.execute("SELECT username FROM users WHERE id=?", (user_id,))
        user = c.fetchone()
        if not user:
            print("用户不存在")
            conn.close()
            return
        
        # 检查用户是否参与了牌局
        c.execute('''
            SELECT COUNT(*) FROM games 
            WHERE player1_id=? OR player2_id=? OR player3_id=? OR player4_id=?
        ''', (user_id, user_id, user_id, user_id))
        game_count = c.fetchone()[0]
        
        if game_count > 0:
            print(f"⚠️ 该用户参与了 {game_count} 局游戏，无法直接删除")
            print("建议保留用户记录以保证数据完整性")
            conn.close()
            return
        
        # 执行删除
        c.execute("DELETE FROM users WHERE id=?", (user_id,))
        conn.commit()
        print(f"✅ 用户 {user[0]} 已删除")
        
        conn.close()
    
    def manual_adjust_score(self):
        """手动调整用户积分"""
        print("\n--- 手动调整积分 ---")
        
        users = self.list_users()
        if not users:
            return
        
        try:
            user_id = int(input("\n请输入要调整积分的用户ID: "))
        except ValueError:
            print("无效输入")
            return
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            SELECT id, username, total_games, total_wins, net_score 
            FROM users WHERE id=?
        ''', (user_id,))
        user = c.fetchone()
        
        if not user:
            print("用户不存在")
            conn.close()
            return
        
        print(f"\n当前用户: {user[1]}")
        print(f"当前净胜分: {user[4]:+d}")
        print(f"总局数: {user[2]}")
        print(f"胜局数: {user[3]}")
        
        print("\n调整方式:")
        print("1. 直接设置新积分")
        print("2. 增加/减少积分")
        
        choice = input("请选择调整方式 (1/2): ").strip()
        
        if choice == '1':
            try:
                new_score = int(input("请输入新的积分值: "))
                change = new_score - user[4]
                
                print(f"\n积分将从 {user[4]:+d} 变为 {new_score:+d}")
                print(f"变化量: {change:+d}")
                
                confirm = input("确认修改？(y/n): ").lower()
                if confirm == 'y':
                    reason = input("请输入调整原因: ").strip()
                    
                    c.execute('''
                        UPDATE users SET net_score = ? WHERE id = ?
                    ''', (new_score, user_id))
                    
                    conn.commit()
                    print(f"✅ 积分已更新为 {new_score:+d}")
                    
                    self._log_manual_adjustment(user[1], user[4], new_score, change, reason)
                else:
                    print("已取消")
                    
            except ValueError:
                print("请输入有效的数字")
        
        elif choice == '2':
            try:
                change = int(input("请输入变化量 (正数增加，负数减少): "))
                new_score = user[4] + change
                
                print(f"\n积分将从 {user[4]:+d} 变为 {new_score:+d}")
                print(f"变化量: {change:+d}")
                
                confirm = input("确认修改？(y/n): ").lower()
                if confirm == 'y':
                    reason = input("请输入调整原因: ").strip()
                    
                    c.execute('''
                        UPDATE users SET net_score = ? WHERE id = ?
                    ''', (new_score, user_id))
                    
                    conn.commit()
                    print(f"✅ 积分已更新为 {new_score:+d}")
                    
                    self._log_manual_adjustment(user[1], user[4], new_score, change, reason)
                else:
                    print("已取消")
                    
            except ValueError:
                print("请输入有效的数字")
        
        else:
            print("无效选择")
        
        conn.close()
    
    def _log_manual_adjustment(self, username, old_score, new_score, change, reason):
        """记录手动调分日志"""
        try:
            with open('score_adjustments.log', 'a', encoding='utf-8') as f:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"[{timestamp}] {username}: {old_score:+d} -> {new_score:+d} ({change:+d}) 原因: {reason}\n")
            print("调整记录已保存到 score_adjustments.log")
        except Exception as e:
            print(f"无法写入日志: {e}")
    
    def transfer_score(self):
        """用户间积分转账"""
        print("\n--- 积分转账 ---")
        
        users = self.list_users()
        if not users:
            return
        
        try:
            from_id = int(input("\n请输入转出方用户ID: "))
            to_id = int(input("请输入转入方用户ID: "))
            
            if from_id == to_id:
                print("不能给自己转账")
                return
            
            amount = int(input("请输入转账金额: "))
            if amount <= 0:
                print("金额必须大于0")
                return
            
        except ValueError:
            print("无效输入")
            return
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('SELECT id, username, net_score FROM users WHERE id=?', (from_id,))
        from_user = c.fetchone()
        
        c.execute('SELECT id, username, net_score FROM users WHERE id=?', (to_id,))
        to_user = c.fetchone()
        
        if not from_user or not to_user:
            print("用户不存在")
            conn.close()
            return
        
        if from_user[2] < amount:
            print(f"余额不足！{from_user[1]} 当前积分: {from_user[2]:+d}")
            conn.close()
            return
        
        print(f"\n转账详情:")
        print(f"转出: {from_user[1]} (当前积分: {from_user[2]:+d})")
        print(f"转入: {to_user[1]} (当前积分: {to_user[2]:+d})")
        print(f"金额: {amount}")
        print(f"转账后 {from_user[1]} 积分: {from_user[2] - amount:+d}")
        print(f"转账后 {to_user[1]} 积分: {to_user[2] + amount:+d}")
        
        reason = input("\n请输入转账原因: ").strip()
        confirm = input("确认转账？(y/n): ").lower()
        
        if confirm == 'y':
            c.execute('UPDATE users SET net_score = net_score - ? WHERE id = ?', 
                     (amount, from_id))
            c.execute('UPDATE users SET net_score = net_score + ? WHERE id = ?', 
                     (amount, to_id))
            conn.commit()
            
            print("✅ 转账成功！")
            
            with open('transfers.log', 'a', encoding='utf-8') as f:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"[{timestamp}] {from_user[1]} -> {to_user[1]} : {amount} 原因: {reason}\n")
        else:
            print("已取消")
        
        conn.close()