from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from app.decorators import admin_required
from app import db
from app.modules.notifications.models import SMTPConfig, NotificationTemplate, InAppNotification
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
        if "username" in data: config.username = data["username"]
        if "password" in data: config.password = data["password"]
        if "sender_name" in data: config.sender_name = data["sender_name"]
        
        db.session.commit()
        return jsonify({"status": "success", "message": "Configuración de Notificaciones Guardada"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": "Ocurrió un error al guardar la configuración SMTP."}), 500

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
            username=config.username,
            password=config.password,
            sender_name=config.sender_name,
            target_email=target_email
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"status": "error", "message": "Error interno del sistema durante la prueba SMTP."}), 500

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
        return jsonify({"status": "error", "message": "Fallo al obtener la plantilla de notificación solicitada."}), 500

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
        return jsonify({"status": "error", "message": "Error grave al intentar guardar la plantilla."}), 500

@notifications_bp.route("/api/active")
@login_required
def get_active_notifications():
    try:
        from datetime import timedelta
        # SILENT MAINTENANCE: Auto-clean old records
        # 1. Delete READ notifications older than 4 days
        four_days_ago = datetime.utcnow() - timedelta(days=4)
        InAppNotification.query.filter(
            InAppNotification.is_read == True,
            InAppNotification.created_at < four_days_ago
        ).delete()
        
        # 2. Delete ALL notifications older than 7 days
        week_ago = datetime.utcnow() - timedelta(days=7)
        InAppNotification.query.filter(
            InAppNotification.created_at < week_ago
        ).delete()
        
        db.session.commit()

        # Hybrid fetch: Global (null) OR specific to user
        notifications = InAppNotification.query.filter(
            (InAppNotification.user_id == None) | (InAppNotification.user_id == current_user.id)
        ).order_by(InAppNotification.created_at.desc()).limit(15).all()
        
        return jsonify({
            "status": "success", 
            "notifications": [n.to_dict() for n in notifications],
            "unread_count": sum(1 for n in notifications if not n.is_read)
        })
    except Exception as e:
        return jsonify({"status": "error", "message": "Falló la lectura del estado de las notificaciones."}), 500

@notifications_bp.route("/api/mark-read", methods=["POST"])
@login_required
def mark_read():
    try:
        data = request.get_json()
        notif_id = data.get("id")
        
        if notif_id:
            # Mark a specific one
            notif = InAppNotification.query.get(notif_id)
            if notif and (notif.user_id == None or notif.user_id == current_user.id):
                notif.is_read = True
        else:
            # Mark all as read for this user
            InAppNotification.query.filter(
                (InAppNotification.user_id == None) | (InAppNotification.user_id == current_user.id)
            ).update({InAppNotification.is_read: True}, synchronize_session=False)

        db.session.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": "Error modificando el registro de las notificaciones."}), 500

@notifications_bp.route("/api/delete-all", methods=["DELETE"])
@login_required
def delete_all():
    try:
        # Delete only notifications relevant to this user (Global or Personal)
        InAppNotification.query.filter(
            (InAppNotification.user_id == None) | (InAppNotification.user_id == current_user.id)
        ).delete(synchronize_session=False)
        
        db.session.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": "Se produjo un fallo al intentar limpiar el registro de notificaciones."}), 500


