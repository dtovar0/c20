import os
import sys
import time
import datetime
import signal
import threading
from dotenv import load_dotenv


# Configuración de PATH y Raíz
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)

load_dotenv(dotenv_path=os.path.join(PROJECT_ROOT, '.env'))

# Configuración de notificaciones
ADMIN_EMAIL = os.getenv('NOTIFICATION_ADMIN_EMAIL', 'admin@example.com')

def get_notification_target(email):
    """Resuelve el destinatario de la notificación consultando preferencias en DB."""
    if not email: return ADMIN_EMAIL
    
    # Intentar buscar al usuario en la base de datos para ver sus preferencias
    user = User.query.filter_by(email=email).first()
    if user:
        if not user.pref_email_notifications:
            print(f"🔇 Notificaciones por correo desactivadas para el usuario: {email}")
            return None
        
        # Si el email es un correo, lo usamos, si no, intentamos resolver
        if '@' in user.email: return user.email
        
    # Fallback: Si no existe el usuario o no tiene correo en email, usamos el ADMIN_EMAIL
    if '@' in email: return email
    return ADMIN_EMAIL

from app import create_app, db
from app.modules.psx.models import PSX5KTask, PSX5KDetail, PSX5KHistory, PSX5KCommandLog
from app.modules.notifications.services import send_notification_by_slug
from app.modules.auth.models import User
from app.modules.audit.services import add_audit_log

# Estado compartido para el Watchdog (Tarea ID -> Ultima notificación timestamp)
notified_stale_tasks = {}

LOCK_FILE = os.path.join(PROJECT_ROOT, "psx5k_worker.pid") # Movido a la raíz para consistencia

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
    """Detecta y limpia tareas que se quedaron colgadas más de X min (configurable via ENV)"""
    with app.app_context():
        # 1. Configuración de tiempos
        notify_timeout = int(os.getenv('PSX_NOTIFY_TASK_TIMEOUT', 60))
        kill_timeout = int(os.getenv('PSX_KILL_TASK_TIMEOUT', 90))
        
        now = datetime.datetime.now()
        limit_notify = now - datetime.timedelta(minutes=notify_timeout)
        limit_kill = now - datetime.timedelta(minutes=kill_timeout)

        # 2. Buscar tareas en ejecución
        executing_tasks = PSX5KTask.query.filter(PSX5KTask.estado == 'Ejecutando').all()
        
        for task in executing_tasks:
            # Validar que tenga fecha de inicio para evitar errores de comparación
            if not task.fecha_inicio:
                continue

            # Caso A: MATAR TAREA (Kill Timeout excedido)
            if task.fecha_inicio < limit_kill:
                print(f"💀 HARD KILL: Tarea ID {task.id} excedió el límite crítico de {kill_timeout} min. Abortando.")
                
                # Cambiamos estado para liberar el worker
                task.estado = 'Error'
                task.fecha_fin = now
                
                # Notificación Crítica
                admin = User.query.filter_by(role='administrador').first()
                if admin and admin.email:
                    send_notification_by_slug(
                        slug='error', 
                        target_email=admin.email,
                        context={
                            'usuario': 'SYSTEM_WATCHDOG', 
                            'ip': 'LOCAL_WORKER', 
                            'error': f'TAREA_ABORTADA_TIMEOUT_ID_{task.id} (>{kill_timeout}min)'
                        }
                    )
                
                add_audit_log(f"OPERACIÓN ABORTADA [TIMEOUT] (PSX-{task.id})", status="error", detail=f"Inactividad excedida: >{kill_timeout}min | Usuario: {task.job.usuario}", user_override="SYSTEM")
                
                # Limpiar de la lista de notificados
                if task.id in notified_stale_tasks:
                    del notified_stale_tasks[task.id]
                
                db.session.commit()
                continue # Pasar a la siguiente tarea

            # Caso B: AVISO DE DEMORA (Notify Timeout excedido)
            if task.fecha_inicio < limit_notify:
                # Intervalo para repetir la notificación (default 30 min)
                notify_again_interval = int(os.getenv('PSX_NOTIFY_AGAIN_INTERVAL', 30))
                last_notify = notified_stale_tasks.get(task.id)
                
                if last_notify:
                    # Si ya se notificó, verificar si ya pasó el intervalo para volver a avisar
                    if (now - last_notify).total_seconds() < (notify_again_interval * 60):
                        continue

                print(f"🕒 ALERTA DE TIEMPO: Tarea ID {task.id} ha superado los {notify_timeout} min de ejecución.")
                
                # Notificamos al administrador
                admin = User.query.filter_by(role='administrador').first()
                if admin and admin.email:
                    send_notification_by_slug(
                        slug='error', 
                        target_email=admin.email,
                        context={'usuario': 'SYSTEM_WATCHDOG', 'ip': 'LOCAL_WORKER', 'error': f'DEMORA_DETECTADA_ID_{task.id} (>{notify_timeout}min)'}
                    )
                
                add_audit_log(f"ALERTA DE DEMORA (PSX-{task.id})", status="warning", detail=f"Tiempo de ejecución >{notify_timeout} min (Aún en curso) | Proceso: {task.job.tarea}", user_override="SYSTEM")
                
                # Marcamos/Actualizamos el timestamp de última notificación
                notified_stale_tasks[task.id] = now
                db.session.commit()


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
                if admin and admin.email:
                    send_notification_by_slug(
                        slug='info', 
                        target_email=admin.email,
                        context={
                            'usuario': 'SYSTEM_WORKER', 
                            'ip': 'DAEMON_PROCESS', 
                            'mensaje': f'PURGA AUTOMÁTICA COMPLETADA: Se eliminaron {count} cuentas de usuario por inactividad prolongada (>30 días). Nombres: {names}'
                        }
                    )
        except Exception as e:
            print(f"⚠️ [HYGIENE] Error en rutina de limpieza: {e}")

