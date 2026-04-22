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
    Crea una nueva tarea PSX5K en la base de datos
    """
    data = request.json
    try:
        new_task = PSX5KTask(
            usuario=current_user.username,
            tarea=data.get('tarea'),
            estado=data.get('estado', 'Pendiente'),
            accion_tipo=data.get('accion_tipo'),
            routing_label=data.get('routing_label'),
            datos_tipo=data.get('datos_tipo'),
            datos=data.get('datos'),
            force=data.get('force', False),
            fecha_inicio=datetime.datetime.now() if data.get('estado') == 'Ejecutando' else None
        )
        db.session.add(new_task)
        db.session.flush() # Para obtener el ID
        
        # Crear detalle inicial (contadores en 0)
        new_detail = PSX5KDetail(
            id=new_task.id,
            total=data.get('total_items', 0),
            ok=0,
            fail=0
        )
        db.session.add(new_detail)
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "Tarea creada correctamente",
            "task_id": new_task.id
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


