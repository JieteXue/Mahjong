# upgrade_db_for_rounds.py
import sqlite3

def upgrade_db():
    """升级数据库，添加大局/小局支持（去掉大局胜）"""
    conn = sqlite3.connect('mahjong.db')
    c = conn.cursor()
    
    print("开始升级数据库，添加大局/小局支持...")
    
    # 1. 检查games表是否有小局相关字段
    c.execute("PRAGMA table_info(games)")
    columns = [col[1] for col in c.fetchall()]
    
    if 'big_game_id' not in columns:
        c.execute("ALTER TABLE games ADD COLUMN big_game_id INTEGER DEFAULT 0")
        print("✅ 添加 big_game_id 列")
    
    if 'round_number' not in columns:
        c.execute("ALTER TABLE games ADD COLUMN round_number INTEGER DEFAULT 1")
        print("✅ 添加 round_number 列")
    
    # 2. 创建大局表
    c.execute('''
        CREATE TABLE IF NOT EXISTS big_games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            season_id INTEGER,
            player1_id INTEGER,
            player2_id INTEGER,
            player3_id INTEGER,
            player4_id INTEGER,
            start_scores TEXT,  -- JSON格式存储初始分数
            end_scores TEXT,     -- JSON格式存储结束分数
            round_count INTEGER DEFAULT 0,
            is_finished INTEGER DEFAULT 0,
            FOREIGN KEY(season_id) REFERENCES seasons(id),
            FOREIGN KEY(player1_id) REFERENCES users(id),
            FOREIGN KEY(player2_id) REFERENCES users(id),
            FOREIGN KEY(player3_id) REFERENCES users(id),
            FOREIGN KEY(player4_id) REFERENCES users(id)
        )
    ''')
    print("✅ 创建 big_games 表")
    
    # 3. 为用户表添加大局统计字段（只加大局数，不加大局胜）
    c.execute("PRAGMA table_info(users)")
    user_columns = [col[1] for col in c.fetchall()]
    
    if 'total_big_games' not in user_columns:
        c.execute("ALTER TABLE users ADD COLUMN total_big_games INTEGER DEFAULT 0")
        print("✅ 添加 total_big_games 列")
    
    if 'total_small_games' not in user_columns:
        c.execute("ALTER TABLE users ADD COLUMN total_small_games INTEGER DEFAULT 0")
        print("✅ 添加 total_small_games 列")
    
    # 如果有旧的total_big_wins字段，可以选择删除（但SQLite不支持直接删除列）
    # 这里我们只是不再使用它
    
    conn.commit()
    conn.close()
    
    print("\n🎉 数据库升级完成！现在支持大局/小局统计（大局胜已移除）")

if __name__ == "__main__":
    upgrade_db()