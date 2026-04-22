import os
import sys
import time
import datetime
import signal
from app import create_app, db
from app.modules.psx.models import PSX5KTask, PSX5KDetail

from app.modules.notifications.services import send_notification_by_slug
from app.modules.auth.models import User

LOCK_FILE = "psx5k_processor.lock"
MAX_LOCK_AGE_MINUTES = 60

def cleanup_lock():
    """Elimina el archivo lock al salir"""
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)
        print("🔓 Lock file eliminado. Proceso finalizado.")

def handle_stale_lock(app):
    """Maneja el caso de un lock antiguo (>60 min)"""
    mtime = os.path.getmtime(LOCK_FILE)
    age_minutes = (time.time() - mtime) / 60
    
    if age_minutes > MAX_LOCK_AGE_MINUTES:
        print(f"🛑 LOCK EXPIRADO ({int(age_minutes)} min). Enviando notificación de error.")
        with app.app_context():
            admin = User.query.filter_by(role='administrador').first()
            if admin and admin.email:
                send_notification_by_slug(
                    slug='error', 
                    target_email=admin.email,
                    context={'usuario': 'SYSTEM_BACKEND', 'ip': 'LOCAL_WORKER', 'error': 'STALE_LOCK_TIMEOUT'}
                )
        return True # Indica que es stale
    return False

def main():
    """
    Motor de procesamiento PSX5K (Backend Service)
    """
    app = create_app()

    # 1. Verificar/Generar LOCK
    if os.path.exists(LOCK_FILE):
        if not handle_stale_lock(app):
            print(f"⚠️ Proceso ya en ejecución o lock activo ({LOCK_FILE}). Abortando.")
            return
        else:
            # Si el lock es stale, lo eliminamos para permitir ejecución
            os.remove(LOCK_FILE)

    try:
        # Crear lock
        with open(LOCK_FILE, "w") as f:
            f.write(str(os.getpid()))
        print(f"🔒 Lock file creado (PID: {os.getpid()})")

        # 2. Inicializar App Context
        app = create_app()
        with app.app_context():
            print(f"🔍 Buscando tareas (Pendientes/Programadas) - {datetime.datetime.now()}")
            
            # Revisar si hay tareas pendientes o programadas (Top 5 por antigüedad)
            tasks = PSX5KTask.query.filter(
                PSX5KTask.estado.in_(['Pendiente', 'Programada'])
            ).order_by(PSX5KTask.created_at.asc()).limit(5).all()

            if not tasks:
                print("📭 No hay tareas por procesar.")
                return # El bloque finally se encargará del lock

            print(f"🎯 Encontradas {len(tasks)} tareas para procesar.")
            
            # 3. Flujo de procesamiento (Placeholder para las instrucciones del usuario)
            for idx, task in enumerate(tasks):
                print(f"⚙️ Procesando Top [{idx+1}/5]: Tarea ID {task.id} ({task.accion})")
                # Aquí irá la lógica de flujo que definas
                # Por ahora simulamos espera
                time.sleep(2)

    except Exception as e:
        print(f"❌ Error crítico en el backend: {str(e)}")
    finally:
        cleanup_lock()

if __name__ == "__main__":
    # Registrar señales para limpieza forzada
    signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))
    signal.signal(signal.SIGTERM, lambda s, f: sys.exit(0))
    
    main()
