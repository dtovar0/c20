import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        result = conn.execute(text("DESCRIBE users;"))
        for row in result:
            print(row)
