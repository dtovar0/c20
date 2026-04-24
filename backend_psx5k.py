import os
import sys
import time
import datetime
import signal
from dotenv import load_dotenv

load_dotenv()

# Configuración de notificaciones
ADMIN_EMAIL = os.getenv('NOTIFICATION_ADMIN_EMAIL', 'admin@example.com')

def get_notification_target(username):
    """Resuelve el destinatario de la notificación."""
    if not username: return ADMIN_EMAIL
    if '@' in username: return username
    # Si es 'admin' o usuario sin arroba, enviamos al admin de .env
    return ADMIN_EMAIL

from app import create_app, db
from app.modules.psx.models import PSX5KTask, PSX5KDetail, PSX5KHistory, PSX5KCommandLog
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
            if admin and admin.username:
                send_notification_by_slug(
                    slug='error', 
                    target_email=admin.username,
                    context={'usuario': 'SYSTEM_WATCHDOG', 'ip': 'LOCAL_WORKER', 'error': f'TASK_TIMEOUT_ID_{task.id}'}
                )
            add_audit_log("tarea terminada", status="error", detail=f"Timeout: {task.id} - Superó 60 min", user_override="SYSTEM")

def handle_user_hygiene(app):
    """Ejecuta la purga de usuarios inactivos y notifica resultados"""
    with app.app_context():
        try:
            from app.modules.auth.services import purge_inactive_users
            from app.modules.notifications.services import send_notification_by_slug, add_in_app_notification
            
            print("🧹 [HYGIENE] Ejecutando rutina de limpieza de usuarios...")
            result = purge_inactive_users(days=30)
            
            if result.get("status") == "success" and result.get("purged_count", 0) > 0:
                count = result["purged_count"]
                names = ", ".join(result["purged_names"])
                print(f"✨ [HYGIENE] Limpieza completada: {count} usuarios eliminados ({names})")
                
                # 1. Notificación Campana
                add_in_app_notification(
                    type='warning',
                    title='Limpieza de Usuarios Inactivos',
                    message=f'Se han eliminado automáticamente {count} cuentas tras 30 días de inactividad: {names}'
                )
                
                # 2. Notificación Email
                admin = User.query.filter_by(role='administrador').first()
                if admin and admin.username:
                    send_notification_by_slug(
                        slug='info', 
                        target_email=admin.username,
                        context={
                            'usuario': 'SYSTEM_WORKER', 
                            'ip': 'DAEMON_PROCESS', 
                            'mensaje': f'PURGA AUTOMÁTICA COMPLETADA: Se eliminaron {count} cuentas de usuario por inactividad prolongada (>30 días). Nombres: {names}'
                        }
                    )
        except Exception as e:
            print(f"⚠️ [HYGIENE] Error en rutina de limpieza: {e}")

