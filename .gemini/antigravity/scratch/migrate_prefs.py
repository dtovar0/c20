from app import create_app, db
from sqlalchemy import text
import sys

app = create_app()

def migrate():
    with app.app_context():
        print("Iniciando migración de tabla 'users'...")
        try:
            # Check if columns already exist to avoid errors
            result = db.session.execute(text("SHOW COLUMNS FROM users"))
            columns = [row[0] for row in result.fetchall()]
            
            if 'pref_notifications' not in columns:
                print("Añadiendo pref_notifications...")
                db.session.execute(text("ALTER TABLE users ADD COLUMN pref_notifications BOOLEAN DEFAULT 1"))
            
            if 'pref_refresh_interval' not in columns:
                print("Añadiendo pref_refresh_interval...")
                db.session.execute(text("ALTER TABLE users ADD COLUMN pref_refresh_interval INTEGER DEFAULT 60"))
            
            if 'pref_tour_enabled' not in columns:
                print("Añadiendo pref_tour_enabled...")
                db.session.execute(text("ALTER TABLE users ADD COLUMN pref_tour_enabled BOOLEAN DEFAULT 1"))
                
            db.session.commit()
            print("Migración completada con éxito.")
        except Exception as e:
            print(f"Error durante la migración: {e}")
            db.session.rollback()
            sys.exit(1)

if __name__ == "__main__":
    migrate()
