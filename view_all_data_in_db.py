# view_complete_db.py
import sqlite3

def view_complete_db():
    """查看数据库中所有的表和完整数据"""
    conn = sqlite3.connect('mahjong.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    print("=" * 80)
    print("数据库完整查看工具")
    print("=" * 80)
    
    # 1. 首先获取所有表
    c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = c.fetchall()
    
    print(f"\n数据库中的所有表 ({len(tables)} 个):")
    for i, table in enumerate(tables, 1):
        print(f"  {i}. {table[0]}")
    
    while True:
        print("\n" + "=" * 80)
        print("请选择操作:")
        print("1. 查看指定表的所有数据")
        print("2. 查看所有表的结构")
        print("3. 搜索特定表")
        print("4. 查看表的数据统计")
        print("5. 执行自定义SQL查询")
        print("0. 退出")
        
        choice = input("\n请选择: ").strip()
        
        if choice == '0':
            break
            
        elif choice == '1':
            # 显示所有表供选择
            print("\n可选的表:")
            for i, table in enumerate(tables, 1):
                print(f"  {i}. {table[0]}")
            
            try:
                idx = int(input("\n请输入表序号: ")) - 1
                if 0 <= idx < len(tables):
                    table_name = tables[idx][0]
                    view_table_data(c, table_name)
                else:
                    print("序号无效")
            except ValueError:
                print("请输入有效数字")
                
        elif choice == '2':
            view_all_table_structures(c, tables)
            
        elif choice == '3':
            search_term = input("请输入要搜索的表名关键词: ").strip()
            found = False
            for table in tables:
                if search_term.lower() in table[0].lower():
                    print(f"  - {table[0]}")
                    found = True
            if not found:
                print("未找到匹配的表")
                
        elif choice == '4':
            show_table_stats(c, tables)
            
        elif choice == '5':
            custom_query(c)
    
    conn.close()
    print("\n感谢使用！")

def view_table_data(c, table_name):
    """查看指定表的所有数据"""
    print(f"\n" + "=" * 60)
    print(f"表: {table_name} - 所有数据")
    print("=" * 60)
    
    # 获取总记录数
    c.execute(f"SELECT COUNT(*) FROM {table_name}")
    total = c.fetchone()[0]
    print(f"总记录数: {total}")
    
    if total == 0:
        print("表是空的")
        return
    
    # 询问是否限制显示
    limit = input(f"\n是否限制显示数量？(直接回车显示全部，或输入数字如100): ").strip()
    
    # 获取表结构
    c.execute(f"PRAGMA table_info({table_name})")
    columns = c.fetchall()
    col_names = [col[1] for col in columns]
    
    # 获取数据
    if limit and limit.isdigit():
        c.execute(f"SELECT * FROM {table_name} LIMIT ?", (int(limit),))
    else:
        c.execute(f"SELECT * FROM {table_name}")
    
    rows = c.fetchall()
    
    if rows:
        # 打印表头
        header = " | ".join([f"{col:15}" for col in col_names])
        print("\n" + header)
        print("-" * len(header))
        
        # 打印数据
        for row in rows:
            row_data = []
            for col in col_names:
                value = row[col]
                if value is None:
                    row_data.append(f"{'NULL':15}")
                else:
                    row_data.append(f"{str(value)[:15]:15}")
            print(" | ".join(row_data))
        
        print(f"\n显示 {len(rows)} 条记录")
    else:
        print("没有数据")

def view_all_table_structures(c, tables):
    """查看所有表的结构"""
    print("\n" + "=" * 60)
    print("所有表的结构")
    print("=" * 60)
    
    for table in tables:
        table_name = table[0]
        print(f"\n--- {table_name} ---")
        
        c.execute(f"PRAGMA table_info({table_name})")
        columns = c.fetchall()
        for col in columns:
            col_id, col_name, col_type, not_null, default, pk = col
            pk_flag = "PRIMARY KEY" if pk else ""
            not_null_flag = "NOT NULL" if not_null else ""
            default_flag = f"DEFAULT {default}" if default else ""
            flags = " ".join([f for f in [pk_flag, not_null_flag, default_flag] if f])
            print(f"  {col_name:20} {col_type:10} {flags}")

def show_table_stats(c, tables):
    """查看每个表的数据统计"""
    print("\n" + "=" * 60)
    print("表数据统计")
    print("=" * 60)
    
    for table in tables:
        table_name = table[0]
        c.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = c.fetchone()[0]
        print(f"  {table_name:20} : {count:6d} 条记录")

def custom_query(c):
    """执行自定义SQL查询"""
    print("\n" + "=" * 60)
    print("自定义SQL查询")
    print("=" * 60)
    print("(输入 'exit' 返回)")
    
    while True:
        query = input("\nSQL> ").strip()
        if query.lower() == 'exit':
            break
        
        if not query:
            continue
        
        try:
            c.execute(query)
            
            # 如果是SELECT查询，显示结果
            if query.strip().upper().startswith('SELECT'):
                rows = c.fetchall()
                if rows:
                    # 获取列名
                    col_names = [description[0] for description in c.description]
                    print("\n" + " | ".join(col_names))
                    print("-" * 80)
                    
                    for row in rows:
                        print(" | ".join(str(val) if val is not None else 'NULL' for val in row))
                    
                    print(f"\n返回 {len(rows)} 行")
                else:
                    print("查询无结果")
            else:
                # 非SELECT查询
                print(f"执行成功，影响行数: {c.rowcount}")
                
        except Exception as e:
            print(f"错误: {e}")

def view_all_tables(c, tables):
    """查看所有表的数据"""
    print("\n" + "=" * 60)
    print("所有表的数据")
    print("=" * 60)
    
    for table in tables:
        table_name = table[0]
        print(f"\n>>> {table_name} <<<")
        
        c.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = c.fetchone()[0]
        print(f"记录数: {count}")
        
        if count > 0:
            show = input(f"  显示 {table_name} 的数据？(y/n): ").lower()
            if show == 'y':
                limit = input("    限制显示数量？(直接回车显示全部，或输入数字): ").strip()
                
                c.execute(f"PRAGMA table_info({table_name})")
                columns = c.fetchall()
                col_names = [col[1] for col in columns]
                
                if limit and limit.isdigit():
                    c.execute(f"SELECT * FROM {table_name} LIMIT ?", (int(limit),))
                else:
                    c.execute(f"SELECT * FROM {table_name}")
                
                rows = c.fetchall()
                if rows:
                    # 打印前几行
                    for i, row in enumerate(rows[:5]):
                        print(f"    行{i+1}: {dict(row)}")
                    if len(rows) > 5:
                        print(f"    ... 还有 {len(rows)-5} 行")

if __name__ == "__main__":
    view_complete_db()