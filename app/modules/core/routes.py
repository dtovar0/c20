from flask import Blueprint, render_template, send_from_directory, current_app
from flask_login import login_required, current_user
from app import db
from app.decorators import admin_required
from app.modules.audit.models import AuditLog
import os

core_bp = Blueprint("core", __name__, url_prefix="/")

@core_bp.route("/")
@login_required
def index():
    try:
        from flask import request
        page = request.args.get('page', 1, type=int)
        
        # Vista Táctica de Usuario: Últimos 20 logs únicamente, divididos en 2 páginas de 10
        subq = db.session.query(AuditLog.id).filter_by(user=current_user.email)\
                                            .order_by(AuditLog.timestamp.desc()).limit(20).subquery()
        pagination = AuditLog.query.filter(AuditLog.id.in_(db.session.query(subq)))\
                                   .order_by(AuditLog.timestamp.desc())\
                                   .paginate(page=page, per_page=10, error_out=False)
                                   
        return render_template("index.html", activity=pagination.items, pagination=pagination)
    except Exception as e:
        current_app.logger.error(f"Error en index: {e}")
        return render_template("index.html", activity=[], pagination=None)

@core_bp.route("/dashboard-2")
@login_required
@admin_required
def dashboard_2():
    try:
        from flask import request
        page = request.args.get('page', 1, type=int)
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        # Vista Táctica: Últimos 20 logs únicamente, divididos en 2 páginas de 10
        subq = db.session.query(AuditLog.id).order_by(AuditLog.timestamp.desc()).limit(20).subquery()
        pagination = AuditLog.query.filter(AuditLog.id.in_(db.session.query(subq))).order_by(AuditLog.timestamp.desc()).paginate(page=page, per_page=10, error_out=False)
            
        return render_template("dashboard_2.html", 
                               activity=pagination.items, 
                               pagination=pagination)
    except Exception as e:
        current_app.logger.error(f"Error en dashboard_2: {e}")
        return "Internal Error", 500

@core_bp.route("/psx5k")
@login_required
def psx5k():
    try:
        return render_template("psx5k.html")
    except Exception as e:
        current_app.logger.error(f"Error en psx5k: {e}")
        return "Internal Error", 500

@core_bp.route('/assets/<path:filename>')
def serve_assets(filename):
    """Handler oficial de assets migrado al Core Blueprint"""
    try:
        return send_from_directory(os.path.join(current_app.root_path, '../assets'), filename)
    except Exception as e:
        current_app.logger.error(f"Error sirviendo asset {filename}: {e}")
        return "Asset not found", 404
