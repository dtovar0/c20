from flask import Blueprint, request, jsonify, render_template
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
from app import db
from .models import PSX5KTask, PSX5KDetail
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
    Lista de tareas PSX5K para la tabla principal
    """
    tasks = PSX5KTask.query.order_by(PSX5KTask.created_at.desc()).all()
    return jsonify({
        "status": "success",
        "tasks": [t.to_dict() for t in tasks]
    })

@psx_bp.route('/detail/<int:task_id>')
@login_required
def task_detail(task_id):
    """
    Vista independiente para el detalle de una tarea PSX5K
    """
    task = PSX5KTask.query.get_or_404(task_id)
    return render_template('psx_detail.html', task=task)

@psx_bp.route('/stats')
@login_required
def get_stats():
    """
    Retorna estadísticas de tareas filtradas por el usuario actual
    """
    try:
        username = current_user.username
        
        # 1. Total de tareas del usuario
        total_tareas = PSX5KTask.query.filter_by(usuario=username).count()
        
        # 2. Tareas Pendientes (Programada o Pendiente)
        pendientes = PSX5KTask.query.filter(
            PSX5KTask.usuario == username,
            PSX5KTask.estado.in_(['Programada', 'Pendiente'])
        ).count()
        
        # 3. Tareas Programadas (Estado Pendiente según solicitud del usuario)
        programadas = PSX5KTask.query.filter_by(usuario=username, estado='Pendiente').count()
        
        # 4. Tarea Activa (La más reciente con estado Ejecutando)
        activa = PSX5KTask.query.filter_by(usuario=username, estado='Ejecutando').order_by(PSX5KTask.created_at.desc()).first()
        
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
        return jsonify({"status": "error", "message": str(e)}), 500

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
        raw_accion = data.get('datos_tipo') if raw_tarea != 'delete' else 'delete' 
        raw_origen = data.get('accion_tipo') # Archivo / Manual
        
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
        
        created_ids = []
        base_name = data.get('tarea_name') or f"Tarea_{raw_tarea}"

        for i, chunk in enumerate(chunks):
            # --- LÓGICA DE PERSISTENCIA SEGÚN ORIGEN ---
            if raw_origen == 'Archivo':
                # Crear un archivo físico para este chunk
                import uuid
                chunk_filename = f"chunks/chunk_{uuid.uuid4().hex}.csv"
                chunk_path = os.path.join('/home/dtovar/bayblade/c20/uploads/psx5k', chunk_filename)
                
                with open(chunk_path, 'w') as f:
                    f.write("\n".join(chunk))
                
                task_data_value = chunk_filename
            else:
                task_data_value = ",".join(chunk)
            
            new_task = PSX5KTask(
                usuario=current_user.username,
                tarea=raw_tarea, # 'add' o 'delete' únicamente
                accion_tipo=raw_accion, 
                datos_tipo=raw_origen, 
                routing_label=data.get('routing_label'),
                datos=task_data_value, 
                force=data.get('force', False)
            )
            db.session.add(new_task)
            db.session.flush()
            
            # Registro individual en auditoría
            add_audit_log("tarea creada", status="info", detail=f"ID: {new_task.id} | {raw_origen} | Parte {i+1}/{total_chunks}")
            
            new_detail = PSX5KDetail(id=new_task.id, total=len(chunk), ok=0, fail=0)
            db.session.add(new_detail)
            created_ids.append(new_task.id)
            
        db.session.commit()
        add_audit_log("tarea creada", status="info", detail=f"{raw_origen} chunked - {total_chunks} partes")
        
        return jsonify({
            "status": "success",
            "message": f"Se han generado {total_chunks} mini-tareas correctamente",
            "task_ids": created_ids
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@psx_bp.route('/upload', methods=['POST'])
def upload_file():
    """
    Endpoint para recibir, etiquetar y almacenar archivos del terminal PSX5K
    """
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


