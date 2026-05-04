import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

db_engine = os.getenv('DB_ENGINE', 'sqlite')
if db_engine == 'mysql':
    db_uri = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
else:
    db_uri = 'sqlite:///nexus.db'

engine = create_engine(db_uri)

def check_table(table_name):
    print(f"\n--- Columns in {table_name} ---")
    try:
        with engine.connect() as conn:
            if db_engine == 'mysql':
                res = conn.execute(text(f"SHOW COLUMNS FROM {table_name}"))
            else:
                res = conn.execute(text(f"PRAGMA table_info({table_name})"))
            for row in res:
                print(row)
    except Exception as e:
        print(f"Error checking {table_name}: {e}")

check_table('psx5k_tasks')
check_table('psx5k_jobs')
check_table('psx5k_details')
check_table('audit_logs')
