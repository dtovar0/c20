from flask import Blueprint, request, jsonify, render_template, current_app
from sqlalchemy import func
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
from app import db
from .models import PSX5KTask, PSX5KDetail, PSX5KHistory, PSX5KCommandLog
import os
import datetime

psx_bp = Blueprint('psx', __name__, url_prefix='/api/psx')

# Configuración de carga
UPLOAD_FOLDER = '/home/dtovar/bayblade/c20/uploads/psx5k'
ALLOWED_EXTENSIONS = {'xml', 'csv', 'xls', 'xlsx'}

@psx_bp.route('/list')
@login_required
def list_tasks():
    """
    Lista de tareas PSX5K para la tabla principal.
    Filtrado por usuario si no es administrador.
    """
    try:
        from .models import PSX5KJob
        query = PSX5KTask.query.join(PSX5KJob)
        
        # 1. Filtro de Seguridad: No-admins solo ven sus propias tareas
        is_admin = current_user.role == 'administrador'
        if not is_admin:
            query = query.filter(PSX5KJob.usuario == current_user.email)
            
        tasks = query.order_by(PSX5KJob.created_at.desc(), PSX5KTask.id.desc()).all()
        
        return jsonify({
            "status": "success",
            "tasks": [t.to_dict() for t in tasks],
            "is_admin": is_admin
        })
    except Exception as e:
        current_app.logger.error(f"Error en list_tasks: {e}")
        return jsonify({"status": "error", "message": "No se pudo obtener la lista de tareas"}), 500

@psx_bp.route('/detail/<int:task_id>')
@login_required
def task_detail(task_id):
    """
    Vista independiente para el detalle de una tarea PSX5K
    """
    try:
        task = PSX5KTask.query.get_or_404(task_id)
        history = PSX5KHistory.query.filter_by(task_id=task_id).order_by(PSX5KHistory.fecha.desc()).all()
        command_log = PSX5KCommandLog.query.filter_by(task_id=task_id).first()
        
        return render_template('psx_detail.html', 
                               task=task, 
                               history=history, 
                               command_log=command_log)
    except Exception as e:
        current_app.logger.error(f"Error en task_detail #{task_id}: {e}")
        return render_template('errors/500.html'), 500

