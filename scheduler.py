"""Task scheduler for background monitoring jobs."""
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from models import get_db
from monitor import check_website
from email_service import send_notification

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
                   match_condition, email_recipient, is_active
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
            'is_active': job_row[8]
        }
        
        # Skip if job is not active
        if not job['is_active']:
            logger.debug(f"Skipping inactive job {job_id}")
            return
        
        logger.info(f"Checking job {job_id}: {job['name']} ({job['url']})")
        
        # Perform check
        result = check_website(job)
        
        # Update last_checked timestamp
        cursor.execute('''
            UPDATE monitor_jobs
            SET last_checked = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (job_id,))
        
        # If match found, update last_match timestamp
        if result.get('match_found'):
            cursor.execute('''
                UPDATE monitor_jobs
                SET last_match = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (job_id,))
            
            # Send email notification
            send_notification(job, result)
        
        # Log check history
        cursor.execute('''
            INSERT INTO check_history 
            (job_id, status, match_found, response_time, error_message)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            job_id,
            'success' if result['success'] else 'failed',
            1 if result.get('match_found') else 0,
            result.get('response_time'),
            result.get('error_message')
        ))
        
        conn.commit()
        
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
