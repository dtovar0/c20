from app import create_app, db
from app.modules.psx.models import PSX5KTask, PSX5KDetail
from datetime import datetime, timedelta
from sqlalchemy import text

app = create_app()

with app.app_context():
    # Reiniciar arquitectura
    print("🔄 Reiniciando arquitectura PSX5K (ID Compartido)...")
    db.session.execute(text("DROP TABLE IF EXISTS psx5k_details"))
    db.session.execute(text("DROP TABLE IF EXISTS psx5k_tasks"))
    db.session.commit()
    db.create_all()
    
    now = datetime.utcnow()
    
    # Tarea 1
    db.session.add(PSX5KTask(id=1, usuario="OPERADOR_ALPHA", accion="add", estado="Terminada", accion_tipo="Archivo"))
    db.session.add(PSX5KDetail(id=1, total=1500, ok=1498, fail=2))
    
    # Tarea 2
    db.session.add(PSX5KTask(id=2, usuario="ADMIN_NEXUS", accion="add", estado="Ejecutando", accion_tipo="Manual"))
    db.session.add(PSX5KDetail(id=2, total=50, ok=35, fail=0))
    
    # Tarea 3
    db.session.add(PSX5KTask(id=3, usuario="TECNICO_09", accion="delete", estado="Programada", accion_tipo="Manual"))
    db.session.add(PSX5KDetail(id=3, total=1, ok=0, fail=0))

    db.session.commit()
    
    print(f"✅ Seeding completado con IDs compartidos.")
