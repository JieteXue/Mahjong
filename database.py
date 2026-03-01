# database.py
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
            total_games INTEGER DEFAULT 0,
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
    
    # 检查games表是否已有season_id列
    c.execute("PRAGMA table_info(games)")
    columns = [col[1] for col in c.fetchall()]
    
    if not columns:  # 表不存在
        # 牌局表（带season_id）
        c.execute('''
            CREATE TABLE games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                season_id INTEGER,
                player1_id INTEGER,
                player2_id INTEGER,
                player3_id INTEGER,
                player4_id INTEGER,
                score1 INTEGER DEFAULT 1000,
                score2 INTEGER DEFAULT 1000,
                score3 INTEGER DEFAULT 1000,
                score4 INTEGER DEFAULT 1000,
                dealer_id INTEGER,
                lianzhuang INTEGER DEFAULT 0,
                bao TEXT,
                is_finished INTEGER DEFAULT 0,
                FOREIGN KEY(season_id) REFERENCES seasons(id),
                FOREIGN KEY(player1_id) REFERENCES users(id),
                FOREIGN KEY(player2_id) REFERENCES users(id),
                FOREIGN KEY(player3_id) REFERENCES users(id),
                FOREIGN KEY(player4_id) REFERENCES users(id),
                FOREIGN KEY(dealer_id) REFERENCES users(id)
            )
        ''')
        print("✅ 创建 games 表")
    elif 'season_id' not in columns:
        # 添加season_id列
        c.execute("ALTER TABLE games ADD COLUMN season_id INTEGER REFERENCES seasons(id)")
        print("✅ 添加 season_id 列到 games 表")
    
    # 操作记录表
    c.execute('''
        CREATE TABLE IF NOT EXISTS actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            action_type TEXT,
            player_id INTEGER,
            score_changes TEXT,
            tai_detail TEXT,
            FOREIGN KEY(game_id) REFERENCES games(id),
            FOREIGN KEY(player_id) REFERENCES users(id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("数据库初始化完成")

if __name__ == "__main__":
    init_db()