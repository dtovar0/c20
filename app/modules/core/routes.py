from flask import Blueprint, render_template

core_bp = Blueprint("core", __name__, url_prefix="/")

@core_bp.route("/")
def index():
    return render_template("index.html")

@core_bp.route("/dashboard-2")
def dashboard_2():
    return render_template("dashboard_2.html")
