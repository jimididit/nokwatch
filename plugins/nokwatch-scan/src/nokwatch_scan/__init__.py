"""nokwatch-scan: Listing scan plugin for Nokwatch."""

from nokwatch_scan.migrations import run_migrations
from nokwatch_scan.check_handler import check_listing_page


def register(app, get_db, register_check_handler, register_menu_item, **kwargs):
    """Plugin entry point: register routes, handler, menu."""
    run_migrations(get_db)
    register_check_handler("listing_scan", check_listing_page)

    from nokwatch_scan.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix="/api/scan")

    from nokwatch_scan.routes import bp as pages_bp
    app.register_blueprint(pages_bp, url_prefix="/scan")

    register_menu_item("Scanner", "/scan/")
