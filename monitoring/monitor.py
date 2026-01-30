"""Core monitoring service for website content checking."""
import re
import time
import random
import logging
import requests
from bs4 import BeautifulSoup
from typing import Dict, Optional

from core.config import Config
from monitoring.json_monitor import is_json_response, extract_text_from_json
from monitoring.auth_handler import build_request_kwargs

logger = logging.getLogger(__name__)


def _run_ai_detection(job: Dict, text_content: str, result: Dict) -> None:
    """If job has AI enabled, run analysis and set match_found when result changes."""
    if not job.get("ai_enabled") or not (job.get("ai_prompt") or "").strip() or not text_content:
        return
    try:
        from ai import analyze_content
        new_result = analyze_content(text_content, job["ai_prompt"])
        if new_result is None:
            return
        result["ai_analysis_result"] = new_result
        last = (job.get("ai_last_result") or "").strip()
        if last != new_result:
            result["match_found"] = True
    except Exception as e:
        logger.warning("AI detection failed: %s", e)


def _get_user_agent(job: Dict) -> str:
    """Use job's custom_user_agent, or rotate from pool, or default."""
    ua = (job.get("custom_user_agent") or "").strip()
    if ua:
        return ua
    pool = getattr(Config, "USER_AGENT_POOL", None) or [Config.USER_AGENT]
    return random.choice(pool) if pool else Config.USER_AGENT

def check_website(job: Dict) -> Dict:
    """
    Perform a website check for a monitoring job.
    
    Args:
        job: Dictionary containing job configuration with keys:
            - id: Job ID
            - url: URL to check
            - match_type: 'string' or 'regex'
            - match_pattern: Pattern to search for
            - match_condition: 'contains' or 'not_contains'
    
    Returns:
        Dictionary with keys:
            - success: Boolean indicating if check succeeded
            - match_found: Boolean indicating if pattern was found
            - response_time: Time taken for request in seconds
            - error_message: Error message if check failed
            - content_length: Length of content checked
    """
    start_time = time.time()
    result = {
        'success': False,
        'match_found': False,
        'response_time': 0,
        'error_message': None,
        'content_length': 0,
        'http_status_code': None,
        'text_content': None  # For diff tracking (when success)
    }
    
    try:
        # Fetch the website (merge auth/headers/cookies from auth_config)
        headers = {'User-Agent': _get_user_agent(job)}
        request_kwargs = build_request_kwargs(job)
        if request_kwargs.get("headers"):
            headers.update(request_kwargs["headers"])
        proxies = None
        proxy_url = (job.get("proxy_url") or "").strip()
        if proxy_url:
            proxies = {"http": proxy_url, "https": proxy_url}
        response = requests.get(
            job['url'],
            headers=headers,
            timeout=Config.REQUEST_TIMEOUT,
            allow_redirects=True,
            auth=request_kwargs.get("auth"),
            cookies=request_kwargs.get("cookies") or {},
            proxies=proxies,
        )
        
        # Capture HTTP status code
        result['http_status_code'] = response.status_code
        
        response.raise_for_status()
        
        content_type = response.headers.get("Content-Type") or ""
        raw_content = response.content
        json_path = job.get("json_path") or ""
        
        # JSON/API mode: extract text via JSONPath when URL returns JSON
        if json_path.strip() and is_json_response(content_type, raw_content):
            ok, text_content, err = extract_text_from_json(raw_content, json_path)
            if not ok:
                result["error_message"] = err
                result["success"] = False
                return result
            text_content = (text_content or "").strip()
            result["content_length"] = len(text_content)
            result["success"] = True
            result["text_content"] = text_content[:100_000] if text_content else None
        else:
            # HTML mode: parse with BeautifulSoup
            soup = BeautifulSoup(raw_content, "html.parser")
            for script in soup(["script", "style"]):
                script.decompose()
            text_content = soup.get_text()
            text_content = " ".join(text_content.split())
            result["content_length"] = len(text_content)
            result["success"] = True
            result["text_content"] = text_content[:100_000] if text_content else None

        # Check for pattern match
        match_found = False
        
        if job['match_type'] == 'string':
            # Simple string search (case-insensitive)
            pattern = job['match_pattern'].lower()
            content_lower = text_content.lower()
            match_found = pattern in content_lower
        elif job['match_type'] == 'regex':
            # Regex pattern matching
            try:
                pattern = re.compile(job['match_pattern'], re.IGNORECASE | re.DOTALL)
                match_found = bool(pattern.search(text_content))
            except re.error as e:
                result['error_message'] = f"Invalid regex pattern: {str(e)}"
                result['success'] = False
                return result
        
        # Apply match condition
        if job['match_condition'] == 'contains':
            result['match_found'] = match_found
        elif job['match_condition'] == 'not_contains':
            result['match_found'] = not match_found

        # AI-powered change detection: if enabled and result differs from last time, set match
        _run_ai_detection(job, text_content, result)

    except requests.exceptions.Timeout:
        result['error_message'] = f"Request timeout after {Config.REQUEST_TIMEOUT} seconds"
        logger.warning(f"Timeout checking {job['url']}")
    except requests.exceptions.ConnectionError as e:
        result['error_message'] = f"Connection error: {str(e)}"
        logger.warning(f"Connection error checking {job['url']}: {e}")
    except requests.exceptions.HTTPError as e:
        if 'response' in locals():
            result['http_status_code'] = response.status_code
        result['error_message'] = f"HTTP error {result.get('http_status_code', 'unknown')}: {str(e)}"
        logger.warning(f"HTTP error checking {job['url']}: {e}")
    except Exception as e:
        result['error_message'] = f"Unexpected error: {str(e)}"
        logger.error(f"Error checking {job['url']}: {e}", exc_info=True)
    finally:
        result['response_time'] = time.time() - start_time
    
    return result
