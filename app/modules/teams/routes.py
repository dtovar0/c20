from flask import Blueprint, request, jsonify, render_template, current_app
from sqlalchemy import func
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
from app import db
from .models import TeamsTask, TeamsDetail, TeamsHistory, TeamsCommandLog
import os
import datetime

teams_bp = Blueprint('teams', __name__, url_prefix='/api/teams')

# Configuración de rutas dinámica
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, 'uploads', 'teams')
ALLOWED_EXTENSIONS = {'xml', 'csv', 'xls', 'xlsx'}

# Identifica a esta sección en las tablas compartidas (historial y espejo)
SECCION = 'teams'

@teams_bp.route('/list')
@login_required
def list_tasks():
    """
    Lista de tareas Teams para la tabla principal.
    Filtrado por usuario si no es administrador.
    """
    try:
        from .models import TeamsJob
        from sqlalchemy.orm import joinedload

        # Carga proactiva de Job y Resumen (Detail) para evitar fallos de sesión/cache
        query = TeamsTask.query.options(
            joinedload(TeamsTask.job),
            joinedload(TeamsTask.resumen)
        ).join(TeamsJob)

        # 1. Filtro de Seguridad: No-admins solo ven sus propias tareas
        is_admin = getattr(current_user, 'role', 'usuario') == 'administrador'
        if not is_admin:
            query = query.filter(TeamsJob.usuario == current_user.email)

        tasks = query.order_by(TeamsJob.created_at.desc(), TeamsTask.id.desc()).all()

        response = jsonify({
            "status": "success",
            "tasks": [t.to_dict() for t in tasks],
            "is_admin": is_admin
        })

        # Evitar caché en el navegador para asegurar datos frescos
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

        return response
    except Exception as e:
        current_app.logger.error(f"Error en list_tasks Teams: {e}")
        return jsonify({"status": "error", "message": "No se pudo obtener la lista de tareas"}), 500

@teams_bp.route('/detail/<int:task_id>')
@login_required
def task_detail(task_id):
    """
    Vista independiente para el detalle de una tarea Teams
    """
    try:
        task = TeamsTask.query.get_or_404(task_id)
        history = TeamsHistory.query.filter_by(seccion=SECCION, task_id=task_id).order_by(TeamsHistory.fecha.desc()).all()
        command_log = TeamsCommandLog.query.filter_by(task_id=task_id).first()

        # Verificar si ya existe un reintento
        has_retry = TeamsTask.query.filter_by(parent_id=task_id).first()

        return render_template('teams_detail.html',
                               task=task,
                               history=history,
                               command_log=command_log,
                               has_retry=has_retry)
    except Exception as e:
        current_app.logger.error(f"Error en task_detail Teams #{task_id}: {e}")
        return render_template('errors/500.html'), 500

