"""Task scheduler for background monitoring jobs."""
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from core.models import get_db
from core.crypto import decrypt_credentials
from core.plugins import get_check_handler
from services.notification_service import send_notification
from services.diff_service import save_snapshot_and_diff
from services.screenshot_service import capture_screenshot

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

def run_check(job_id: int):
    """
    Run a check for a specific monitoring job.
    
    Args:
        job_id: ID of the job to check
    """
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Get job details (SELECT * so plugin-added columns flow through)
        cursor.execute('SELECT * FROM monitor_jobs WHERE id = ?', (job_id,))
        job_row = cursor.fetchone()
        if not job_row:
            logger.warning(f"Job {job_id} not found")
            return

        # Build job dict from row (supports plugin-added columns)
        job = dict(job_row)
        # Decrypt auth_config
        if job.get('auth_config'):
            job['auth_config'] = decrypt_credentials(job['auth_config'])
        # Normalize booleans and defaults
        job['notification_throttle_seconds'] = 3600 if job.get('notification_throttle_seconds') is None else job['notification_throttle_seconds']
        job['json_path'] = job.get('json_path') or ""
        job['proxy_url'] = job.get('proxy_url') or ""
        job['custom_user_agent'] = job.get('custom_user_agent') or ""
        job['capture_screenshot'] = bool(job.get('capture_screenshot'))
        job['ai_enabled'] = bool(job.get('ai_enabled'))
        
        # Skip if job is not active
        if not job['is_active']:
            logger.debug(f"Skipping inactive job {job_id}")
            return
        
        logger.info(f"Checking job {job_id}: {job['name']} ({job['url']})")

        # Perform check (dispatch to plugin handler or default check_website)
        handler = get_check_handler(job)
        result = handler(job)
        
        # Check HTTP status code monitoring
        should_alert = False
        alert_reason = None
        
        if result.get('match_found'):
            should_alert = True
            alert_reason = "match_found"
        
        # Check HTTP status code monitoring
        if job.get('status_code_monitor') and result.get('http_status_code'):
            if result['http_status_code'] == job['status_code_monitor']:
                should_alert = True
                alert_reason = f"status_code_{result['http_status_code']}"
        
        # Check response time threshold
        if job.get('response_time_threshold') and result.get('response_time'):
            if result['response_time'] > job['response_time_threshold']:
                should_alert = True
                alert_reason = "response_time_threshold"
        
        # Update last_checked timestamp (local time)
        cursor.execute('''
            UPDATE monitor_jobs
            SET last_checked = datetime('now', 'localtime')
            WHERE id = ?
        ''', (job_id,))
        
        # If match found, update last_match timestamp (local time)
        if result.get('match_found'):
            cursor.execute('''
                UPDATE monitor_jobs
                SET last_match = datetime('now', 'localtime')
                WHERE id = ?
            ''', (job_id,))

        # Store AI analysis result for next comparison
        ai_result = result.get('ai_analysis_result')
        if ai_result is not None:
            cursor.execute('''
                UPDATE monitor_jobs
                SET ai_last_result = ?
                WHERE id = ?
            ''', (ai_result, job_id))

        # Content diff tracking: save snapshot and compute diff when match found (use same conn to avoid DB lock)
        content_snapshot_id = None
        diff_data = None
        if result.get('match_found') and result.get('text_content'):
            snapshot_id, diff_text = save_snapshot_and_diff(job_id, result['text_content'], conn=conn)
            content_snapshot_id = snapshot_id
            diff_data = diff_text if diff_text else None
        
        # Optional screenshot on match (or first matched item when plugin returns matched_items)
        screenshot_path = None
        if result.get('match_found') and job.get('capture_screenshot'):
            if result.get('matched_items'):
                # Plugin returned item URLs; screenshot first item
                first_item = result['matched_items'][0]
                item_url = first_item.get('url') or job['url']
                screenshot_path = capture_screenshot(item_url, job_id, suffix="_item0")
            else:
                screenshot_path = capture_screenshot(job['url'], job_id)
        
        # Log check history (include content_snapshot_id, diff_data, screenshot_path when present); timestamp in local time
        now_local = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT INTO check_history 
            (job_id, timestamp, status, match_found, response_time, error_message, http_status_code, content_snapshot_id, diff_data, screenshot_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            job_id,
            now_local,
            'success' if result['success'] else 'failed',
            1 if result.get('match_found') else 0,
            result.get('response_time'),
            result.get('error_message'),
            result.get('http_status_code'),
            content_snapshot_id,
            diff_data,
            screenshot_path
        ))
        
        # Commit and release DB lock before sending notifications (avoids "database is locked")
        conn.commit()

        # Build match_status for notification (include matched_items, screenshot_path from plugins)
        match_status = dict(result)
        if screenshot_path:
            match_status['screenshot_path'] = screenshot_path

        # Send notification if alert condition met (after commit so notification_service can write throttle)
        if should_alert:
            send_notification(job, match_status)
        
        if result['success']:
            logger.info(f"Check completed for job {job_id}: match={result.get('match_found')}")
        else:
            logger.warning(f"Check failed for job {job_id}: {result.get('error_message')}")
            
    except Exception as e:
        logger.error(f"Error running check for job {job_id}: {e}", exc_info=True)
        conn.rollback()
    finally:
        conn.close()

def add_job_to_scheduler(job_id: int, check_interval: int):
    """
    Add a monitoring job to the scheduler.
    
    Args:
        job_id: ID of the job
        check_interval: Interval in seconds between checks
    """
    job_id_str = f"monitor_job_{job_id}"
    
    # Remove existing job if it exists
    try:
        scheduler.remove_job(job_id_str)
    except:
        pass
    
    # Add new job
    scheduler.add_job(
        run_check,
        trigger=IntervalTrigger(seconds=check_interval),
        args=[job_id],
        id=job_id_str,
        replace_existing=True
    )
    
    logger.info(f"Added job {job_id} to scheduler with interval {check_interval}s")

def remove_job_from_scheduler(job_id: int):
    """
    Remove a monitoring job from the scheduler.
    
    Args:
        job_id: ID of the job
    """
    job_id_str = f"monitor_job_{job_id}"
    
    try:
        scheduler.remove_job(job_id_str)
        logger.info(f"Removed job {job_id} from scheduler")
    except:
        pass

def reload_all_jobs():
    """Reload all active jobs into the scheduler."""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id, check_interval, is_active
            FROM monitor_jobs
        ''')
        
        jobs = cursor.fetchall()
        
        for job in jobs:
            job_id, check_interval, is_active = job
            if is_active:
                add_job_to_scheduler(job_id, check_interval)
            else:
                remove_job_from_scheduler(job_id)
        
        logger.info(f"Reloaded {len(jobs)} jobs into scheduler")
    except Exception as e:
        logger.error(f"Error reloading jobs: {e}", exc_info=True)
    finally:
        conn.close()

def start_scheduler():
    """Start the background scheduler."""
    if not scheduler.running:
        scheduler.start()
        reload_all_jobs()
        logger.info("Scheduler started")

def stop_scheduler():
    """Stop the background scheduler."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")
