import sys
import os

# Agrega la ruta base del proyecto explícitamente para asegurar que los módulos de app se puedan importar
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from sqlalchemy import text

def migrate_db():
    app = create_app()
    with app.app_context():
        with db.engine.connect() as conn:
            # 1. Quitar el constraint UNIQUE de email si existe (a veces MySQL arroja error si intentamos quitar la columna directamente dependiendo de las key)
            try:
                conn.execute(text("ALTER TABLE users DROP INDEX email;"))
                print("✅ Constraint UNIQUE de email eliminado.")
            except Exception as e:
                print(f"ℹ️ Constraint email no requiere cambios: {e}")

            # 2. Quitar la columna email
            try:
                conn.execute(text("ALTER TABLE users DROP COLUMN email;"))
                print("✅ Columna email eliminada permanentemente.")
            except Exception as e:
                print(f"ℹ️ Columna email no encontrada o ya eliminada: {e}")

            # 3. Agregar columna nombre
            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN nombre VARCHAR(100) DEFAULT NULL;"))
                print("✅ Columna nombre agregada.")
            except Exception as e:
                print(f"ℹ️ Columna nombre ya existía o error: {e}")

if __name__ == '__main__':
    migrate_db()
