"""Unit tests for nokwatch-scan plugin: listing_extractor and check_handler (mocked)."""
import json
import sys
from pathlib import Path
import pytest

# Allow importing nokwatch_scan when running pytest from project root (plugin not installed)
_plugin_src = Path(__file__).resolve().parent.parent / "plugins" / "nokwatch-scan" / "src"
if _plugin_src.exists() and str(_plugin_src) not in sys.path:
    sys.path.insert(0, str(_plugin_src))

nokwatch_scan = pytest.importorskip("nokwatch_scan")
from nokwatch_scan.listing_extractor import (
    extract_items,
    _jsonpath_one,
    JSONPATH_AVAILABLE,
    BS4_AVAILABLE,
)


class TestExtractItemsJson:
    """extract_items with JSON content."""

    def test_empty_items_path_returns_empty_list(self):
        items = extract_items(
            b'{"data": []}',
            "application/json",
            {"items_path": ""},
            "https://example.com",
        )
        assert items == []

    @pytest.mark.skipif(not JSONPATH_AVAILABLE, reason="jsonpath-ng not installed")
    def test_valid_jsonpath_returns_items(self):
        raw = json.dumps({
            "products": [
                {"id": "1", "name": "Item A", "url": "/a", "price": "10"},
                {"id": "2", "name": "Item B", "url": "/b", "price": "20"},
            ]
        }).encode("utf-8")
        config = {
            "items_path": "$.products[*]",
            "item_id": "$.id",
            "item_title": "$.name",
            "item_url": "$.url",
            "item_price": "$.price",
        }
        items = extract_items(raw, "application/json", config, "https://example.com")
        assert len(items) == 2
        assert items[0]["id"] == "1"
        assert items[0]["title"] == "Item A"
        assert items[0]["url"] == "https://example.com/a"
        assert items[0]["price"] == "10"
        assert items[1]["title"] == "Item B"
        assert items[1]["price"] == "20"

    @pytest.mark.skipif(not JSONPATH_AVAILABLE, reason="jsonpath-ng not installed")
    def test_invalid_json_returns_empty_list(self):
        items = extract_items(
            b"not json",
            "application/json",
            {"items_path": "$.items"},
            "https://example.com",
        )
        assert items == []


class TestExtractItemsHtml:
    """extract_items with HTML content."""

    @pytest.mark.skipif(not BS4_AVAILABLE, reason="beautifulsoup4 not installed")
    def test_empty_item_selector_returns_empty_list(self):
        items = extract_items(
            b"<html><body><div class='item'>x</div></body></html>",
            "text/html",
            {"item_selector": ""},
            "https://example.com",
        )
        assert items == []

    @pytest.mark.skipif(not BS4_AVAILABLE, reason="beautifulsoup4 not installed")
    def test_valid_selectors_returns_items(self):
        html = """
        <html><body>
        <div class="item">
            <a class="link" href="/p/1">Product 1</a>
            <span class="price">9.99</span>
        </div>
        <div class="item">
            <a class="link" href="/p/2">Product 2</a>
            <span class="price">19.99</span>
        </div>
        </body></html>
        """
        config = {
            "item_selector": ".item",
            "title_selector": ".link",
            "link_selector": ".link",
            "price_selector": ".price",
        }
        items = extract_items(
            html.encode("utf-8"),
            "text/html",
            config,
            "https://example.com",
        )
        assert len(items) == 2
        assert items[0]["title"] == "Product 1"
        assert items[0]["url"] == "https://example.com/p/1"
        assert items[0]["price"] == "9.99"
        assert items[1]["title"] == "Product 2"
        assert items[1]["price"] == "19.99"


class TestJsonpathOne:
    """_jsonpath_one helper."""

    @pytest.mark.skipif(not JSONPATH_AVAILABLE, reason="jsonpath-ng not installed")
    def test_single_value(self):
        obj = {"a": 1, "b": "two"}
        assert _jsonpath_one(obj, "$.b") == "two"
        assert _jsonpath_one(obj, "$.a") == "1"

    @pytest.mark.skipif(not JSONPATH_AVAILABLE, reason="jsonpath-ng not installed")
    def test_missing_path_returns_none(self):
        obj = {"a": 1}
        assert _jsonpath_one(obj, "$.x") is None

    def test_empty_path_returns_none(self):
        assert _jsonpath_one({"a": 1}, "") is None


class TestCheckHandler:
    """check_listing_page (with mocked requests)."""

    @pytest.mark.skipif(not JSONPATH_AVAILABLE, reason="jsonpath-ng not installed")
    def test_no_url_returns_error(self):
        from nokwatch_scan.check_handler import check_listing_page
        job = {"url": "", "item_extractor_config": {"items_path": "$.x"}}
        result = check_listing_page(job)
        assert result["success"] is False
        assert "url" in (result.get("error_message") or "").lower()

    @pytest.mark.skipif(not JSONPATH_AVAILABLE, reason="jsonpath-ng not installed")
    def test_no_extractor_config_returns_error(self):
        from nokwatch_scan.check_handler import check_listing_page
        job = {"url": "https://example.com"}
        result = check_listing_page(job)
        assert result["success"] is False
        assert "item_extractor" in (result.get("error_message") or "").lower()

    @pytest.mark.skipif(not JSONPATH_AVAILABLE, reason="jsonpath-ng not installed")
    def test_success_with_mocked_response(self):
        from unittest.mock import patch, MagicMock
        from nokwatch_scan.check_handler import check_listing_page

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = json.dumps({"items": [{"id": "1", "title": "T", "url": "https://a.com/1", "price": "5"}]}).encode("utf-8")
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.raise_for_status = MagicMock()

        job = {
            "url": "https://example.com/list",
            "item_extractor_config": {"items_path": "$.items[*]", "item_id": "$.id", "item_title": "$.title", "item_url": "$.url", "item_price": "$.price"},
            "match_pattern": "",
            "price_min": None,
            "price_max": None,
        }
        with patch("nokwatch_scan.check_handler.requests.get", return_value=mock_response):
            result = check_listing_page(job)
        assert result["success"] is True
        assert result.get("matched_items") is not None
        assert result["response_time"] >= 0
