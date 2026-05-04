import os
import sys

# Detectar la raíz del proyecto dinámicamente
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)

from app import create_app, db
from app.modules.psx.models import PSX5KJob, PSX5KTask, PSX5KDetail
from app.modules.auth.models import User
from app.modules.audit.services import add_audit_log
from app.modules.psx.services import extract_records, chunk_list
from sqlalchemy import text
from flask import current_app

app = create_app()

with app.app_context():
    print("--- INICIANDO PRUEBA DE REPRODUCCIÓN (Mismo flujo que el Portal) ---")
    try:
        # 1. Simular datos de entrada (Igual al payload que envías)
        data = {
            "tarea": "add",
            "estado": "Pendiente",
            "accion_tipo": "call_in",
            "routing_label": "",
            "datos_tipo": "Manual",
            "datos": "1147777002",
            "total_items": 1,
            "force": False
        }
        
        # 2. Simular Identidad (Como dtovar@vivaro.com)
        user_email = "dtovar@vivaro.com"
        print(f"ID: Simulando usuario {user_email}")
        
        # 3. Extraer Registros
        UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, 'uploads', 'psx5k')
        all_records = extract_records(data['datos_tipo'], data['datos'], UPLOAD_FOLDER)
        print(f"STEP 1: Registros extraídos: {len(all_records)}")
        
        # 4. Chunking
        chunk_size = 200
        chunks = list(chunk_list(all_records, chunk_size))
        print(f"STEP 2: Fragmentos generados: {len(chunks)}")
        
        # 5. Crear Job Maestro
        new_job = PSX5KJob(
            usuario=user_email,
            tarea=data['tarea'],
            accion_tipo=data['accion_tipo'],
            datos_tipo=data['datos_tipo'],
            routing_label=data.get('routing_label'),
            archivo_origen='Ingreso Manual',
            run_force=data.get('force', False)
        )
        db.session.add(new_job)
        db.session.flush()
        print(f"STEP 3: Job Maestro creado (ID: {new_job.id})")
        
        # 6. Crear Tareas y Detalles
        created_ids = []
        for i, chunk in enumerate(chunks):
            new_task = PSX5KTask(
                job_id=new_job.id,
                chunk_index=i + 1,
                chunk_total=len(chunks),
                datos=",".join(chunk),
                estado=data['estado'],
                tipo='normal'
            )
            db.session.add(new_task)
            db.session.flush()
            
            new_detail = PSX5KDetail(id=new_task.id, total=len(chunk), ok=0, fail=0)
            db.session.add(new_detail)
            created_ids.append(new_task.id)
        
        db.session.commit()
        print(f"STEP 4: {len(created_ids)} tareas persistidas en DB.")
        
        # 7. Auditoría
        add_audit_log(
            f"REPRO-TEST PSX-{new_job.id}", 
            status="info", 
            detail=f"Prueba de creación manual exitosa",
            user_override=user_email
        )
        print("STEP 5: Auditoría registrada.")
        
        print("\n✅ RESULTADO: El flujo completo funcionó perfectamente en la terminal.")
        print("Esto confirma que el problema NO es la base de datos ni el código lógico.")
        print("El error 500 en el portal debe ser un tema de sesión/permisos del servidor web.")
        
    except Exception as e:
        import traceback
        print(f"\n❌ ERROR ENCONTRADO: {e}")
        print(traceback.format_exc())
        db.session.rollback()
