"""JSON/API monitoring: parse JSON response and extract text via JSONPath for matching."""
import json
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

try:
    from jsonpath_ng import parse as jsonpath_parse
    JSONPATH_AVAILABLE = True
except ImportError:
    JSONPATH_AVAILABLE = False


def is_json_response(content_type: Optional[str], raw_content: bytes) -> bool:
    """Return True if response looks like JSON (Content-Type or content)."""
    if content_type and "json" in content_type.lower():
        return True
    if not raw_content or len(raw_content) < 2:
        return False
    start = raw_content.lstrip()[:1]
    return start in (b"{", b"[")


def extract_text_from_json(
    raw_content: bytes, json_path: str
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Parse JSON and extract text at the given JSONPath.
    Returns (success, extracted_text, error_message).
    Extracted text is normalized to a string (for matching/diff): if multiple matches, joined with newlines.
    """
    if not JSONPATH_AVAILABLE:
        return False, None, "jsonpath-ng not installed"
    if not json_path or not json_path.strip():
        return False, None, "JSONPath is empty"
    try:
        data = json.loads(raw_content.decode("utf-8", errors="replace"))
    except json.JSONDecodeError as e:
        return False, None, f"Invalid JSON: {e}"
    try:
        expr = jsonpath_parse(json_path.strip())
        matches = expr.find(data)
    except Exception as e:
        return False, None, f"JSONPath error: {e}"
    if not matches:
        return True, "", None  # Path matched nothing; empty string for "not contains" etc.
    parts = []
    for m in matches:
        v = m.value
        if v is None:
            parts.append("")
        elif isinstance(v, (dict, list)):
            parts.append(json.dumps(v, ensure_ascii=False))
        else:
            parts.append(str(v))
    text = "\n".join(parts)
    return True, text, None
