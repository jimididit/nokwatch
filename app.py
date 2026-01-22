"""Main Flask application for website monitoring tool."""
import logging
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from models import get_db, init_db
from scheduler import start_scheduler, add_job_to_scheduler, remove_job_from_scheduler, reload_all_jobs
from config import Config
from notification_service import (
    send_notification, add_notification_channel, remove_notification_channel,
    get_job_notification_channels
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY

# Initialize database
init_db()

# Start scheduler
start_scheduler()

@app.route('/')
def index():
    """Render main dashboard."""
    return render_template('index.html')

@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    """Get all monitoring jobs."""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id, name, url, check_interval, match_type, match_pattern,
                   match_condition, email_recipient, is_active,
                   created_at, last_checked, last_match,
                   notification_throttle_seconds, status_code_monitor, response_time_threshold
            FROM monitor_jobs
            ORDER BY created_at DESC
        ''')
        
        jobs = []
        for row in cursor.fetchall():
            job_data = {
                'id': row[0],
                'name': row[1],
                'url': row[2],
                'check_interval': row[3],
                'match_type': row[4],
                'match_pattern': row[5],
                'match_condition': row[6],
                'email_recipient': row[7],
                'is_active': bool(row[8]),
                'created_at': row[9],
                'last_checked': row[10],
                'last_match': row[11],
                'notification_throttle_seconds': row[12] or 3600,
                'status_code_monitor': row[13],
                'response_time_threshold': row[14]
            }
            # Get notification channels for this job
            job_data['notification_channels'] = get_job_notification_channels(row[0])
            jobs.append(job_data)
        
        return jsonify({'jobs': jobs})
    except Exception as e:
        logger.error(f"Error fetching jobs: {e}", exc_info=True)
        return jsonify({'error': 'Failed to fetch jobs'}), 500
    finally:
        conn.close()

@app.route('/api/jobs', methods=['POST'])
def create_job():
    """Create a new monitoring job."""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['name', 'url', 'check_interval', 'match_type', 
                      'match_pattern', 'match_condition', 'email_recipient']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # Validate match_type
    if data['match_type'] not in ['string', 'regex']:
        return jsonify({'error': 'match_type must be "string" or "regex"'}), 400
    
    # Validate match_condition
    if data['match_condition'] not in ['contains', 'not_contains']:
        return jsonify({'error': 'match_condition must be "contains" or "not_contains"'}), 400
    
    # Validate check_interval
    try:
        check_interval = int(data['check_interval'])
        if check_interval < 30:
            return jsonify({'error': 'check_interval must be at least 30 seconds'}), 400
    except (ValueError, TypeError):
        return jsonify({'error': 'check_interval must be a valid integer'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Get optional fields with defaults
        notification_throttle = data.get('notification_throttle_seconds', 3600)
        status_code_monitor = data.get('status_code_monitor')
        response_time_threshold = data.get('response_time_threshold')
        
        cursor.execute('''
            INSERT INTO monitor_jobs 
            (name, url, check_interval, match_type, match_pattern, 
             match_condition, email_recipient, is_active,
             notification_throttle_seconds, status_code_monitor, response_time_threshold)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['name'],
            data['url'],
            check_interval,
            data['match_type'],
            data['match_pattern'],
            data['match_condition'],
            data['email_recipient'],
            1 if data.get('is_active', True) else 0,
            notification_throttle,
            status_code_monitor,
            response_time_threshold
        ))
        
        job_id = cursor.lastrowid
        conn.commit()
        
        # Add notification channels if provided
        if 'notification_channels' in data:
            for channel in data['notification_channels']:
                channel_type = channel.get('channel_type')
                config = channel.get('config', {})
                if channel_type and config:
                    add_notification_channel(job_id, channel_type, config)
        
        # Add job to scheduler if active
        if data.get('is_active', True):
            add_job_to_scheduler(job_id, check_interval)
        
        logger.info(f"Created job {job_id}: {data['name']}")
        
        return jsonify({'id': job_id, 'message': 'Job created successfully'}), 201
        
    except Exception as e:
        logger.error(f"Error creating job: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'error': 'Failed to create job'}), 500
    finally:
        conn.close()

@app.route('/api/jobs/<int:job_id>', methods=['PUT'])
def update_job(job_id):
    """Update an existing monitoring job."""
    data = request.get_json()
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Get current job
        cursor.execute('SELECT id, check_interval, is_active FROM monitor_jobs WHERE id = ?', (job_id,))
        job = cursor.fetchone()
        
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        
        # Build update query dynamically
        update_fields = []
        values = []
        
        if 'name' in data:
            update_fields.append('name = ?')
            values.append(data['name'])
        
        if 'url' in data:
            update_fields.append('url = ?')
            values.append(data['url'])
        
        if 'check_interval' in data:
            check_interval = int(data['check_interval'])
            if check_interval < 30:
                return jsonify({'error': 'check_interval must be at least 30 seconds'}), 400
            update_fields.append('check_interval = ?')
            values.append(check_interval)
        
        if 'match_type' in data:
            if data['match_type'] not in ['string', 'regex']:
                return jsonify({'error': 'match_type must be "string" or "regex"'}), 400
            update_fields.append('match_type = ?')
            values.append(data['match_type'])
        
        if 'match_pattern' in data:
            update_fields.append('match_pattern = ?')
            values.append(data['match_pattern'])
        
        if 'match_condition' in data:
            if data['match_condition'] not in ['contains', 'not_contains']:
                return jsonify({'error': 'match_condition must be "contains" or "not_contains"'}), 400
            update_fields.append('match_condition = ?')
            values.append(data['match_condition'])
        
        if 'email_recipient' in data:
            update_fields.append('email_recipient = ?')
            values.append(data['email_recipient'])
        
        if 'is_active' in data:
            update_fields.append('is_active = ?')
            values.append(bool(data['is_active']))
        
        if 'notification_throttle_seconds' in data:
            update_fields.append('notification_throttle_seconds = ?')
            values.append(int(data['notification_throttle_seconds']))
        
        if 'status_code_monitor' in data:
            status_code = data['status_code_monitor']
            if status_code is not None:
                try:
                    status_code = int(status_code)
                    if status_code < 100 or status_code > 599:
                        return jsonify({'error': 'status_code_monitor must be between 100 and 599'}), 400
                except (ValueError, TypeError):
                    return jsonify({'error': 'status_code_monitor must be a valid integer'}), 400
            update_fields.append('status_code_monitor = ?')
            values.append(status_code)
        
        if 'response_time_threshold' in data:
            threshold = data['response_time_threshold']
            if threshold is not None:
                try:
                    threshold = float(threshold)
                    if threshold <= 0:
                        return jsonify({'error': 'response_time_threshold must be greater than 0'}), 400
                except (ValueError, TypeError):
                    return jsonify({'error': 'response_time_threshold must be a valid number'}), 400
            update_fields.append('response_time_threshold = ?')
            values.append(threshold)
        
        if not update_fields:
            return jsonify({'error': 'No fields to update'}), 400
        
        values.append(job_id)
        
        query = f'UPDATE monitor_jobs SET {", ".join(update_fields)} WHERE id = ?'
        cursor.execute(query, values)
        conn.commit()
        
        # Update scheduler
        new_check_interval = data.get('check_interval', job[1])
        new_is_active = data.get('is_active', job[2])
        
        if new_is_active:
            add_job_to_scheduler(job_id, new_check_interval)
        else:
            remove_job_from_scheduler(job_id)
        
        logger.info(f"Updated job {job_id}")
        
        return jsonify({'message': 'Job updated successfully'})
        
    except Exception as e:
        logger.error(f"Error updating job {job_id}: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'error': 'Failed to update job'}), 500
    finally:
        conn.close()

@app.route('/api/jobs/<int:job_id>', methods=['DELETE'])
def delete_job(job_id):
    """Delete a monitoring job."""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Check if job exists
        cursor.execute('SELECT id FROM monitor_jobs WHERE id = ?', (job_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Job not found'}), 404
        
        # Remove from scheduler
        remove_job_from_scheduler(job_id)
        
        # Delete job (cascade will delete check_history)
        cursor.execute('DELETE FROM monitor_jobs WHERE id = ?', (job_id,))
        conn.commit()
        
        logger.info(f"Deleted job {job_id}")
        
        return jsonify({'message': 'Job deleted successfully'})
        
    except Exception as e:
        logger.error(f"Error deleting job {job_id}: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'error': 'Failed to delete job'}), 500
    finally:
        conn.close()

@app.route('/api/jobs/<int:job_id>/history', methods=['GET'])
def get_job_history(job_id):
    """Get check history for a specific job."""
    limit = request.args.get('limit', 50, type=int)
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id, timestamp, status, match_found, response_time, error_message, http_status_code
            FROM check_history
            WHERE job_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (job_id, limit))
        
        history = []
        for row in cursor.fetchall():
            history.append({
                'id': row[0],
                'timestamp': row[1],
                'status': row[2],
                'match_found': bool(row[3]),
                'response_time': row[4],
                'error_message': row[5],
                'http_status_code': row[6]
            })
        
        return jsonify({'history': history})
        
    except Exception as e:
        logger.error(f"Error fetching history for job {job_id}: {e}", exc_info=True)
        return jsonify({'error': 'Failed to fetch history'}), 500
    finally:
        conn.close()

@app.route('/api/jobs/<int:job_id>/toggle', methods=['POST'])
def toggle_job(job_id):
    """Toggle job active/inactive status."""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT id, check_interval, is_active FROM monitor_jobs WHERE id = ?', (job_id,))
        job = cursor.fetchone()
        
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        
        new_status = not bool(job[2])
        
        cursor.execute('UPDATE monitor_jobs SET is_active = ? WHERE id = ?', (1 if new_status else 0, job_id))
        conn.commit()
        
        # Update scheduler
        if new_status:
            add_job_to_scheduler(job_id, job[1])
        else:
            remove_job_from_scheduler(job_id)
        
        logger.info(f"Toggled job {job_id} to {'active' if new_status else 'inactive'}")
        
        return jsonify({'is_active': new_status, 'message': f'Job {"activated" if new_status else "deactivated"}'})
        
    except Exception as e:
        logger.error(f"Error toggling job {job_id}: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'error': 'Failed to toggle job'}), 500
    finally:
        conn.close()

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/jobs/<int:job_id>/run-check', methods=['POST'])
def run_check_now(job_id):
    """Manually trigger a check for a specific job."""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Get job details
        cursor.execute('''
            SELECT id, name, url, check_interval, match_type, match_pattern,
                   match_condition, email_recipient, is_active,
                   notification_throttle_seconds, status_code_monitor, response_time_threshold
            FROM monitor_jobs
            WHERE id = ?
        ''', (job_id,))
        
        job_row = cursor.fetchone()
        if not job_row:
            return jsonify({'error': 'Job not found'}), 404
        
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
            'notification_throttle_seconds': job_row[9] or 3600,
            'status_code_monitor': job_row[10],
            'response_time_threshold': job_row[11]
        }
        
        # Import here to avoid circular imports
        from scheduler import run_check
        
        # Run the check in a separate thread to avoid blocking
        import threading
        thread = threading.Thread(target=run_check, args=(job_id,))
        thread.daemon = True
        thread.start()
        
        logger.info(f"Manually triggered check for job {job_id}")
        
        return jsonify({
            'success': True,
            'message': f'Check started for job "{job["name"]}". Results will be available in check history shortly.'
        })
        
    except Exception as e:
        logger.error(f"Error triggering check for job {job_id}: {e}", exc_info=True)
        return jsonify({'error': f'Failed to trigger check: {str(e)}'}), 500
    finally:
        conn.close()

@app.route('/api/test-email', methods=['POST'])
def test_email():
    """Send a test email to verify SMTP configuration."""
    data = request.get_json() or {}
    recipient = data.get('email', Config.SMTP_USERNAME)
    
    if not recipient:
        return jsonify({'error': 'No email address provided and SMTP_USERNAME not configured'}), 400
    
    if not Config.SMTP_USERNAME or not Config.SMTP_PASSWORD:
        return jsonify({'error': 'SMTP credentials not configured'}), 400
    
    try:
        # Create a test job object
        test_job = {
            'id': 0,  # Test job ID
            'name': 'Test Email',
            'url': 'https://example.com',
            'email_recipient': recipient
        }
        
        # Create a test match status
        test_status = {
            'match_found': True,
            'response_time': 0.5,
            'content_length': 1000
        }
        
        # Send test notification (will use email_recipient as fallback)
        success = send_notification(test_job, test_status, is_test=True)
        
        if success:
            logger.info(f"Test email sent successfully to {recipient}")
            return jsonify({
                'success': True,
                'message': f'Test email sent successfully to {recipient}'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to send test email. Check logs for details.'
            }), 500
            
    except Exception as e:
        logger.error(f"Error sending test email: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Error sending test email: {str(e)}'
        }), 500

@app.route('/api/jobs/<int:job_id>/notification-channels', methods=['GET'])
def get_notification_channels(job_id):
    """Get all notification channels for a job."""
    try:
        channels = get_job_notification_channels(job_id)
        return jsonify({'channels': channels})
    except Exception as e:
        logger.error(f"Error fetching notification channels for job {job_id}: {e}", exc_info=True)
        return jsonify({'error': 'Failed to fetch notification channels'}), 500

@app.route('/api/jobs/<int:job_id>/notification-channels', methods=['POST'])
def create_notification_channel(job_id):
    """Add a notification channel to a job."""
    data = request.get_json()
    
    if not data or 'channel_type' not in data or 'config' not in data:
        return jsonify({'error': 'Missing required fields: channel_type, config'}), 400
    
    channel_type = data['channel_type']
    if channel_type not in ['email', 'discord', 'slack']:
        return jsonify({'error': 'channel_type must be "email", "discord", or "slack"'}), 400
    
    # Validate config based on channel type
    config = data['config']
    if channel_type == 'email':
        if 'email_addresses' not in config:
            return jsonify({'error': 'email_addresses required in config'}), 400
    elif channel_type in ['discord', 'slack']:
        if 'webhook_url' not in config:
            return jsonify({'error': 'webhook_url required in config'}), 400
    
    # Verify job exists
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT id FROM monitor_jobs WHERE id = ?', (job_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Job not found'}), 404
    finally:
        conn.close()
    
    try:
        success = add_notification_channel(job_id, channel_type, config)
        if success:
            return jsonify({'message': 'Notification channel added successfully'}), 201
        else:
            return jsonify({'error': 'Failed to add notification channel'}), 500
    except Exception as e:
        logger.error(f"Error adding notification channel: {e}", exc_info=True)
        return jsonify({'error': f'Failed to add notification channel: {str(e)}'}), 500

@app.route('/api/jobs/<int:job_id>/notification-channels/<int:channel_id>', methods=['DELETE'])
def delete_notification_channel(job_id, channel_id):
    """Remove a notification channel from a job."""
    try:
        success = remove_notification_channel(channel_id)
        if success:
            return jsonify({'message': 'Notification channel removed successfully'})
        else:
            return jsonify({'error': 'Notification channel not found'}), 404
    except Exception as e:
        logger.error(f"Error removing notification channel: {e}", exc_info=True)
        return jsonify({'error': 'Failed to remove notification channel'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=Config.FLASK_DEBUG)
