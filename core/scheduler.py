"""Task scheduler for background monitoring jobs."""
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from core.models import get_db
from monitoring.monitor import check_website
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
        # Get job details
        cursor.execute('''
            SELECT id, name, url, check_interval, match_type, match_pattern,
                   match_condition, email_recipient, is_active,
                   notification_throttle_seconds, status_code_monitor, response_time_threshold,
                   json_path, auth_config, proxy_url, custom_user_agent, capture_screenshot,
                   ai_enabled, ai_prompt, ai_last_result
            FROM monitor_jobs
            WHERE id = ?
        ''', (job_id,))

        job_row = cursor.fetchone()
        if not job_row:
            logger.warning(f"Job {job_id} not found")
            return

        job = {
            'id': job_row[0],
            'name': job_row[1],
            'url': job_row[2],
            'check_interval': job_row[3],
            'match_type': job_row[4],
            'match_pattern': job_row[5],
            'match_condition': job_row[6],
            'email_recipient': job_row[7],
            'is_active': job_row[8],
            'notification_throttle_seconds': 3600 if job_row[9] is None else job_row[9],
            'status_code_monitor': job_row[10],
            'response_time_threshold': job_row[11],
            'json_path': job_row[12] or "",
            'auth_config': job_row[13],
            'proxy_url': job_row[14] or "",
            'custom_user_agent': job_row[15] or "",
            'capture_screenshot': bool(job_row[16]) if len(job_row) > 16 else False,
            'ai_enabled': bool(job_row[17]) if len(job_row) > 17 else False,
            'ai_prompt': job_row[18] if len(job_row) > 18 else None,
            'ai_last_result': job_row[19] if len(job_row) > 19 else None,
        }
        
        # Skip if job is not active
        if not job['is_active']:
            logger.debug(f"Skipping inactive job {job_id}")
            return
        
        logger.info(f"Checking job {job_id}: {job['name']} ({job['url']})")
        
        # Perform check
        result = check_website(job)
        
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
        
        # Optional screenshot on match
        screenshot_path = None
        if result.get('match_found') and job.get('capture_screenshot'):
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
        
        # Send notification if alert condition met (after commit so notification_service can write throttle)
        if should_alert:
            send_notification(job, result)
        
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
