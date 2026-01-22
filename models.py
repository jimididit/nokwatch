"""Database models for the website monitoring application."""
import sqlite3
from datetime import datetime
from pathlib import Path
from config import Config

def get_db():
    """Get database connection."""
    db_path = Path(Config.DATABASE_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with required tables."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Create MonitorJob table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS monitor_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            check_interval INTEGER NOT NULL,
            match_type TEXT NOT NULL CHECK(match_type IN ('string', 'regex')),
            match_pattern TEXT NOT NULL,
            match_condition TEXT NOT NULL CHECK(match_condition IN ('contains', 'not_contains')),
            email_recipient TEXT NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_checked TIMESTAMP,
            last_match TIMESTAMP
        )
    ''')
    
    # Create CheckHistory table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS check_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT NOT NULL CHECK(status IN ('success', 'failed')),
            match_found INTEGER NOT NULL DEFAULT 0,
            response_time REAL,
            error_message TEXT,
            FOREIGN KEY (job_id) REFERENCES monitor_jobs(id) ON DELETE CASCADE
        )
    ''')
    
    # Create indexes for better query performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_job_id ON check_history(job_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON check_history(timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_is_active ON monitor_jobs(is_active)')
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully!")
