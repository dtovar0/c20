import sys
import os

# Asegurar que el contexto de la app se pueda cargar
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from sqlalchemy import inspect, text

def check_database_schema(auto_fix=True):
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
            
            if auto_fix:
                print("🛠️  AUTOREPARACIÓN: Creando tablas faltantes...")
                db.create_all()
                print("✅ Tablas creadas con éxito.")
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
                
                # Column references for auto-fix
                model_col_objects = {col.name: col for col in db.Model.metadata.tables[table_name].columns}
                
                if missing_cols_db:
                    print(f"   ❌ Columnas esperadas en código pero FALTAN en la DB: {missing_cols_db}")
                    if auto_fix:
                        for col_name in missing_cols_db:
                            col_obj = model_col_objects[col_name]
                            # Intentar inferir el tipo de dato para DDL
                            try:
                                compiled_type = col_obj.type.compile(db.engine.dialect)
                                alter_sql = f"ALTER TABLE `{table_name}` ADD COLUMN `{col_name}` {compiled_type}"
                                db.session.execute(text(alter_sql))
                                print(f"     🔨 AUTOREPARACIÓN: Añadida columna `{col_name}` a `{table_name}`")
                            except Exception as e:
                                print(f"     ⚠️ Fallo al añadir columna `{col_name}`: {e}")
                            
                if extra_cols_db:
                    print(f"   ⚠️ Columnas existentes en la DB pero NO están en el código: {extra_cols_db}")
                    if auto_fix:
                        for col_name in extra_cols_db:
                            try:
                                alter_sql = f"ALTER TABLE `{table_name}` DROP COLUMN `{col_name}`"
                                db.session.execute(text(alter_sql))
                                print(f"     🔨 AUTOREPARACIÓN: Eliminada columna basura `{col_name}` de `{table_name}`")
                            except Exception as e:
                                print(f"     ⚠️ Fallo al eliminar columna `{col_name}`: {e}")
                                
                if auto_fix:
                    db.session.commit()
                    
        if not issues_found:
            print("✅ No se encontraron diferencias en las columnas de las tablas comunes.")
            print("\n✨ LA BASE DE DATOS Y EL CÓDIGO ESTÁN EN PERFECTA SINCRONÍA ✨")
        else:
            if auto_fix:
                print("\n✅ AUTOREPARACIÓN COMPLETADA: La base de datos ha sido sincronizada con tu código.")
            else:
                print("\n🚨 ATENCIÓN: Es necesario aplicar migraciones (ALTER TABLE) para solucionar las discrepancias.")

if __name__ == '__main__':
    # Ejecutamos con auto-fix activado por defecto mediante el argumento sys
    import sys
    auto_fix = '--fix' in sys.argv or True # En true por defecto para acatar mandato
    check_database_schema(auto_fix)

