from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from app.decorators import admin_required
from app import db
from app.modules.notifications.models import SMTPConfig
from app.modules.notifications.services import send_test_email

notifications_bp = Blueprint("notifications", __name__, url_prefix="/notifications")

@notifications_bp.route("/")
@login_required
@admin_required
def index():
    config = SMTPConfig.query.first()
    return render_template("notifications.html", config=config)

@notifications_bp.route("/save", methods=["POST"])
@login_required
@admin_required
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

@notifications_bp.route("/test", methods=["POST"])
@login_required
@admin_required
def test_connection():
    try:
        data = request.get_json()
        target_email = data.get("target_email")
        
        if not target_email:
            return jsonify({"status": "error", "message": "Falta el correo destinatario"}), 400
            
        config = SMTPConfig.query.first()
        if not config:
            return jsonify({"status": "error", "message": "Configura y guarda el servidor primero"}), 400
            
        result = send_test_email(
            server=config.server,
            port=config.port,
            encryption=config.encryption,
            user=config.user,
            password=config.password,
            sender_name=config.sender_name,
            sender_email=config.sender_email,
            target_email=target_email
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
