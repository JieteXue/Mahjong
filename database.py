# database.py (完整修复版)
import sqlite3

def init_db():
    """初始化数据库，创建所有表"""
    conn = sqlite3.connect('mahjong.db')
    
    # 启用WAL模式（更好的并发和恢复能力）
    conn.execute("PRAGMA journal_mode=WAL")
    
    c = conn.cursor()
    
    # 用户表
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            total_games INTEGER DEFAULT 0,        -- 大局总数
            total_rounds INTEGER DEFAULT 0,       -- 小局总数
            total_wins INTEGER DEFAULT 0,
            net_score INTEGER DEFAULT 0
        )
    ''')
    
    # 赛季表
    c.execute('''
        CREATE TABLE IF NOT EXISTS seasons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            is_active INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            description TEXT
        )
    ''')
    
    # ========== 处理 games 表 ==========
    c.execute("PRAGMA table_info(games)")
    columns = [col[1] for col in c.fetchall()]
    
    if not columns:  # 表不存在，创建新表
        c.execute('''
            CREATE TABLE games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                finished_at TEXT,
                season_id INTEGER,
                player1_id INTEGER,
                player2_id INTEGER,
                player3_id INTEGER,
                player4_id INTEGER,
                final_score1 INTEGER DEFAULT 1000,
                final_score2 INTEGER DEFAULT 1000,
                final_score3 INTEGER DEFAULT 1000,
                final_score4 INTEGER DEFAULT 1000,
                bao TEXT,
                is_finished INTEGER DEFAULT 0,
                total_rounds INTEGER DEFAULT 0,
                dealer_id INTEGER,
                lianzhuang INTEGER DEFAULT 0,
                FOREIGN KEY(season_id) REFERENCES seasons(id),
                FOREIGN KEY(player1_id) REFERENCES users(id),
                FOREIGN KEY(player2_id) REFERENCES users(id),
                FOREIGN KEY(player3_id) REFERENCES users(id),
                FOREIGN KEY(player4_id) REFERENCES users(id),
                FOREIGN KEY(dealer_id) REFERENCES users(id)
            )
        ''')
        print("✅ 创建 games 表")
    else:
        # 检查是否需要重命名旧表并创建新表
        old_columns = ['score1', 'score2', 'score3', 'score4']
        new_columns = ['final_score1', 'final_score2', 'final_score3', 'final_score4', 'finished_at', 'total_rounds']
        
        # 如果还是旧结构（有score1但没有final_score1），需要迁移
        if 'score1' in columns and 'final_score1' not in columns:
            print("⚠️ 检测到旧版games表结构，正在进行数据迁移...")
            
            # 1. 重命名旧表
            c.execute("ALTER TABLE games RENAME TO games_old")
            
            # 2. 创建新表
            c.execute('''
                CREATE TABLE games (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    finished_at TEXT,
                    season_id INTEGER,
                    player1_id INTEGER,
                    player2_id INTEGER,
                    player3_id INTEGER,
                    player4_id INTEGER,
                    final_score1 INTEGER DEFAULT 1000,
                    final_score2 INTEGER DEFAULT 1000,
                    final_score3 INTEGER DEFAULT 1000,
                    final_score4 INTEGER DEFAULT 1000,
                    bao TEXT,
                    is_finished INTEGER DEFAULT 0,
                    total_rounds INTEGER DEFAULT 0,
                    dealer_id INTEGER,
                    lianzhuang INTEGER DEFAULT 0,
                    FOREIGN KEY(season_id) REFERENCES seasons(id),
                    FOREIGN KEY(player1_id) REFERENCES users(id),
                    FOREIGN KEY(player2_id) REFERENCES users(id),
                    FOREIGN KEY(player3_id) REFERENCES users(id),
                    FOREIGN KEY(player4_id) REFERENCES users(id),
                    FOREIGN KEY(dealer_id) REFERENCES users(id)
                )
            ''')
            
            # 3. 迁移数据
            c.execute('''
                INSERT INTO games (
                    id, created_at, season_id, player1_id, player2_id, 
                    player3_id, player4_id, final_score1, final_score2, 
                    final_score3, final_score4, bao, is_finished, dealer_id, lianzhuang
                )
                SELECT 
                    id, created_at, season_id, player1_id, player2_id, 
                    player3_id, player4_id, score1, score2, score3, score4, 
                    bao, is_finished, dealer_id, lianzhuang
                FROM games_old
            ''')
            
            # 4. 删除旧表
            c.execute("DROP TABLE games_old")
            
            print("✅ games表迁移完成")
        else:
            # 检查并添加缺失的列
            if 'finished_at' not in columns:
                c.execute("ALTER TABLE games ADD COLUMN finished_at TEXT")
                print("✅ 添加 finished_at 列")
            
            if 'total_rounds' not in columns:
                c.execute("ALTER TABLE games ADD COLUMN total_rounds INTEGER DEFAULT 0")
                print("✅ 添加 total_rounds 列")
            
            # 检查是否还有score列，需要重命名为final_score
            if 'score1' in columns and 'final_score1' not in columns:
                print("⚠️ 需要重命名分数列...")
                # SQLite不支持直接重命名列，需要重建表
                c.execute("ALTER TABLE games RENAME TO games_temp")
                
                c.execute('''
                    CREATE TABLE games (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        finished_at TEXT,
                        season_id INTEGER,
                        player1_id INTEGER,
                        player2_id INTEGER,
                        player3_id INTEGER,
                        player4_id INTEGER,
                        final_score1 INTEGER DEFAULT 1000,
                        final_score2 INTEGER DEFAULT 1000,
                        final_score3 INTEGER DEFAULT 1000,
                        final_score4 INTEGER DEFAULT 1000,
                        bao TEXT,
                        is_finished INTEGER DEFAULT 0,
                        total_rounds INTEGER DEFAULT 0,
                        dealer_id INTEGER,
                        lianzhuang INTEGER DEFAULT 0,
                        FOREIGN KEY(season_id) REFERENCES seasons(id),
                        FOREIGN KEY(player1_id) REFERENCES users(id),
                        FOREIGN KEY(player2_id) REFERENCES users(id),
                        FOREIGN KEY(player3_id) REFERENCES users(id),
                        FOREIGN KEY(player4_id) REFERENCES users(id),
                        FOREIGN KEY(dealer_id) REFERENCES users(id)
                    )
                ''')
                
                # 构建SELECT语句，包含所有列
                select_cols = ['id', 'created_at', 'finished_at', 'season_id', 
                              'player1_id', 'player2_id', 'player3_id', 'player4_id']
                
                # 重命名分数列
                if 'score1' in columns:
                    select_cols.append('score1 as final_score1')
                if 'score2' in columns:
                    select_cols.append('score2 as final_score2')
                if 'score3' in columns:
                    select_cols.append('score3 as final_score3')
                if 'score4' in columns:
                    select_cols.append('score4 as final_score4')
                
                select_cols.extend(['bao', 'is_finished', 'dealer_id', 'lianzhuang'])
                if 'total_rounds' in columns:
                    select_cols.append('total_rounds')
                
                select_sql = f"INSERT INTO games SELECT {', '.join(select_cols)} FROM games_temp"
                c.execute(select_sql)
                
                c.execute("DROP TABLE games_temp")
                print("✅ 分数列重命名完成")
    
    # ========== 处理 rounds 表 ==========
    c.execute("PRAGMA table_info(rounds)")
    columns = [col[1] for col in c.fetchall()]
    
    if not columns:  # 表不存在
        c.execute('''
            CREATE TABLE rounds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id INTEGER,
                round_number INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                dealer_id INTEGER,
                winner_id INTEGER,
                tai INTEGER DEFAULT 0,
                lianzhuang INTEGER DEFAULT 0,
                score1 INTEGER,
                score2 INTEGER,
                score3 INTEGER,
                score4 INTEGER,
                score_change1 INTEGER,
                score_change2 INTEGER,
                score_change3 INTEGER,
                score_change4 INTEGER,
                FOREIGN KEY(game_id) REFERENCES games(id),
                FOREIGN KEY(dealer_id) REFERENCES users(id),
                FOREIGN KEY(winner_id) REFERENCES users(id)
            )
        ''')
        print("✅ 创建 rounds 表")
    
    # ========== 处理 baiban_records 表 ==========
    c.execute("PRAGMA table_info(baiban_records)")
    columns = [col[1] for col in c.fetchall()]
    
    if not columns:  # 表不存在
        c.execute('''
            CREATE TABLE baiban_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                round_id INTEGER,
                player_id INTEGER,
                count INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(round_id) REFERENCES rounds(id),
                FOREIGN KEY(player_id) REFERENCES users(id)
            )
        ''')
        print("✅ 创建 baiban_records 表")
    
    # ========== 处理 actions 表 ==========
    c.execute("PRAGMA table_info(actions)")
    columns = [col[1] for col in c.fetchall()]
    
    if not columns:  # 表不存在
        c.execute('''
            CREATE TABLE actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id INTEGER,
                round_id INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                action_type TEXT,
                player_id INTEGER,
                score_changes TEXT,
                tai_detail TEXT,
                FOREIGN KEY(game_id) REFERENCES games(id),
                FOREIGN KEY(round_id) REFERENCES rounds(id),
                FOREIGN KEY(player_id) REFERENCES users(id)
            )
        ''')
        print("✅ 创建 actions 表")
    elif 'round_id' not in columns:
        c.execute("ALTER TABLE actions ADD COLUMN round_id INTEGER REFERENCES rounds(id)")
        print("✅ 添加 round_id 列到 actions 表")
    
    # ========== 检查并更新users表 ==========
    c.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in c.fetchall()]
    
    if 'total_rounds' not in columns:
        c.execute("ALTER TABLE users ADD COLUMN total_rounds INTEGER DEFAULT 0")
        print("✅ 添加 total_rounds 列到 users 表")
    
    conn.commit()
    conn.close()
    print("✅ 数据库初始化完成（支持大局/小局记录）")

if __name__ == "__main__":
    init_db()