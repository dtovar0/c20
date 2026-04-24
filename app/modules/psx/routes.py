from flask import Blueprint, request, jsonify, render_template, current_app
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
from app import db
from .models import PSX5KTask, PSX5KDetail, PSX5KHistory
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
            query = query.filter(PSX5KJob.usuario == current_user.username)
            
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
        return render_template('psx_detail.html', task=task, history=history)
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
        username = current_user.username
        from .models import PSX5KJob
        
        # 1. Total de tareas del usuario (Fragmentos)
        total_tareas = PSX5KTask.query.join(PSX5KJob).filter(PSX5KJob.usuario == username).count()
        
        # 2. Tareas Pendientes (Programada o Pendiente)
        pendientes = PSX5KTask.query.join(PSX5KJob).filter(
            PSX5KJob.usuario == username,
            PSX5KTask.estado.in_(['Programada', 'Pendiente'])
        ).count()
        
        # 3. Tareas Programadas (Estado Pendiente según solicitud del usuario)
        programadas = PSX5KTask.query.join(PSX5KJob).filter(
            PSX5KJob.usuario == username,
            PSX5KTask.estado == 'Pendiente'
        ).count()
        
        # 4. Tarea Activa (La más reciente con estado Ejecutando)
        activa = PSX5KTask.query.join(PSX5KJob).filter(
            PSX5KJob.usuario == username, 
            PSX5KTask.estado == 'Ejecutando'
        ).order_by(PSX5KJob.created_at.desc()).first()
        
        return jsonify({
            "status": "success",
            "stats": {
                "total": total_tareas,
                "pending": pendientes,
                "scheduled": programadas,
                "active_task": activa.id if activa else "NINGUNA"
            }
        })
    except Exception as e:
        current_app.logger.error(f"Error en get_stats: {e}")
        return jsonify({"status": "error", "message": "Error al calcular estadísticas"}), 500

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
        chunks = list(chunk_list(all_records, 200))
        total_chunks = len(chunks)
        
        # --- NUEVA LÓGICA: CREAR JOB MAESTRO ---
        from .models import PSX5KJob
        new_job = PSX5KJob(
            usuario=current_user.username,
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
        for i, chunk in enumerate(chunks):
            task_data_value = ",".join(chunk)
            
            new_task = PSX5KTask(
                job_id=new_job.id, # Vínculo al maestro
                chunk_index=i + 1,
                chunk_total=total_chunks,
                datos=task_data_value
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
        db.session.rollback()
        current_app.logger.error(f"Error form tarea PSX: {e}")
        return jsonify({"status": "error", "message": "Ocurrió un error interno al procesar la tarea. Consulte logs para más detalles."}), 500

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
            username = current_user.username if current_user.is_authenticated else "anon"
            clean_filename = secure_filename(file.filename)
            
            nexus_filename = f"{username}_{timestamp}_{clean_filename}"
            
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
                    t.fecha_inicio = data.get('scheduled_time') if data.get('is_scheduled') else None
                    updated_count += 1
            
            db.session.commit()
            add_audit_log("tarea reactivada", status="info", detail=f"Job ID: {job_id} reactivado ({updated_count} fragmentos).")
            return jsonify({"status": "success", "message": f"Se han reactivado {updated_count} fragmentos satisfactoriamente."})

        # Si el job ya terminó/canceló y se pide modificar -> CLONAMOS (REPROCESO)
        if finished and action == 'modify':
            origin_task_id = data.get('origin_task_id')
            new_job = PSX5KJob(
                usuario=current_user.username,
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
                    fecha_inicio=data.get('scheduled_time') if data.get('is_scheduled') else None
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
                    t.fecha_inicio = data.get('scheduled_time') if data.get('is_scheduled') else None
            
            db.session.commit()
            add_audit_log("tarea modificada", status="info", detail=f"Job ID: {job_id} actualizado. Label: {old_label} -> {job.routing_label}")
            return jsonify({"status": "success", "message": "Tarea actualizada correctamente."})

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error procesando Job #{job_id}: {e}")
        return jsonify({"status": "error", "message": "Error interno al modificar la tarea. Por favor, reintente más tarde."}), 500
