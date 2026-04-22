import os
import sys
import time
import datetime
import signal
import xml.etree.ElementTree as ET
from app import create_app, db
from app.modules.psx.models import PSX5KTask, PSX5KDetail
from app.modules.notifications.services import send_notification_by_slug
from app.modules.auth.models import User

# Configuración Global
LOCK_FILE = "/tmp/psx5k_processor.lock"
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
        return True 
    return False

def process_task_data(task):
    """
    Procesa el origen de datos (Manual o Archivo) y retorna la lista de registros (ANI).
    """
    records = []
    if task.accion_tipo == 'Manual':
        print(f"📝 Procesando entrada MANUAL para Tarea {task.id}")
        raw_data = task.datos or ""
        items = raw_data.replace(';', '\n').replace(',', '\n').split('\n')
        for item in items:
            item = item.strip()
            if not item: continue
            if '-' in item:
                try:
                    parts = item.split('-')
                    start = int(parts[0].strip())
                    end = int(parts[1].strip())
                    if start <= end:
                        records.extend([str(x) for x in range(start, end + 1)])
                    else:
                        records.extend([str(x) for x in range(end, start + 1)])
                except Exception as e:
                    print(f"⚠️ Error procesando rango '{item}': {e}")
            else:
                records.append(item)
    elif task.accion_tipo == 'Archivo':
        print(f"📁 Procesando ARCHIVO para Tarea {task.id}")
        file_path = os.path.join('uploads/psx', task.datos)
        if not os.path.exists(file_path):
            print(f"❌ Archivo no encontrado: {file_path}")
            return []
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            for ani_tag in root.findall('.//ANI'):
                if ani_tag.text:
                    records.append(ani_tag.text.strip())
            if not records:
                for elem in root.iter():
                    if elem.tag.upper() == 'ANI' and elem.text:
                        records.append(elem.text.strip())
        except Exception as e:
            print(f"⚠️ Error procesando XML '{task.datos}': {e}")
            try:
                with open(file_path, 'r') as f:
                    records = [line.strip() for line in f if line.strip()]
            except:
                pass
    return list(set(records))

def main():
    """
    Motor de procesamiento PSX5K (Backend Service)
    """
    app = create_app()

    if os.path.exists(LOCK_FILE):
        if not handle_stale_lock(app):
            print(f"⚠️ Proceso ya en ejecución o lock activo ({LOCK_FILE}). Abortando.")
            return
        else:
            os.remove(LOCK_FILE)

    try:
        with open(LOCK_FILE, "w") as f:
            f.write(str(os.getpid()))
        print(f"🔒 Lock file creado (PID: {os.getpid()})")

        with app.app_context():
            print(f"🔍 Buscando tareas (Pendientes/Programadas) - {datetime.datetime.now()}")
            tasks = PSX5KTask.query.filter(
                PSX5KTask.estado.in_(['Pendiente', 'Programada'])
            ).order_by(PSX5KTask.created_at.asc()).limit(5).all()

            if not tasks:
                print("📭 No hay tareas por procesar.")
                return

            print(f"🎯 Encontradas {len(tasks)} tareas para procesar.")
            
            for idx, task in enumerate(tasks):
                print(f"⚙️ Iniciando Ejecución [{idx+1}/5]: Tarea ID {task.id} (Tarea: {task.tarea})")
                
                task.estado = 'Ejecutando'
                task.fecha_inicio = datetime.datetime.now()
                db.session.commit()

                admin = User.query.filter_by(role='administrador').first()
                if admin and admin.email:
                    send_notification_by_slug(
                        slug='inicio',
                        target_email=admin.email,
                        context={'usuario': task.usuario, 'hora': task.fecha_inicio.strftime('%Y-%m-%d %H:%M:%S')}
                    )

                # --- PROCESAMIENTO DE DATOS ---
                ani_list = process_task_data(task)
                total_count = len(ani_list)
                
                detail = PSX5KDetail.query.get(task.id)
                if not detail:
                    detail = PSX5KDetail(id=task.id)
                    db.session.add(detail)
                
                detail.total = total_count
                db.session.commit()
                
                print(f"📊 Tarea {task.id}: {total_count} registros identificados.")
                
                if total_count == 0:
                    print(f"⚠️ Tarea {task.id} abortada: No se encontraron registros válidos.")
                    task.estado = 'Error'
                    db.session.commit()
                    continue
                
                ####### INICIO SCRIPT #########
                # Importar y ejecutar función validada desde archivo externo
                from s5k_cmd import s5k_cmd
                
                # Mapear tipos de llamada para el script
                type_map = {
                    'Bloqueo (Entrante)': 'call_in',
                    'Routing Label (Activo)': 'call_inout'
                }
                l_type = type_map.get(task.datos_tipo, 'call_in')
                
                results = s5k_cmd(
                    line_task=task.tarea, 
                    line_number=ani_list,
                    line_type=l_type,
                    routing_label=task.routing_label,
                    force=task.force
                )
                
                # Persistir resultados en DB
                detail.ok = results.get("ok", 0) + results.get("dup", 0)
                detail.fail = results.get("fail", 0)
                db.session.commit()

                # Marcar como finalizada
                task.estado = 'Terminada'
                task.fecha_fin = datetime.datetime.now()
                db.session.commit()
                ####### FIN SCRIPT #########

                # Notificar finalización
                if admin and admin.email:
                    send_notification_by_slug(
                        slug='terminado', 
                        target_email=admin.email,
                        context={'usuario': task.usuario, 'hora': task.fecha_fin.strftime('%Y-%m-%d %H:%M:%S')}
                    )

                time.sleep(1)

            print("✅ Bloque de tareas finalizado.")

    except Exception as e:
        print(f"❌ Error crítico en el backend: {str(e)}")
    finally:
        cleanup_lock()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))
    signal.signal(signal.SIGTERM, lambda s, f: sys.exit(0))
    main()
