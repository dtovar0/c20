from app import create_app, db
from app.modules.psx.models import PSX5K
from datetime import datetime, timedelta
from sqlalchemy import text

app = create_app()

with app.app_context():
    # Forzar la recreación de la tabla para asegurar consistencia
    print("🔄 Reiniciando tabla PSX5K para seeding masivo...")
    db.session.execute(text("DROP TABLE IF EXISTS psx5k"))
    db.session.commit()
    db.create_all()
    
    now = datetime.utcnow()
    
    example_tasks = [
        PSX5K(
            id=1,
            usuario="OPERADOR_ALPHA",
            accion="add",
            estado="Terminada",
            fecha_inicio=now - timedelta(days=1, hours=5),
            fecha_fin=now - timedelta(days=1, hours=4),
            datos='{"job": "LOTE_77", "type": "CRITICAL_UPDATE", "node": "NEXUS_MAIN"}'
        ),
        PSX5K(
            id=2,
            usuario="SISTEMA_AUTO",
            accion="delete",
            estado="Terminada",
            fecha_inicio=now - timedelta(hours=10),
            fecha_fin=now - timedelta(hours=9, minutes=30),
            datos='{"cleanup": "OLD_TEMP_LOGS", "size": "450MB"}'
        ),
        PSX5K(
            id=3,
            usuario="ADMIN_NEXUS",
            accion="add",
            estado="Ejecutando",
            fecha_inicio=now - timedelta(minutes=45),
            fecha_fin=None,
            datos='{"process": "NETWORK_SYNC", "progress": "65%", "priority": "HIGH"}'
        ),
        PSX5K(
            id=4,
            usuario="TECNICO_09",
            accion="add",
            estado="Programada",
            fecha_inicio=None,
            fecha_fin=None,
            datos='{"schedule": "MIDNIGHT_RUN", "task": "DB_MAINTENANCE"}'
        ),
        PSX5K(
            id=5,
            usuario="ADMIN_NEXUS",
            accion="delete",
            estado="Programada",
            fecha_inicio=now + timedelta(hours=5),
            fecha_fin=None,
            datos='{"target": "LEGACY_TABLE_B", "safety_checkpoint": "true"}'
        )
    ]
    
    db.session.add_all(example_tasks)
    db.session.commit()
    
    print(f"✅ Se han generado {len(example_tasks)} registros de prueba exitosamente.")
    print("URL de validación (Ejecutando): http://localhost:5000/api/psx/detail/3")
    print("URL de validación (Terminada): http://localhost:5000/api/psx/detail/1")
