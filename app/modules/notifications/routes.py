from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from app import db
from app.modules.notifications.models import SMTPConfig

notifications_bp = Blueprint("notifications", __name__, url_prefix="/notifications")

@notifications_bp.route("/")
@login_required
def index():
    config = SMTPConfig.query.first()
    return render_template("notifications.html", config=config)

@notifications_bp.route("/save", methods=["POST"])
@login_required
def save():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
            
        config = SMTPConfig.query.first()
        if not config:
            config = SMTPConfig()
            db.session.add(config)
            
        # Update SMTP Config
        if "server" in data: config.server = data["server"]
        if "port" in data: config.port = data["port"]
        if "encryption" in data: config.encryption = data["encryption"]
        if "auth_enabled" in data: config.auth_enabled = data["auth_enabled"]
        if "user" in data: config.user = data["user"]
        if "password" in data: config.password = data["password"]
        if "sender_name" in data: config.sender_name = data["sender_name"]
        if "sender_email" in data: config.sender_email = data["sender_email"]
        
        db.session.commit()
        return jsonify({"status": "success", "message": "Configuración de Notificaciones Guardada"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
