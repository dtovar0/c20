import os
import sys
from dotenv import load_dotenv

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

from app import create_app, db
from app.modules.audit.models import AuditLog

app = create_app()
with app.app_context():
    total_logs = AuditLog.query.count()
    per_page = 20
    pages = (total_logs + per_page - 1) // per_page
    print(f"Total Logs: {total_logs}")
    print(f"Registros por página: {per_page}")
    print(f"Total de páginas esperadas: {pages}")
