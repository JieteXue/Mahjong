# maintenance_manager.py
import sqlite3
import os
import shutil
from datetime import datetime

class MaintenanceManager:
    def __init__(self, db_path='mahjong.db'):
        self.db_path = db_path
    
    def get_all_tables(self):
        """获取数据库中所有表名"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in c.fetchall()]
        conn.close()
        return tables
    
    def backup_database(self):
        """备份数据库"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"mahjong_backup_{timestamp}.db"
        
        try:
            shutil.copy2(self.db_path, backup_file)
            print(f"✅ 数据库已备份到: {backup_file}")
            return backup_file
        except Exception as e:
            print(f"❌ 备份失败: {e}")
            return None
    
    def clear_all_data(self):
        """清空所有数据"""
        print("\n⚠️  警告：这将删除所有用户、大局、小局、赛季数据！")
        
        # 先备份
        backup_file = self.backup_database()
        if not backup_file:
            confirm = input("备份失败，继续清空？(y/n): ").lower()
            if confirm != 'y':
                return False
        
        confirm1 = input("请输入 'DELETE' 确认: ").strip()
        if confirm1 != 'DELETE':
            print("操作已取消")
            return False
        
        confirm2 = input("最后确认？(y/n): ").lower()
        if confirm2 != 'y':
            print("操作已取消")
            return False
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # 按照外键依赖顺序删除（先删子表，再删父表）
        delete_order = [
            'baiban_records',
            'actions',
            'rounds',
            'games',
            'seasons',
            'users'
        ]
        
        tables = self.get_all_tables()
        deleted_count = 0
        
        for table in delete_order:
            if table in tables:
                try:
                    c.execute(f"DELETE FROM {table}")
                    print(f"✅ 清空 {table} 表")
                    deleted_count += 1
                except Exception as e:
                    print(f"❌ 清空 {table} 表失败: {e}")
        
        # 重置自增序列
        try:
            c.execute("DELETE FROM sqlite_sequence")
            print("✅ 重置自增序列")
        except:
            pass  # sqlite_sequence 可能不存在
        
        conn.commit()
        conn.close()
        
        print(f"\n✅ 数据清空完成！共清空 {deleted_count} 张表")
        return True
    
    def clear_games_only(self):
        """只清空大局记录"""
        print("\n⚠️  警告：这将删除所有大局、小局和操作记录！")
        
        backup_file = self.backup_database()
        if not backup_file:
            confirm = input("备份失败，继续清空？(y/n): ").lower()
            if confirm != 'y':
                return False
        
        confirm = input("确定清空？(y/n): ").lower()
        if confirm != 'y':
            print("操作已取消")
            return False
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        tables = self.get_all_tables()
        results = {}
        
        # 按照依赖顺序删除
        delete_order = ['baiban_records', 'actions', 'rounds', 'games']
        
        for table in delete_order:
            if table in tables:
                try:
                    c.execute(f"DELETE FROM {table}")
                    count = c.rowcount
                    results[table] = count
                    print(f"✅ 清空 {table} 表，删除 {count} 条记录")
                except Exception as e:
                    print(f"❌ 清空 {table} 表失败: {e}")
        
        conn.commit()
        conn.close()
        
        print("\n✅ 大局记录已清空！")
        return True
    
    def clear_rounds_only(self):
        """只清空小局记录"""
        print("\n⚠️  警告：这将删除所有小局记录和操作记录，但保留大局框架！")
        
        backup_file = self.backup_database()
        if not backup_file:
            confirm = input("备份失败，继续清空？(y/n): ").lower()
            if confirm != 'y':
                return False
        
        confirm = input("确定清空？(y/n): ").lower()
        if confirm != 'y':
            print("操作已取消")
            return False
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        tables = self.get_all_tables()
        results = {}
        
        # 清空小局相关表
        delete_order = ['baiban_records', 'actions', 'rounds']
        
        for table in delete_order:
            if table in tables:
                try:
                    c.execute(f"DELETE FROM {table}")
                    count = c.rowcount
                    results[table] = count
                    print(f"✅ 清空 {table} 表，删除 {count} 条记录")
                except Exception as e:
                    print(f"❌ 清空 {table} 表失败: {e}")
        
        # 重置大局中的小局数
        if 'games' in tables:
            try:
                c.execute("UPDATE games SET total_rounds = 0")
                print("✅ 重置大局小局计数")
            except Exception as e:
                print(f"❌ 重置大局小局计数失败: {e}")
        
        conn.commit()
        conn.close()
        
        print("\n✅ 小局记录已清空！")
        return True
    
    def clear_actions_only(self):
        """只清空操作记录"""
        print("\n⚠️  警告：这将删除所有操作记录！")
        
        backup_file = self.backup_database()
        if not backup_file:
            confirm = input("备份失败，继续清空？(y/n): ").lower()
            if confirm != 'y':
                return False
        
        confirm = input("确定清空？(y/n): ").lower()
        if confirm != 'y':
            print("操作已取消")
            return False
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        tables = self.get_all_tables()
        
        if 'actions' in tables:
            try:
                c.execute("DELETE FROM actions")
                count = c.rowcount
                print(f"✅ 清空 actions 表，删除 {count} 条记录")
            except Exception as e:
                print(f"❌ 清空 actions 表失败: {e}")
        else:
            print("⚠️ actions 表不存在")
        
        conn.commit()
        conn.close()
        
        print("\n✅ 操作记录已清空！")
        return True
    
    def reset_user_scores(self):
        """重置用户积分"""
        print("\n⚠️  警告：这将重置所有用户积分为0")
        
        backup_file = self.backup_database()
        if not backup_file:
            confirm = input("备份失败，继续重置？(y/n): ").lower()
            if confirm != 'y':
                return False
        
        confirm = input("确定重置？(y/n): ").lower()
        if confirm != 'y':
            print("操作已取消")
            return False
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        try:
            c.execute('''
                UPDATE users SET 
                    total_games = 0,
                    total_rounds = 0,
                    total_wins = 0,
                    net_score = 0
            ''')
            count = c.rowcount
            print(f"✅ 已重置 {count} 个用户的积分")
        except Exception as e:
            print(f"❌ 重置用户积分失败: {e}")
        
        conn.commit()
        conn.close()
        
        return True
    
    def vacuum_database(self):
        """压缩数据库"""
        print("\n正在压缩数据库...")
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("VACUUM")
            conn.close()
            print("✅ 数据库压缩完成")
            return True
        except Exception as e:
            print(f"❌ 数据库压缩失败: {e}")
            return False
    
    def check_database_integrity(self):
        """检查数据库完整性"""
        print("\n正在检查数据库完整性...")
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        try:
            c.execute("PRAGMA integrity_check")
            result = c.fetchone()
            if result[0] == "ok":
                print("✅ 数据库完整性检查通过")
            else:
                print(f"⚠️ 数据库完整性检查结果: {result[0]}")
        except Exception as e:
            print(f"❌ 数据库完整性检查失败: {e}")
        
        # 显示数据库统计信息
        tables = self.get_all_tables()
        print(f"\n📊 数据库统计:")
        for table in tables:
            try:
                c.execute(f"SELECT COUNT(*) FROM {table}")
                count = c.fetchone()[0]
                print(f"  {table}: {count} 条记录")
            except:
                pass
        
        conn.close()
        return True
    
    def export_to_csv(self):
        """导出数据到CSV"""
        import csv
        
        print("\n正在导出数据到CSV...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_dir = f"export_{timestamp}"
        
        try:
            os.makedirs(export_dir, exist_ok=True)
            
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            tables = self.get_all_tables()
            
            for table in tables:
                c.execute(f"SELECT * FROM {table}")
                rows = c.fetchall()
                
                # 获取列名
                c.execute(f"PRAGMA table_info({table})")
                columns = [col[1] for col in c.fetchall()]
                
                # 写入CSV
                filename = f"{export_dir}/{table}.csv"
                with open(filename, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(columns)
                    writer.writerows(rows)
                
                print(f"✅ 导出 {table} 到 {filename} ({len(rows)} 条记录)")
            
            conn.close()
            print(f"\n✅ 所有数据已导出到 {export_dir}/ 目录")
            
        except Exception as e:
            print(f"❌ 导出失败: {e}")