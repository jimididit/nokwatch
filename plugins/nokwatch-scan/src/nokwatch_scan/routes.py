"""Page routes for Scanner plugin."""
import os
from flask import Blueprint, render_template

_tpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
bp = Blueprint("nokwatch_scan_pages", __name__, template_folder=_tpl_dir)


@bp.route("/")
def list_scans():
    """List scan jobs."""
    return render_template("scan/list.html")


@bp.route("/new")
def new_scan():
    """Add scan job form."""
    return render_template("scan/new.html")


@bp.route("/<int:job_id>/edit")
def edit_scan(job_id):
    """Edit scan job form."""
    return render_template("scan/edit.html", job_id=job_id)


@bp.route("/settings")
def settings():
    """Plugin settings (optional)."""
    return render_template("scan/settings.html")