def process_task_data(task):
    """Retorna la lista de números desde archivo o datos directos en DB"""
    if not task.datos: return []
    
    # Si detectamos comas, es probable que sean datos directos en DB (formato chunk nuevo)
    if ',' in task.datos:
        return [x.strip() for x in task.datos.split(',') if x.strip()]
    
    # Si no hay comas, comprobamos si es un archivo físico (formato legacy o archivo único)
    base_path = os.getenv('PROJECT_ROOT', os.getcwd())
    file_path = os.path.join(base_path, 'uploads/psx5k', task.datos)
    
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                # Soporte para CSV básico o TXT por líneas
                return [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"⚠️ Error leyendo archivo físico {task.datos}: {e}")
            return []
    
    # Fallback: intentar tratarlo como un solo número o una lista mal formateada
    return [task.datos.strip()]

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
    handle_user_hygiene(app) # Limpieza de inactividad al arrancar

    last_health_check = datetime.datetime.now()
    last_hygiene_check = datetime.datetime.now()
    
    HEALTH_CHECK_INTERVAL = 3600 # 1 hora si está idle
    HYGIENE_CHECK_INTERVAL = 86400 # 24 horas para purga de usuarios

    while True:
        try:
            # Monitorear tareas colgadas en cada ciclo
            handle_stale_tasks(app)
            
            # Monitorear higiene de usuarios cada 24h
            now = datetime.datetime.now()
            if (now - last_hygiene_check).total_seconds() > HYGIENE_CHECK_INTERVAL:
                handle_user_hygiene(app)
                last_hygiene_check = now
            
            with app.app_context():
                # Buscar una tarea pendiente
                task = PSX5KTask.query.filter(
                    PSX5KTask.estado.in_(['Pendiente', 'Programada'])
                ).order_by(PSX5KTask.id.asc()).first()

                # --- LÓGICA DE MONITOREO INTEGRADA ---
                now = datetime.datetime.now()
                should_check = False
                
                if task:
                    # Si hay tarea, validamos conectividad antes de empezar
                    should_check = True
                elif (now - last_health_check).total_seconds() > HEALTH_CHECK_INTERVAL:
                    # Si está idle, validamos cada hora
                    should_check = True
                    last_health_check = now

                if should_check:
                    from psx5k_cmd import test_connectivity
                    ok, msg = test_connectivity()
                    if not ok:
                        print(f"🚨 [WATCHDOG] Fallo de conectividad detectado: {msg}")
                        
                        # 1. Auditoría
                        add_audit_log("error conectividad", status="error", detail=f"PSX: {msg}", user_override="SYSTEM_WORKER")
                        
                        # 2. Notificación In-App (Campana)
                        from app.modules.notifications.services import add_in_app_notification
                        add_in_app_notification(
                            type='error',
                            title='Fallo de Conexión PSX',
                            message=f'No se pudo establecer conexión con el nodo PSX: {msg}'
                        )

                        # 3. Notificación por Correo
                        admin = User.query.filter_by(role='administrador').first()
                        if admin and admin.username:
                            send_notification_by_slug(
                                slug='error', 
                                target_email=admin.username,
                                context={'usuario': 'SYSTEM_WORKER', 'ip': os.getenv('PSX_IP', 'PSX_NODE'), 'error': f'CONECTIVIDAD FALLIDA: {msg}'}
                            )
                        
                        if task:
                            # Si había una tarea, la dejamos en pendiente para reintento y saltamos este ciclo
                            print("⏳ Pospone tarea por falta de conectividad.")
                            time.sleep(60)
                            continue
                # ------------------------------------

                if not task:
                    time.sleep(SLEEP_IDLE)
                    continue

                print(f"🎯 Procesando Tarea ID {task.id}: {task.job.tarea}")
                
                # Marcar inicio
                task.estado = 'Ejecutando'
                task.fecha_inicio = datetime.datetime.now()
                db.session.commit()

                # Notificación de inicio al propietario
                target = get_notification_target(task.job.usuario)
                if target:
                    send_notification_by_slug(slug='inicio', target_email=target, 
                                            context={'usuario': task.job.usuario, 'hora': task.fecha_inicio.strftime('%H:%M:%S')})
                    print(f"📧 Correo de inicio enviado satisfactoriamente a: {target}")
                
                add_audit_log("tarea iniciada", status="info", detail=f"ID: {task.id} - {task.job.tarea}", user_override=task.job.usuario)

                # Procesar datos
                ani_list = process_task_data(task)
                detail = db.session.get(PSX5KDetail, task.id) or PSX5KDetail(id=task.id)
                detail.total = len(ani_list)
                db.session.add(detail)
                if detail.total == 0:
                    print(f"⚠️ Tarea {task.id} abortada: No se encontraron registros válidos.")
                    task.estado = 'Error'
                    db.session.commit()
                    add_audit_log("tarea terminada", status="error", detail=f"ID: {task.id} - Abortada: Sin registros válidos", user_override=task.job.usuario)
                    continue

                # Ejecutar comando PSX
                try:
                    from psx5k_cmd import psx5k_cmd
                    results = psx5k_cmd(
                        line_task=task.job.tarea, 
                        line_number=ani_list,
                        line_type=task.job.accion_tipo,
                        routing_label=task.job.routing_label,
                        force=task.job.force
                    )
                except Exception as task_err:
                    print(f"❌ Error ejecutando Tarea ID {task.id}: {task_err}")
                    task.estado = 'Error'
                    db.session.commit()
                    add_audit_log("tarea terminada", status="error", detail=f"ID: {task.id} - Fallo Técnico: {str(task_err)[:100]}", user_override=task.job.usuario)
                    # Notificación de error al propietario
                    target = get_notification_target(task.job.usuario)
                    if target:
                        send_notification_by_slug(slug='error', target_email=target,
                                                context={'usuario': task.job.usuario, 'ip': 'PSX_NODE', 'error': str(task_err)[:100]})
                        print(f"📧 Correo de error enviado satisfactoriamente a: {target}")
                    continue
               
                # Resultados Detallados
                detail.ok = results.get("ok", 0)
                detail.fail = results.get("fail", 0)
                detail.force_ok = results.get("force_ok", 0)
                detail.dup = results.get("dup", 0)
                
                # Historial detallado
                for log_entry in results.get('logs', []):
                    try:
                        parts = log_entry.split(' ', 2)
                        status_tag = parts[0].strip('[]')
                        number = parts[1]
                        db.session.add(PSX5KHistory(
                            task_id=task.id, usuario=task.job.usuario,
                            numero=number, routing_label=task.job.routing_label,
                            accion=task.job.tarea, estado=status_tag, fecha=datetime.datetime.now()
                        ))
                    except: pass
                
                # Guardar el flujo completo de comandos
                if results.get("full_flow"):
                    db.session.add(PSX5KCommandLog(
                        task_id=task.id,
                        raw_log=results["full_flow"]
                    ))

                # Finalizar
                task.estado = 'Terminada'
                task.fecha_fin = datetime.datetime.now()
                # task.datos = None  # Se deshabilita la purga por solicitud del usuario
                db.session.commit()
                
                add_audit_log("tarea terminada", status="success", detail=f"ID: {task.id} | OK: {detail.ok} | FAIL: {detail.fail}", user_override=task.job.usuario)
                
                # Notificación de término al propietario
                target = get_notification_target(task.job.usuario)
                if target:
                    send_notification_by_slug(slug='terminado', target_email=target, 
                                            context={'usuario': task.job.usuario, 'hora': task.fecha_fin.strftime('%H:%M:%S')})
                    print(f"📧 Correo de término enviado satisfactoriamente a: {target}")

            time.sleep(SLEEP_BETWEEN)

        except Exception as e:
            print(f"❌ Error en el ciclo del worker: {str(e)}")
            time.sleep(SLEEP_IDLE) # Esperar antes de reintentar si hay error crítico

if __name__ == "__main__":
    main()