@teams_bp.route('/stats')
@login_required
def get_stats():
    """
    Retorna estadísticas de tareas Teams filtradas por el usuario actual
    """
    try:
        email = current_user.email
        from .models import TeamsJob

        # 1. Total de tareas del usuario (Fragmentos)
        total_tareas = TeamsTask.query.join(TeamsJob).filter(TeamsJob.usuario == email).count()

        # 2. Tareas en Espera
        pendientes = TeamsTask.query.join(TeamsJob).filter(
            TeamsJob.usuario == email,
            TeamsTask.estado == 'Pendiente'
        ).count()

        # 3. Tareas Programadas
        programadas = TeamsTask.query.join(TeamsJob).filter(
            TeamsJob.usuario == email,
            TeamsTask.estado == 'Programada'
        ).count()

        # 4. Tarea Activa (GLOBAL: La más reciente con estado Ejecutando en todo el sistema)
        activa = TeamsTask.query.filter(
            TeamsTask.estado == 'Ejecutando'
        ).order_by(TeamsTask.id.desc()).first()

        # 5. Dashboard Premium Stats: Volumen Hoy & Eficiencia
        today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        # Volumen y eficiencia se miden sobre OFC2CODE: es la tabla por la que pasa
        # cada número una sola vez (SNPANAME/TOFCNAME operan sobre ladas y series
        # deduplicadas, así que sus totales no representan el tamaño del lote).
        volumen_hoy = db.session.query(func.sum(TeamsDetail.ofc2code_total)).join(
            TeamsTask, TeamsTask.id == TeamsDetail.id
        ).join(TeamsJob).filter(
            TeamsJob.usuario == email,
            TeamsTask.fecha_inicio >= today
        ).scalar() or 0

        # Eficiencia (Éxitos / Procesados) de las tareas terminadas hoy
        stats_data = db.session.query(
            func.sum(TeamsDetail.ofc2code_ok),
            func.sum(TeamsDetail.ofc2code_fail)
        ).join(TeamsTask, TeamsTask.id == TeamsDetail.id).join(TeamsJob).filter(
            TeamsJob.usuario == email,
            TeamsTask.estado.in_(['Completado', 'Terminado con Errores']),
            TeamsTask.fecha_inicio >= today
        ).first()

        s_ok = stats_data[0] or 0
        s_fail = stats_data[1] or 0
        total_p = s_ok + s_fail
        eficiencia = (s_ok / total_p * 100) if total_p > 0 else 0.0

        # 6. Total de tareas TERMINADAS
        total_procesadas = TeamsTask.query.join(TeamsJob).filter(
            TeamsJob.usuario == email,
            TeamsTask.estado.in_(['Completado', 'Terminado con Errores'])
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
                        "ok": t.resumen.ofc2code_ok if t.resumen else 0,
                        "fail": t.resumen.ofc2code_fail if t.resumen else 0,
                        "total": t.resumen.ofc2code_total if t.resumen else 0
                    } for t in sorted(TeamsTask.query.join(TeamsJob).filter(
                        TeamsJob.usuario == email,
                        TeamsTask.estado.in_(['Completado', 'Terminado con Errores'])
                    ).order_by(TeamsTask.id.desc()).limit(7).all(), key=lambda x: x.id)
                ]
            }
        })
    except Exception as e:
        current_app.logger.error(f"Error en get_stats Teams: {e}")
        return jsonify({"status": "error", "message": "Error al calcular estadísticas"}), 500

