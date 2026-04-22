from flask import Blueprint, render_template, jsonify
from flask_login import login_required
from app.decorators import admin_required
from .models import AuditLog

audit_bp = Blueprint('audit', __name__, url_prefix='/audit')

@audit_bp.route('/')
@login_required
@admin_required
def index():
    return render_template('audit.html')

@audit_bp.route('/api/list')
@login_required
@admin_required
def list_audit():
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(500).all()
    return jsonify({
        "status": "success",
        "logs": [log.to_dict() for log in logs]
    })
