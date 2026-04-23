import sys
import os

# Añadir el raíz del proyecto al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from sqlalchemy import inspect, text

def validate_and_update_db():
    app = create_app()
    with app.app_context():
        engine = db.engine
        inspector = inspect(engine)
        
        # Obtener todas las tablas en la base de datos
        existing_tables = inspector.get_table_names()
        
        print("🚀 Validando estructura de la base de datos...")
        
        # Obtener todas las tablas requeridas por los modelos
        for table_name, table_obj in db.metadata.tables.items():
            if table_name not in existing_tables:
                print(f"⚠️ La tabla '{table_name}' no existe. db.create_all() la creará.")
                db.create_all()
                continue
                
            # Obtener las columnas existentes en la DB
            existing_columns = {col['name'] for col in inspector.get_columns(table_name)}
            
            # Obtener las columnas definidas en el modelo
            model_columns = {col.name: col for col in table_obj.columns}
            
            # Identificar columnas faltantes
            missing_columns = set(model_columns.keys()) - existing_columns
            
            if missing_columns:
                print(f"\n⚡ Actualizando tabla '{table_name}'...")
                for col_name in missing_columns:
                    col_obj = model_columns[col_name]
                    # Construir el tipo de dato SQL (básico)
                    col_type = col_obj.type.compile(engine.dialect)
                    
                    # Construir el query
                    query = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"
                    
                    try:
                        print(f"  Ejecutando: {query}")
                        with engine.connect() as conn:
                            conn.execute(text(query))
                            conn.commit()
                        print(f"  ✅ Columna '{col_name}' añadida exitosamente.")
                    except Exception as e:
                        print(f"  ❌ Error al añadir '{col_name}': {e}")
            else:
                pass
                
        print("\n✅ Validación y estructura completada.")

if __name__ == '__main__':
    validate_and_update_db()
