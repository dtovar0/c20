from app import create_app, db
import sqlalchemy
from sqlalchemy import text

app = create_app()
with app.app_context():
    # Check if columns exist
    inspector = sqlalchemy.inspect(db.engine)
    columns = [c['name'] for c in inspector.get_columns('psx5k_details')]
    
    if 'del' not in columns:
        print("Adding 'del' column...")
        db.session.execute(text("ALTER TABLE psx5k_details ADD COLUMN `del` INTEGER DEFAULT 0"))
    else:
        print("'del' column already exists.")
        
    if 'delcheck' not in columns:
        print("Adding 'delcheck' column...")
        db.session.execute(text("ALTER TABLE psx5k_details ADD COLUMN `delcheck` INTEGER DEFAULT 0"))
    else:
        print("'delcheck' column already exists.")
        
    db.session.commit()
    print("Migration finished.")
