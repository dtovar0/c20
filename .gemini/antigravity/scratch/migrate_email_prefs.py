from app import create_app, db
from sqlalchemy import text
import sys

app = create_app()

def migrate():
    with app.app_context():
        print("Iniciando migración de pref_email_notifications...")
        try:
            result = db.session.execute(text("SHOW COLUMNS FROM users"))
            columns = [row[0] for row in result.fetchall()]
            
            if 'pref_email_notifications' not in columns:
                db.session.execute(text("ALTER TABLE users ADD COLUMN pref_email_notifications BOOLEAN DEFAULT 1"))
                db.session.commit()
                print("Columna pref_email_notifications añadida.")
            else:
                print("La columna ya existe.")
        except Exception as e:
            print(f"Error: {e}")
            db.session.rollback()
            sys.exit(1)

if __name__ == "__main__":
    migrate()
