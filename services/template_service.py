"""Template management for pre-built monitor configurations."""
import json
from pathlib import Path

from core.config import Config

# Path to bundled templates (project root / templates / monitor_templates.json)
_TEMPLATES_PATH = Config.BASE_DIR / "templates" / "monitor_templates.json"

_templates_cache = None


def _load_templates():
    """Load templates from JSON file; cache in memory."""
    global _templates_cache
    if _templates_cache is not None:
        return _templates_cache
    if not _TEMPLATES_PATH.exists():
        _templates_cache = []
        return _templates_cache
    try:
        with open(_TEMPLATES_PATH, "r", encoding="utf-8") as f:
            _templates_cache = json.load(f)
    except (json.JSONDecodeError, OSError):
        _templates_cache = []

    return _templates_cache


def get_all_templates():
    """Return list of all template dicts (id, name, description, and default fields)."""
    return list(_load_templates())


def get_template_by_id(template_id):
    """Return a single template by id, or None if not found."""
    for t in _load_templates():
        if t.get("id") == template_id:
            return t
    return None


def apply_template_to_job_data(template_id, job_data):
    """
    Override job_data keys with template defaults where the template defines them.
    job_data should be a dict (e.g. form payload); it is modified in place.
    """
    t = get_template_by_id(template_id)
    if not t:
        return
    mapping = {
        "check_interval": "check_interval",
        "match_type": "match_type",
        "match_condition": "match_condition",
        "match_pattern": "match_pattern",
        "notification_throttle_seconds": "notification_throttle_seconds",
    }
    for template_key, job_key in mapping.items():
        if template_key in t and t[template_key] is not None:
            job_data[job_key] = t[template_key]
