"""Main Flask application for website monitoring tool."""
import json
import logging
from datetime import datetime
from flask import Flask, render_template, jsonify, request

from core.config import Config
from core.models import get_db, init_db
from core.scheduler import start_scheduler, add_job_to_scheduler, remove_job_from_scheduler, reload_all_jobs
from services.notification_service import (
    send_notification, add_notification_channel, remove_notification_channel,
    get_job_notification_channels, delete_channels_for_job
)
from services.statistics_service import get_global_stats, get_checks_over_time, get_job_stats
from services.template_service import get_all_templates, get_template_by_id
from wizard.wizard_service import fetch_page_text, suggest_monitor_config

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


@app.route('/api/templates', methods=['GET'])
def list_templates():
    """Return all pre-built monitor templates."""
    try:
        templates = get_all_templates()
        return jsonify({'templates': templates})
    except Exception as e:
        logger.error(f"Error listing templates: {e}", exc_info=True)
        return jsonify({'error': 'Failed to list templates'}), 500


def _safe_json_load(s):
    """Parse JSON string; return None on error."""
    if not s:
        return None
    try:
        return json.loads(s)
    except (TypeError, json.JSONDecodeError):
        return None


def _get_job_tag_names(conn, job_id):
    """Return list of tag names for a job."""
    cursor = conn.cursor()
    cursor.execute('''
        SELECT t.name FROM tags t
        INNER JOIN job_tags jt ON jt.tag_id = t.id
        WHERE jt.job_id = ?
    ''', (job_id,))
    return [r[0] for r in cursor.fetchall()]


def _ensure_tag_id(conn, name):
    """Get or create tag by name; return tag id."""
    name = (name or "").strip()
    if not name:
        return None
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM tags WHERE name = ?', (name,))
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute('INSERT INTO tags (name) VALUES (?)', (name,))
    return cursor.lastrowid


def _set_job_tags(conn, job_id, tag_names):
    """Replace job's tags with the given list of tag names."""
    cursor = conn.cursor()
    cursor.execute('DELETE FROM job_tags WHERE job_id = ?', (job_id,))
    for name in (tag_names or []):
        tag_id = _ensure_tag_id(conn, name)
        if tag_id:
            cursor.execute('INSERT OR IGNORE INTO job_tags (job_id, tag_id) VALUES (?, ?)', (job_id, tag_id))


