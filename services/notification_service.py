"""Unified notification service supporting multiple channels."""
import logging
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from core.models import get_db
from services.email_service import send_notification as send_email_notification
from services.discord_service import send_discord_notification
from services.slack_service import send_slack_notification

logger = logging.getLogger(__name__)

def get_notification_channels(job_id: int) -> List[Dict]:
    """
    Get all notification channels for a job.
    
    Args:
        job_id: ID of the job
    
    Returns:
        List of channel dictionaries with 'channel_type' and 'config' keys
    """
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT channel_type, config
            FROM notification_channels
            WHERE job_id = ?
        ''', (job_id,))
        
        channels = []
        for row in cursor.fetchall():
            try:
                config = json.loads(row[1])
                channels.append({
                    'channel_type': row[0],
                    'config': config
                })
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON config for job {job_id}, channel {row[0]}")
        
        return channels
    finally:
        conn.close()

def check_notification_throttle(job_id: int, throttle_seconds: int) -> bool:
    """
    Check if notification should be throttled (within cooldown period).
    
    Args:
        job_id: ID of the job
        throttle_seconds: Cooldown period in seconds
    
    Returns:
        True if notification should be sent, False if throttled
    """
    if throttle_seconds <= 0:
        return True  # No throttling
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Get last notification time
        cursor.execute('''
            SELECT last_notification_time
            FROM notification_throttles
            WHERE job_id = ?
        ''', (job_id,))
        
        row = cursor.fetchone()
        if not row or not row[0]:
            return True  # No previous notification, allow
        
        last_notification = datetime.fromisoformat(row[0])
        time_since_notification = datetime.now() - last_notification
        
        if time_since_notification.total_seconds() >= throttle_seconds:
            return True  # Cooldown period passed
        
        logger.debug(f"Notification throttled for job {job_id}: {time_since_notification.total_seconds():.0f}s < {throttle_seconds}s")
        return False  # Still in cooldown period
        
    finally:
        conn.close()

def update_notification_throttle(job_id: int):
    """
    Update the last notification time for a job.
    
    Args:
        job_id: ID of the job
    """
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO notification_throttles (job_id, last_notification_time)
            VALUES (?, CURRENT_TIMESTAMP)
        ''', (job_id,))
        conn.commit()
    finally:
        conn.close()

def send_notification(job: Dict, match_status: Dict, is_test: bool = False) -> bool:
    """
    Send notifications through all configured channels for a job.
    
    Args:
        job: Dictionary containing job configuration
        match_status: Dictionary containing match status information
        is_test: Boolean indicating if this is a test notification
    
    Returns:
        Boolean indicating if at least one notification was sent successfully
    """
    job_id = job.get('id')
    
    # For test emails, skip throttle and channel checks, use email_recipient directly
    if is_test:
        if job.get('email_recipient'):
            logger.info(f"Sending test email to {job.get('email_recipient')}")
            return send_email_notification(job, match_status, is_test=True)
        else:
            logger.warning("No email_recipient provided for test email")
            return False
    
    if not job_id:
        logger.warning("Job ID not provided, cannot send notifications")
        return False
    
    # Check throttle (skip for test notifications)
    throttle_seconds = job.get('notification_throttle_seconds', 3600)
    if not check_notification_throttle(job_id, throttle_seconds):
        logger.info(f"Notification throttled for job {job_id}")
        return False
    
    # Get notification channels
    channels = get_notification_channels(job_id)
    if channels:
        logger.info(f"Job {job_id}: sending to {len(channels)} channel(s): {[c['channel_type'] for c in channels]}")
    
    # If no channels configured, fall back to email_recipient (backward compatibility)
    if not channels and job.get('email_recipient'):
        logger.info(f"No notification channels configured for job {job_id}, using email_recipient")
        success = send_email_notification(job, match_status, is_test)
        if success:
            update_notification_throttle(job_id)
        return success
    
    # Send through all configured channels
    success_count = 0
    for channel in channels:
        channel_type = channel['channel_type']
        config = channel['config']
        
        try:
            success = False
            
            if channel_type == 'email':
                # Support multiple email recipients
                email_addresses = config.get('email_addresses', [])
                if isinstance(email_addresses, str):
                    email_addresses = [addr.strip() for addr in email_addresses.split(',')]
                
                for email in email_addresses:
                    job_copy = job.copy()
                    job_copy['email_recipient'] = email.strip()
                    if send_email_notification(job_copy, match_status, is_test):
                        success = True
                        
            elif channel_type == 'discord':
                webhook_url = config.get('webhook_url')
                if webhook_url:
                    success = send_discord_notification(webhook_url, job, match_status, is_test)
                else:
                    logger.warning(f"Discord webhook URL not configured for job {job_id}")
                    
            elif channel_type == 'slack':
                webhook_url = config.get('webhook_url')
                if webhook_url:
                    success = send_slack_notification(webhook_url, job, match_status, is_test)
                else:
                    logger.warning(f"Slack webhook URL not configured for job {job_id}")
            
            if success:
                success_count += 1
                
        except Exception as e:
            logger.error(f"Error sending {channel_type} notification for job {job_id}: {e}", exc_info=True)
    
    # Update throttle if at least one notification succeeded (and not a test)
    if success_count > 0 and not is_test:
        update_notification_throttle(job_id)
    
    return success_count > 0

def add_notification_channel(job_id: int, channel_type: str, config: Dict) -> bool:
    """
    Add a notification channel to a job.
    
    Args:
        job_id: ID of the job
        channel_type: Type of channel ('email', 'discord', 'slack')
        config: Configuration dictionary (will be stored as JSON)
    
    Returns:
        Boolean indicating success
    """
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO notification_channels (job_id, channel_type, config)
            VALUES (?, ?, ?)
        ''', (job_id, channel_type, json.dumps(config)))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error adding notification channel: {e}", exc_info=True)
        conn.rollback()
        return False
    finally:
        conn.close()

def delete_channels_for_job(job_id: int) -> bool:
    """
    Delete all notification channels for a job.
    
    Args:
        job_id: ID of the job
    
    Returns:
        Boolean indicating success
    """
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM notification_channels WHERE job_id = ?', (job_id,))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error deleting channels for job {job_id}: {e}", exc_info=True)
        conn.rollback()
        return False
    finally:
        conn.close()

def remove_notification_channel(channel_id: int) -> bool:
    """
    Remove a notification channel.
    
    Args:
        channel_id: ID of the channel to remove
    
    Returns:
        Boolean indicating success
    """
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('DELETE FROM notification_channels WHERE id = ?', (channel_id,))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Error removing notification channel: {e}", exc_info=True)
        conn.rollback()
        return False
    finally:
        conn.close()

def get_job_notification_channels(job_id: int) -> List[Dict]:
    """
    Get all notification channels for a job with their IDs.
    
    Args:
        job_id: ID of the job
    
    Returns:
        List of channel dictionaries with 'id', 'channel_type', and 'config' keys
    """
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id, channel_type, config
            FROM notification_channels
            WHERE job_id = ?
        ''', (job_id,))
        
        channels = []
        for row in cursor.fetchall():
            try:
                config = json.loads(row[2])
                channels.append({
                    'id': row[0],
                    'channel_type': row[1],
                    'config': config
                })
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON config for channel {row[0]}")
        
        return channels
    finally:
        conn.close()
