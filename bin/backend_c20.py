"""
Worker C20: daemon que procesa la cola de tareas contra el nodo C20.

Sigue el mismo ciclo de vida que el worker de PSX5K (Pendiente/Programada ->
Ejecutando -> Completado), pero la ejecución es por lotes: prepara los archivos
de entrada, lanza los scripts expect en orden jerárquico y consolida los logs.
"""
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
sys.path.insert(0, os.path.dirname(__file__))

load_dotenv(dotenv_path=os.path.join(PROJECT_ROOT, '.env'))

ADMIN_EMAIL = os.getenv('NOTIFICATION_ADMIN_EMAIL', 'admin@example.com')

from app import create_app, db
from app.modules.c20.models import (
    C20Task, C20Detail, C20History, C20CommandLog,
    C20Snpaname, C20Tofcname, C20Ofc2code, C20Dnscrn,
    C20_TABLES,
)
from app.modules.notifications.services import send_notification_by_slug
from app.modules.auth.models import User
from app.modules.audit.services import add_audit_log

LOCK_FILE = os.path.join(PROJECT_ROOT, "c20_worker.pid")

SLEEP_IDLE = 10   # Segundos a esperar si no hay tareas
SLEEP_BETWEEN = 2 # Segundos entre tareas para no saturar DB

# Estado compartido para el Watchdog (Tarea ID -> timestamp de última notificación)
notified_stale_tasks = {}


def get_notification_target(email):
    """Resuelve el destinatario de la notificación consultando preferencias en DB."""
    if not email:
        return ADMIN_EMAIL

    user = User.query.filter_by(email=email).first()
    if user:
        if not user.pref_email_notifications:
            print(f"🔇 Notificaciones por correo desactivadas para el usuario: {email}")
            return None
        if '@' in user.email:
            return user.email

    if '@' in email:
        return email
    return ADMIN_EMAIL


def cleanup_lock():
    """Elimina el archivo con el PID al salir"""
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)
        print("🔓 Worker C20 detenido. Lock file eliminado.")


def check_single_instance():
    """Verifica que no haya otro worker C20 corriendo"""
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, 'r') as f:
                pid = int(f.read().strip())
            os.kill(pid, 0)
            print(f"⚠️ El Worker C20 ya está en ejecución (PID: {pid}). Abortando.")
            sys.exit(1)
        except (OSError, ValueError):
            print("🕒 Detectado lock huérfano. Limpiando...")
            os.remove(LOCK_FILE)


def process_task_data(task):
    """Retorna la lista de números desde archivo o datos directos en DB"""
    if not task.datos:
        return []

    if ',' in task.datos:
        return [x.strip() for x in task.datos.split(',') if x.strip()]

    file_path = os.path.join(PROJECT_ROOT, 'uploads/c20', task.datos)
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                return [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"⚠️ Error leyendo archivo físico {task.datos}: {e}")
            return []

    return [task.datos.strip()]


def sync_mirror(accion, numeros, ladas, series, usuario):
    """
    Mantiene el espejo local alineado con lo que se envió al nodo.

    En 'add' se insertan las filas que no existan; en 'del' se retiran los números
    (las ladas y series permanecen, igual que en el nodo). El espejo es el que
    permite saber qué ya está dado de alta sin interrogar al C20.
    """
    now = datetime.datetime.now()

    if accion == 'add':
        for lada in ladas:
            if not db.session.get(C20Snpaname, lada):
                db.session.add(C20Snpaname(lada=lada, fecha=now, usuario=usuario))

        for item in series:
            partes = item.split()
            if len(partes) != 2:
                continue
            lada, serie = partes
            if not db.session.get(C20Tofcname, (lada, serie)):
                db.session.add(C20Tofcname(lada=lada, serie=serie, fecha=now, usuario=usuario))

        for numero in numeros:
            if not db.session.get(C20Ofc2code, numero):
                db.session.add(C20Ofc2code(numero=numero, fecha=now, usuario=usuario))
            if not db.session.get(C20Dnscrn, numero):
                db.session.add(C20Dnscrn(numero=numero, fecha=now, usuario=usuario))
    else:
        for numero in numeros:
            fila_o = db.session.get(C20Ofc2code, numero)
            if fila_o:
                db.session.delete(fila_o)
            fila_d = db.session.get(C20Dnscrn, numero)
            if fila_d:
                db.session.delete(fila_d)


