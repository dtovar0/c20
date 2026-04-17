from flask import Blueprint, render_template
from .services import HomeService

home_bp = Blueprint("home", __name__, template_folder="templates")

@home_bp.route("/")
def index():
    try:
        return render_template("home/index.html", active_page='dashboard')
    except Exception as e:
        return f"Error: {str(e)}", 500

@home_bp.route("/botones")
def botones():
    try:
        return render_template("components/botones.html", active_page='botones')
    except Exception as e:
        return f"Error: {str(e)}", 500

@home_bp.route("/modales")
def modales():
    try:
        return render_template("components/modales.html", active_page='modales')
    except Exception as e:
        return f"Error: {str(e)}", 500

@home_bp.route("/notificaciones")
def notificaciones():
    try:
        return render_template("components/notificaciones.html", active_page='notificaciones')
    except Exception as e:
        return f"Error: {str(e)}", 500

@home_bp.route("/cards")
def cards():
    try:
        return render_template("components/cards.html", active_page='cards')
    except Exception as e:
        return f"Error: {str(e)}", 500

@home_bp.route("/timelines")
def timelines():
    try:
        return render_template("components/timelines.html", active_page='timelines')
    except Exception as e:
        return f"Error: {str(e)}", 500
