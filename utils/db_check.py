import sys
import os

# Asegurar que el contexto de la app se pueda cargar
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from sqlalchemy import inspect

def check_database_schema():
    app = create_app()
    with app.app_context():
        print("🔍 INICIANDO REVISIÓN DE ESQUEMA DE BASE DE DATOS")
        print("==================================================")
        
        # 1. Obtener la estructura actual en la Base de Datos (Producción/Dev)
        inspector = inspect(db.engine)
        db_tables = set(inspector.get_table_names())
        
        # 2. Obtener la estructura definida en el Código (Modelos de SQLAlchemy)
        model_tables = set(db.Model.metadata.tables.keys())
        
        # --- TABLAS FALTANTES O SOBRANTES ---
        missing_in_db = model_tables - db_tables
        extra_in_db = db_tables - model_tables
        
        print(f"\n📁 Análisis de Tablas ({len(db_tables)} en DB, {len(model_tables)} en Código)")
        if missing_in_db:
            print("❌ Tablas DEFINIDAS en el código pero FALTAN en la Base de Datos:")
            for t in missing_in_db:
                print(f"   - {t}")
        else:
            print("✅ Todas las tablas del código existen en la base de datos.")
            
        if extra_in_db:
            print("⚠️ Tablas en la Base de Datos que NO están en los modelos (pueden ser obsoletas o backups):")
            for t in extra_in_db:
                print(f"   - {t}")
        
        # --- COLUMNAS (Para las tablas que coinciden) ---
        print("\n📄 Análisis Exhaustivo de Columnas")
        common_tables = db_tables.intersection(model_tables)
        
        issues_found = False
        for table_name in common_tables:
            # Obtener columnas de la BD real
            real_cols = {col['name'] for col in inspector.get_columns(table_name)}
            
            # Obtener columnas del modelo
            model_cols = {col.name for col in db.Model.metadata.tables[table_name].columns}
            
            missing_cols_db = model_cols - real_cols
            extra_cols_db = real_cols - model_cols
            
            if missing_cols_db or extra_cols_db:
                issues_found = True
                print(f"\n🔔 Discrepancia en tabla: {table_name}")
                if missing_cols_db:
                    print(f"   ❌ Columnas esperadas en código pero FALTAN en la DB: {missing_cols_db}")
                if extra_cols_db:
                    print(f"   ⚠️ Columnas existentes en la DB pero NO están en el código: {extra_cols_db}")
                    
        if not issues_found:
            print("✅ No se encontraron diferencias en las columnas de las tablas comunes.")
            print("\n✨ LA BASE DE DATOS Y EL CÓDIGO ESTÁN EN PERFECTA SINCRONÍA ✨")
        else:
            print("\n🚨 ATENCIÓN: Es necesario aplicar migraciones (ALTER TABLE) para solucionar las discrepancias.")

if __name__ == '__main__':
    check_database_schema()
