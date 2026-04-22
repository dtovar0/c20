from app import create_app, db
from app.modules.notifications.services import add_in_app_notification

app = create_app()
with app.app_context():
    # Global notification
    add_in_app_notification(
        type='system',
        title='Sistema Actualizado',
        message='La plataforma Nexus ha sido actualizada a la versión 4.2.16 con éxito.'
    )
    
    # Warning notification
    add_in_app_notification(
        type='warning',
        title='Intento de Acceso',
        message='Se detectó un intento de inicio de sesión desde una nueva IP: 192.168.1.45.'
    )
    
    print("Notificaciones de prueba creadas correctamente.")
