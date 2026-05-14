import sqlite3
from pathlib import Path
from datetime import datetime

def init_db(base_dir: Path):
    db_path = base_dir / "sort_log.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sort_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            original_filename TEXT,
            new_filename TEXT,
            destination_folder TEXT,
            year TEXT,
            evaluation_rule TEXT
        )
    ''')
    conn.commit()
    conn.close()

def log_to_db(base_dir: Path, original_filename: str, new_filename: str, destination_folder: str, year: str, evaluation_rule: str):
    db_path = base_dir / "sort_log.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO sort_logs (original_filename, new_filename, destination_folder, year, evaluation_rule)
        VALUES (?, ?, ?, ?, ?)
    ''', (original_filename, new_filename, destination_folder, year, evaluation_rule))
    conn.commit()
    conn.close()

def get_recent_logs(base_dir: Path, limit: int = 50):
    db_path = base_dir / "sort_log.db"
    if not db_path.exists():
        return []
        
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM sort_logs
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (limit,))
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]
