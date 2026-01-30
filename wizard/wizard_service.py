"""Smart setup wizard: fetch URL and suggest monitor configuration (optionally via AI)."""
import json
import logging
from typing import Optional, Tuple
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from core.config import Config
from ai.ai_config import is_ai_available, OPENAI_API_KEY

logger = logging.getLogger(__name__)

# Max content to send to AI
MAX_CONTENT_CHARS = 6000


def fetch_page_text(url: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Fetch URL and return plain text content.
    Returns (success, text_content, error_message).
    """
    if not url or not url.strip():
        return False, None, "URL is required"
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    try:
        headers = {"User-Agent": Config.USER_AGENT}
        response = requests.get(
            url,
            headers=headers,
            timeout=Config.REQUEST_TIMEOUT,
            allow_redirects=True,
        )
        response.raise_for_status()
        content_type = response.headers.get("Content-Type") or ""
        raw = response.content
        if "application/json" in content_type:
            try:
                data = response.json()
                text = json.dumps(data, indent=0)[:MAX_CONTENT_CHARS]
                return True, text, None
            except Exception:
                text = response.text[:MAX_CONTENT_CHARS] if response.text else ""
                return True, text or None, None
        soup = BeautifulSoup(raw, "html.parser")
        for tag in soup(["script", "style"]):
            tag.decompose()
        text = soup.get_text()
        text = " ".join(text.split()).strip()
        return True, (text[:100_000] if text else None), None
    except requests.exceptions.Timeout:
        return False, None, "Request timed out"
    except requests.exceptions.RequestException as e:
        return False, None, str(e)
    except Exception as e:
        logger.warning("Wizard fetch error: %s", e)
        return False, None, str(e)


def suggest_monitor_config(url: str, text_content: Optional[str]) -> dict:
    """
    Suggest monitor name and pattern from URL and page content.
    If AI is available, use OpenAI; otherwise return defaults derived from URL.
    """
    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path
    if domain.startswith("www."):
        domain = domain[4:]
    default_name = domain.replace(".", " ").title()[:50] or "New Monitor"
    result = {
        "name": default_name,
        "match_pattern": "",
        "match_condition": "contains",
        "match_type": "string",
        "check_interval": 3600,
    }
    if not text_content or not text_content.strip():
        return result
    content = text_content.strip()
    if len(content) > MAX_CONTENT_CHARS:
        content = content[:MAX_CONTENT_CHARS] + "\n[... truncated]"
    if not is_ai_available():
        return result
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You suggest a website monitor configuration. Reply with a JSON object only, no markdown, with keys: name (short monitor name), match_pattern (a short phrase or word to watch for, e.g. 'waitlist is open' or 'In Stock'), match_condition (either 'contains' or 'not_contains'), check_interval (seconds, e.g. 3600 for 1 hour). Be concise; match_pattern should be something that would change when the user cares (e.g. availability, status)."
                },
                {
                    "role": "user",
                    "content": f"URL: {url}\n\nPage content:\n{content}"
                }
            ],
            max_tokens=200,
        )
        raw = (response.choices and response.choices[0] and response.choices[0].message and response.choices[0].message.content or "").strip()
        if raw:
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0]
            sug = json.loads(raw)
            if isinstance(sug.get("name"), str) and sug["name"].strip():
                result["name"] = sug["name"].strip()[:100]
            if isinstance(sug.get("match_pattern"), str) and sug["match_pattern"].strip():
                result["match_pattern"] = sug["match_pattern"].strip()[:500]
            if sug.get("match_condition") in ("contains", "not_contains"):
                result["match_condition"] = sug["match_condition"]
            if isinstance(sug.get("check_interval"), (int, float)) and 30 <= sug["check_interval"] <= 86400:
                result["check_interval"] = int(sug["check_interval"])
    except json.JSONDecodeError as e:
        logger.warning("Wizard AI JSON parse error: %s", e)
    except Exception as e:
        logger.warning("Wizard AI suggestion error: %s", e)
    return result