@teams_bp.route('/create', methods=['POST'])
@login_required
def create_task():
    """
    Crea nuevas tareas Teams.
    Aplica Auto-Chunking de 200 registros tanto a Manual como a Archivos.
    """
    from .services import extract_records, chunk_list
    from app.modules.audit.services import add_audit_log

    data = request.json
    try:
        if not data:
            return jsonify({"status": "error", "message": "No se recibieron datos (JSON vacío)"}), 400

        raw_tarea = data.get('tarea') # add / delete
        raw_accion = data.get('accion_tipo', 'N/A') # Modo: call_in / call_inout
        raw_origen = data.get('datos_tipo', 'Manual') # Procedencia: Manual / Archivo

        if not raw_tarea:
            return jsonify({"status": "error", "message": "El campo 'tarea' es obligatorio"}), 400

        # 1. Extraer registros
        all_records = extract_records(
            raw_origen,
            data.get('datos'),
            UPLOAD_FOLDER
        )

        if not all_records:
            return jsonify({"status": "error", "message": "No se encontraron registros válidos para procesar"}), 400

        # 2. Chunking
        chunk_size = current_app.config.get('TEAMS_CHUNK_SIZE', 200)
        chunks = list(chunk_list(all_records, chunk_size))
        total_chunks = len(chunks)

        # --- IDENTIDAD DEL USUARIO ---
        user_email = getattr(current_user, 'email', None) or "usuario_desconocido"

        # --- CREAR JOB MAESTRO ---
        from .models import TeamsJob
        try:
            new_job = TeamsJob(
                usuario=user_email,
                tarea=raw_tarea,
                accion_tipo=raw_accion,
                datos_tipo=raw_origen,
                archivo_origen=data.get('datos') if raw_origen == 'Archivo' else 'Ingreso Manual',
                # Prefijo del lote: entra literalmente en el comando del nodo
                prefijo=data.get('prefijo') or os.getenv('TEAMS_PREFIJO_DEFAULT', ''),
                cliente=data.get('cliente')
            )
            db.session.add(new_job)
            db.session.flush() # Para obtener el new_job.id
        except Exception as job_err:
            db.session.rollback()
            current_app.logger.error(f"TEAMS_CREATE: Failed to create TeamsJob: {job_err}")
            return jsonify({"status": "error", "message": f"Error al crear el trabajo maestro: {str(job_err)}"}), 500

        created_ids = []
        raw_estado = data.get('estado', 'Pendiente')
        from datetime import datetime
        raw_fecha_inicio = None

        if data.get('fecha_inicio'):
            try:
                f_str = data['fecha_inicio'].replace('Z', '+00:00')
                utc_dt = datetime.fromisoformat(f_str)
                raw_fecha_inicio = utc_dt.astimezone().replace(tzinfo=None)
            except Exception as e:
                current_app.logger.error(f"TEAMS_CREATE: Date parsing error {data['fecha_inicio']}: {e}")

        # 3. Crear Tareas y Detalles
        try:
            for i, chunk in enumerate(chunks):
                task_data_value = ",".join(chunk)
                new_task = TeamsTask(
                    job_id=new_job.id,
                    chunk_index=i + 1,
                    chunk_total=total_chunks,
                    datos=task_data_value,
                    estado=raw_estado,
                    fecha_inicio=raw_fecha_inicio,
                    tipo='normal'
                )
                db.session.add(new_task)
                db.session.flush()

                # Los contadores los rellena el worker al parsear los logs de cada tabla
                new_detail = TeamsDetail(id=new_task.id)
                db.session.add(new_detail)
                created_ids.append(new_task.id)

            db.session.commit()
        except Exception as task_err:
            db.session.rollback()
            current_app.logger.error(f"TEAMS_CREATE: Task creation loop failed: {task_err}")
            return jsonify({"status": "error", "message": f"Error al generar fragmentos: {str(task_err)}"}), 500

        # 4. Auditoría (Final)
        try:
            add_audit_log(
                f"Lote Teams-{new_job.id} Creado",
                status="info",
                detail=f"Tarea: {raw_tarea} | Origen: {raw_origen} | {total_chunks} fragmentos | {len(all_records)} registros",
                user_override=user_email
            )
        except Exception as audit_err:
            current_app.logger.warning(f"TEAMS_CREATE: Audit log failed (non-critical): {audit_err}")

        return jsonify({
            "status": "success",
            "message": f"Se han generado {total_chunks} mini-tareas correctamente",
            "task_ids": created_ids,
            "job_id": new_job.id
        }), 201

    except Exception as e:
        import traceback
        db.session.rollback()
        error_details = traceback.format_exc()
        current_app.logger.error(f"Error fatal en create_task Teams: {e}\n{error_details}")
        return jsonify({
            "status": "error",
            "message": f"Error interno: {str(e)}",
            "debug": error_details
        }), 500


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@teams_bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """
    Endpoint para recibir, etiquetar y almacenar archivos del terminal Teams
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
        current_app.logger.error(f"Error en upload_file Teams: {e}")
        return jsonify({"status": "error", "message": "Fallo crítico al subir archivo"}), 500


@teams_bp.route('/check-connectivity')
@login_required
def check_teams_connectivity():
    """
    Verifica la conectividad con el nodo Teams
    """
    try:
        import sys
        bin_path = os.path.join(PROJECT_ROOT, 'bin')
        if bin_path not in sys.path:
            sys.path.insert(0, bin_path)

        from c20_cmd import test_connectivity
        ok, message = test_connectivity()

        if ok:
            return jsonify({"status": "success", "message": message})
        return jsonify({"status": "error", "message": message}), 500
    except Exception as e:
        current_app.logger.error(f"Error en check_teams_connectivity: {e}")
        return jsonify({"status": "error", "message": "Fallo inesperado de conexión con el nodo"}), 500


@teams_bp.route('/logs/<int:task_id>')
@login_required
def task_logs(task_id):
    """
    Devuelve los logs crudos por tabla de una tarea (se sirven aparte del detalle
    porque son voluminosos).
    """
    try:
        detail = db.session.get(TeamsDetail, task_id)
        if not detail:
            return jsonify({"status": "error", "message": "Tarea sin resumen registrado"}), 404
        return jsonify({"status": "success", "logs": detail.logs_dict()})
    except Exception as e:
        current_app.logger.error(f"Error en task_logs Teams #{task_id}: {e}")
        return jsonify({"status": "error", "message": "Error al obtener los logs"}), 500


@teams_bp.route('/download_duplicates/<int:task_id>')
@login_required
def download_duplicates(task_id):
    """
    Genera y descarga un CSV con los números no aplicados (estado FAIL).

    En Teams un FAIL no es un error: significa que el registro no estaba en el
    estado esperado (en 'add' ya existía; en 'del' no existía).
    """
    try:
        from flask import Response

        history = TeamsHistory.query.filter_by(seccion=SECCION, task_id=task_id, estado='FAIL').all()
        if not history:
            return jsonify({"status": "error", "message": "No hay registros sin aplicar en esta tarea"}), 404

        csv_content = "numero,prefijo,fecha\n"
        for item in history:
            csv_content += f"{item.numero},{item.parametro or ''},{item.fecha}\n"

        return Response(
            csv_content,
            mimetype="text/csv",
            headers={"Content-disposition": f"attachment; filename=no_aplicados_teams_task_{task_id}.csv"}
        )
    except Exception as e:
        current_app.logger.error(f"Error en download_duplicates Teams #{task_id}: {e}")
        return jsonify({"status": "error", "message": "Error al generar el archivo"}), 500

@teams_bp.route('/reprocess_duplicates/<int:task_id>/', methods=['POST'])
@login_required
def reprocess_duplicates(task_id):
    """
    Crea una nueva tarea con los registros que no se aplicaron (FAIL) en una
    tarea previa. Limitado a un único reintento por tarea origen.

    Nota: en Teams no existe el modo Force del PSX5K —los .exp no sobrescriben—,
    así que el reintento vuelve a intentar la misma operación tal cual. Solo
    tiene sentido si el estado del nodo cambió desde la ejecución original.
    """
    try:
        from app.modules.audit.services import add_audit_log

        parent_task = TeamsTask.query.get_or_404(task_id)

        # 1. Validar si esta tarea ya generó un reintento
        has_retry = TeamsTask.query.filter_by(parent_id=task_id).first()

        if has_retry:
            return jsonify({
                "status": "error",
                "message": f"Acción bloqueada: La tarea #{task_id} ya cuenta con una tarea complementaria asociada (ID: #{has_retry.id})."
            }), 400

        # 2. Obtener los registros no aplicados
        pendientes = TeamsHistory.query.filter_by(seccion=SECCION, task_id=task_id, estado='FAIL').all()
        if not pendientes:
            return jsonify({"status": "error", "message": "No se encontraron registros sin aplicar para reprocesar."}), 400

        # 3. Crear el nuevo Job y Tarea clónica
        from .models import TeamsJob

        new_job = TeamsJob(
            usuario=parent_task.job.usuario,
            tarea=parent_task.job.tarea,
            accion_tipo=parent_task.job.accion_tipo,
            datos_tipo=parent_task.job.datos_tipo,
            prefijo=parent_task.job.prefijo,
            cliente=parent_task.job.cliente,
            archivo_origen=f"RETRY_TASK_{task_id}"
        )
        db.session.add(new_job)
        db.session.flush()

        ani_list = [d.numero for d in pendientes]
        task_data_value = ",".join(ani_list)

        new_task = TeamsTask(
            job_id=new_job.id,
            chunk_index=1,
            chunk_total=1,
            datos=task_data_value,
            parent_id=task_id
        )

        db.session.add(new_task)
        db.session.flush()

        new_detail = TeamsDetail(id=new_task.id)
        db.session.add(new_detail)

        add_audit_log("reproceso registros no aplicados Teams", status="info", detail=f"Target: #{new_task.id} | Parent: #{task_id} | Registros: {len(ani_list)}")

        db.session.commit()

        return jsonify({
            "status": "success",
            "message": f"Tarea #{new_task.id} creada correctamente",
            "task_id": new_task.id
        }), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error en reprocess_duplicates Teams #{task_id}: {e}")
        return jsonify({"status": "error", "message": "Error al procesar reintento de duplicados"}), 500

@teams_bp.route('/history/search')
@login_required
def search_history():
    """
    Búsqueda profunda en el historial.

    Por omisión busca solo en Teams. Con ?seccion=all devuelve el historial
    combinado de las tres secciones, y con ?seccion=wse|teams el de una concreta.
    """
    try:
        query_str = request.args.get('q', '').strip()
        if not query_str:
            return jsonify({"status": "success", "results": []})

        seccion = request.args.get('seccion', SECCION).lower()

        query = TeamsHistory.query.filter(
            (TeamsHistory.numero.like(f'%{query_str}%')) |
            (TeamsHistory.parametro.like(f'%{query_str}%')) |
            (TeamsHistory.estado.like(f'%{query_str}%'))
        )
        if seccion != 'all':
            query = query.filter(TeamsHistory.seccion == seccion)

        results = query.order_by(TeamsHistory.fecha.desc()).limit(100).all()

        return jsonify({
            "status": "success",
            "seccion": seccion,
            "results": [r.to_dict() for r in results]
        })
    except Exception as e:
        current_app.logger.error(f"Error en search_history Teams: {e}")
        return jsonify({"status": "error", "message": "Error en el motor de búsqueda"}), 500


@teams_bp.route('/history/numero/<numero>')
@login_required
def history_by_number(numero):
    """
    Trazabilidad de un número: todos sus movimientos en orden cronológico,
    atravesando las tres secciones.

    Responde a "qué le ha pasado a este número": desde qué sección se dio de
    alta, si alguien lo intentó de nuevo desde otra, y cuándo se dio de baja.
    """
    try:
        movimientos = TeamsHistory.query.filter_by(numero=numero.strip()) \
            .order_by(TeamsHistory.fecha.asc()).limit(500).all()

        if not movimientos:
            return jsonify({"status": "success", "numero": numero, "movimientos": [], "secciones": []})

        return jsonify({
            "status": "success",
            "numero": numero,
            "total": len(movimientos),
            "secciones": sorted({m.seccion for m in movimientos}),
            "movimientos": [m.to_dict() for m in movimientos]
        })
    except Exception as e:
        current_app.logger.error(f"Error en history_by_number Teams #{numero}: {e}")
        return jsonify({"status": "error", "message": "Error al consultar el historial del número"}), 500

@teams_bp.route('/job/update/<int:job_id>', methods=['PATCH', 'POST'])
@login_required
def update_or_reprocess_job(job_id):
    """
    Actualiza un Job Teams existente o crea uno nuevo si ya finalizó.
    """
    from .models import TeamsJob
    from app.modules.audit.services import add_audit_log

    job = TeamsJob.query.get_or_404(job_id)
    data = request.json
    action = data.get('action') # 'modify' / 'cancel' / 'activate'

    # Parsing common de fecha para programación
    parsed_scheduled_time = None
    if data.get('is_scheduled') and data.get('scheduled_time'):
        from datetime import datetime
        try:
            # Parse UTC ISO and convert to Local System TZ
            utc_dt = datetime.fromisoformat(data['scheduled_time'].replace('Z', '+00:00'))
            parsed_scheduled_time = utc_dt.astimezone().replace(tzinfo=None)
        except Exception as e:
            current_app.logger.error(f"Error parsing date in update Teams: {e}")

    # Si alguna tarea está en 'Ejecutando', bloqueamos
    active_tasks = TeamsTask.query.filter(TeamsTask.job_id == job_id, TeamsTask.estado == 'Ejecutando').count()
    if active_tasks > 0:
        return jsonify({"status": "error", "message": "No se puede modificar un Job con fragmentos en ejecución."}), 400

    # Estado global del job (basado en sus tareas)
    finished = all(t.estado in ['Completado', 'Completada', 'Terminado con Errores', 'Error', 'Cancelada', 'Cancelado', 'Abortada'] for t in job.tasks)

    try:
        if action == 'cancel':
            # Acción de Cancelación (Solo para tareas no terminadas)
            updated_count = 0
            for t in job.tasks:
                if t.estado in ['Pendiente', 'Programada', 'Ejecutando', 'Activa']:
                    t.estado = 'Cancelada'
                    updated_count += 1
            db.session.commit()
            add_audit_log(f"OPERACIÓN CANCELADA (TEAMS-JOB-{job_id})", status="warning", detail=f"El usuario '{current_user.email}' ha abortado el job íntegramente.")
            return jsonify({"status": "success", "message": f"Se han cancelado {updated_count} fragmentos."})

        if action == 'activate':
            # Acción de Reactivación (Reponer en cola fragmentos no terminados o errores)
            updated_count = 0
            for t in job.tasks:
                # Si los datos se purgaron (en terminadas), los recuperamos del historial
                if not t.datos:
                    recovery = TeamsHistory.query.filter_by(seccion=SECCION, task_id=t.id).all()
                    if recovery:
                        t.datos = ",".join([r.numero for r in recovery])

                if t.estado in ['Cancelada', 'Cancelado', 'Error', 'Completado', 'Completada', 'Terminado con Errores', 'Abortada']:
                    t.estado = 'Pendiente' if not data.get('is_scheduled') else 'Programada'
                    t.fecha_inicio = parsed_scheduled_time if data.get('is_scheduled') else None
                    updated_count += 1

            db.session.commit()
            add_audit_log(f"OPERACIÓN REACTIVADA (TEAMS-JOB-{job_id})", status="info", detail=f"Se han retornado {updated_count} fragmentos de la tarea a estado PENDIENTE.")
            return jsonify({"status": "success", "message": f"Se han reactivado {updated_count} fragmentos satisfactoriamente."})

        # Si el job ya terminó/canceló y se pide modificar -> CLONAMOS (REPROCESO)
        if finished and action == 'modify':
            origin_task_id = data.get('origin_task_id')
            new_job = TeamsJob(
                usuario=current_user.email,
                tarea=data.get('tarea', job.tarea),
                accion_tipo=data.get('accion_tipo', job.accion_tipo),
                datos_tipo=job.datos_tipo,
                prefijo=data.get('prefijo', job.prefijo),
                cliente=data.get('cliente', job.cliente),
                archivo_origen=f"REPROCESO_TASK_{origin_task_id}" if origin_task_id else f"REPROCESO_FROM_{job_id}"
            )
            db.session.add(new_job)
            db.session.flush()

            # Clonar tareas
            for old_task in job.tasks:
                # Recuperar datos si están purgados
                task_data = old_task.datos
                if not task_data:
                    recovery = TeamsHistory.query.filter_by(seccion=SECCION, task_id=old_task.id).all()
                    if recovery:
                        task_data = ",".join([r.numero for r in recovery])

                new_task = TeamsTask(
                    job_id=new_job.id,
                    chunk_index=old_task.chunk_index,
                    chunk_total=old_task.chunk_total,
                    datos=task_data,
                    estado='Pendiente' if not data.get('is_scheduled') else 'Programada',
                    fecha_inicio=parsed_scheduled_time if data.get('is_scheduled') else None
                )
                db.session.add(new_task)
                db.session.flush()
                db.session.add(TeamsDetail(id=new_task.id)) # Los contadores se recalculan al ejecutar

            db.session.commit()
            add_audit_log(f"RE-PROGRAMACIÓN (TEAMS-{new_job.id})", status="info", detail=f"Nueva instancia operativa generada basada en el Job Maestro {job_id}")
            return jsonify({"status": "success", "message": "Nueva tarea creada satisfactoriamente.", "new_job_id": new_job.id})

        else:
            # UPDATE In-place (Para estados pendientes/programados/cancelados)
            old_prefijo = job.prefijo
            job.tarea = data.get('tarea', job.tarea)
            job.accion_tipo = data.get('accion_tipo', job.accion_tipo)
            job.prefijo = data.get('prefijo', job.prefijo)
            job.cliente = data.get('cliente', job.cliente)

            # Actualizar estado y tiempos de las tareas asociadas
            for t in job.tasks:
                if t.estado in ['Pendiente', 'Programada', 'Cancelada', 'Cancelado', 'Error', 'Completado', 'Completada', 'Terminado con Errores']:
                    if not t.datos:
                        recovery = TeamsHistory.query.filter_by(seccion=SECCION, task_id=t.id).all()
                        if recovery:
                            t.datos = ",".join([r.numero for r in recovery])

                    t.estado = 'Pendiente' if not data.get('is_scheduled') else 'Programada'
                    t.fecha_inicio = parsed_scheduled_time if data.get('is_scheduled') else None

            db.session.commit()
            add_audit_log(f"MODIFICACIÓN PORTAFOLIO (TEAMS-JOB-{job_id})", status="info", detail=f"Actualización de Prefijo: {old_prefijo} -> {job.prefijo}")
            return jsonify({"status": "success", "message": "Tarea actualizada correctamente."})

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error procesando Job Teams #{job_id}: {e}")
        return jsonify({"status": "error", "message": "Error interno al modificar la tarea. Por favor, reintente más tarde."}), 500
