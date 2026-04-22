from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.decorators import admin_required
from app.modules.audit.models import AuditLog

core_bp = Blueprint("core", __name__, url_prefix="/")

@core_bp.route("/")
@login_required
def index():
    # Obtener los últimos 12 logs de auditoría del usuario actual (2 páginas de 6)
    recent_activity = AuditLog.query.filter_by(user=current_user.username)\
                                    .order_by(AuditLog.timestamp.desc())\
                                    .limit(12).all()
    return render_template("index.html", activity=recent_activity)

@core_bp.route("/dashboard-2")
@login_required
@admin_required
def dashboard_2():
    return render_template("dashboard_2.html")

@core_bp.route("/psx5k")
@login_required
def psx5k():
    return render_template("psx5k.html")
