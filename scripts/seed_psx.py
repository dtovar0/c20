from app import create_app, db
from app.modules.psx.models import PSX5KTask, PSX5KDetail
from datetime import datetime, timedelta
from sqlalchemy import text

app = create_app()

with app.app_context():
    # Forzar la recreación de las tablas para asegurar consistencia con el nuevo esquema
    print("🔄 Reiniciando arquitectura PSX5K (Schema Update: accion_tipo, routing_label, etc.)...")
    db.session.execute(text("DROP TABLE IF EXISTS psx5k_details"))
    db.session.execute(text("DROP TABLE IF EXISTS psx5k_tasks"))
    db.session.commit()
    db.create_all()
    
    now = datetime.utcnow()
    
    # 1. Tarea con la nueva estructura
    task1 = PSX5KTask(
        id=1, 
        usuario="OPERADOR_ALPHA", 
        accion="add", 
        estado="Terminada", 
        accion_tipo="Archivo",
        routing_label="Ruta_Norte_V4",
        fecha_inicio=now - timedelta(days=1), 
        fecha_fin=now - timedelta(hours=23),
        datos_tipo="Lote Masivo",
        datos="Proceso de migración de nodos del sector norte."
    )
    
    db.session.add(task1)
    
    items1 = [
        PSX5KDetail(task_id=1, item_value="8147777001", item_status="Procesado"),
        PSX5KDetail(task_id=1, item_value="8147777002", item_status="Procesado"),
        PSX5KDetail(task_id=1, item_value="8147777003", item_status="Error", error_msg="Timeout on Node B")
    ]
    db.session.add_all(items1)
    
    # 2. Tarea en ejecución
    task2 = PSX5KTask(
        id=2, 
        usuario="ADMIN_NEXUS", 
        accion="add", 
        estado="Ejecutando", 
        accion_tipo="Manual",
        routing_label="Ruta_Emergencia",
        fecha_inicio=now - timedelta(minutes=15),
        datos_tipo="Nodo Crítico",
        datos="Actualización manual de prioridad para sincronización central."
    )
    db.session.add(task2)
    
    items2 = [
        PSX5KDetail(task_id=2, item_value="NODE_S_CENTRAL", item_status="Procesado"),
        PSX5KDetail(task_id=2, item_value="NODE_S_SOUTH", item_status="Pendiente")
    ]
    db.session.add_all(items2)
    
    # 3. Tarea programada
    task3 = PSX5KTask(
        id=3, 
        usuario="TECNICO_09", 
        accion="delete", 
        estado="Programada", 
        accion_tipo="Manual",
        routing_label="Limpieza_Automática",
        datos_tipo="Cleanup",
        datos="Eliminación de registros obsoletos de la base operativa."
    )
    db.session.add(task3)
    db.session.add(PSX5KDetail(task_id=3, item_value="LEGACY_STORAGE_99"))

    db.session.commit()
    
    print(f"✅ Arquitectura actualizada y datos de prueba generados exitosamente.")
    print("Validación:")
    print(" - Detalle con nuevo esquema: http://localhost:5000/api/psx/detail/1")
