"""Content diff tracking: snapshots and difflib-based diff calculation."""
import difflib
import logging
from typing import Optional, Tuple

from core.models import get_db

logger = logging.getLogger(__name__)

# Max snapshots to keep per job
SNAPSHOT_RETENTION = 10

# Max content length to store (chars) to avoid huge DB
SNAPSHOT_MAX_LENGTH = 100_000

# Max diff lines to store (truncate if larger)
DIFF_MAX_LINES = 500


def save_snapshot(job_id: int, content: str, conn=None) -> Optional[int]:
    """
    Save content as a new snapshot for the job. Prune old snapshots (keep last N).
    Returns snapshot id or None if content empty/invalid.
    If conn is provided, use it (caller owns transaction). Otherwise get_db(), commit, close.
    """
    if not content or not content.strip():
        return None
    truncated = content[:SNAPSHOT_MAX_LENGTH] if len(content) > SNAPSHOT_MAX_LENGTH else content
    own_conn = conn is None
    if own_conn:
        conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            'INSERT INTO content_snapshots (job_id, content) VALUES (?, ?)',
            (job_id, truncated)
        )
        snapshot_id = cursor.lastrowid
        # Prune: keep only last SNAPSHOT_RETENTION per job
        cursor.execute('''
            DELETE FROM content_snapshots
            WHERE job_id = ? AND id NOT IN (
                SELECT id FROM content_snapshots
                WHERE job_id = ?
                ORDER BY id DESC
                LIMIT ?
            )
        ''', (job_id, job_id, SNAPSHOT_RETENTION))
        if own_conn:
            conn.commit()
        return snapshot_id
    except Exception as e:
        logger.error(f"Error saving snapshot for job {job_id}: {e}", exc_info=True)
        if own_conn:
            conn.rollback()
        return None
    finally:
        if own_conn:
            conn.close()


def get_previous_snapshot_content(job_id: int, exclude_snapshot_id: Optional[int] = None, conn=None) -> Optional[str]:
    """Get content of the most recent snapshot for this job (excluding given snapshot id if any)."""
    own_conn = conn is None
    if own_conn:
        conn = get_db()
    cursor = conn.cursor()
    try:
        if exclude_snapshot_id:
            cursor.execute('''
                SELECT content FROM content_snapshots
                WHERE job_id = ? AND id != ?
                ORDER BY id DESC LIMIT 1
            ''', (job_id, exclude_snapshot_id))
        else:
            cursor.execute('''
                SELECT content FROM content_snapshots
                WHERE job_id = ?
                ORDER BY id DESC LIMIT 1
            ''', (job_id,))
        row = cursor.fetchone()
        return row[0] if row else None
    finally:
        if own_conn:
            conn.close()


def compute_diff(old_content: Optional[str], new_content: str) -> str:
    """
    Compute unified diff between old and new content.
    Returns diff text (possibly truncated).
    """
    if not new_content:
        return ""
    old_lines = (old_content or "").splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)
    if not old_lines and not new_lines:
        return ""
    diff = list(difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile="previous",
        tofile="current",
        lineterm=""
    ))
    result = "\n".join(diff[:DIFF_MAX_LINES])
    if len(diff) > DIFF_MAX_LINES:
        result += "\n... (truncated)"
    return result


def save_snapshot_and_diff(job_id: int, current_content: str, conn=None) -> Tuple[Optional[int], str]:
    """
    Save current content as snapshot, get previous content, compute diff.
    Returns (snapshot_id, diff_text).
    If conn is provided, use it for all DB operations (avoids "database is locked" when called from scheduler).
    """
    snapshot_id = save_snapshot(job_id, current_content, conn=conn)
    if snapshot_id is None:
        return None, ""
    # Previous snapshot is the one before this (same query but we just saved, so "previous" is 2nd latest)
    previous = get_previous_snapshot_content(job_id, exclude_snapshot_id=snapshot_id, conn=conn)
    diff_text = compute_diff(previous, current_content[:SNAPSHOT_MAX_LENGTH])
    return snapshot_id, diff_text


def get_diff_for_history(history_id: int) -> Optional[dict]:
    """Get diff data for a check_history entry. Returns dict with diff, snapshot_id or None."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT content_snapshot_id, diff_data
            FROM check_history
            WHERE id = ?
        ''', (history_id,))
        row = cursor.fetchone()
        if not row or row[0] is None:
            return None
        return {
            "content_snapshot_id": row[0],
            "diff_data": row[1] or "",
        }
    finally:
        conn.close()
