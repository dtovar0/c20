import os
import sys
from dotenv import load_dotenv

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

from app import create_app, db
from app.modules.psx.models import PSX5KTask, PSX5KJob

app = create_app()
with app.app_context():
    last_tasks = PSX5KTask.query.order_by(PSX5KTask.id.desc()).limit(5).all()
    print("Últimas 5 tareas creadas:")
    for t in last_tasks:
        print(f" - ID: {t.id} | Estado: {t.estado} | Job ID: {t.job_id}")
    
    # Intentar fixear las huerfanas para que sean visibles
    # Buscamos el admin o el primer usuario
    from app.modules.auth.models import User
    admin = User.query.first()
    if admin:
        print(f"\nIntentando migrar tareas huérfanas al usuario: {admin.email}")
        # Crear un Job Genérico para las huerfanas
        gen_job = PSX5KJob(
            usuario=admin.email,
            tarea='legacy',
            accion_tipo='N/A',
            datos_tipo='Legacy',
            archivo_origen='Antiguo sistema'
        )
        db.session.add(gen_job)
        db.session.flush()
        
        huerfanas = PSX5KTask.query.filter(PSX5KTask.job_id == None).all()
        for t in huerfanas:
            t.job_id = gen_job.id
        
        db.session.commit()
        print(f"¡Migradas {len(huerfanas)} tareas huérfanas al Job #{gen_job.id}!")
    else:
        print("\nNo se encontró un usuario para migrar.")
