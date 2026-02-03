"""Plugin loader: discover, load, and dispatch to check handlers via setuptools entry points."""
import importlib.metadata
import logging
from typing import Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

# Map job_type -> handler function
_check_handlers: Dict[str, Callable] = {}

# Menu items registered by plugins: [{name, url, icon?}, ...]
_menu_items: List[Dict] = []


def register_check_handler(job_type: str, handler: Callable) -> None:
    """Register a check handler for jobs with the given job_type."""
    _check_handlers[job_type] = handler
    logger.info(f"Registered check handler for job_type={job_type}")


def get_check_handler(job: Dict) -> Callable:
    """
    Return the handler for the job's type. Uses job_type or scan_mode (backward compat).
    Defaults to check_website from monitoring.monitor.
    """
    job_type = job.get("job_type") or job.get("scan_mode")
    if job_type and job_type in _check_handlers:
        return _check_handlers[job_type]
    from monitoring.monitor import check_website
    return check_website


def register_menu_item(name: str, url: str, icon: Optional[str] = None) -> None:
    """Register a menu item for the nav. Plugins call this during register()."""
    _menu_items.append({"name": name, "url": url, "icon": icon})


def get_menu_items() -> List[Dict]:
    """Return registered menu items for template rendering."""
    return list(_menu_items)


def load_plugins(
    app,
    get_db,
    *,
    register_check_handler_fn=None,
    register_menu_item_fn=None,
    get_screenshot_service=None,
    get_notification_service=None,
) -> None:
    """
    Load all plugins from entry points group 'nokwatch.plugins'.
    Each plugin exposes a 'register' function called with app, get_db, and hooks.
    """
    if register_check_handler_fn is None:
        register_check_handler_fn = register_check_handler
    if register_menu_item_fn is None:
        register_menu_item_fn = register_menu_item

    entry_points = []
    try:
        eps = importlib.metadata.entry_points(group="nokwatch.plugins")
        entry_points = list(eps)
    except Exception as e:
        logger.debug("No nokwatch.plugins entry points or error: %s", e)

    for ep in entry_points:
        try:
            plugin_module = ep.load()
            register_fn = plugin_module if callable(plugin_module) else getattr(plugin_module, "register", None)
            if not register_fn:
                logger.warning("Plugin %s has no register function", ep.name)
                continue
            register_fn(
                app=app,
                get_db=get_db,
                register_check_handler=register_check_handler_fn,
                register_menu_item=register_menu_item_fn,
                get_screenshot_service=get_screenshot_service,
                get_notification_service=get_notification_service,
            )
            logger.info("Loaded plugin: %s", ep.name)
        except Exception as e:
            logger.exception("Failed to load plugin %s: %s", ep.name, e)
