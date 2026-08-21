import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.modules.notifications.models import SMTPConfig, NotificationTemplate, InAppNotification

def add_in_app_notification(type, title, message, user_id=None, solo_admins=False):
    """
    Creates a persistent in-app notification.
    type: success, error, warning, info
    user_id: ID of the user (NULL for global)
    solo_admins: dirige el aviso a cada administrador en vez de dejarlo global.

    Un aviso sin user_id es global, y la campana los muestra a cualquiera que
    inicie sesión (filtra por 'user_id IS NULL OR user_id = <yo>'). Los avisos
    de infraestructura —fallos del nodo, purga de cuentas— no son para toda la
    plantilla: su correo equivalente ya se limita al administrador, y la campana
    debe hacer lo mismo. De ahí solo_admins, que inserta una fila por cada
    administrador para que todos se enteren, no solo el primero.
    """
    from app import db
    from app.modules.auth.models import User
    try:
        if solo_admins:
            admins = User.query.filter_by(role='administrador').all()
            if not admins:
                # Sin administradores no hay a quién avisar. Se deja constancia
                # en consola en vez de caer en un aviso global, que es
                # justamente lo que se quiere evitar.
                print(f"⚠️  Aviso de sistema sin destinatario (no hay administradores): {title}")
                return False
            for admin in admins:
                db.session.add(InAppNotification(
                    type=type, title=title, message=message, user_id=admin.id
                ))
        else:
            db.session.add(InAppNotification(
                type=type, title=title, message=message, user_id=user_id
            ))
        db.session.commit()
        return True
    except Exception as e:
        print(f"Error adding notification: {e}")
        db.session.rollback()
        return False


def send_test_email(server, port, encryption, username, password, sender_name, target_email):
    """
    Sends a test email to verify SMTP configuration.
    """
    try:
        msg = MIMEMultipart()
        msg['From'] = f"{sender_name} <{username}>"
        msg['To'] = target_email
        msg['Subject'] = "⚡ Nexus Premium - SMTP Verification"

        body = f"""
        <html>
            <body style="font-family: sans-serif; color: #1a1a1a;">
                <h2 style="color: #6366f1;">⚡ Nexus System Verification</h2>
                <p>Usted está recibiendo este mensaje porque se ha solicitado una prueba de conectividad desde el panel de administración.</p>
                <div style="background: #f8fafc; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0;">
                    <p><b>Status:</b> Conexión Exitosa</p>
                    <p><b>Servidor:</b> {server}:{port}</p>
                    <p><b>Cifrado:</b> {encryption.upper()}</p>
                </div>
            </body>
        </html>
        """
        msg.attach(MIMEText(body, 'html'))

        if encryption == 'ssl':
            smtp = smtplib.SMTP_SSL(server, port, timeout=10)
        else:
            smtp = smtplib.SMTP(server, port, timeout=10)
            if encryption == 'starttls':
                smtp.starttls()
                
        import os
        if os.getenv('DEBUG_SMTP') == 'true':
            smtp.set_debuglevel(1)

        if username and password:
            smtp.login(username, password)

        smtp.send_message(msg)
        smtp.quit()
        return {"status": "success", "message": "Correo de prueba enviado correctamente"}
    except Exception as e:
        return {"status": "error", "message": "Error al enviar correo de prueba."}

def send_notification_by_slug(slug, target_email, context=None, html_body=None,
                              subject_override=None):
    """
    Sends a pre-defined notification template using the global SMTP configuration.

    html_body sustituye el cuerpo de la plantilla por HTML ya armado, para los
    avisos cuyo contenido es una tabla de cifras que no se puede expresar con
    placeholders (el resumen operativo de una tarea). La plantilla sigue
    haciendo falta: de ella salen el asunto y el registro editable en la UI.
    subject_override hace lo propio con el asunto.

    Un slug puede tener varios emisores (PSX5K y C20 comparten 'terminado'), así
    que quien no pase html_body conserva exactamente el comportamiento anterior.
    """
    from app import db
    import os
    from dotenv import load_dotenv
    
    # Reload env to catch changes without restart
    load_dotenv(override=True)
    
    # Global Switch Check
    if os.getenv('ENABLE_NOTIFICATIONS', 'true').lower() != 'true':
        print(f"🔕 Notificaciones desactivadas globalmente (.env). Omitiendo slug: {slug}")
        return {"status": "success", "message": "Notifications disabled globally"}

    try:
        config = SMTPConfig.query.first()
        template = NotificationTemplate.query.filter_by(slug=slug).first()
        if not config or not template:
            return {"status": "error", "message": "Missing SMTP config or Template"}

        # Prepare content
        body = html_body if html_body is not None else template.body
        subject = subject_override or template.subject
        if context:
            for key, val in context.items():
                # Un cuerpo inyectado ya viene completo; sustituir dentro de él
                # solo podría estropear su marcado.
                if html_body is None:
                    body = body.replace(f"{{{key}}}", str(val))
                subject = subject.replace(f"{{{key}}}", str(val))

        # Los placeholders que el emisor no rellenó se sustituyen por '-' en vez
        # de quedar literales en el correo: una misma plantilla la usan varios
        # emisores (PSX5K, C20, Teams) y no todos aportan los mismos campos.
        # No se aplica al cuerpo inyectado: sus llaves son CSS, no huecos.
        import re as _re
        _hueco = _re.compile(r'\{[a-zA-Z_][a-zA-Z0-9_]*\}')
        if html_body is None:
            body = _hueco.sub('-', body)
        # En el asunto se elimina además el fragmento que rodeaba al hueco, para
        # no dejar restos como "Tarea #" sin número. Los fragmentos se delimitan
        # por '·', así que un asunto sin ningún dato conserva solo su cabecera.
        partes = [p.strip() for p in subject.split('·')]
        partes = [p for p in partes if p and not _hueco.search(p)]
        subject = ' · '.join(partes) if partes else _hueco.sub('', template.subject).strip(' ·')

        msg = MIMEMultipart()
        msg['From'] = f"{config.sender_name} <{config.username}>"
        msg['To'] = target_email
        msg['Subject'] = subject
        es_html = True if html_body is not None else template.is_html
        msg.attach(MIMEText(body, 'html' if es_html else 'plain'))

        # Connection
        if config.encryption == 'ssl':
            smtp = smtplib.SMTP_SSL(config.server, config.port, timeout=10)
        else:
            smtp = smtplib.SMTP(config.server, config.port, timeout=10)
            if config.encryption == 'starttls':
                smtp.starttls()

        import os
        if os.getenv('DEBUG_SMTP') == 'true':
            smtp.set_debuglevel(1)

        if config.auth_enabled and config.username and config.password:
            smtp.login(config.username, config.password)

        smtp.send_message(msg)
        smtp.quit()
        return {"status": "success", "message": f"Notificación '{slug}' enviada"}

    except Exception as e:
        return {"status": "error", "message": "Error interno enviando notificación."}
