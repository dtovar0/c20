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