@psx_bp.route('/stats')
@login_required
def get_stats():
    """
    Retorna estadísticas de tareas filtradas por el usuario actual
    """
    try:
        email = current_user.email
        from .models import PSX5KJob
        
        # 1. Total de tareas del usuario (Fragmentos)
        total_tareas = PSX5KTask.query.join(PSX5KJob).filter(PSX5KJob.usuario == email).count()
        
        # 2. Tareas en Espera 
        pendientes = PSX5KTask.query.join(PSX5KJob).filter(
            PSX5KJob.usuario == email,
            PSX5KTask.estado == 'Pendiente'
        ).count()
        
        # 3. Tareas Programadas
        programadas = PSX5KTask.query.join(PSX5KJob).filter(
            PSX5KJob.usuario == email,
            PSX5KTask.estado == 'Programada'
        ).count()
        
        # 4. Tarea Activa (GLOBAL: La más reciente con estado Ejecutando en todo el sistema)
        activa = PSX5KTask.query.filter(
            PSX5KTask.estado == 'Ejecutando'
        ).order_by(PSX5KTask.id.desc()).first()
        
        # 5. Dashboard Premium Stats: Volumen Hoy & Eficiencia
        today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Volumen Operativo (Registros totales procesados hoy por el usuario)
        volumen_hoy = db.session.query(func.sum(PSX5KDetail.total)).join(
            PSX5KTask, PSX5KTask.id == PSX5KDetail.id
        ).join(PSX5KJob).filter(
            PSX5KJob.usuario == email,
            PSX5KTask.fecha_inicio >= today
        ).scalar() or 0
        
        # Eficiencia (Éxitos / Procesados) de las tareas terminadas hoy
        stats_data = db.session.query(
            func.sum(PSX5KDetail.ok),
            func.sum(PSX5KDetail.fail)
        ).join(PSX5KTask, PSX5KTask.id == PSX5KDetail.id).join(PSX5KJob).filter(
            PSX5KJob.usuario == email,
            PSX5KTask.estado.in_(['Completado', 'Terminado con Errores']),
            PSX5KTask.fecha_inicio >= today
        ).first()

        s_ok = stats_data[0] or 0
        s_fail = stats_data[1] or 0
        total_p = s_ok + s_fail
        eficiencia = (s_ok / total_p * 100) if total_p > 0 else 0.0

        # 6. Total de tareas TERMINADAS
        total_procesadas = PSX5KTask.query.join(PSX5KJob).filter(
            PSX5KJob.usuario == email,
            PSX5KTask.estado.in_(['Completado', 'Terminado con Errores'])
        ).count()

        return jsonify({
            "status": "success",
            "stats": {
                "total": total_tareas,
                "processed_total": total_procesadas,
                "pending": pendientes,
                "scheduled": programadas,
                "active_task": activa.id if activa else "NINGUNA",
                "volume_today": int(volumen_hoy),
                "efficiency": round(eficiencia, 1),
                "breakdown": {
                    "ok": int(s_ok),
                    "fail": int(s_fail)
                },
                "last_7_tasks": [
                    {
                        "id": t.id,
                        "ok": t.resumen.ok if t.resumen else 0,
                        "fail": t.resumen.fail if t.resumen else 0,
                        "total": t.resumen.total if t.resumen else 0
                    } for t in sorted(PSX5KTask.query.join(PSX5KJob).filter(
                        PSX5KJob.usuario == email,
                        PSX5KTask.estado.in_(['Completado', 'Terminado con Errores'])
                    ).order_by(PSX5KTask.id.desc()).limit(7).all(), key=lambda x: x.id)
                ]
            }
        })
    except Exception as e:
        current_app.logger.error(f"Error en get_stats: {e}")
        return jsonify({"status": "error", "message": "Error al calcular estadísticas"}), 500

