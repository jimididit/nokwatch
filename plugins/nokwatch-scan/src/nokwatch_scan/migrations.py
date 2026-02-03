"""Plugin migrations: add scan columns to monitor_jobs."""
import json
import logging
import sqlite3

logger = logging.getLogger(__name__)


def run_migrations(get_db):
    """Add plugin columns to monitor_jobs if they don't exist."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        migrations = [
            ("job_type", "TEXT"),
            ("scan_mode", "TEXT"),
            ("item_extractor_config", "TEXT"),
            ("price_min", "REAL"),
            ("price_max", "REAL"),
            ("seen_item_ids", "TEXT"),
        ]
        for col, typ in migrations:
            try:
                cursor.execute(f"ALTER TABLE monitor_jobs ADD COLUMN {col} {typ}")
                conn.commit()
                logger.info("Added column monitor_jobs.%s", col)
            except sqlite3.OperationalError:
                pass  # Column exists
        conn.close()
    except Exception as e:
        logger.error("Migration failed: %s", e, exc_info=True)
        conn.close()
        raise
