import os
import sys
import time
import datetime
import signal
from app import create_app, db
from app.modules.psx.models import PSX5KTask, PSX5KDetail

LOCK_FILE = "psx5k_processor.lock"

def cleanup_lock():
    """Elimina el archivo lock al salir"""
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)
        print("🔓 Lock file eliminado. Proceso finalizado.")

def main():
    """
    Motor de procesamiento PSX5K (Backend Service)
    """
    # 1. Verificar/Generar LOCK
    if os.path.exists(LOCK_FILE):
        print(f"⚠️ Proceso ya en ejecución o lock existente ({LOCK_FILE}). Abortando.")
        return

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
