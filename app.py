"""Main Flask application for website monitoring tool."""
import logging
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from models import get_db, init_db
from scheduler import start_scheduler, add_job_to_scheduler, remove_job_from_scheduler, reload_all_jobs
from config import Config

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
                   created_at, last_checked, last_match
            FROM monitor_jobs
            ORDER BY created_at DESC
        ''')
        
        jobs = []
        for row in cursor.fetchall():
            jobs.append({
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
                'last_match': row[11]
            })
        
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
        cursor.execute('''
            INSERT INTO monitor_jobs 
            (name, url, check_interval, match_type, match_pattern, 
             match_condition, email_recipient, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['name'],
            data['url'],
            check_interval,
            data['match_type'],
            data['match_pattern'],
            data['match_condition'],
            data['email_recipient'],
            1 if data.get('is_active', True) else 0
        ))
        
        job_id = cursor.lastrowid
        conn.commit()
        
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
            SELECT id, timestamp, status, match_found, response_time, error_message
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
                'error_message': row[5]
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
                   match_condition, email_recipient, is_active
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
            'is_active': job_row[8]
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
        from email_service import send_notification
        
        # Create a test job object
        test_job = {
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
        
        # Send test email
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=Config.FLASK_DEBUG)
