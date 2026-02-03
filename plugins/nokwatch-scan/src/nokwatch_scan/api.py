"""API routes for scan job CRUD."""
import json
import logging
from flask import Blueprint, request, jsonify

from core.models import get_db
from core.crypto import encrypt_credentials, decrypt_credentials

logger = logging.getLogger(__name__)

bp = Blueprint("nokwatch_scan_api", __name__)


def _job_from_row(row) -> dict:
    """Build job dict from DB row."""
    d = dict(row)
    if d.get("auth_config"):
        d["auth_config"] = decrypt_credentials(d["auth_config"])
    raw = d.get("item_extractor_config")
    if isinstance(raw, str) and raw:
        try:
            d["item_extractor_config"] = json.loads(raw)
        except json.JSONDecodeError:
            d["item_extractor_config"] = {}
    raw = d.get("seen_item_ids")
    if isinstance(raw, str) and raw:
        try:
            d["seen_item_ids"] = json.loads(raw)
        except json.JSONDecodeError:
            d["seen_item_ids"] = []
    return d


@bp.route("/jobs", methods=["GET"])
def list_scan_jobs():
    """List all scan jobs."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT * FROM monitor_jobs WHERE job_type = 'listing_scan' OR scan_mode = 'listing'
           ORDER BY created_at DESC"""
    )
    rows = cursor.fetchall()
    conn.close()
    jobs = [_job_from_row(r) for r in rows]
    return jsonify({"jobs": jobs})


@bp.route("/jobs", methods=["POST"])
def create_scan_job():
    """Create a scan job."""
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    url = (data.get("url") or "").strip()
    check_interval = int(data.get("check_interval", 300))
    if check_interval < 30:
        check_interval = 300
    match_pattern = (data.get("match_pattern") or "").strip()
    item_extractor_config = data.get("item_extractor_config") or {}
    price_min = data.get("price_min")
    price_max = data.get("price_max")
    email_recipient = (data.get("email_recipient") or "").strip()
    if not name or not url:
        return jsonify({"error": "name and url required"}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO monitor_jobs
           (name, url, check_interval, match_type, match_pattern, match_condition,
            email_recipient, is_active, job_type, scan_mode, item_extractor_config,
            price_min, price_max)
           VALUES (?, ?, ?, 'regex', ?, 'contains', ?, 1, 'listing_scan', 'listing', ?, ?, ?)""",
        (
            name,
            url,
            check_interval,
            match_pattern,
            email_recipient,
            json.dumps(item_extractor_config),
            price_min,
            price_max,
        ),
    )
    job_id = cursor.lastrowid
    conn.commit()
    conn.close()

    from core.scheduler import add_job_to_scheduler
    add_job_to_scheduler(job_id, check_interval)

    return jsonify({"id": job_id, "message": "Scan job created"}), 201


@bp.route("/jobs/<int:job_id>", methods=["GET"])
def get_scan_job(job_id):
    """Get a scan job by ID."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM monitor_jobs WHERE id = ? AND (job_type = 'listing_scan' OR scan_mode = 'listing')",
        (job_id,),
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Not found"}), 404
    return jsonify(_job_from_row(row))


@bp.route("/jobs/<int:job_id>", methods=["PUT"])
def update_scan_job(job_id):
    """Update a scan job."""
    data = request.get_json() or {}
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, check_interval, is_active FROM monitor_jobs WHERE id = ? AND (job_type = 'listing_scan' OR scan_mode = 'listing')",
        (job_id,),
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Not found"}), 404

    updates = []
    values = []
    for key, col in [
        ("name", "name"),
        ("url", "url"),
        ("check_interval", "check_interval"),
        ("match_pattern", "match_pattern"),
        ("email_recipient", "email_recipient"),
        ("price_min", "price_min"),
        ("price_max", "price_max"),
        ("item_extractor_config", "item_extractor_config"),
    ]:
        if key in data:
            val = data[key]
            if key == "item_extractor_config":
                val = json.dumps(val) if isinstance(val, dict) else val
            updates.append(f"{col} = ?")
            values.append(val)

    if updates:
        values.append(job_id)
        cursor.execute(
            f"UPDATE monitor_jobs SET {', '.join(updates)} WHERE id = ?",
            values,
        )
        conn.commit()

        check_interval = data.get("check_interval", row[1])
        is_active = data.get("is_active", row[2])
        from core.scheduler import add_job_to_scheduler, remove_job_from_scheduler
        if is_active:
            add_job_to_scheduler(job_id, check_interval)
        else:
            remove_job_from_scheduler(job_id)

    conn.close()
    return jsonify({"message": "Updated"})


@bp.route("/jobs/<int:job_id>", methods=["DELETE"])
def delete_scan_job(job_id):
    """Delete a scan job."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM monitor_jobs WHERE id = ? AND (job_type = 'listing_scan' OR scan_mode = 'listing')",
        (job_id,),
    )
    deleted = cursor.rowcount
    conn.commit()
    conn.close()

    if deleted:
        from core.scheduler import remove_job_from_scheduler
        remove_job_from_scheduler(job_id)
        return jsonify({"message": "Deleted"})
    return jsonify({"error": "Not found"}), 404
