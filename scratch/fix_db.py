import os
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask import Flask

load_dotenv()

app = Flask(__name__)
db_engine = os.getenv('DB_ENGINE', 'sqlite')
if db_engine == 'mysql':
    db_uri = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
else:
    db_uri = 'sqlite:///nexus.db'

app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

def fix():
    with app.app_context():
        # Using raw SQL to be safe across engines
        try:
            print(f"Buscando modificar tabla system_config en {db_engine}...")
            db.session.execute(db.text("ALTER TABLE system_config ADD COLUMN portal_identity_type VARCHAR(10) DEFAULT 'icon'"))
            db.session.commit()
            print("✅ Columna portal_identity_type añadida exitosamente.")
        except Exception as e:
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                print("ℹ️ La columna ya existe.")
            else:
                print(f"❌ Error: {e}")
                print("Intentando recrear tablas...")
                db.drop_all()
                db.create_all()
                print("✅ Tablas recreadas desde cero.")

if __name__ == "__main__":
    fix()
