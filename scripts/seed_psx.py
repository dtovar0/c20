from app import create_app, db
from app.modules.psx.models import PSX5KTask, PSX5KDetail
from datetime import datetime, timedelta
from sqlalchemy import text

app = create_app()

with app.app_context():
    # Forzar la recreación de las tablas para asegurar consistencia con contadores
    print("🔄 Reiniciando arquitectura PSX5K (Schema Update: Contadores en Details)...")
    db.session.execute(text("DROP TABLE IF EXISTS psx5k_details"))
    db.session.execute(text("DROP TABLE IF EXISTS psx5k_tasks"))
    db.session.commit()
    db.create_all()
    
    now = datetime.utcnow()
    
    # 1. Tarea Finalizada con contadores
    task1 = PSX5KTask(id=1, usuario="OPERADOR_ALPHA", accion="add", estado="Terminada", accion_tipo="Archivo",
                     routing_label="Ruta_Norte_V4", fecha_inicio=now - timedelta(days=1), 
                     fecha_fin=now - timedelta(hours=23), datos_tipo="Lote Masivo")
    db.session.add(task1)
    db.session.add(PSX5KDetail(task_id=1, total=1500, ok=1498, fail=2))
    
    # 2. Tarea en ejecución con progreso parcial
    task2 = PSX5KTask(id=2, usuario="ADMIN_NEXUS", accion="add", estado="Ejecutando", accion_tipo="Manual",
                     routing_label="Ruta_Emergencia", fecha_inicio=now - timedelta(minutes=15), 
                     datos_tipo="Nodo Crítico")
    db.session.add(task2)
    db.session.add(PSX5KDetail(task_id=2, total=50, ok=35, fail=0))
    
    # 3. Tarea programada (contadores en 0)
    task3 = PSX5KTask(id=3, usuario="TECNICO_09", accion="delete", estado="Programada", accion_tipo="Manual",
                     routing_label="Limpieza_Automática")
    db.session.add(task3)
    db.session.add(PSX5KDetail(task_id=3, total=1, ok=0, fail=0))

    db.session.commit()
    
    print(f"✅ Arquitectura de contadores desplegada exitosamente.")
