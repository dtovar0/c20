from flask import Blueprint, render_template
from .services import HomeService

home_bp = Blueprint("home", __name__, template_folder="templates")

@home_bp.route("/")
def index():
    try:
        message = HomeService.get_welcome_message()
        return render_template("home/index.html", message=message)
    except Exception as e:
        # Log error here in a real scenario
        return f"Error loading home page: {str(e)}", 500
