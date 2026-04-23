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

            # 3. Agregar columna nombre si no existe
            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN nombre VARCHAR(100) DEFAULT NULL;"))
                print("✅ Columna nombre agregada.")
            except Exception as e:
                print(f"ℹ️ Columna nombre ya existía (ignorando): {e}")

            # 4. Expandir username de 50 a 120 (para soportar correos LDAP largos)
            try:
                conn.execute(text("ALTER TABLE users MODIFY username VARCHAR(120) NOT NULL;"))
                print("✅ Columna username expandida a VARCHAR(120).")
            except Exception as e:
                print(f"❌ Error al expandir username: {e}")

            # 5. Desbloquear el candado NOT NULL de password_hash (esencial para LDAP shadow users)
            try:
                conn.execute(text("ALTER TABLE users MODIFY COLUMN password_hash VARCHAR(255) NULL;"))
                print("✅ Columna password_hash desprotegida (permite ahora claves foráneas vacías).")
            except Exception as e:
                print(f"❌ Error al desbloquear candado de password_hash: {e}")

            # 6. Reordenamiento visual estético
            try:
                conn.execute(text("ALTER TABLE users MODIFY COLUMN nombre VARCHAR(100) DEFAULT NULL AFTER username;"))
                print("✅ Columna nombre movida estéticamente después de username.")
            except Exception as e:
                print(f"ℹ️ Error u omisión al reordenar nombre: {e}")

            try:
                conn.execute(text("ALTER TABLE users MODIFY COLUMN auth_source VARCHAR(10) DEFAULT 'local' AFTER password_hash;"))
                print("✅ Columna auth_source movida estéticamente antes de role.")
            except Exception as e:
                print(f"ℹ️ Error u omisión al reordenar auth_source: {e}")

if __name__ == '__main__':
    print("🚀 Iniciando Consolidación de Migración V2.6 para Producción...")
    migrate_db()