def watchdog_loop(app):
    """Bucle de monitoreo en segundo plano (Watchdog + Hygiene)"""
    print("🛰️  Watchdog Thread iniciado (Monitoreo paralelo activo)")
    
    # Marcadores de tiempo para tareas periódicas
    last_hygiene_check = datetime.datetime.now() - datetime.timedelta(hours=23) # Forzar primer check pronto
    HYGIENE_CHECK_INTERVAL = 86400 # 24 horas
    
    while True:
        try:
            # 1. Monitorear y limpiar tareas estancadas
            handle_stale_tasks(app)
            
            # 2. Monitorear higiene de usuarios cada 24h
            now = datetime.datetime.now()
            if (now - last_hygiene_check).total_seconds() > HYGIENE_CHECK_INTERVAL:
                handle_user_hygiene(app)
                last_hygiene_check = now
            
            # Dormir 5 minutos antes del próximo escaneo global
            time.sleep(300)
        except Exception as e:
            print(f"⚠️ [WATCHDOG-THREAD] Error crítico: {e}")
            time.sleep(60)

def process_task_data(task):

    """Retorna la lista de números desde archivo o datos directos en DB"""
    if not task.datos: return []
    
    # Si detectamos comas, es probable que sean datos directos en DB (formato chunk nuevo)
    if ',' in task.datos:
        return [x.strip() for x in task.datos.split(',') if x.strip()]
    
    # Si no hay comas, comprobamos si es un archivo físico (formato legacy o archivo único)
    file_path = os.path.join(PROJECT_ROOT, 'uploads/psx5k', task.datos)
    
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
    
    # Limpieza inicial síncrona
    handle_stale_tasks(app)
    
    # Iniciar Watchdog en paralelo (HILO INDEPENDIENTE) si está habilitado
    if os.getenv('PSX_WATCHDOG_ENABLED', 'true').lower() == 'true':
        monitor_thread = threading.Thread(target=watchdog_loop, args=(app,), daemon=True)
        monitor_thread.start()
    else:
        print("ℹ️  Watchdog paralelo deshabilitado por configuración (ENV)")


    last_health_check = datetime.datetime.now()
    HEALTH_CHECK_INTERVAL = int(os.getenv('PSX_WATCHDOG_MIN_INTERVAL', 60)) * 60 

    while True:
        try:
            
            with app.app_context():
                # 1. Validar que no haya tareas activas (Ejecutando) en todo el sistema
                # Esto previene colisiones incluso si el lock fallara o hay tareas huérfanas
                is_running = PSX5KTask.query.filter_by(estado='Ejecutando').first()
                if is_running:
                    # Si ya hay una en curso, esperamos a que termine o que el Watchdog la limpie
                    time.sleep(SLEEP_IDLE)
                    continue

                # 2. Buscar una tarea pendiente o programada que ya deba iniciar
                now = datetime.datetime.now()
                task = PSX5KTask.query.filter(
                    (PSX5KTask.estado == 'Pendiente') | 
                    ((PSX5KTask.estado == 'Programada') & (PSX5KTask.fecha_inicio <= now))
                ).order_by(PSX5KTask.id.asc()).first()


                # --- LÓGICA DE MONITOREO INTEGRADA ---
                now = datetime.datetime.now()
                should_check = False
                
                if task:
                    # Siempre validamos conectividad si hay una tarea a procesar
                    should_check = True
                elif os.getenv('PSX_WATCHDOG_IDLE_ENABLED', 'false').lower() == 'true':
                    # Solo validamos periódicamente si el Watchdog está explícitamente activado en .env
                    if (now - last_health_check).total_seconds() > HEALTH_CHECK_INTERVAL:
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
                        if admin and admin.email:
                            send_notification_by_slug(
                                slug='error', 
                                target_email=admin.email,
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
                
                # Procesar datos
                ani_list = process_task_data(task)
                
                add_audit_log(f"EJECUCIÓN INICIADA (PSX-{task.id})", status="info", detail=f"Proceso: {task.job.tarea} | Usuario: {task.job.usuario} | Registros: {len(ani_list)}", user_override=task.job.usuario)
                
                if os.getenv('DEBUG_PSX', 'false').lower() == 'true':
                    print(f"🔍 DEBUG: [Task:{task.job.tarea}] [ANIs:{len(ani_list)}] [Type:{task.job.accion_tipo}] [Route:{task.job.routing_label}] [Force:{task.job.run_force}]")

                detail = db.session.get(PSX5KDetail, task.id) or PSX5KDetail(id=task.id)
                detail.total = len(ani_list)
                db.session.add(detail)
                if detail.total == 0:
                    print(f"⚠️ Tarea {task.id} abortada: No se encontraron registros válidos.")
                    task.estado = 'Error'
                    db.session.commit()
                    add_audit_log(f"OPERACIÓN FINALIZADA [VACÍO] (PSX-{task.id})", status="error", detail=f"No se detectaron registros válidos en el origen de datos.", user_override=task.job.usuario)
                    # Limpiar de la lista de notificados si existía
                    if task.id in notified_stale_tasks:
                        del notified_stale_tasks[task.id]
                    continue


                # Ejecutar comando PSX
                try:
                    from psx5k_cmd import psx5k_cmd
                    results = psx5k_cmd(
                        line_task=task.job.tarea, 
                        line_number=ani_list,
                        line_type=task.job.accion_tipo if task.job.tarea == 'add' else None,
                        routing_label=task.job.routing_label,
                        force=task.job.run_force
                    )
                    if os.getenv('DEBUG_PSX', 'false').lower() == 'true':
                        # Omitimos logs y full_flow para no saturar la consola
                        debug_res = {k: v for k, v in results.items() if k not in ['logs', 'full_flow']}
                        print(f"✅ DEBUG RESULT: {debug_res}")
                except Exception as task_err:
                    print(f"❌ Error ejecutando Tarea ID {task.id}: {task_err}")
                    task.estado = 'Error'
                    db.session.commit()
                    add_audit_log(f"OPERACIÓN FINALIZADA [ERROR] (PSX-{task.id})", status="error", detail=f"Fallo Técnico: {str(task_err)[:100]}", user_override=task.job.usuario)
                    # Notificación de error al propietario
                    target = get_notification_target(task.job.usuario)
                    if target:
                        send_notification_by_slug(slug='error', target_email=target,
                                                context={'usuario': task.job.usuario, 'ip': 'PSX_NODE', 'error': str(task_err)[:100]})
                        print(f"📧 Correo de error enviado satisfactoriamente a: {target}")

                    # Limpiar de la lista de notificados si existía
                    if task.id in notified_stale_tasks:
                        del notified_stale_tasks[task.id]

                    continue

               
                # Resultados Detallados
                detail.ok = results.get("ok", 0)
                detail.fail = results.get("fail", 0)
                detail.force_ok = results.get("force_ok", 0)
                detail.dup = results.get("dup", 0)
                detail.del_ = results.get("del", 0)
                detail.delcheck = results.get("delcheck", 0)
                
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
                task.estado = 'Completada'
                task.fecha_fin = datetime.datetime.now()
                # task.datos = None  # Se deshabilita la purga por solicitud del usuario
                db.session.commit()
                
                # Limpiar de la lista de notificados si existía
                if task.id in notified_stale_tasks:
                    del notified_stale_tasks[task.id]

                
                add_audit_log(f"OPERACIÓN FINALIZADA [ÉXITO] (PSX-{task.id})", status="success", detail=f"OK: {detail.ok} | FAIL: {detail.fail} | DUP: {detail.dup} | FORCE: {detail.force_ok} | DEL: {detail.del_} | DELCHECK: {detail.delcheck}", user_override=task.job.usuario)
                
                # Notificación de término al propietario
                target = get_notification_target(task.job.usuario)
                if target:
                    base_url = os.getenv('BASE_URL', 'http://10.224.2.146')
                    task_url = f"{base_url}/api/psx/detail/{task.id}"
                    send_notification_by_slug(slug='terminado', target_email=target, 
                                            context={
                                                'usuario': task.job.usuario, 
                                                'hora': task.fecha_fin.strftime('%H:%M:%S'),
                                                'url': task_url
                                            })
                    print(f"📧 Correo de término enviado satisfactoriamente a: {target} | URL: {task_url}")

            time.sleep(SLEEP_BETWEEN)

        except Exception as e:
            print(f"❌ Error en el ciclo del worker: {str(e)}")
            time.sleep(SLEEP_IDLE) # Esperar antes de reintentar si hay error crítico

if __name__ == "__main__":
    main()
