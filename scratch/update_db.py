import sqlite3
import os

db_path = 'nexus.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE psx5k_details ADD COLUMN 'del' INTEGER DEFAULT 0;")
        print("Column 'del' added.")
    except sqlite3.OperationalError:
        print("Column 'del' already exists or error.")
    
    try:
        cursor.execute("ALTER TABLE psx5k_details ADD COLUMN delcheck INTEGER DEFAULT 0;")
        print("Column delcheck added.")
    except sqlite3.OperationalError:
        print("Column delcheck already exists or error.")
    
    conn.commit()
    conn.close()
else:
    print("Database not found.")
