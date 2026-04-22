from app import create_app, db
from app.modules.psx.models import PSX5K
from datetime import datetime, timedelta

app = create_app()

with app.app_context():
    from sqlalchemy import text
    # Forzar la recreación de la tabla para incluir los nuevos campos (usuario, datos)
    print("🔄 Sincronizando esquema de tabla PSX5K...")
    db.session.execute(text("DROP TABLE IF EXISTS psx5k"))
    db.session.commit()
    db.create_all()

    # Generar dato de ejemplo
    test_task = PSX5K(
        id=1,
        usuario="ADMIN_NEXUS",
        accion="add",
        estado="Ejecutando",
        fecha_inicio=datetime.utcnow() - timedelta(hours=2),
        fecha_fin=None,
        datos='{"protocol": "SECURE_LNK", "payload": "BATCH_UPLOAD_0422", "nodes": ["NODE_A", "NODE_B"], "encryption": "AES-256", "priority": "CRITICAL"}'
    )
    
    db.session.add(test_task)
    db.session.commit()
    
    print("✅ Dato de ejemplo generado exitosamente en la tabla psx5k.")
    print("URL de validación: http://localhost:5000/api/psx/detail/1")
