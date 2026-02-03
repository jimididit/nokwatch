"""Extract items from JSON or HTML listing pages."""
import json
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

try:
    from jsonpath_ng import parse as jsonpath_parse
    JSONPATH_AVAILABLE = True
except ImportError:
    JSONPATH_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False


def extract_items(
    response_content: bytes,
    content_type: str,
    config: Dict[str, Any],
    base_url: str,
) -> List[Dict[str, Any]]:
    """
    Extract items from JSON or HTML. Returns [{id, url, title, price}, ...].
    config for JSON: items_path, item_url, item_title, item_price (JSONPath per item)
    config for HTML: item_selector, title_selector, link_selector, price_selector (CSS)
    """
    content_type = (content_type or "").lower()
    is_json = "json" in content_type or (
        response_content and len(response_content) >= 2 and response_content.lstrip()[:1] in (b"{", b"[")
    )

    if is_json:
        return _extract_items_json(response_content, config, base_url)
    return _extract_items_html(response_content, config, base_url)


def _extract_items_json(
    raw: bytes,
    config: Dict[str, Any],
    base_url: str,
) -> List[Dict[str, Any]]:
    """Extract items from JSON using JSONPath."""
    if not JSONPATH_AVAILABLE:
        logger.warning("jsonpath-ng not available")
        return []
    items_path = (config.get("items_path") or "").strip()
    if not items_path:
        return []
    try:
        data = json.loads(raw.decode("utf-8", errors="replace"))
    except json.JSONDecodeError as e:
        logger.warning("Invalid JSON: %s", e)
        return []
    try:
        expr = jsonpath_parse(items_path)
        matches = expr.find(data)
    except Exception as e:
        logger.warning("JSONPath error for %s: %s", items_path, e)
        return []

    item_url_path = (config.get("item_url") or "").strip()
    item_title_path = (config.get("item_title") or "").strip()
    item_price_path = (config.get("item_price") or "").strip()
    item_id_path = (config.get("item_id") or "").strip() or item_url_path

    items = []
    for i, m in enumerate(matches):
        ctx = m.value
        if not isinstance(ctx, dict):
            continue
        item_id = _jsonpath_one(ctx, item_id_path, i)
        url = _jsonpath_one(ctx, item_url_path, i)
        title = _jsonpath_one(ctx, item_title_path, i)
        price = _jsonpath_one(ctx, item_price_path, i)
        if url and not url.startswith(("http://", "https://")):
            url = urljoin(base_url, url)
        items.append({
            "id": item_id or url or str(i),
            "url": url or "",
            "title": title or "",
            "price": price or "",
        })
    return items


def _jsonpath_one(obj: Any, path: str, default: Any = None) -> Optional[str]:
    """Evaluate a JSONPath on a single object. Returns first match or default."""
    if not path or not isinstance(obj, dict):
        return str(default) if default is not None else None
    try:
        expr = jsonpath_parse(path)
        matches = expr.find(obj)
        if matches:
            v = matches[0].value
            return str(v) if v is not None else None
    except Exception:
        pass
    return None


def _extract_items_html(
    raw: bytes,
    config: Dict[str, Any],
    base_url: str,
) -> List[Dict[str, Any]]:
    """Extract items from HTML using BeautifulSoup selectors."""
    if not BS4_AVAILABLE:
        logger.warning("beautifulsoup4 not available")
        return []
    item_sel = (config.get("item_selector") or "").strip()
    if not item_sel:
        return []
    try:
        soup = BeautifulSoup(raw, "html.parser")
    except Exception as e:
        logger.warning("BeautifulSoup parse error: %s", e)
        return []

    title_sel = (config.get("title_selector") or "").strip()
    link_sel = (config.get("link_selector") or "").strip()
    price_sel = (config.get("price_selector") or "").strip()

    items = []
    for i, el in enumerate(soup.select(item_sel)):
        title = _sel_text(el, title_sel)
        href = _sel_attr(el, link_sel, "href")
        price = _sel_text(el, price_sel)
        url = urljoin(base_url, href) if href else ""
        item_id = url or str(i)
        items.append({
            "id": item_id,
            "url": url,
            "title": title or "",
            "price": price or "",
        })
    return items


def _sel_text(parent, selector: str) -> str:
    """Get text of first match of selector within parent."""
    if not selector:
        return ""
    try:
        el = parent.select_one(selector)
        return (el.get_text(strip=True) or "") if el else ""
    except Exception:
        return ""


def _sel_attr(parent, selector: str, attr: str) -> str:
    """Get attr of first match of selector within parent."""
    if not selector:
        return ""
    try:
        el = parent.select_one(selector)
        return (el.get(attr) or "") if el else ""
    except Exception:
        return ""
