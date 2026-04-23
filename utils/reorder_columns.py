import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE users MODIFY COLUMN nombre VARCHAR(100) DEFAULT NULL AFTER username;"))
            print("✅ Columna 'nombre' movida después de 'username'.")
            
            conn.execute(text("ALTER TABLE users MODIFY COLUMN auth_source VARCHAR(10) DEFAULT 'local' AFTER password_hash;"))
            print("✅ Columna 'auth_source' movida antes de 'role'.")
        except Exception as e:
            print(f"❌ Error reorganizando columnas: {e}")
