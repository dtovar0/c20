from flask import Blueprint, render_template
from flask_login import login_required
from app.decorators import admin_required

audit_bp = Blueprint('audit', __name__, url_prefix='/audit')

@audit_bp.route('/')
@login_required
@admin_required
def index():
    return render_template('audit.html')
