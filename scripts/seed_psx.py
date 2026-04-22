from app import create_app, db
from app.modules.psx.models import PSX5KTask, PSX5KDetail
from datetime import datetime, timedelta
from sqlalchemy import text

app = create_app()

with app.app_context():
    # Forzar la recreación de las tablas para asegurar consistencia
    print("🔄 Reiniciando arquitectura PSX5K (Tasks + Details)...")
    db.session.execute(text("DROP TABLE IF EXISTS psx5k_details"))
    db.session.execute(text("DROP TABLE IF EXISTS psx5k_tasks"))
    db.session.execute(text("DROP TABLE IF EXISTS psx5k")) # Antigua tabla
    db.session.commit()
    db.create_all()
    
    now = datetime.utcnow()
    
    # 1. Tarea con múltiples items (Simulando archivo)
    task1 = PSX5KTask(id=1, usuario="OPERADOR_ALPHA", accion="add", estado="Terminada", tipo="Archivo",
                     fecha_inicio=now - timedelta(days=1), fecha_fin=now - timedelta(hours=23),
                     config_json='{"node": "NODE_MASTER", "retries": 3}')
    
    db.session.add(task1)
    
    items1 = [
        PSX5KDetail(task_id=1, item_value="8147777001", item_status="Procesado"),
        PSX5KDetail(task_id=1, item_value="8147777002", item_status="Procesado"),
        PSX5KDetail(task_id=1, item_value="8147777003", item_status="Error", error_msg="Timeout on Node B")
    ]
    db.session.add_all(items1)
    
    # 2. Tarea en ejecución
    task2 = PSX5KTask(id=2, usuario="ADMIN_NEXUS", accion="add", estado="Ejecutando", tipo="Manual",
                     fecha_inicio=now - timedelta(minutes=15), config_json='{"priority": "HIGH"}')
    db.session.add(task2)
    
    items2 = [
        PSX5KDetail(task_id=2, item_value="NODE_S_CENTRAL", item_status="Procesado"),
        PSX5KDetail(task_id=2, item_value="NODE_S_SOUTH", item_status="Pendiente")
    ]
    db.session.add_all(items2)
    
    # 3. Tarea programada
    task3 = PSX5KTask(id=3, usuario="TECNICO_09", accion="delete", estado="Programada", tipo="Manual",
                     config_json='{"safe_delete": true}')
    db.session.add(task3)
    db.session.add(PSX5KDetail(task_id=3, item_value="LEGACY_STORAGE_99"))

    db.session.commit()
    
    print(f"✅ Arquitectura normalizada desplegada exitosamente.")
    print("Validación:")
    print(" - Detalle con items: http://localhost:5000/api/psx/detail/1")