@psx_bp.route('/stats/global')
@login_required
def get_global_stats():
    """
    Retorna estadísticas globales del sistema para el dashboard de administrador
    """
    try:
        from app.modules.auth.models import User
        from .models import PSX5KJob
        
        # 1. Usuarios totales
        total_users = User.query.count()
        
        # 2. Tareas totales (Fragmentos en todo el sistema)
        total_tareas = PSX5KTask.query.count()
        
        # 3. Tareas en Espera (Pendientes vs Programadas)
        pendientes = PSX5KTask.query.filter(PSX5KTask.estado == 'Pendiente').count()
        programadas = PSX5KTask.query.filter(PSX5KTask.estado == 'Programada').count()

        # 4. TRABAJOS EN COLA (Global - Cuántos Jobs únicos tienen fragmentos activos)
        cola_total = db.session.query(PSX5KTask.job_id).filter(
            PSX5KTask.estado.in_(['Programada', 'Pendiente', 'Ejecutando'])
        ).distinct().count()
        
        # 5. Tarea Activa (GLOBAL: La más reciente con estado Ejecutando en todo el sistema)
        activas = PSX5KTask.query.filter(PSX5KTask.estado == 'Ejecutando').count()
        activa_obj = PSX5KTask.query.filter(
            PSX5KTask.estado == 'Ejecutando'
        ).order_by(PSX5KTask.id.desc()).first()
        
        active_name = "N/A"
        if activa_obj and activa_obj.job and activa_obj.job.tarea:
            active_name = activa_obj.job.tarea.upper()

        # 6. Top 5 Usuarios con Desglose de Estados (Stacked Column Data)
        from sqlalchemy import case
        top_users_base = db.session.query(PSX5KJob.usuario, func.count(PSX5KJob.id))\
            .group_by(PSX5KJob.usuario)\
            .order_by(func.count(PSX5KJob.id).desc())\
            .limit(5).all()
        
        top_usernames = [u[0] for u in top_users_base]

        status_breakdown = db.session.query(
            PSX5KJob.usuario,
            func.count(case((PSX5KTask.estado == 'Completado', 1))),
            func.count(case((PSX5KTask.estado == 'Terminado con Errores', 1))),
            func.count(case((PSX5KTask.estado == 'Pendiente', 1))),
            func.count(case((PSX5KTask.estado == 'Programada', 1))),
            func.count(case((PSX5KTask.estado == 'Ejecutando', 1)))
        ).join(PSX5KTask).filter(PSX5KJob.usuario.in_(top_usernames)).group_by(PSX5KJob.usuario).all()

        # Formatear para ApexCharts: Series por estado (Dashboard 1 & 2)
        top_users_data = {
            "users": [u[0] for u in status_breakdown],
            "ok": [u[1] for u in status_breakdown],
            "fail": [u[2] for u in status_breakdown],
            "pending": [u[3] for u in status_breakdown],
            "scheduled": [u[4] for u in status_breakdown],
            "active": [u[5] for u in status_breakdown]
        }

        # 7. Tareas por Día (Últimos 7 días para gráfica de tendencia)
        from datetime import timedelta, datetime
        seven_days_ago = datetime.now() - timedelta(days=7)
        daily_query = db.session.query(
            func.date(PSX5KJob.created_at).label('day'),
            func.count(PSX5KJob.id).label('count')
        ).filter(PSX5KJob.created_at >= seven_days_ago)\
        .group_by('day')\
        .order_by('day').all()
        
        daily_tasks = [{"day": d.day.strftime('%d %b'), "count": d.count} for d in daily_query]

        # 8. Análisis Diario (Agregación de psx5k_details por día)
        from .models import PSX5KDetail
        analysis_query = db.session.query(
            func.date(PSX5KTask.fecha_inicio).label('day'),
            func.sum(PSX5KDetail.ok).label('ok'),
            func.sum(PSX5KDetail.fail).label('fail'),
            func.sum(PSX5KDetail.force_ok).label('force'),
            func.sum(PSX5KDetail.dup).label('dup')
        ).join(PSX5KDetail, PSX5KTask.id == PSX5KDetail.id)\
         .filter(PSX5KTask.fecha_inicio >= seven_days_ago)\
         .group_by('day')\
         .order_by('day').limit(7).all()
        
        analysis_daily = {
            "days": [d.day.strftime('%d %b') for d in analysis_query],
            "ok": [int(d.ok or 0) for d in analysis_query],
            "fail": [int(d.fail or 0) for d in analysis_query],
            "force": [int(d.force or 0) for d in analysis_query],
            "dup": [int(d.dup or 0) for d in analysis_query]
        }

        # 9. Monitoreo de Tareas (Hoy)
        today_date = datetime.now().date()
        today_stats_query = db.session.query(
            PSX5KTask.estado,
            func.count(PSX5KTask.id)
        ).join(PSX5KJob).filter(func.date(PSX5KJob.created_at) == today_date)\
         .group_by(PSX5KTask.estado).all()
        
        # Mapeo de estados para la gráfica de dona
        t_stats = {"Pendiente": 0, "Ejecutando": 0, "Error": 0, "Completado": 0}
        for s in today_stats_query:
            state = s[0]
            count = s[1]
            if state in ['Pendiente', 'Programada']: t_stats["Pendiente"] += count
            elif state == 'Ejecutando': t_stats["Ejecutando"] += count
            elif state == 'Terminado con Errores': t_stats["Error"] += count
            elif state == 'Completado': t_stats["Completado"] += count

        today_stats = [t_stats["Completado"], t_stats["Ejecutando"], t_stats["Pendiente"], t_stats["Error"]]

        # 10. Total de ANI procesados (Lifetime - Suma de todos los registros en tareas terminadas)
        from .models import PSX5KDetail
        total_ani_processed = db.session.query(func.sum(PSX5KDetail.total)).join(
            PSX5KTask, PSX5KTask.id == PSX5KDetail.id
        ).filter(
            PSX5KTask.estado == 'Completado'
        ).scalar() or 0

        # 11. Volumen de hoy (Suma de registros procesados hoy)
        volume_today = db.session.query(func.sum(PSX5KDetail.total)).join(
            PSX5KTask, PSX5KTask.id == PSX5KDetail.id
        ).join(PSX5KJob).filter(func.date(PSX5KJob.created_at) == today_date).scalar() or 0

        # 12. Breakdown de hoy
        breakdown_today = db.session.query(
            func.sum(PSX5KDetail.ok),
            func.sum(PSX5KDetail.fail),
            func.sum(PSX5KDetail.force_ok),
            func.sum(PSX5KDetail.dup)
        ).join(PSX5KTask, PSX5KTask.id == PSX5KDetail.id)\
         .join(PSX5KJob).filter(func.date(PSX5KJob.created_at) == today_date).first()

        # 13. Últimas 7 tareas terminadas (Global)
        last_7 = [
            {
                "id": t.id,
                "ok": t.resumen.ok if t.resumen else 0,
                "fail": t.resumen.fail if t.resumen else 0,
                "force": t.resumen.force_ok if t.resumen else 0,
                "dup": t.resumen.dup if t.resumen else 0
            } for t in PSX5KTask.query.filter(PSX5KTask.estado == 'Completado').order_by(PSX5KTask.id.desc()).limit(7).all()
        ]

        return jsonify({
            "status": "success",
            "stats": {
                # Dashboard 1 & 2 Shared/Aliases
                "total": total_tareas,
                "tasks": total_tareas,
                "users": total_users,
                "pending": pendientes,
                "scheduled": programadas,
                "queue": int(total_ani_processed), # Dashboard 2 espera queue para total procesado
                
                # Dashboard 1 Specific
                "active_task": str(activa_obj.id) if activa_obj else "NINGUNA",
                "volume_today": int(volume_today),
                "processed_total": int(total_ani_processed),
                "breakdown": {
                    "ok": int(breakdown_today[0] or 0),
                    "fail": int(breakdown_today[1] or 0),
                    "force": int(breakdown_today[2] or 0),
                    "dup": int(breakdown_today[3] or 0)
                },
                "last_7_tasks": last_7,

                # Dashboard 2 Specific
                "active_id": activa_obj.id if activa_obj else None,
                "active_name": active_name if activa_obj else None,
                "top_users": top_users_data,
                "daily_tasks": daily_tasks,
                "analysis_daily": analysis_daily,
                "today_stats": today_stats
            }
        })
    except Exception as e:
        current_app.logger.error(f"Error en get_global_stats: {e}")
        return jsonify({"status": "error", "message": "Error al calcular estadísticas globales"}), 500

