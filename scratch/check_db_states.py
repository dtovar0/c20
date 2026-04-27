import os
import sys
from dotenv import load_dotenv

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

from app import create_app, db
from app.modules.psx.models import PSX5KTask
from datetime import datetime

app = create_app()
with app.app_context():
    now = datetime.now()
    print(f"Server Time (Local): {now}")
    
    tasks = db.session.query(PSX5KTask.id, PSX5KTask.fecha_inicio).order_by(PSX5KTask.fecha_inicio.desc()).limit(10).all()
    print("\nÚltimas 10 tareas por fecha_inicio (DESC):")
    for tid, f in tasks:
        print(f" - ID: {tid} | Fecha: {f}")

    future_tasks = PSX5KTask.query.filter(PSX5KTask.fecha_inicio > now).count()
    print(f"\nTareas con fecha mayor a 'now' del servidor: {future_tasks}")
