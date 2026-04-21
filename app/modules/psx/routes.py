from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os

psx_bp = Blueprint('psx', __name__, url_prefix='/api/psx')

# Configuración de carga
UPLOAD_FOLDER = '/home/dtovar/bayblade/c20/uploads/psx5k'
ALLOWED_EXTENSIONS = {'xml', 'csv'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@psx_bp.route('/upload', methods=['POST'])
def upload_file():
    """
    Endpoint para recibir y almacenar archivos del terminal PSX5K
    """
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No se detectó parte de archivo"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"status": "error", "message": "No se seleccionó ningún archivo"}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Asegurar que el directorio existe
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)
            
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(save_path)
        
        return jsonify({
            "status": "success", 
            "message": "Archivo cargado correctamente",
            "filename": filename,
            "path": save_path
        }), 200
    
    return jsonify({"status": "error", "message": "Extensión de archivo no permitida (Solo XML/CSV)"}), 400
