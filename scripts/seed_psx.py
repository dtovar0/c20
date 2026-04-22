from app import create_app, db
from app.modules.psx.models import PSX5K
from datetime import datetime, timedelta
from sqlalchemy import text

app = create_app()

with app.app_context():
    # Forzar la recreación de la tabla para asegurar consistencia
    print("🔄 Reiniciando tabla PSX5K para seeding con nuevos estados...")
    db.session.execute(text("DROP TABLE IF EXISTS psx5k"))
    db.session.commit()
    db.create_all()
    
    now = datetime.utcnow()
    
    example_tasks = [
        PSX5K(id=1, usuario="OPERADOR_ALPHA", accion="add", estado="Terminada", 
              fecha_inicio=now - timedelta(days=1), fecha_fin=now - timedelta(hours=23),
              datos='{"job": "LOTE_77", "node": "NEXUS_MAIN"}'),
              
        PSX5K(id=2, usuario="SISTEMA_AUTO", accion="delete", estado="Terminada", 
              fecha_inicio=now - timedelta(hours=5), fecha_fin=now - timedelta(hours=4),
              datos='{"cleanup": "OLD_TEMP_LOGS"}'),
              
        PSX5K(id=3, usuario="ADMIN_NEXUS", accion="add", estado="Ejecutando", 
              fecha_inicio=now - timedelta(minutes=20), fecha_fin=None,
              datos='{"process": "NETWORK_SYNC", "progress": "45%"}'),
              
        PSX5K(id=4, usuario="TECNICO_09", accion="add", estado="Programada", 
              fecha_inicio=now + timedelta(hours=2), fecha_fin=None,
              datos='{"schedule": "MIDNIGHT_RUN"}'),
              
        PSX5K(id=5, usuario="ADMIN_NEXUS", accion="delete", estado="Programada", 
              fecha_inicio=now + timedelta(days=1), fecha_fin=None,
              datos='{"target": "LEGACY_DATA"}'),
              
        PSX5K(id=6, usuario="SISTEMA_AUTO", accion="add", estado="Pendiente", 
              fecha_inicio=None, fecha_fin=None,
              datos='{"reason": "WAITING_IN_QUEUE"}')
    ]
    
    db.session.add_all(example_tasks)
    db.session.commit()
    
    print(f"✅ Se han generado {len(example_tasks)} registros de prueba.")
    print("URLs de Verificación:")
    print(" - Pendiente (Gris): http://localhost:5000/api/psx/detail/6")
    print(" - Programada (Violeta): http://localhost:5000/api/psx/detail/4")