@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    """Get all monitoring jobs. Optional query: tag=name to filter by tag."""
    tag_filter = request.args.get('tag', '').strip()
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        if tag_filter:
            cursor.execute('''
                SELECT DISTINCT m.id, m.name, m.url, m.check_interval, m.match_type, m.match_pattern,
                       m.match_condition, m.email_recipient, m.is_active,
                       m.created_at, m.last_checked, m.last_match,
                       m.notification_throttle_seconds, m.status_code_monitor, m.response_time_threshold,
                       m.json_path, m.auth_config, m.proxy_url, m.custom_user_agent, m.capture_screenshot,
                       m.ai_enabled, m.ai_prompt, m.ai_last_result
                FROM monitor_jobs m
                INNER JOIN job_tags jt ON jt.job_id = m.id
                INNER JOIN tags t ON t.id = jt.tag_id AND t.name = ?
                ORDER BY m.created_at DESC
            ''', (tag_filter,))
        else:
            cursor.execute('''
                SELECT id, name, url, check_interval, match_type, match_pattern,
                       match_condition, email_recipient, is_active,
                       created_at, last_checked, last_match,
                       notification_throttle_seconds, status_code_monitor, response_time_threshold,
                       json_path, auth_config, proxy_url, custom_user_agent, capture_screenshot,
                       ai_enabled, ai_prompt, ai_last_result
                FROM monitor_jobs
                ORDER BY created_at DESC
            ''')
        
        jobs = []
        for row in cursor.fetchall():
            job_id = row[0]
            job_data = {
                'id': job_id,
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
                'notification_throttle_seconds': 3600 if row[12] is None else row[12],
                'status_code_monitor': row[13],
                'response_time_threshold': row[14],
                'json_path': row[15] or "",
                'auth_config': row[16],
                'proxy_url': row[17] or "",
                'custom_user_agent': row[18] or "",
                'capture_screenshot': bool(row[19]) if len(row) > 19 else False,
                'ai_enabled': bool(row[20]) if len(row) > 20 else False,
                'ai_prompt': row[21] if len(row) > 21 else None,
                'ai_last_result': row[22] if len(row) > 22 else None,
            }
            job_data['notification_channels'] = get_job_notification_channels(job_id)
            job_data['tags'] = _get_job_tag_names(conn, job_id)
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
        json_path = (data.get('json_path') or "").strip() or None
        auth_config = data.get('auth_config')
        auth_config_str = json.dumps(auth_config) if auth_config else None
        proxy_url = (data.get('proxy_url') or "").strip() or None
        custom_user_agent = (data.get('custom_user_agent') or "").strip() or None
        capture_screenshot = 1 if data.get('capture_screenshot') else 0
        ai_enabled = 1 if data.get('ai_enabled') else 0
        ai_prompt = (data.get('ai_prompt') or "").strip() or None

        cursor.execute('''
            INSERT INTO monitor_jobs 
            (name, url, check_interval, match_type, match_pattern,
             match_condition, email_recipient, is_active,
             notification_throttle_seconds, status_code_monitor, response_time_threshold, json_path, auth_config, proxy_url, custom_user_agent, capture_screenshot, ai_enabled, ai_prompt)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            response_time_threshold,
            json_path,
            auth_config_str,
            proxy_url,
            custom_user_agent,
            capture_screenshot,
            ai_enabled,
            ai_prompt,
        ))
        
        job_id = cursor.lastrowid
        
        # Add tags if provided
        if 'tags' in data and data['tags']:
            _set_job_tags(conn, job_id, data['tags'])
        
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
        
        if 'json_path' in data:
            json_path = (data.get('json_path') or "").strip() or None
            update_fields.append('json_path = ?')
            values.append(json_path)
        
        if 'auth_config' in data:
            auth_config = data.get('auth_config')
            auth_config_str = json.dumps(auth_config) if auth_config else None
            update_fields.append('auth_config = ?')
            values.append(auth_config_str)
        
        if 'proxy_url' in data:
            proxy_url = (data.get('proxy_url') or "").strip() or None
            update_fields.append('proxy_url = ?')
            values.append(proxy_url)
        
        if 'custom_user_agent' in data:
            custom_user_agent = (data.get('custom_user_agent') or "").strip() or None
            update_fields.append('custom_user_agent = ?')
            values.append(custom_user_agent)

        if 'ai_enabled' in data:
            update_fields.append('ai_enabled = ?')
            values.append(1 if data.get('ai_enabled') else 0)
        if 'ai_prompt' in data:
            ai_prompt = (data.get('ai_prompt') or "").strip() or None
            update_fields.append('ai_prompt = ?')
            values.append(ai_prompt)

        if 'capture_screenshot' in data:
            update_fields.append('capture_screenshot = ?')
            values.append(1 if data.get('capture_screenshot') else 0)
        
        if 'tags' in data:
            _set_job_tags(conn, job_id, data['tags'])
        
        if not update_fields and 'notification_channels' not in data and 'tags' not in data:
            return jsonify({'error': 'No fields to update'}), 400
        
        if update_fields:
            values.append(job_id)
            query = f'UPDATE monitor_jobs SET {", ".join(update_fields)} WHERE id = ?'
            cursor.execute(query, values)
        
        conn.commit()
        conn.close()
        
        # Replace notification channels if provided (use separate connection to avoid lock)
        if 'notification_channels' in data:
            delete_channels_for_job(job_id)
            for channel in data['notification_channels']:
                channel_type = channel.get('channel_type')
                config = channel.get('config', {})
                if channel_type and config:
                    add_notification_channel(job_id, channel_type, config)
            logger.info(f"Job {job_id}: replaced notification channels with {len(data['notification_channels'])} channel(s)")
        
        # Re-open connection for scheduler update if we closed it
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT check_interval, is_active FROM monitor_jobs WHERE id = ?', (job_id,))
            row = cursor.fetchone()
            if row:
                new_check_interval, new_is_active = row[0], bool(row[1])
                if new_is_active:
                    add_job_to_scheduler(job_id, new_check_interval)
                else:
                    remove_job_from_scheduler(job_id)
        finally:
            conn.close()
        
        logger.info(f"Updated job {job_id}")
        
        return jsonify({'message': 'Job updated successfully'})
        
    except Exception as e:
        logger.error(f"Error updating job {job_id}: {e}", exc_info=True)
        try:
            conn.rollback()
        except Exception:
            pass
        return jsonify({'error': 'Failed to update job'}), 500
    finally:
        try:
            conn.close()
        except Exception:
            pass

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
            SELECT id, timestamp, status, match_found, response_time, error_message, http_status_code,
                   content_snapshot_id, diff_data, screenshot_path
            FROM check_history
            WHERE job_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (job_id, limit))
        
        history = []
        for row in cursor.fetchall():
            item = {
                'id': row[0],
                'timestamp': row[1],
                'status': row[2],
                'match_found': bool(row[3]),
                'response_time': row[4],
                'error_message': row[5],
                'http_status_code': row[6],
                'content_snapshot_id': row[7],
                'diff_data': row[8],
                'screenshot_path': row[9] if len(row) > 9 else None,
            }
            item['has_diff'] = bool(row[8] and row[8].strip())
            history.append(item)
        
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


@app.route('/api/wizard/analyze', methods=['POST'])
def wizard_analyze():
    """Analyze a URL and return suggested monitor configuration (name, pattern, etc.)."""
    data = request.get_json() or {}
    url = (data.get('url') or '').strip()
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    try:
        ok, text_content, err = fetch_page_text(url)
        if not ok:
            return jsonify({'error': err or 'Failed to fetch URL'}), 400
        suggestions = suggest_monitor_config(url, text_content)
        # Normalize URL (add https if missing)
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        suggestions['url'] = url
        return jsonify({'success': True, 'suggestions': suggestions})
    except Exception as e:
        logger.error(f"Wizard analyze error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/export', methods=['GET'])
def export_config():
    """Export all jobs as JSON (for backup/import elsewhere)."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT id, name, url, check_interval, match_type, match_pattern,
                   match_condition, email_recipient, is_active,
                   notification_throttle_seconds, status_code_monitor, response_time_threshold,
                   json_path, auth_config, proxy_url, custom_user_agent, capture_screenshot,
                   ai_enabled, ai_prompt
            FROM monitor_jobs
            ORDER BY id
        ''')
        jobs_export = []
        for row in cursor.fetchall():
            job_id = row[0]
            job = {
                'name': row[1],
                'url': row[2],
                'check_interval': row[3],
                'match_type': row[4],
                'match_pattern': row[5],
                'match_condition': row[6],
                'email_recipient': row[7],
                'is_active': bool(row[8]),
                'notification_throttle_seconds': 3600 if row[9] is None else row[9],
                'status_code_monitor': row[10],
                'response_time_threshold': row[11],
                'json_path': row[12] or "",
                'auth_config': _safe_json_load(row[13]) if row[13] else None,
                'proxy_url': row[14] or "",
                'custom_user_agent': row[15] or "",
                'capture_screenshot': bool(row[16]) if len(row) > 16 else False,
                'ai_enabled': bool(row[17]) if len(row) > 17 else False,
                'ai_prompt': row[18] if len(row) > 18 else None,
                'tags': _get_job_tag_names(conn, job_id),
                'notification_channels': get_job_notification_channels(job_id),
            }
            jobs_export.append(job)
        payload = {
            'version': 1,
            'exported_at': datetime.now().isoformat(),
            'jobs': jobs_export,
        }
        return jsonify(payload)
    except Exception as e:
        logger.error(f"Error exporting config: {e}", exc_info=True)
        return jsonify({'error': 'Failed to export'}), 500
    finally:
        conn.close()


