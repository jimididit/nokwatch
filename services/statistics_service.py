"""Statistics calculation from check_history for dashboard."""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from core.models import get_db

logger = logging.getLogger(__name__)


def get_global_stats(hours: int = 24) -> Dict:
    """
    Aggregate stats from check_history for the last N hours.
    Returns: total_checks, success_count, failed_count, match_count, avg_response_time, success_rate_pct.
    """
    conn = get_db()
    cursor = conn.cursor()
    try:
        since = (datetime.now() - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_count,
                SUM(CASE WHEN match_found = 1 THEN 1 ELSE 0 END) as match_count,
                AVG(CASE WHEN response_time IS NOT NULL THEN response_time END) as avg_response_time
            FROM check_history
            WHERE timestamp >= ?
        """, (since,))
        row = cursor.fetchone()
        total = row[0] or 0
        success_count = row[1] or 0
        failed_count = row[2] or 0
        match_count = row[3] or 0
        avg_rt = row[4]
        success_rate = (100.0 * success_count / total) if total else 0
        return {
            "total_checks": total,
            "success_count": success_count,
            "failed_count": failed_count,
            "match_count": match_count,
            "avg_response_time_seconds": round(avg_rt, 2) if avg_rt is not None else None,
            "success_rate_pct": round(success_rate, 1),
            "period_hours": hours,
        }
    except Exception as e:
        logger.error(f"Error computing global stats: {e}", exc_info=True)
        return {
            "total_checks": 0,
            "success_count": 0,
            "failed_count": 0,
            "match_count": 0,
            "avg_response_time_seconds": None,
            "success_rate_pct": 0,
            "period_hours": hours,
        }
    finally:
        conn.close()


def get_job_stats(job_id: int, hours: int = 24) -> Dict:
    """Per-job stats for the last N hours."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        since = (datetime.now() - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
                SUM(CASE WHEN match_found = 1 THEN 1 ELSE 0 END) as match_count,
                AVG(CASE WHEN response_time IS NOT NULL THEN response_time END) as avg_response_time
            FROM check_history
            WHERE job_id = ? AND timestamp >= ?
        """, (job_id, since))
        row = cursor.fetchone()
        total = row[0] or 0
        success_count = row[1] or 0
        match_count = row[2] or 0
        avg_rt = row[3]
        success_rate = (100.0 * success_count / total) if total else 0
        return {
            "job_id": job_id,
            "total_checks": total,
            "success_count": success_count,
            "match_count": match_count,
            "avg_response_time_seconds": round(avg_rt, 2) if avg_rt is not None else None,
            "success_rate_pct": round(success_rate, 1),
            "period_hours": hours,
        }
    except Exception as e:
        logger.error(f"Error computing job stats: {e}", exc_info=True)
        return {
            "job_id": job_id,
            "total_checks": 0,
            "success_count": 0,
            "match_count": 0,
            "avg_response_time_seconds": None,
            "success_rate_pct": 0,
            "period_hours": hours,
        }
    finally:
        conn.close()


def get_checks_over_time(hours: int = 24, bucket_hours: int = 1) -> List[Dict]:
    """
    Bucketed check counts over time for a simple chart.
    Returns list of { period_start, total, success_count, match_count }.
    """
    conn = get_db()
    cursor = conn.cursor()
    try:
        since = (datetime.now() - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            SELECT
                strftime('%Y-%m-%d %H:00:00', timestamp) as period_start,
                COUNT(*) as total,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
                SUM(CASE WHEN match_found = 1 THEN 1 ELSE 0 END) as match_count
            FROM check_history
            WHERE timestamp >= ?
            GROUP BY period_start
            ORDER BY period_start
        """, (since,))
        rows = cursor.fetchall()
        return [
            {
                "period_start": row[0],
                "total": row[1],
                "success_count": row[2],
                "match_count": row[3],
            }
            for row in rows
        ]
    except Exception as e:
        logger.error(f"Error computing checks over time: {e}", exc_info=True)
        return []
    finally:
        conn.close()
