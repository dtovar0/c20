from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from .models import AuditLog

audit_bp = Blueprint('audit', __name__, url_prefix='/audit')

@audit_bp.route('/')
@login_required
def index():
    return render_template('audit.html')

@audit_bp.route('/api/list')
@login_required
def list_audit():
    # If not admin, filter by current username
    if current_user.role != 'administrador':
        query = AuditLog.query.filter_by(user=current_user.username)
    else:
        query = AuditLog.query

    logs = query.order_by(AuditLog.timestamp.desc()).limit(500).all()
    
    return jsonify({
        "status": "success",
        "logs": [log.to_dict() for log in logs]
    })
