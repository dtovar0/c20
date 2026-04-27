from flask import Blueprint, jsonify, request
from app.modules.api.decorators import api_key_required
from app.modules.psx.models import PSX5KTask
from app import db

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

@api_bp.route('/status', methods=['GET'])
@api_key_required
def get_status():
    """
    Health check publico para la API
    """
    return jsonify({
        "status": "online",
        "version": "1.0.0",
        "message": "NEXUS API Táctica activa y protegida"
    })

@api_bp.route('/tasks', methods=['GET'])
@api_key_required
def list_tasks():
    """
    Lista las ultimas tareas procesadas
    """
    limit = request.args.get('limit', 20, type=int)
    tasks = PSX5KTask.query.order_by(PSX5KTask.id.desc()).limit(limit).all()
    
    return jsonify({
        "status": "success",
        "count": len(tasks),
        "data": [t.to_dict() for t in tasks]
    })

@api_bp.route('/tasks/upload', methods=['POST'])
@api_key_required
def upload_api_file():
    """
    Sube un archivo para ser usado en una tarea posterior.
    Soporta: .xml, .csv, .xls, .xlsx
    """
    from app.modules.psx.routes import allowed_file, UPLOAD_FOLDER
    from werkzeug.utils import secure_filename
    import os
    import datetime
    
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No selected file"}), 400
        
    if file and allowed_file(file.filename):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        clean_filename = secure_filename(file.filename)
        nexus_filename = f"api_upload_{timestamp}_{clean_filename}"
        
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)
            
        save_path = os.path.join(UPLOAD_FOLDER, nexus_filename)
        file.save(save_path)
        
        return jsonify({
            "status": "success",
            "filename": nexus_filename
        })
    
    return jsonify({"status": "error", "message": "File type not allowed"}), 400

@api_bp.route('/tasks/create', methods=['POST'])
@api_key_required
def create_api_task():
    """
    Crea una tarea PSX5K desde la API.
    JSON Body:
    {
        "tarea": "add" / "delete",
        "accion_tipo": "bulk",
        "datos_tipo": "Manual" / "Archivo",
        "datos": "1141231231,1141231232" O "nombre_archivo_subido.csv",
        "routing_label": "MY_LABEL",
        "force": true/false,
        "fecha_inicio": "2024-04-27T12:00:00Z" (opcional)
    }
    """
    from app.modules.psx.services import extract_records, chunk_list
    from app.modules.psx.models import PSX5KJob, PSX5KTask, PSX5KDetail
    from app.modules.audit.services import add_audit_log
    
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "Missing JSON body"}), 400
        
    tarea = data.get('tarea')
    datos_tipo = data.get('datos_tipo', 'Manual')
    datos = data.get('datos')
    
    if not tarea or not datos:
        return jsonify({"status": "error", "message": "Missing required fields (tarea, datos)"}), 400

    try:
        # Extraer registros
        all_records = extract_records(datos_tipo, datos, '/home/dtovar/bayblade/c20/uploads/psx5k')
        if not all_records:
            return jsonify({"status": "error", "message": "No valid records extracted"}), 400
            
        chunk_size = current_app.config.get('PSX_CHUNK_SIZE', 200)
        chunks = list(chunk_list(all_records, chunk_size))
        
        # Crear Job (User: api_system)
        new_job = PSX5KJob(
            usuario="api_system",
            tarea=tarea,
            accion_tipo=data.get('accion_tipo', 'api_request'),
            datos_tipo=datos_tipo,
            routing_label=data.get('routing_label'),
            archivo_origen=datos if datos_tipo == 'Archivo' else 'API Manual',
            run_force=data.get('force', False)
        )
        db.session.add(new_job)
        db.session.flush()

        created_ids = []
        for i, chunk in enumerate(chunks):
            new_task = PSX5KTask(
                job_id=new_job.id,
                chunk_index=i + 1,
                chunk_total=len(chunks),
                datos=",".join(chunk),
                estado='Pendiente'
            )
            db.session.add(new_task)
            db.session.flush()
            db.session.add(PSX5KDetail(id=new_task.id, total=len(chunk)))
            created_ids.append(new_task.id)
            
        db.session.commit()
        return jsonify({
            "status": "success",
            "job_id": new_job.id,
            "task_ids": created_ids
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@api_bp.route('/tasks/<int:task_id>/cancel', methods=['POST'])
@api_key_required
def cancel_api_task(task_id):
    """
    Cancela una tarea específica si no ha terminado.
    """
    task = PSX5KTask.query.get_or_404(task_id)
    if task.estado in ['Completado', 'Terminado con Errores', 'Cancelado']:
        return jsonify({"status": "error", "message": "Task already finished"}), 400
        
    task.estado = 'Cancelada'
    db.session.commit()
    return jsonify({"status": "success", "message": f"Task {task_id} cancelled"})

@api_bp.route('/tasks/<int:task_id>', methods=['GET'])
@api_key_required
def get_task_detail(task_id):
    """
    Obtiene el detalle tecnico de una tarea especifica
    """
    task = PSX5KTask.query.get(task_id)
    if not task:
        return jsonify({
            "status": "error",
            "message": f"Tarea con ID {task_id} no encontrada"
        }), 404
        
    return jsonify({
        "status": "success",
        "data": task.to_dict()
    })
