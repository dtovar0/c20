from flask import Blueprint, render_template
from flask_login import login_required

core_bp = Blueprint("core", __name__, url_prefix="/")

@core_bp.route("/")
@login_required
def index():
    return render_template("index.html")

@core_bp.route("/dashboard-2")
@login_required
def dashboard_2():
    return render_template("dashboard_2.html")
