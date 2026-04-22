from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    try:
        db.session.execute(text('ALTER TABLE auth_config ADD COLUMN ldap_role_mappings TEXT'))
        db.session.commit()
        print("✅ Columna ldap_role_mappings añadida correctamente.")
    except Exception as e:
        print(f"❌ Error al migrar: {e}")