@psx_bp.route('/create', methods=['POST'])
@login_required
def create_task():
    """
    Crea nuevas tareas PSX5K. 
    Aplica Auto-Chunking de 200 registros tanto a Manual como a Archivos.
    """
    from .services import extract_records, chunk_list
    from app.modules.audit.services import add_audit_log
    
    data = request.json
    try:
        # --- AUTO-MIGRACIÓN RÁPIDA (Para asegurar job_id en servidores remotos) ---
        from sqlalchemy import text
        try:
            # Intentar ver si la columna existe (MySQL style)
            db.session.execute(text("SELECT job_id FROM psx5k_tasks LIMIT 1"))
        except Exception:
            db.session.rollback()
            current_app.logger.warning("Auto-Migración: La columna job_id no existe. Intentando crearla...")
            try:
                # 1. Asegurar que existe psx5k_jobs
                db.session.execute(text("""
                    CREATE TABLE IF NOT EXISTS psx5k_jobs (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        usuario VARCHAR(100) NOT NULL,
                        tarea VARCHAR(50),
                        accion_tipo VARCHAR(50),
                        datos_tipo VARCHAR(50),
                        routing_label VARCHAR(100),
                        archivo_origen VARCHAR(255),
                        run_force BOOLEAN DEFAULT FALSE,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                # 2. Añadir job_id a psx5k_tasks
                db.session.execute(text("ALTER TABLE psx5k_tasks ADD COLUMN job_id INT"))
                # 3. Añadir fecha_inicio a psx5k_tasks
                db.session.execute(text("ALTER TABLE psx5k_tasks ADD COLUMN fecha_inicio DATETIME"))
                db.session.commit()
                current_app.logger.info("Auto-Migración: Columna job_id y tabla psx5k_jobs creadas con éxito.")
            except Exception as migrate_err:
                db.session.rollback()
                current_app.logger.error(f"Fallo en Auto-Migración: {migrate_err}")
                # No detenemos el flujo, si falla aquí probablemente falle la inserción después con el error real
        # -------------------------------------------------------------------------

        raw_tarea = data.get('tarea') # add / delete
        raw_accion = data.get('accion_tipo', 'N/A') # Modo: call_in / call_inout
        raw_origen = data.get('datos_tipo', 'Manual') # Procedencia: Manual / Archivo
        
        # 1. Extraer TODOS los registros del origen (sea archivo o manual)
        all_records = extract_records(
            raw_origen, 
            data.get('datos'), 
            '/home/dtovar/bayblade/c20/uploads/psx5k'
        )
        
        if not all_records:
            return jsonify({"status": "error", "message": "No se encontraron registros válidos para procesar"}), 400
            
        # 2. Aplicar DIVISION (Auto-Chunking) cada 200 registros
        chunk_size = current_app.config.get('PSX_CHUNK_SIZE', 200)
        chunks = list(chunk_list(all_records, chunk_size))
        total_chunks = len(chunks)
        
        # --- NUEVA LÓGICA: CREAR JOB MAESTRO ---
        from .models import PSX5KJob
        new_job = PSX5KJob(
            usuario=current_user.email,
            tarea=raw_tarea,
            accion_tipo=raw_accion,
            datos_tipo=raw_origen,
            routing_label=data.get('routing_label'),
            archivo_origen=data.get('datos') if raw_origen == 'Archivo' else 'Ingreso Manual',
            run_force=data.get('force', False)
        )
        db.session.add(new_job)
        db.session.flush() # Para obtener el new_job.id

        created_ids = []
        raw_estado = data.get('estado', 'Pendiente')
        from datetime import datetime
        raw_fecha_inicio = None
        if data.get('fecha_inicio'):
            try:
                # 1. Parse UTC ISO string from JS
                utc_dt = datetime.fromisoformat(data['fecha_inicio'].replace('Z', '+00:00'))
                
                # 2. Convert to Local System TZ (Set in app/__init__.py)
                # and make it naive local for DB comparison consistency
                raw_fecha_inicio = utc_dt.astimezone().replace(tzinfo=None)
            except Exception as e:
                current_app.logger.error(f"Error parsing/converting date {data['fecha_inicio']}: {e}")

        for i, chunk in enumerate(chunks):
            task_data_value = ",".join(chunk)
            
            new_task = PSX5KTask(
                job_id=new_job.id, # Vínculo al maestro
                chunk_index=i + 1,
                chunk_total=total_chunks,
                datos=task_data_value,
                estado=raw_estado,
                fecha_inicio=raw_fecha_inicio
            )
            db.session.add(new_task)
            db.session.flush()
            
            # Registro individual en auditoría
            add_audit_log("tarea creada", status="info", detail=f"Job: {new_job.id} | Task: {new_task.id} | Parte {i+1}/{total_chunks}")
            
            new_detail = PSX5KDetail(id=new_task.id, total=len(chunk), ok=0, fail=0)
            db.session.add(new_detail)
            created_ids.append(new_task.id)
            
        db.session.commit()
        add_audit_log("tarea creada - batch", status="info", detail=f"Origen: {raw_origen} | {total_chunks} fragmentos (DB-stored)")
        
        return jsonify({
            "status": "success",
            "message": f"Se han generado {total_chunks} mini-tareas correctamente",
            "task_ids": created_ids
        }), 201
        
    except Exception as e:
        import traceback
        db.session.rollback()
        error_details = traceback.format_exc()
        current_app.logger.error(f"Error form tarea PSX: {e}\n{error_details}")
        return jsonify({
            "status": "error", 
            "message": f"Error interno: {str(e)}",
            "debug": error_details if current_app.debug or True else None
        }), 500

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@psx_bp.route('/upload', methods=['POST'])
def upload_file():
    """
    Endpoint para recibir, etiquetar y almacenar archivos del terminal PSX5K
    """
    try:
        if 'file' not in request.files:
            return jsonify({"status": "error", "message": "No se detectó parte de archivo"}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"status": "error", "message": "No se seleccionó ningún archivo"}), 400
        
        if file and allowed_file(file.filename):
            # 1. Generar Etiqueta Operativa: usuario_fecha_hora_original
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            email = current_user.email if current_user.is_authenticated else "anon"
            clean_filename = secure_filename(file.filename)
            
            nexus_filename = f"{email}_{timestamp}_{clean_filename}"
            
            # 2. Asegurar que el directorio existe
            if not os.path.exists(UPLOAD_FOLDER):
                os.makedirs(UPLOAD_FOLDER)
                
            save_path = os.path.join(UPLOAD_FOLDER, nexus_filename)
            file.save(save_path)
            
            return jsonify({
                "status": "success", 
                "message": "Archivo etiquetado y cargado correctamente",
                "filename": nexus_filename,
                "path": save_path
            }), 200
        
        return jsonify({"status": "error", "message": "Extensión no permitida (Solo CSV, XLS, XLSX, XML)"}), 400
    except Exception as e:
        current_app.logger.error(f"Error en upload_file: {e}")
        return jsonify({"status": "error", "message": "Fallo crítico al subir archivo"}), 500

@psx_bp.route('/check-connectivity')
@login_required
def check_psx_connectivity():
    """
    Endpoint para verificar la conectividad con el nodo PSX5K
    """
    try:
        from bin.psx5k_cmd import test_connectivity
        ok, message = test_connectivity()
        
        if ok:
            return jsonify({"status": "success", "message": message})
        else:
            return jsonify({"status": "error", "message": message}), 500
    except Exception as e:
        current_app.logger.error(f"Error en check_psx_connectivity: {e}")
        return jsonify({"status": "error", "message": "Fallo inesperado de conexión con el nodo"}), 500


@psx_bp.route('/download_duplicates/<int:task_id>')
@login_required
def download_duplicates(task_id):
    """
    Genera y descarga un CSV con los números marcados como DUP
    """
    try:
        from flask import Response
        
        history = PSX5KHistory.query.filter_by(task_id=task_id, estado='DUP').all()
        if not history:
            return jsonify({"status": "error", "message": "No hay registros duplicados en esta tarea"}), 404
            
        csv_content = "numero,routing_label,fecha\n"
        for item in history:
            csv_content += f"{item.numero},{item.routing_label or ''},{item.fecha}\n"
            
        return Response(
            csv_content,
            mimetype="text/csv",
            headers={"Content-disposition": f"attachment; filename=duplicates_task_{task_id}.csv"}
        )
    except Exception as e:
        current_app.logger.error(f"Error en download_duplicates #{task_id}: {e}")
        return jsonify({"status": "error", "message": "Error al generar archivo de duplicados"}), 500

@psx_bp.route('/reprocess_duplicates/<int:task_id>', methods=['POST'])
@login_required
def reprocess_duplicates(task_id):
    """
    Crea una nueva tarea basada en los registros duplicados de una tarea previa.
    Limitado a máximo 2 reintentos por tarea origen.
    """
    try:
        from app.modules.audit.services import add_audit_log
        
        parent_task = PSX5KTask.query.get_or_404(task_id)
        
        # 1. Validar si esta tarea ya generó un reintento (Uso el nuevo campo parent_id)
        has_retry = PSX5KTask.query.filter_by(parent_id=task_id).first()
        
        if has_retry:
            return jsonify({
                "status": "error", 
                "message": f"Acción bloqueada: La tarea #{task_id} ya cuenta con una tarea complementaria asociada (ID: #{has_retry.id})."
            }), 400

        # 2. Obtener los duplicados
        duplicates = PSX5KHistory.query.filter_by(task_id=task_id, estado='DUP').all()
        if not duplicates:
            return jsonify({"status": "error", "message": "No se encontraron registros duplicados para procesar."}), 400

        # 3. Crear la nueva tarea clónica
        ani_list = [d.numero for d in duplicates]
        task_data_value = ",".join(ani_list)
        
        new_task = PSX5KTask(
            job_id=parent_task.job_id,  # Vinculamos al mismo job maestro
            chunk_index=1,
            chunk_total=1,
            datos=task_data_value,
            parent_id=task_id
        )
        
        db.session.add(new_task)
        db.session.flush()

        new_detail = PSX5KDetail(id=new_task.id, total=len(ani_list), ok=0, fail=0)
        db.session.add(new_detail)
        
        add_audit_log("tarea duplicados - reintento", status="info", detail=f"Target: #{new_task.id} | Parent: #{task_id} | Registros: {len(ani_list)}")
        
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": f"Tarea #{new_task.id} creada correctamente",
            "task_id": new_task.id
        }), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error en reprocess_duplicates #{task_id}: {e}")
        return jsonify({"status": "error", "message": "Error al procesar reintento de duplicados"}), 500

@psx_bp.route('/history/search')
@login_required
def search_history():
    """
    Búsqueda profunda en la tabla de historial (psx5k_history)
    """
    try:
        query_str = request.args.get('q', '').strip()
        if not query_str:
            return jsonify({"status": "success", "results": []})
        
        # Búsqueda por número, etiqueta o estado
        results = PSX5KHistory.query.filter(
            (PSX5KHistory.numero.like(f'%{query_str}%')) |
            (PSX5KHistory.routing_label.like(f'%{query_str}%')) |
            (PSX5KHistory.estado.like(f'%{query_str}%'))
        ).order_by(PSX5KHistory.fecha.desc()).limit(100).all()
        
        return jsonify({
            "status": "success",
            "results": [r.to_dict() for r in results]
        })
    except Exception as e:
        current_app.logger.error(f"Error en search_history: {e}")
        return jsonify({"status": "error", "message": "Error en el motor de búsqueda"}), 500
@psx_bp.route('/job/update/<int:job_id>', methods=['PATCH', 'POST'])
@login_required
def update_or_reprocess_job(job_id):
    """
    Actualiza un Job existente o crea uno nuevo si ya finalizó.
    """
    from .models import PSX5KJob, PSX5KTask, PSX5KDetail
    from app.modules.audit.services import add_audit_log
    
    job = PSX5KJob.query.get_or_404(job_id)
    data = request.json
    action = data.get('action') # 'modify' or 'cancel'

    # Parsing common de fecha para programación
    parsed_scheduled_time = None
    if data.get('is_scheduled') and data.get('scheduled_time'):
        from datetime import datetime
        try:
            # Parse UTC ISO and convert to Local System TZ
            utc_dt = datetime.fromisoformat(data['scheduled_time'].replace('Z', '+00:00'))
            parsed_scheduled_time = utc_dt.astimezone().replace(tzinfo=None)
        except Exception as e:
            current_app.logger.error(f"Error parsing date in update: {e}")
    
    # Determinar si editamos o clonamos
    # Si alguna tarea está en 'Ejecutando', bloqueamos
    active_tasks = PSX5KTask.query.filter(PSX5KTask.job_id == job_id, PSX5KTask.estado == 'Ejecutando').count()
    if active_tasks > 0:
        return jsonify({"status": "error", "message": "No se puede modificar un Job con fragmentos en ejecución."}), 400

    # Estado global del job (basado en sus tareas)
    finished = all(t.estado in ['Terminada', 'Cancelada', 'Error'] for t in job.tasks)
    
    try:
        if action == 'cancel':
            # Acción de Cancelación (Solo para tareas no terminadas)
            updated_count = 0
            for t in job.tasks:
                if t.estado in ['Pendiente', 'Programada', 'Ejecutando', 'Activa']:
                    t.estado = 'Cancelada'
                    updated_count += 1
            db.session.commit()
            add_audit_log("tarea cancelada", status="warning", detail=f"Job ID: {job_id} cancelado por usuario.")
            return jsonify({"status": "success", "message": f"Se han cancelado {updated_count} fragmentos."})

        if action == 'activate':
            # Acción de Reactivación (Reponer en cola fragmentos no terminados o errores)
            updated_count = 0
            for t in job.tasks:
                # Si los datos se purgaron (en terminadas), los recuperamos del historial
                if not t.datos:
                    recovery = PSX5KHistory.query.filter_by(task_id=t.id).all()
                    if recovery:
                        t.datos = ",".join([r.numero for r in recovery])
                
                if t.estado in ['Cancelada', 'Error', 'Terminada']:
                    t.estado = 'Pendiente' if not data.get('is_scheduled') else 'Programada'
                    t.fecha_inicio = parsed_scheduled_time if data.get('is_scheduled') else None
                    updated_count += 1
            
            db.session.commit()
            add_audit_log("tarea reactivada", status="info", detail=f"Job ID: {job_id} reactivado ({updated_count} fragmentos).")
            return jsonify({"status": "success", "message": f"Se han reactivado {updated_count} fragmentos satisfactoriamente."})

        # Si el job ya terminó/canceló y se pide modificar -> CLONAMOS (REPROCESO)
        if finished and action == 'modify':
            origin_task_id = data.get('origin_task_id')
            new_job = PSX5KJob(
                usuario=current_user.email,
                tarea=data.get('tarea', job.tarea),
                accion_tipo=data.get('accion_tipo', job.accion_tipo),
                datos_tipo=job.datos_tipo,
                routing_label=data.get('routing_label', job.routing_label),
                archivo_origen=f"REPROCESO_TASK_{origin_task_id}" if origin_task_id else f"REPROCESO_FROM_{job_id}",
                run_force=data.get('force', job.run_force)
            )
            db.session.add(new_job)
            db.session.flush()
            
            # Clonar tareas
            for old_task in job.tasks:
                # Recuperar datos si están purgados
                task_data = old_task.datos
                if not task_data:
                    recovery = PSX5KHistory.query.filter_by(task_id=old_task.id).all()
                    if recovery:
                        task_data = ",".join([r.numero for r in recovery])

                new_task = PSX5KTask(
                    job_id=new_job.id,
                    chunk_index=old_task.chunk_index,
                    chunk_total=old_task.chunk_total,
                    datos=task_data, 
                    estado='Pendiente' if not data.get('is_scheduled') else 'Programada',
                    fecha_inicio=parsed_scheduled_time if data.get('is_scheduled') else None
                )
                db.session.add(new_task)
                db.session.flush()
                db.session.add(PSX5KDetail(id=new_task.id, total=0)) # El total se recalcula al iniciar
            
            db.session.commit()
            add_audit_log("tarea reprogramada", status="info", detail=f"Nuevo Job ID: {new_job.id} basado en {job_id}")
            return jsonify({"status": "success", "message": "Nueva tarea creada satisfactoriamente.", "new_job_id": new_job.id})

        else:
            # UPDATE In-place (Para estados pendientes/programados/cancelados)
            old_label = job.routing_label
            job.tarea = data.get('tarea', job.tarea)
            job.accion_tipo = data.get('accion_tipo', job.accion_tipo)
            job.routing_label = data.get('routing_label', job.routing_label)
            job.run_force = data.get('force', job.run_force)
            
            # Actualizar estado y tiempos de las tareas asociadas
            for t in job.tasks:
                if t.estado in ['Pendiente', 'Programada', 'Cancelada', 'Error']:
                    if not t.datos:
                        recovery = PSX5KHistory.query.filter_by(task_id=t.id).all()
                        if recovery:
                            t.datos = ",".join([r.numero for r in recovery])
                            
                    t.estado = 'Pendiente' if not data.get('is_scheduled') else 'Programada'
                    t.fecha_inicio = parsed_scheduled_time if data.get('is_scheduled') else None
            
            db.session.commit()
            add_audit_log("tarea modificada", status="info", detail=f"Job ID: {job_id} actualizado. Label: {old_label} -> {job.routing_label}")
            return jsonify({"status": "success", "message": "Tarea actualizada correctamente."})

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error procesando Job #{job_id}: {e}")
        return jsonify({"status": "error", "message": "Error interno al modificar la tarea. Por favor, reintente más tarde."}), 500