def handle_stale_tasks(app):
    """Detecta y limpia tareas C20 colgadas más de X min (configurable via ENV)"""
    with app.app_context():
        notify_timeout = int(os.getenv('C20_NOTIFY_TASK_TIMEOUT', 60))
        kill_timeout = int(os.getenv('C20_KILL_TASK_TIMEOUT', 90))

        now = datetime.datetime.now()
        limit_notify = now - datetime.timedelta(minutes=notify_timeout)
        limit_kill = now - datetime.timedelta(minutes=kill_timeout)

        for task in C20Task.query.filter(C20Task.estado == 'Ejecutando').all():
            if not task.fecha_inicio:
                continue

            # Caso A: MATAR TAREA (Kill Timeout excedido)
            if task.fecha_inicio < limit_kill:
                print(f"💀 HARD KILL: Tarea C20 {task.id} excedió {kill_timeout} min. Abortando.")
                task.estado = 'Error'
                task.fecha_fin = now

                admin = User.query.filter_by(role='administrador').first()
                if admin and admin.email:
                    send_notification_by_slug(
                        slug='error', target_email=admin.email,
                        context={
                            'usuario': 'SYSTEM_WATCHDOG', 'ip': 'LOCAL_WORKER',
                            'error': f'TAREA_C20_ABORTADA_TIMEOUT_ID_{task.id} (>{kill_timeout}min)'
                        }
                    )

                add_audit_log(
                    f"OPERACIÓN ABORTADA [TIMEOUT] (C20-{task.id})", status="error",
                    detail=f"Inactividad excedida: >{kill_timeout}min | Usuario: {task.job.usuario}",
                    user_override="SYSTEM"
                )
                notified_stale_tasks.pop(task.id, None)
                db.session.commit()
                continue

            # Caso B: AVISO DE DEMORA (Notify Timeout excedido)
            if task.fecha_inicio < limit_notify:
                notify_again_interval = int(os.getenv('C20_NOTIFY_AGAIN_INTERVAL', 30))
                last_notify = notified_stale_tasks.get(task.id)
                if last_notify and (now - last_notify).total_seconds() < (notify_again_interval * 60):
                    continue

                print(f"🕒 ALERTA DE TIEMPO: Tarea C20 {task.id} superó {notify_timeout} min.")
                admin = User.query.filter_by(role='administrador').first()
                if admin and admin.email:
                    try:
                        send_notification_by_slug(
                            slug='error', target_email=admin.email,
                            context={
                                'usuario': 'SYSTEM_WATCHDOG', 'ip': 'LOCAL_WORKER',
                                'error': f'DEMORA_DETECTADA_C20_ID_{task.id} (>{notify_timeout}min)'
                            }
                        )
                    except Exception as e:
                        print(f"❌ [WATCHDOG] Excepción al enviar correo: {e}")

                add_audit_log(
                    f"ALERTA DE DEMORA (C20-{task.id})", status="warning",
                    detail=f"Tiempo de ejecución >{notify_timeout} min (Aún en curso) | Proceso: {task.job.tarea}",
                    user_override="SYSTEM"
                )
                notified_stale_tasks[task.id] = now
                db.session.commit()


def watchdog_loop(app):
    """Bucle de monitoreo en segundo plano"""
    print("🛰️  Watchdog C20 iniciado (Monitoreo paralelo activo)")
    while True:
        try:
            handle_stale_tasks(app)
            time.sleep(int(os.getenv('C20_WATCHDOG_LOOP_INTERVAL', 60)))
        except Exception as e:
            print(f"⚠️ [WATCHDOG-THREAD] Error crítico: {e}")
            time.sleep(60)


