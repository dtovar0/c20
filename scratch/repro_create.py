import os
import sys
# Add app to path
sys.path.append('/home/dtovar/bayblade/c20')

from app import create_app, db
from app.modules.psx.models import PSX5KJob, PSX5KTask, PSX5KDetail
from app.modules.auth.models import User
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        # Simulate current_user
        user = User.query.filter_by(role='administrador').first()
        if not user:
            user = User(email='test@vivaro.com', nombre='Test', role='administrador')
            db.session.add(user)
            db.session.commit()
        
        print(f"Using user: {user.email}")
        
        # Payload simulation
        raw_tarea = 'add'
        raw_accion = 'call_in'
        raw_origen = 'Manual'
        all_records = ['1234567890', '0987654321']
        
        # 1. Crear Job Maestro
        new_job = PSX5KJob(
            usuario=user.email,
            tarea=raw_tarea,
            accion_tipo=raw_accion,
            datos_tipo=raw_origen,
            routing_label='TEST_LABEL',
            archivo_origen='Ingreso Manual',
            run_force=False
        )
        db.session.add(new_job)
        db.session.flush()
        print(f"Job created with ID: {new_job.id}")
        
        # 2. Crear Task
        new_task = PSX5KTask(
            job_id=new_job.id,
            chunk_index=1,
            chunk_total=1,
            datos="1234567890,0987654321",
            estado='Pendiente'
        )
        db.session.add(new_task)
        db.session.flush()
        print(f"Task created with ID: {new_task.id}")
        
        # 3. Crear Detail
        new_detail = PSX5KDetail(id=new_task.id, total=2, ok=0, fail=0)
        db.session.add(new_detail)
        db.session.flush()
        print(f"Detail created with ID: {new_detail.id}")
        
        db.session.commit()
        print("Test successful!")
        
    except Exception as e:
        import traceback
        print(f"Test failed: {e}")
        print(traceback.format_exc())
        db.session.rollback()
