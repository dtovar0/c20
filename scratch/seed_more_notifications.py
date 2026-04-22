from app import create_app, db
from app.modules.notifications.services import add_in_app_notification

app = create_app()
with app.app_context():
    # Success notification
    add_in_app_notification(
        type='success',
        title='Tarea Programada',
        message='La sincronización de backups con el servidor remoto se ha completado al 100%.'
    )
    
    # Info notification
    add_in_app_notification(
        type='info',
        title='Nueva Versión',
        message='Una nueva actualización de seguridad está disponible para el kernel del sistema.'
    )
    
    print("2 nuevas notificaciones de prueba creadas.")
