"""
Worker del switch: daemon que procesa las colas de C20 y Teams.

Un solo proceso atiende ambas secciones porque el nodo admite una única conexión
activa: dos workers separados —aunque compartieran archivo de lock— podrían
superar la comprobación a la vez, y cada uno solo vería su propia cola en BD. Con
un único proceso decidiendo qué tarea toca, el solape es imposible por
construcción.

En cada ciclo toma la tarea pendiente más antigua de cualquier sección, la
ejecuta contra el switch y consolida sus resultados en las tablas de esa sección.
El historial y el espejo son compartidos: reflejan el estado del nodo, que es uno
solo.
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
from app.modules.c20.models import C20Task, C20Detail, C20CommandLog
from app.modules.teams.models import TeamsTask, TeamsDetail, TeamsCommandLog
from app.modules.switch.models import (
    SwitchHistory, SwitchSnpaname, SwitchTofcname, SwitchOfc2code, SwitchDnscrn,
    SWITCH_TABLES,
)
from app.modules.notifications.services import send_notification_by_slug
from app.modules.auth.models import User
from app.modules.audit.services import add_audit_log

# Lock COMPARTIDO: el nodo admite una sola conexión activa.
LOCK_FILE = os.path.join(PROJECT_ROOT, "switch_worker.pid")

SLEEP_IDLE = 10   # Segundos a esperar si no hay tareas
SLEEP_BETWEEN = 2 # Segundos entre tareas para no saturar DB

# Estado compartido para el Watchdog (clave (seccion, id) -> última notificación)
notified_stale_tasks = {}

# Registro de secciones: cada una aporta sus propios modelos y el campo cuyo
# valor viaja al nodo como parámetro del comando (zona en C20, prefijo en Teams).
SECCIONES = {
    'c20': {
        'label': 'C20',
        'task': C20Task,
        'detail': C20Detail,
        'command_log': C20CommandLog,
        'param_attr': 'zona',
        'upload_dir': 'uploads/c20',
        'detail_url': '/api/c20/detail',
    },
    'teams': {
        'label': 'Teams',
        'task': TeamsTask,
        'detail': TeamsDetail,
        'command_log': TeamsCommandLog,
        'param_attr': 'prefijo',
        'upload_dir': 'uploads/teams',
        'detail_url': '/api/teams/detail',
    },
}


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
        print("🔓 Worker del switch detenido. Lock file eliminado.")


def check_single_instance():
    """Verifica que no haya otro worker del switch corriendo"""
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, 'r') as f:
                pid = int(f.read().strip())
            os.kill(pid, 0)
            print(f"⚠️ Ya hay un worker del switch en ejecución (PID: {pid}). Abortando.")
            sys.exit(1)
        except (OSError, ValueError):
            print("🕒 Detectado lock huérfano. Limpiando...")
            os.remove(LOCK_FILE)


def process_task_data(task, upload_dir):
    """Retorna la lista de números desde archivo o datos directos en DB"""
    if not task.datos:
        return []

    if ',' in task.datos:
        return [x.strip() for x in task.datos.split(',') if x.strip()]

    file_path = os.path.join(PROJECT_ROOT, upload_dir, task.datos)
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                return [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"⚠️ Error leyendo archivo físico {task.datos}: {e}")
            return []

    return [task.datos.strip()]


def sync_mirror(accion, numeros, ladas, series, usuario, seccion):
    """
    Mantiene el espejo alineado con lo que se aplicó en el nodo.

    En 'add' se insertan las filas que no existan; en 'del' se retiran los
    números (las ladas y series permanecen, igual que en el nodo). El espejo es
    compartido: un número dado de alta desde C20 ya existe para Teams.
    """
    now = datetime.datetime.now()

    if accion == 'add':
        for lada in ladas:
            if not db.session.get(SwitchSnpaname, lada):
                db.session.add(SwitchSnpaname(lada=lada, fecha=now,
                                              usuario=usuario, seccion=seccion))

        for item in series:
            partes = item.split()
            if len(partes) != 2:
                continue
            lada, serie = partes
            if not db.session.get(SwitchTofcname, (lada, serie)):
                db.session.add(SwitchTofcname(lada=lada, serie=serie, fecha=now,
                                              usuario=usuario, seccion=seccion))

        for numero in numeros:
            if not db.session.get(SwitchOfc2code, numero):
                db.session.add(SwitchOfc2code(numero=numero, fecha=now,
                                              usuario=usuario, seccion=seccion))
            if not db.session.get(SwitchDnscrn, numero):
                db.session.add(SwitchDnscrn(numero=numero, fecha=now,
                                            usuario=usuario, seccion=seccion))
    else:
        for numero in numeros:
            fila_o = db.session.get(SwitchOfc2code, numero)
            if fila_o:
                db.session.delete(fila_o)
            fila_d = db.session.get(SwitchDnscrn, numero)
            if fila_d:
                db.session.delete(fila_d)


def handle_stale_tasks(app):
    """Detecta y limpia tareas colgadas más de X min, en todas las secciones"""
    with app.app_context():
        notify_timeout = int(os.getenv('SWITCH_NOTIFY_TASK_TIMEOUT',
                                       os.getenv('C20_NOTIFY_TASK_TIMEOUT', 60)))
        kill_timeout = int(os.getenv('SWITCH_KILL_TASK_TIMEOUT',
                                     os.getenv('C20_KILL_TASK_TIMEOUT', 90)))

        now = datetime.datetime.now()
        limit_notify = now - datetime.timedelta(minutes=notify_timeout)
        limit_kill = now - datetime.timedelta(minutes=kill_timeout)

        for seccion, cfg in SECCIONES.items():
            label = cfg['label']
            for task in cfg['task'].query.filter(cfg['task'].estado == 'Ejecutando').all():
                if not task.fecha_inicio:
                    continue
                clave = (seccion, task.id)

                # Caso A: MATAR TAREA (Kill Timeout excedido)
                if task.fecha_inicio < limit_kill:
                    print(f"💀 HARD KILL: Tarea {label} {task.id} excedió {kill_timeout} min.")
                    task.estado = 'Error'
                    task.fecha_fin = now

                    admin = User.query.filter_by(role='administrador').first()
                    if admin and admin.email:
                        send_notification_by_slug(
                            slug='error', target_email=admin.email,
                            context={
                                'usuario': 'SYSTEM_WATCHDOG', 'ip': 'LOCAL_WORKER',
                                'error': f'TAREA_{label.upper()}_ABORTADA_TIMEOUT_ID_{task.id} (>{kill_timeout}min)'
                            }
                        )

                    add_audit_log(
                        f"OPERACIÓN ABORTADA [TIMEOUT] ({label.upper()}-{task.id})", status="error",
                        detail=f"Inactividad excedida: >{kill_timeout}min | Usuario: {task.job.usuario}",
                        user_override="SYSTEM"
                    )
                    notified_stale_tasks.pop(clave, None)
                    db.session.commit()
                    continue

                # Caso B: AVISO DE DEMORA (Notify Timeout excedido)
                if task.fecha_inicio < limit_notify:
                    notify_again = int(os.getenv('SWITCH_NOTIFY_AGAIN_INTERVAL',
                                                 os.getenv('C20_NOTIFY_AGAIN_INTERVAL', 30)))
                    last = notified_stale_tasks.get(clave)
                    if last and (now - last).total_seconds() < (notify_again * 60):
                        continue

                    print(f"🕒 ALERTA DE TIEMPO: Tarea {label} {task.id} superó {notify_timeout} min.")
                    admin = User.query.filter_by(role='administrador').first()
                    if admin and admin.email:
                        try:
                            send_notification_by_slug(
                                slug='error', target_email=admin.email,
                                context={
                                    'usuario': 'SYSTEM_WATCHDOG', 'ip': 'LOCAL_WORKER',
                                    'error': f'DEMORA_DETECTADA_{label.upper()}_ID_{task.id} (>{notify_timeout}min)'
                                }
                            )
                        except Exception as e:
                            print(f"❌ [WATCHDOG] Excepción al enviar correo: {e}")

                    add_audit_log(
                        f"ALERTA DE DEMORA ({label.upper()}-{task.id})", status="warning",
                        detail=f"Tiempo de ejecución >{notify_timeout} min (Aún en curso) | Proceso: {task.job.tarea}",
                        user_override="SYSTEM"
                    )
                    notified_stale_tasks[clave] = now
                    db.session.commit()


def watchdog_loop(app):
    """Bucle de monitoreo en segundo plano"""
    print("🛰️  Watchdog del switch iniciado (Monitoreo paralelo activo)")
    while True:
        try:
            handle_stale_tasks(app)
            time.sleep(int(os.getenv('SWITCH_WATCHDOG_LOOP_INTERVAL',
                                     os.getenv('C20_WATCHDOG_LOOP_INTERVAL', 60))))
        except Exception as e:
            print(f"⚠️ [WATCHDOG-THREAD] Error crítico: {e}")
            time.sleep(60)


def hay_tarea_activa():
    """
    True si alguna sección tiene una tarea en ejecución.

    Respaldo del lock: cubre el caso de que este fallara o de que una caída
    dejara tareas colgadas. Dos tareas en paralelo abrirían dos sesiones contra
    el mismo nodo, que solo admite una.
    """
    return any(cfg['task'].query.filter_by(estado='Ejecutando').first()
               for cfg in SECCIONES.values())


def siguiente_tarea():
    """
    Devuelve (seccion, cfg, task) de la tarea pendiente más antigua entre todas
    las secciones, o (None, None, None) si no hay ninguna lista.

    Se ordena por fecha de creación del job para que ninguna sección monopolice
    la cola: la que lleve más tiempo esperando va primero.
    """
    now = datetime.datetime.now()
    candidatas = []

    for seccion, cfg in SECCIONES.items():
        Task = cfg['task']
        task = Task.query.filter(
            (Task.estado == 'Pendiente') |
            ((Task.estado == 'Programada') & (Task.fecha_inicio <= now))
        ).order_by(Task.id.asc()).first()
        if task:
            candidatas.append((task.job.created_at, seccion, cfg, task))

    if not candidatas:
        return None, None, None

    candidatas.sort(key=lambda x: x[0])
    _, seccion, cfg, task = candidatas[0]
    return seccion, cfg, task


def ejecutar_tarea(seccion, cfg, task):
    """Procesa una tarea completa contra el nodo y persiste sus resultados."""
    from switch_cmd import switch_cmd

    label = cfg['label']
    parametro = getattr(task.job, cfg['param_attr'], None)

    print(f"🎯 Procesando Tarea {label} ID {task.id}: {task.job.tarea}")

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

    numeros = process_task_data(task, cfg['upload_dir'])

    add_audit_log(
        f"EJECUCIÓN INICIADA ({label.upper()}-{task.id})", status="info",
        detail=f"Proceso: {task.job.tarea} | Usuario: {task.job.usuario} | Registros: {len(numeros)}",
        user_override=task.job.usuario
    )

    detail = db.session.get(cfg['detail'], task.id) or cfg['detail'](id=task.id)
    db.session.add(detail)

    if not numeros:
        print(f"⚠️ Tarea {label} {task.id} abortada: sin registros válidos.")
        task.estado = 'Error'
        db.session.commit()
        add_audit_log(
            f"OPERACIÓN FINALIZADA [VACÍO] ({label.upper()}-{task.id})", status="error",
            detail="No se detectaron registros válidos en el origen de datos.",
            user_override=task.job.usuario
        )
        notified_stale_tasks.pop((seccion, task.id), None)
        return

    # Ejecutar el lote contra el nodo
    try:
        results = switch_cmd(
            line_task=task.job.tarea,
            line_number=numeros,
            parametro=parametro,
            seccion=seccion
        )
    except Exception as task_err:
        print(f"❌ Error ejecutando Tarea {label} {task.id}: {task_err}")
        task.estado = 'Error'
        task.fecha_fin = datetime.datetime.now()
        db.session.commit()
        add_audit_log(
            f"OPERACIÓN FINALIZADA [ERROR] ({label.upper()}-{task.id})", status="error",
            detail=f"Fallo Técnico: {str(task_err)[:100]}",
            user_override=task.job.usuario
        )
        target = get_notification_target(task.job.usuario)
        if target:
            send_notification_by_slug(
                slug='error', target_email=target,
                context={'usuario': task.job.usuario, 'ip': 'SWITCH_NODE',
                         'error': str(task_err)[:100]}
            )
        notified_stale_tasks.pop((seccion, task.id), None)
        return

    # Consolidar contadores por tabla. Los ERROR (nodo sin respuesta) se suman a
    # fail para que los totales cuadren con el lote.
    for tabla in SWITCH_TABLES:
        datos = results.get(tabla, {})
        setattr(detail, f"{tabla}_total", datos.get("total", 0))
        setattr(detail, f"{tabla}_ok", datos.get("ok", 0))
        setattr(detail, f"{tabla}_fail", datos.get("fail", 0) + datos.get("error", 0))

    accion = results.get("accion", 'add')

    # Historial por número, tomando OFC2CODE como referencia: es la tabla por la
    # que pasa cada número exactamente una vez.
    estados = {'ok': 'OK', 'fail': 'FAIL', 'error': 'ERROR'}
    for valor, verdict in results.get('ofc2code', {}).get('entries', []):
        db.session.add(SwitchHistory(
            seccion=seccion, task_id=task.id, usuario=task.job.usuario,
            numero=valor, parametro=parametro,
            accion=task.job.tarea,
            estado=estados.get(verdict, 'FAIL'),
            fecha=datetime.datetime.now()
        ))

    # Sincronizar el espejo con lo que sí se aplicó
    aplicados = [v for v, verdict in results.get('ofc2code', {}).get('entries', [])
                 if verdict == 'ok']
    if aplicados:
        sync_mirror(accion, aplicados, results.get('ladas', []),
                    results.get('series', []), task.job.usuario, seccion)

    # Guardar el flujo crudo de la sesión (una sola, para todas las tablas)
    if results.get("full_flow"):
        db.session.add(cfg['command_log'](task_id=task.id, raw_log=results["full_flow"]))

    # Cerrar la tarea. Un fallo de sesión o un número sin respuesta la marcan con
    # errores: los contadores por sí solos no lo revelarían.
    task.fecha_fin = datetime.datetime.now()
    detail.duracion = int((task.fecha_fin - task.fecha_inicio).total_seconds())

    errores = list(results.get("errors", []))
    sin_respuesta = sum(results.get(t, {}).get("error", 0) for t in SWITCH_TABLES)
    if sin_respuesta:
        errores.append(f"{sin_respuesta} registro(s) sin respuesta del nodo")
    task.estado = 'Terminado con Errores' if errores else 'Completado'
    db.session.commit()

    notified_stale_tasks.pop((seccion, task.id), None)

    resumen = " | ".join(
        f"{t.upper()}: {results.get(t, {}).get('ok', 0)}/{results.get(t, {}).get('total', 0)}"
        for t in SWITCH_TABLES if results.get(t, {}).get('total', 0)
    )
    add_audit_log(
        f"OPERACIÓN FINALIZADA [{'ERRORES' if errores else 'ÉXITO'}] ({label.upper()}-{task.id})",
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
                     'url': f"{base_url}{cfg['detail_url']}/{task.id}"}
        )


def main():
    """Motor de procesamiento persistente (Daemon)"""
    check_single_instance()

    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))

    print(f"🚀 Nexus Worker del switch iniciado (PID: {os.getpid()}) "
          f"| Secciones: {', '.join(c['label'] for c in SECCIONES.values())}")

    app = create_app()

    def signal_handler(sig, frame):
        cleanup_lock()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    handle_stale_tasks(app)

    if os.getenv('SWITCH_WATCHDOG_ENABLED',
                 os.getenv('C20_WATCHDOG_ENABLED', 'true')).lower() == 'true':
        threading.Thread(target=watchdog_loop, args=(app,), daemon=True).start()
    else:
        print("ℹ️  Watchdog paralelo deshabilitado por configuración (ENV)")

    while True:
        try:
            with app.app_context():
                # 1. Una sola tarea a la vez en todo el switch
                if hay_tarea_activa():
                    time.sleep(SLEEP_IDLE)
                    continue

                # 2. Siguiente tarea pendiente, de la sección que sea
                seccion, cfg, task = siguiente_tarea()
                if not task:
                    time.sleep(SLEEP_IDLE)
                    continue

                # 3. Validar conectividad antes de comprometer la tarea
                from switch_cmd import test_connectivity
                ok, msg = test_connectivity()
                if not ok:
                    print(f"🚨 Fallo de conectividad con el nodo: {msg}")
                    add_audit_log("error conectividad", status="error",
                                  detail=f"SWITCH: {msg}", user_override="SYSTEM_WORKER")

                    from app.modules.notifications.services import add_in_app_notification
                    add_in_app_notification(
                        type='error', title='Fallo de Conexión con el Switch',
                        message=f'No se pudo establecer conexión con el nodo: {msg}'
                    )

                    admin = User.query.filter_by(role='administrador').first()
                    if admin and admin.email:
                        send_notification_by_slug(
                            slug='error', target_email=admin.email,
                            context={'usuario': 'SYSTEM_WORKER',
                                     'ip': os.getenv('C20_HOST', 'SWITCH_NODE'),
                                     'error': f'CONECTIVIDAD FALLIDA: {msg}'}
                        )

                    print("⏳ Pospone tarea por falta de conectividad.")
                    time.sleep(60)
                    continue

                # 4. Ejecutar
                ejecutar_tarea(seccion, cfg, task)

            time.sleep(SLEEP_BETWEEN)

        except Exception as e:
            print(f"❌ Error en el ciclo del worker: {str(e)}")
            time.sleep(SLEEP_IDLE)


if __name__ == "__main__":
    main()
