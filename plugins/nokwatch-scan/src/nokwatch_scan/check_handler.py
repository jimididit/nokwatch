"""Check handler for listing scan jobs."""
import json
import re
import time
import logging
from typing import Any, Dict, List

import requests

from core.config import Config
from monitoring.auth_handler import build_request_kwargs
from nokwatch_scan.listing_extractor import extract_items

logger = logging.getLogger(__name__)


def check_listing_page(job: Dict) -> Dict:
    """
    Scan a listing page for new items matching criteria. Same contract as check_website:
    {success, match_found, response_time, error_message, text_content?, matched_items?, ...}
    """
    start_time = time.time()
    result = {
        "success": False,
        "match_found": False,
        "response_time": 0,
        "error_message": None,
        "content_length": 0,
        "matched_items": [],
    }

    try:
        url = job.get("url") or ""
        if not url:
            result["error_message"] = "No URL configured"
            return result

        config = _get_extractor_config(job)
        if not config:
            result["error_message"] = "item_extractor_config required for listing scan"
            return result

        # Fetch page
        headers = {"User-Agent": (job.get("custom_user_agent") or "") or Config.USER_AGENT}
        request_kwargs = build_request_kwargs(job)
        if request_kwargs.get("headers"):
            headers.update(request_kwargs["headers"])
        proxies = None
        proxy_url = (job.get("proxy_url") or "").strip()
        if proxy_url:
            proxies = {"http": proxy_url, "https": proxy_url}

        response = requests.get(
            url,
            headers=headers,
            timeout=getattr(Config, "REQUEST_TIMEOUT", 10),
            allow_redirects=True,
            auth=request_kwargs.get("auth"),
            cookies=request_kwargs.get("cookies") or {},
            proxies=proxies,
        )

        result["http_status_code"] = response.status_code
        response.raise_for_status()
        raw = response.content
        content_type = response.headers.get("Content-Type", "")

        # Extract items
        items = extract_items(raw, content_type, config, url)
        result["content_length"] = len(raw)
        result["success"] = True

        # Filter: title matches match_pattern; price in range
        match_pattern = (job.get("match_pattern") or "").strip()
        price_min = job.get("price_min")
        price_max = job.get("price_max")
        if isinstance(price_min, str):
            try:
                price_min = float(price_min) if price_min else None
            except ValueError:
                price_min = None
        if isinstance(price_max, str):
            try:
                price_max = float(price_max) if price_max else None
            except ValueError:
                price_max = None

        filtered = []
        for item in items:
            if match_pattern:
                title = item.get("title") or ""
                try:
                    if re.search(match_pattern, title, re.IGNORECASE):
                        pass
                    else:
                        continue
                except re.error:
                    if match_pattern.lower() not in title.lower():
                        continue
            price_val = _parse_price(item.get("price"))
            if price_min is not None and (price_val is None or price_val < price_min):
                continue
            if price_max is not None and (price_val is None or price_val > price_max):
                continue
            filtered.append(item)

        # Diff vs seen_item_ids
        seen = set(_get_seen_ids(job))
        new_items = [it for it in filtered if it.get("id") and it["id"] not in seen]
        result["match_found"] = len(new_items) > 0
        result["matched_items"] = new_items

        # Update seen_item_ids in DB (merge, cap at 500)
        if new_items:
            from core.models import get_db
            new_ids = [it["id"] for it in new_items]
            merged = list(seen) + new_ids
            merged = merged[-500:]
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE monitor_jobs SET seen_item_ids = ? WHERE id = ?",
                (json.dumps(merged), job["id"]),
            )
            conn.commit()
            conn.close()

    except requests.exceptions.Timeout:
        result["error_message"] = "Request timeout"
    except requests.exceptions.RequestException as e:
        result["error_message"] = str(e)
    except Exception as e:
        result["error_message"] = str(e)
        logger.exception("check_listing_page error")

    result["response_time"] = time.time() - start_time
    return result


def _get_extractor_config(job: Dict) -> Dict | None:
    raw = job.get("item_extractor_config")
    if not raw:
        return None
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None
    return None


def _get_seen_ids(job: Dict) -> List[str]:
    raw = job.get("seen_item_ids")
    if not raw:
        return []
    if isinstance(raw, list):
        return [str(x) for x in raw]
    if isinstance(raw, str):
        try:
            return [str(x) for x in json.loads(raw)]
        except json.JSONDecodeError:
            return []
    return []


def _parse_price(s: Any) -> float | None:
    if s is None:
        return None
    s = str(s).strip()
    if not s:
        return None
    s = re.sub(r"[^\d.,\-]", "", s)
    s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None
