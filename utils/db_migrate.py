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

            # 6. Agregar columnas de preferencias si no existen
            pref_columns = [
                ("pref_notifications", "TINYINT(1) DEFAULT 1"),
                ("pref_refresh_interval", "INT DEFAULT 60"),
                ("pref_tour_enabled", "TINYINT(1) DEFAULT 1"),
                ("pref_email_notifications", "TINYINT(1) DEFAULT 1"),
                ("pref_status_colors", "TEXT DEFAULT NULL")
            ]

            for col_name, col_type in pref_columns:
                try:
                    conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type};"))
                    print(f"✅ Columna {col_name} agregada.")
                except Exception as e:
                    print(f"ℹ️ Columna {col_name} ya existía u omitida: {e}")

            # 7. Reordenamiento visual estético
            try:
                conn.execute(text("ALTER TABLE users MODIFY COLUMN nombre VARCHAR(100) DEFAULT NULL AFTER username;"))
                conn.execute(text("ALTER TABLE users MODIFY COLUMN pref_notifications TINYINT(1) DEFAULT 1 AFTER created_at;"))
                conn.execute(text("ALTER TABLE users MODIFY COLUMN pref_refresh_interval INT DEFAULT 60 AFTER pref_notifications;"));
                conn.execute(text("ALTER TABLE users MODIFY COLUMN pref_tour_enabled TINYINT(1) DEFAULT 1 AFTER pref_refresh_interval;"))
                conn.execute(text("ALTER TABLE users MODIFY COLUMN pref_email_notifications TINYINT(1) DEFAULT 1 AFTER pref_tour_enabled;"))
                conn.execute(text("ALTER TABLE users MODIFY COLUMN pref_status_colors TEXT DEFAULT NULL AFTER pref_email_notifications;"))
                print("✅ Reordenamiento estético de columnas completado.")
            except Exception as e:
                print(f"ℹ️ Error u omisión al reordenar columnas: {e}")

if __name__ == '__main__':
    print("🚀 Iniciando Consolidación de Migración V3.0 para Producción...")
    migrate_db()
