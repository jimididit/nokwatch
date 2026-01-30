"""Optional screenshot capture (requires Playwright). On match, save to static/screenshots/."""
import logging
from pathlib import Path
from datetime import datetime

from core.config import Config

logger = logging.getLogger(__name__)

# Base dir for screenshots (project root / static / screenshots)
SCREENSHOTS_DIR = Config.BASE_DIR / "static" / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

_playwright_available = None


def _check_playwright():
    global _playwright_available
    if _playwright_available is not None:
        return _playwright_available
    try:
        from playwright.sync_api import sync_playwright
        _playwright_available = True
    except ImportError:
        _playwright_available = False
    return _playwright_available


def capture_screenshot(url: str, job_id: int) -> str | None:
    """
    Capture a screenshot of the given URL. Saves to static/screenshots/.
    Returns relative path like 'screenshots/job_1_20250101_120000.png' or None if unavailable.
    """
    if not _check_playwright():
        logger.debug("Playwright not installed; skipping screenshot")
        return None
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"job_{job_id}_{timestamp}.png"
    filepath = SCREENSHOTS_DIR / filename
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1280, "height": 720})
            page.goto(url, wait_until="networkidle", timeout=15000)
            page.screenshot(path=str(filepath))
            browser.close()
        return f"screenshots/{filename}"
    except Exception as e:
        logger.warning(f"Screenshot capture failed for {url}: {e}")
        return None
