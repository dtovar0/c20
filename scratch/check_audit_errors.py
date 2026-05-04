import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)

from app import create_app, db
from app.modules.audit.models import AuditLog

app = create_app()
with app.app_context():
    print("--- ÚLTIMOS ERRORES REGISTRADOS EN AUDITORÍA ---")
    logs = AuditLog.query.filter(AuditLog.status=='error').order_by(AuditLog.id.desc()).limit(10).all()
    if not logs:
        print("No se encontraron errores en la tabla audit_logs.")
    for l in logs:
        print(f"[{l.timestamp}] {l.action}: {l.detail}")
