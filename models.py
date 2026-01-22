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
            last_match TIMESTAMP,
            notification_throttle_seconds INTEGER DEFAULT 3600,
            status_code_monitor INTEGER,
            response_time_threshold REAL
        )
    ''')
    
    # Migrate existing tables - add new columns if they don't exist
    try:
        cursor.execute('ALTER TABLE monitor_jobs ADD COLUMN notification_throttle_seconds INTEGER DEFAULT 3600')
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cursor.execute('ALTER TABLE monitor_jobs ADD COLUMN status_code_monitor INTEGER')
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cursor.execute('ALTER TABLE monitor_jobs ADD COLUMN response_time_threshold REAL')
    except sqlite3.OperationalError:
        pass  # Column already exists
    
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
            http_status_code INTEGER,
            FOREIGN KEY (job_id) REFERENCES monitor_jobs(id) ON DELETE CASCADE
        )
    ''')
    
    # Migrate check_history - add http_status_code if it doesn't exist
    try:
        cursor.execute('ALTER TABLE check_history ADD COLUMN http_status_code INTEGER')
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # Create NotificationChannels table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notification_channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            channel_type TEXT NOT NULL CHECK(channel_type IN ('email', 'discord', 'slack')),
            config TEXT NOT NULL,
            FOREIGN KEY (job_id) REFERENCES monitor_jobs(id) ON DELETE CASCADE
        )
    ''')
    
    # Create NotificationThrottles table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notification_throttles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            last_notification_time TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES monitor_jobs(id) ON DELETE CASCADE,
            UNIQUE(job_id)
        )
    ''')
    
    # Create indexes for better query performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_job_id ON check_history(job_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON check_history(timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_is_active ON monitor_jobs(is_active)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_notification_channels_job_id ON notification_channels(job_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_notification_throttles_job_id ON notification_throttles(job_id)')
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully!")