@app.route('/api/import', methods=['POST'])
def import_config():
    """Import jobs from JSON. Body: { jobs: [...] }. Each job same shape as create_job."""
    data = request.get_json()
    if not data or 'jobs' not in data:
        return jsonify({'error': 'Missing "jobs" array in body'}), 400
    jobs_in = data['jobs']
    if not isinstance(jobs_in, list):
        return jsonify({'error': '"jobs" must be an array'}), 400
    created = 0
    errors = []
    for i, job_data in enumerate(jobs_in):
        if not isinstance(job_data, dict):
            errors.append({'index': i, 'error': 'Job must be an object'})
            continue
        # Validate required fields
        for field in ['name', 'url', 'check_interval', 'match_type', 'match_pattern', 'match_condition', 'email_recipient']:
            if field not in job_data:
                errors.append({'index': i, 'name': job_data.get('name'), 'error': f'Missing {field}'})
                break
        else:
            if job_data.get('match_type') not in ('string', 'regex'):
                errors.append({'index': i, 'name': job_data.get('name'), 'error': 'match_type must be string or regex'})
                continue
            if job_data.get('match_condition') not in ('contains', 'not_contains'):
                errors.append({'index': i, 'name': job_data.get('name'), 'error': 'match_condition must be contains or not_contains'})
                continue
            try:
                check_interval = int(job_data.get('check_interval', 300))
                if check_interval < 30:
                    errors.append({'index': i, 'name': job_data.get('name'), 'error': 'check_interval must be at least 30'})
                    continue
            except (ValueError, TypeError):
                errors.append({'index': i, 'name': job_data.get('name'), 'error': 'check_interval must be an integer'})
                continue
            conn = get_db()
            cursor = conn.cursor()
            try:
                notification_throttle = job_data.get('notification_throttle_seconds', 3600)
                status_code_monitor = job_data.get('status_code_monitor')
                response_time_threshold = job_data.get('response_time_threshold')
                json_path = (job_data.get('json_path') or "").strip() or None
                auth_config = job_data.get('auth_config')
                auth_config_str = json.dumps(auth_config) if auth_config else None
                proxy_url = (job_data.get('proxy_url') or "").strip() or None
                custom_user_agent = (job_data.get('custom_user_agent') or "").strip() or None
                capture_screenshot = 1 if job_data.get('capture_screenshot') else 0
                ai_enabled = 1 if job_data.get('ai_enabled') else 0
                ai_prompt = (job_data.get('ai_prompt') or "").strip() or None
                cursor.execute('''
                    INSERT INTO monitor_jobs
                    (name, url, check_interval, match_type, match_pattern,
                     match_condition, email_recipient, is_active,
                     notification_throttle_seconds, status_code_monitor, response_time_threshold, json_path, auth_config, proxy_url, custom_user_agent, capture_screenshot, ai_enabled, ai_prompt)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    job_data['name'],
                    job_data['url'],
                    check_interval,
                    job_data['match_type'],
                    job_data['match_pattern'],
                    job_data['match_condition'],
                    job_data['email_recipient'],
                    1 if job_data.get('is_active', True) else 0,
                    notification_throttle,
                    status_code_monitor,
                    response_time_threshold,
                    json_path,
                    auth_config_str,
                    proxy_url,
                    custom_user_agent,
                    capture_screenshot,
                    ai_enabled,
                    ai_prompt,
                ))
                job_id = cursor.lastrowid
                if job_data.get('tags'):
                    _set_job_tags(conn, job_id, job_data['tags'])
                conn.commit()
                if job_data.get('notification_channels'):
                    for ch in job_data['notification_channels']:
                        if ch.get('channel_type') and ch.get('config'):
                            add_notification_channel(job_id, ch['channel_type'], ch['config'])
                if job_data.get('is_active', True):
                    add_job_to_scheduler(job_id, check_interval)
                created += 1
            except Exception as e:
                conn.rollback()
                errors.append({'index': i, 'name': job_data.get('name'), 'error': str(e)})
            finally:
                conn.close()
    return jsonify({
        'created': created,
        'errors': errors,
        'message': f'Imported {created} job(s)' + (f'; {len(errors)} error(s)' if errors else ''),
    })


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Get global and time-series statistics for the dashboard."""
    hours = request.args.get('hours', 24, type=int)
    hours = min(max(hours, 1), 168)  # 1h to 7 days
    try:
        global_stats = get_global_stats(hours=hours)
        over_time = get_checks_over_time(hours=hours)
        return jsonify({
            'global': global_stats,
            'checks_over_time': over_time,
        })
    except Exception as e:
        logger.error(f"Error fetching statistics: {e}", exc_info=True)
        return jsonify({'error': 'Failed to fetch statistics'}), 500


@app.route('/api/jobs/<int:job_id>/statistics', methods=['GET'])
def get_job_statistics(job_id):
    """Get statistics for a single job."""
    hours = request.args.get('hours', 24, type=int)
    hours = min(max(hours, 1), 168)
    try:
        stats = get_job_stats(job_id, hours=hours)
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error fetching job statistics: {e}", exc_info=True)
        return jsonify({'error': 'Failed to fetch statistics'}), 500

@app.route('/api/jobs/<int:job_id>/run-check', methods=['POST'])
def run_check_now(job_id):
    """Manually trigger a check for a specific job."""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Get job details (include AI fields for run_check)
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
            'notification_throttle_seconds': 3600 if job_row[9] is None else job_row[9],
            'status_code_monitor': job_row[10],
            'response_time_threshold': job_row[11],
            'json_path': job_row[12] or "",
            'auth_config': job_row[13],
            'proxy_url': job_row[14] or "",
            'custom_user_agent': job_row[15] or "",
            'capture_screenshot': bool(job_row[16]) if len(job_row) > 16 else False,
        }
        
        # Import here to avoid circular imports
        from core.scheduler import run_check
        
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

@app.route('/api/tags', methods=['GET'])
def get_tags():
    """Get all tags."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT id, name FROM tags ORDER BY name')
        tags = [{'id': r[0], 'name': r[1]} for r in cursor.fetchall()]
        return jsonify({'tags': tags})
    except Exception as e:
        logger.error(f"Error fetching tags: {e}", exc_info=True)
        return jsonify({'error': 'Failed to fetch tags'}), 500
    finally:
        conn.close()


@app.route('/api/tags', methods=['POST'])
def create_tag():
    """Create a tag by name."""
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'error': 'Tag name is required'}), 400
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT id FROM tags WHERE name = ?', (name,))
        row = cursor.fetchone()
        if row:
            return jsonify({'id': row[0], 'name': name, 'message': 'Tag already exists'}), 200
        cursor.execute('INSERT INTO tags (name) VALUES (?)', (name,))
        conn.commit()
        return jsonify({'id': cursor.lastrowid, 'name': name}), 201
    except Exception as e:
        logger.error(f"Error creating tag: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'error': 'Failed to create tag'}), 500
    finally:
        conn.close()


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
