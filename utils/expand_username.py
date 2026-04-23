import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        conn.execute(text("ALTER TABLE users MODIFY username VARCHAR(120) NOT NULL;"))
        print("username expanded to 120.")
