from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from app.decorators import admin_required
from app import db
from app.modules.notifications.models import SMTPConfig, NotificationTemplate
from app.modules.notifications.services import send_test_email

notifications_bp = Blueprint("notifications", __name__, url_prefix="/notifications")

@notifications_bp.route("/")
@login_required
@admin_required
def index():
    config = SMTPConfig.query.first()
    
    # Ensuring default templates exist
    default_slugs = ['test', 'inicio', 'error', 'guardado', 'terminado']
    existing_slugs = [t.slug for t in NotificationTemplate.query.filter(NotificationTemplate.slug.in_(default_slugs)).all()]
    
    defaults = {
        'test': {'name': 'Test', 'subject': '🟢 NEXUS: VERIFICACIÓN_SISTEMA', 'body': '⚡ ALERTA DE PRUEBA\nEstado: SISTEMA_OK\nUsuario: {usuario}\nVerificación: EXITOSA', 'is_html': False},
        'inicio': {'name': 'Inicio', 'subject': '🚀 NEXUS: ARRANQUE_INICIAL_{usuario}', 'body': '🚀 ARRANQUE NEXUS\nOperación: INICIALIZANDO\nUsuario: {usuario}\nHora: {hora}\nBienvenido de vuelta a la matriz.', 'is_html': False},
        'error': {'name': 'Error', 'subject': '🛑 NEXUS: ALERTA_SEGURIDAD_CRÍTICA', 'body': '🛑 NEXUS CRÍTICO\nError: ACCESO_DENEGADO\nUsuario: {usuario}\nIP: {ip}\nAcción: BLOQUEO_SEGURIDAD', 'is_html': False},
        'guardado': {'name': 'Guardado', 'subject': '💾 NEXUS: SINCRONIZACIÓN_DATOS', 'body': '💾 SINCRONIZACIÓN NEXUS\nDestino: BASE_DATOS_CORE\nEstado: DATOS_GUARDADOS\nUsuario: {usuario}', 'is_html': False},
        'terminado': {'name': 'Terminado', 'subject': '✅ NEXUS: PROCESO_FINALIZADO', 'body': '✅ NEXUS COMPLETADO\nProceso: TAREA_FINALIZADA\nEjecutor: {usuario}\nEstado: ARCHIVOS_SINCRONIZADOS', 'is_html': False}
    }
    
    for slug in default_slugs:
        if slug not in existing_slugs:
            d = defaults[slug]
            tmpl = NotificationTemplate(slug=slug, name=d['name'], subject=d['subject'], body=d['body'], is_html=d['is_html'])
            db.session.add(tmpl)
    
    if any(slug not in existing_slugs for slug in default_slugs):
        db.session.commit()

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

@notifications_bp.route("/templates/get/<slug>")
@login_required
@admin_required
def get_template(slug):
    try:
        template = NotificationTemplate.query.filter_by(slug=slug).first()
        if not template:
            return jsonify({"status": "error", "message": "Plantilla no encontrada"}), 404
        return jsonify({"status": "success", "template": template.to_dict()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@notifications_bp.route("/templates/save", methods=["POST"])
@login_required
@admin_required
def save_template():
    try:
        data = request.get_json()
        slug = data.get("slug")
        if not slug:
            return jsonify({"status": "error", "message": "Identificador de plantilla requerido"}), 400
            
        template = NotificationTemplate.query.filter_by(slug=slug).first()
        if not template:
            template = NotificationTemplate(slug=slug)
            db.session.add(template)
            
        template.name = data.get("name", slug.capitalize())
        template.subject = data.get("subject", "")
        template.body = data.get("body", "")
        template.is_html = data.get("is_html", False)
        
        db.session.commit()
        return jsonify({"status": "success", "message": f"Plantilla '{slug.upper()}' guardada correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