def main():
    """Motor de procesamiento persistente (Daemon)"""
    check_single_instance()

    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))

    print(f"🚀 Nexus Worker C20 iniciado (PID: {os.getpid()})")

    app = create_app()

    def signal_handler(sig, frame):
        cleanup_lock()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    handle_stale_tasks(app)

    if os.getenv('C20_WATCHDOG_ENABLED', 'true').lower() == 'true':
        threading.Thread(target=watchdog_loop, args=(app,), daemon=True).start()
    else:
        print("ℹ️  Watchdog paralelo deshabilitado por configuración (ENV)")

    while True:
        try:
            with app.app_context():
                # 1. Un solo lote a la vez. Respaldo del lock file: cubre el caso
                #    de que este fallara o de que una caída dejara tareas colgadas.
                #    Dos tareas en paralelo abrirían dos sesiones contra el mismo nodo.
                if C20Task.query.filter_by(estado='Ejecutando').first():
                    time.sleep(SLEEP_IDLE)
                    continue

                # 2. Buscar una tarea pendiente o programada que ya deba iniciar
                now = datetime.datetime.now()
                task = C20Task.query.filter(
                    (C20Task.estado == 'Pendiente') |
                    ((C20Task.estado == 'Programada') & (C20Task.fecha_inicio <= now))
                ).order_by(C20Task.id.asc()).first()

                if not task:
                    time.sleep(SLEEP_IDLE)
                    continue

                # 3. Validar conectividad antes de comprometer la tarea
                from c20_cmd import test_connectivity, c20_cmd
                ok, msg = test_connectivity()
                if not ok:
                    print(f"🚨 Fallo de conectividad con el nodo C20: {msg}")
                    add_audit_log("error conectividad", status="error",
                                  detail=f"C20: {msg}", user_override="SYSTEM_WORKER")

                    from app.modules.notifications.services import add_in_app_notification
                    add_in_app_notification(
                        type='error', title='Fallo de Conexión C20',
                        message=f'No se pudo establecer conexión con el nodo C20: {msg}'
                    )

                    admin = User.query.filter_by(role='administrador').first()
                    if admin and admin.email:
                        send_notification_by_slug(
                            slug='error', target_email=admin.email,
                            context={'usuario': 'SYSTEM_WORKER',
                                     'ip': os.getenv('C20_HOST', 'C20_NODE'),
                                     'error': f'CONECTIVIDAD FALLIDA: {msg}'}
                        )

                    print("⏳ Pospone tarea por falta de conectividad.")
                    time.sleep(60)
                    continue

                print(f"🎯 Procesando Tarea C20 ID {task.id}: {task.job.tarea}")

                task.estado = 'Ejecutando'
                task.fecha_inicio = datetime.datetime.now()
                db.session.commit()

                target = get_notification_target(task.job.usuario)
                if target:
                    send_notification_by_slug(
                        slug='inicio', target_email=target,
                        context={'usuario': task.job.usuario,
                                 'hora': task.fecha_inicio.strftime('%H:%M:%S')}
                    )

                numeros = process_task_data(task)

                add_audit_log(
                    f"EJECUCIÓN INICIADA (C20-{task.id})", status="info",
                    detail=f"Proceso: {task.job.tarea} | Usuario: {task.job.usuario} | Registros: {len(numeros)}",
                    user_override=task.job.usuario
                )

                detail = db.session.get(C20Detail, task.id) or C20Detail(id=task.id)
                db.session.add(detail)

                if not numeros:
                    print(f"⚠️ Tarea C20 {task.id} abortada: sin registros válidos.")
                    task.estado = 'Error'
                    db.session.commit()
                    add_audit_log(
                        f"OPERACIÓN FINALIZADA [VACÍO] (C20-{task.id})", status="error",
                        detail="No se detectaron registros válidos en el origen de datos.",
                        user_override=task.job.usuario
                    )
                    notified_stale_tasks.pop(task.id, None)
                    continue

                # 4. Ejecutar el lote contra el nodo
                try:
                    results = c20_cmd(
                        line_task=task.job.tarea,
                        line_number=numeros,
                        zona=task.job.zona
                    )
                except Exception as task_err:
                    print(f"❌ Error ejecutando Tarea C20 {task.id}: {task_err}")
                    task.estado = 'Error'
                    task.fecha_fin = datetime.datetime.now()
                    db.session.commit()
                    add_audit_log(
                        f"OPERACIÓN FINALIZADA [ERROR] (C20-{task.id})", status="error",
                        detail=f"Fallo Técnico: {str(task_err)[:100]}",
                        user_override=task.job.usuario
                    )
                    target = get_notification_target(task.job.usuario)
                    if target:
                        send_notification_by_slug(
                            slug='error', target_email=target,
                            context={'usuario': task.job.usuario, 'ip': 'C20_NODE',
                                     'error': str(task_err)[:100]}
                        )
                    notified_stale_tasks.pop(task.id, None)
                    continue

                # 5. Consolidar contadores por tabla. Los ERROR (nodo sin respuesta)
                #    se suman a fail para que los totales cuadren con el lote.
                for tabla in C20_TABLES:
                    datos = results.get(tabla, {})
                    setattr(detail, f"{tabla}_total", datos.get("total", 0))
                    setattr(detail, f"{tabla}_ok", datos.get("ok", 0))
                    setattr(detail, f"{tabla}_fail", datos.get("fail", 0) + datos.get("error", 0))

                accion = results.get("accion", 'add')

                # 6. Historial por número, tomando OFC2CODE como referencia:
                #    es la tabla por la que pasa cada número exactamente una vez.
                estados = {'ok': 'OK', 'fail': 'FAIL', 'error': 'ERROR'}
                for valor, verdict in results.get('ofc2code', {}).get('entries', []):
                    db.session.add(C20History(
                        task_id=task.id, usuario=task.job.usuario,
                        numero=valor, zona=task.job.zona,
                        accion=task.job.tarea,
                        estado=estados.get(verdict, 'FAIL'),
                        fecha=datetime.datetime.now()
                    ))

                # 7. Sincronizar el espejo local con lo que sí se aplicó
                aplicados = [v for v, verdict in results.get('ofc2code', {}).get('entries', [])
                             if verdict == 'ok']
                if aplicados:
                    sync_mirror(accion, aplicados, results.get('ladas', []),
                                results.get('series', []), task.job.usuario)

                # 8. Guardar el flujo crudo de la sesión (una sola, para todas las tablas)
                if results.get("full_flow"):
                    db.session.add(C20CommandLog(task_id=task.id, raw_log=results["full_flow"]))

                # 9. Cerrar la tarea. Un fallo de sesión o un número sin respuesta
                #    la marcan con errores: los contadores solos no lo revelarían.
                task.fecha_fin = datetime.datetime.now()
                detail.duracion = int((task.fecha_fin - task.fecha_inicio).total_seconds())

                errores = list(results.get("errors", []))
                sin_respuesta = sum(results.get(t, {}).get("error", 0) for t in C20_TABLES)
                if sin_respuesta:
                    errores.append(f"{sin_respuesta} registro(s) sin respuesta del nodo")
                task.estado = 'Terminado con Errores' if errores else 'Completado'
                db.session.commit()

                notified_stale_tasks.pop(task.id, None)

                resumen = " | ".join(
                    f"{t.upper()}: {results.get(t, {}).get('ok', 0)}/{results.get(t, {}).get('total', 0)}"
                    for t in C20_TABLES if results.get(t, {}).get('total', 0)
                )
                add_audit_log(
                    f"OPERACIÓN FINALIZADA [{'ERRORES' if errores else 'ÉXITO'}] (C20-{task.id})",
                    status="error" if errores else "success",
                    detail=f"{resumen}{' | Fallos: ' + '; '.join(errores) if errores else ''}",
                    user_override=task.job.usuario
                )

                target = get_notification_target(task.job.usuario)
                if target:
                    base_url = os.getenv('BASE_URL', 'http://10.224.2.146')
                    send_notification_by_slug(
                        slug='terminado', target_email=target,
                        context={'usuario': task.job.usuario,
                                 'hora': task.fecha_fin.strftime('%H:%M:%S'),
                                 'url': f"{base_url}/api/c20/detail/{task.id}"}
                    )

            time.sleep(SLEEP_BETWEEN)

        except Exception as e:
            print(f"❌ Error en el ciclo del worker C20: {str(e)}")
            time.sleep(SLEEP_IDLE)


if __name__ == "__main__":
    main()
