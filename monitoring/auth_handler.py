"""Authentication support for monitored requests: Basic Auth, headers, cookies."""
import json
import logging
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


def parse_auth_config(auth_config_json: Optional[str]) -> Optional[Dict[str, Any]]:
    """Parse auth_config JSON from DB. Returns dict or None."""
    if not auth_config_json or not auth_config_json.strip():
        return None
    try:
        return json.loads(auth_config_json)
    except json.JSONDecodeError:
        return None


def build_request_auth(auth_config: Optional[Dict]) -> Tuple[Optional[Tuple[str, str]], Dict[str, str], Dict[str, str]]:
    """
    Build (auth_tuple, headers, cookies) for requests from job auth_config.
    auth_config: { "basic": {"username": "u", "password": "p"}, "headers": {"Name": "value"}, "cookies": {"name": "value"} }
    Returns: ( (user, pass) or None, headers_dict, cookies_dict )
    """
    auth_tuple: Optional[Tuple[str, str]] = None
    headers: Dict[str, str] = {}
    cookies: Dict[str, str] = {}
    if not auth_config:
        return None, headers, cookies
    basic = auth_config.get("basic")
    if isinstance(basic, dict) and basic.get("username"):
        auth_tuple = (str(basic["username"]), str(basic.get("password", "")))
    h = auth_config.get("headers")
    if isinstance(h, dict):
        headers = {str(k): str(v) for k, v in h.items() if k and v is not None}
    elif isinstance(h, list):
        for item in h:
            if isinstance(item, dict) and item.get("name"):
                headers[str(item["name"])] = str(item.get("value", ""))
    c = auth_config.get("cookies")
    if isinstance(c, dict):
        cookies = {str(k): str(v) for k, v in c.items() if k and v is not None}
    return auth_tuple, headers, cookies


def build_request_kwargs(job: Dict) -> Dict:
    """
    Build kwargs for requests.get from job (must include auth_config key if present).
    Returns dict with auth=, headers= (merged with existing), cookies= as appropriate.
    """
    auth_config = job.get("auth_config")
    if isinstance(auth_config, str):
        auth_config = parse_auth_config(auth_config)
    auth_tuple, extra_headers, cookies = build_request_auth(auth_config)
    kwargs = {}
    if auth_tuple:
        kwargs["auth"] = auth_tuple
    if extra_headers:
        kwargs["headers"] = extra_headers
    if cookies:
        kwargs["cookies"] = cookies
    return kwargs
