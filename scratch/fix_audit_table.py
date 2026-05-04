import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)

from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    try:
        db.session.execute(text('ALTER TABLE audit_logs MODIFY COLUMN user VARCHAR(100)'))
        db.session.commit()
        print('✅ Tabla audit_logs actualizada (user -> 100)')
    except Exception as e:
        db.session.rollback()
        print(f'❌ Error al actualizar audit_logs: {e}')
