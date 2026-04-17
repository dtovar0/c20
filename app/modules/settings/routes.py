from flask import Blueprint, render_template

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")

@settings_bp.route("/")
def index():
    return render_template("settings.html")
