import os
import sys
import time
import datetime
import signal
from app import create_app, db
from app.modules.psx.models import PSX5KTask, PSX5KDetail, PSX5KHistory
from app.modules.notifications.services import send_notification_by_slug
from app.modules.auth.models import User
from app.modules.audit.services import add_audit_log

# Configuración Global
LOCK_FILE = "/tmp/psx5k_worker.pid"
SLEEP_IDLE = 10  # Segundos a esperar si no hay tareas
SLEEP_BETWEEN = 2 # Segundos entre tareas para no saturar DB

def cleanup_lock():
    """Elimina el archivo con el PID al salir"""
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)
        print("🔓 Worker detenido. Lock file eliminado.")

def check_single_instance():
    """Verifica que no haya otro worker corriendo"""
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, 'r') as f:
                pid = int(f.read().strip())
            # Verificar si el proceso sigue vivo
            os.kill(pid, 0)
            print(f"⚠️ El Worker ya está en ejecución (PID: {pid}). Abortando.")
            sys.exit(1)
        except (OSError, ValueError):
            # El PID no existe o el archivo está corrupto, podemos seguir
            print("🕒 Detectado lock huérfano. Limpiando...")
            os.remove(LOCK_FILE)

def handle_stale_tasks(app):
    """Detecta y limpia tareas que se quedaron colgadas más de 60 min"""
    with app.app_context():
        limit = datetime.datetime.now() - datetime.timedelta(minutes=60)
        stale_tasks = PSX5KTask.query.filter(
            PSX5KTask.estado == 'Ejecutando',
            PSX5KTask.fecha_inicio < limit
        ).all()
        
        for task in stale_tasks:
            print(f"🚨 Tarea estancada detectada (ID: {task.id}). Cancelando...")
            task.estado = 'Error'
            db.session.commit()
            
            admin = User.query.filter_by(role='administrador').first()
            if admin and admin.email:
                send_notification_by_slug(
                    slug='error', 
                    target_email=admin.email,
                    context={'usuario': 'SYSTEM_WATCHDOG', 'ip': 'LOCAL_WORKER', 'error': f'TASK_TIMEOUT_ID_{task.id}'}
                )
            add_audit_log("tarea terminada", status="error", detail=f"Timeout: {task.id} - Superó 60 min", user_override="SYSTEM")

def process_task_data(task):
    """Retorna la lista de números desde archivo o manual"""
    if not task.datos: return []
    
    base_path = os.getenv('PROJECT_ROOT', os.getcwd())
    
    if task.datos_tipo == 'Archivo':
        file_path = os.path.join(base_path, 'uploads/psx5k', task.datos)
        if not os.path.exists(file_path):
            print(f"❌ Fragmento no encontrado: {file_path}")
            return []
        try:
            with open(file_path, 'r') as f:
                return [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"⚠️ Error leyendo fragmento {task.datos}: {e}")
            return []
    else:
        return [x.strip() for x in task.datos.split(',') if x.strip()]

def main():
    """Motor de procesamiento persistente (Daemon)"""
    check_single_instance()
    
    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))
    
    print(f"🚀 Nexus Worker iniciado (PID: {os.getpid()})")
    
    app = create_app()
    
    # Manejador de señales para salida limpia
    def signal_handler(sig, frame):
        cleanup_lock()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Limpieza inicial
    handle_stale_tasks(app)

    while True:
        try:
            # Monitorear tareas colgadas en cada ciclo
            handle_stale_tasks(app)
            
            with app.app_context():
                # Buscar una tarea pendiente
                task = PSX5KTask.query.filter(
                    PSX5KTask.estado.in_(['Pendiente', 'Programada'])
                ).order_by(PSX5KTask.created_at.asc()).first()

                if not task:
                    time.sleep(SLEEP_IDLE)
                    continue

                print(f"🎯 Procesando Tarea ID {task.id}: {task.tarea}")
                
                # Marcar inicio
                task.estado = 'Ejecutando'
                task.fecha_inicio = datetime.datetime.now()
                db.session.commit()

                # Notificación de inicio
                admin = User.query.filter_by(role='administrador').first()
                if admin and admin.email:
                    send_notification_by_slug(slug='inicio', target_email=admin.email, 
                                            context={'usuario': task.usuario, 'hora': task.fecha_inicio.strftime('%H:%M:%S')})
                
                add_audit_log("tarea iniciada", status="info", detail=f"ID: {task.id} - {task.tarea}", user_override=task.usuario)

                # Procesar datos
                ani_list = process_task_data(task)
                detail = PSX5KDetail.query.get(task.id) or PSX5KDetail(id=task.id)
                detail.total = len(ani_list)
                db.session.add(detail)
                db.session.commit()

                if detail.total == 0:
                    task.estado = 'Error'
                    db.session.commit()
                    continue

                # Ejecutar comando PSX
                from psx5k_cmd import psx5k_cmd
                results = psx5k_cmd(
                    line_task=task.tarea, 
                    line_number=ani_list,
                    line_type=task.accion_tipo,
                    routing_label=task.routing_label,
                    force=task.force
                )
                
                # Resultados
                detail.ok = results.get("ok", 0) + results.get("dup", 0)
                detail.fail = results.get("fail", 0)
                detail.force_ok = results.get("force_ok", 0)
                
                # Historial detallado
                for log_entry in results.get('logs', []):
                    try:
                        parts = log_entry.split(' ', 2)
                        status_tag = parts[0].strip('[]')
                        number = parts[1]
                        db.session.add(PSX5KHistory(
                            task_id=task.id, usuario=task.usuario,
                            numero=number, routing_label=task.routing_label,
                            accion=task.tarea, estado=status_tag, fecha=datetime.datetime.now()
                        ))
                    except: pass
                
                # Finalizar
                task.estado = 'Terminada'
                task.fecha_fin = datetime.datetime.now()
                db.session.commit()
                
                add_audit_log("tarea terminada", status="success", detail=f"ID: {task.id} | OK: {detail.ok} | FAIL: {detail.fail}", user_override=task.usuario)

                if admin and admin.email:
                    send_notification_by_slug(slug='terminado', target_email=admin.email, 
                                            context={'usuario': task.usuario, 'hora': task.fecha_fin.strftime('%H:%M:%S')})

            time.sleep(SLEEP_BETWEEN)

        except Exception as e:
            print(f"❌ Error en el ciclo del worker: {str(e)}")
            time.sleep(SLEEP_IDLE) # Esperar antes de reintentar si hay error crítico

if __name__ == "__main__":
    main()
