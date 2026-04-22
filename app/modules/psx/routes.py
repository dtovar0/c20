from flask import Blueprint, request, jsonify, render_template
from flask_login import current_user, login_required
from .models import PSX5K
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
    tasks = PSX5K.query.order_by(PSX5K.created_at.desc()).all()
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
    task = PSX5K.query.get_or_404(task_id)
    return render_template('psx_detail.html', task=task)

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


