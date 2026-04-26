import sqlite3
import os

db_path = 'nexus.db'
if not os.path.exists(db_path):
    print(f"File {db_path} not found.")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, username, nombre, role FROM users;")
        rows = cursor.fetchall()
        print("--- USUARIOS EN NEXUS.DB ---")
        for row in rows:
            print(f"ID: {row[0]} | Username: {row[1]} | Nombre: {row[2]} | Role: {row[3]}")
    except Exception as e:
        print(f"Error: {e}")
    conn.close()
