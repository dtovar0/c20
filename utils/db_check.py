import sys
import os

# Asegurar que el contexto de la app se pueda cargar
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from sqlalchemy import inspect, text

# Capacidad en caracteres de los tipos de texto de MySQL, para distinguir un
# ensanchamiento real de una diferencia meramente cosmética en el nombre del tipo.
_TEXT_CAPACITY = {
    'TINYTEXT': 2 ** 8 - 1,
    'TEXT': 2 ** 16 - 1,
    'MEDIUMTEXT': 2 ** 24 - 1,
    'LONGTEXT': 2 ** 32 - 1,
}


def _text_capacity(sa_type):
    """Capacidad de un tipo textual, o None si no es texto de tamaño conocido."""
    name = type(sa_type).__name__.upper()
    if name in _TEXT_CAPACITY:
        return _TEXT_CAPACITY[name]
    if name in ('VARCHAR', 'STRING', 'CHAR', 'NVARCHAR'):
        return getattr(sa_type, 'length', None)
    return None


def check_database_schema(auto_fix=True):
    app = create_app()
    with app.app_context():
        print("\n" + "="*60)
        print("🔍 NEXUS DB-SYNC: REVISIÓN DE INTEGRIDAD DE ESQUEMA")
        print("="*60)
        
        inspector = inspect(db.engine)
        db_tables = set(inspector.get_table_names())
        model_tables = set(db.Model.metadata.tables.keys())
        
        # --- ANÁLISIS DE TABLAS ---
        missing_in_db = model_tables - db_tables
        extra_in_db = db_tables - model_tables
        
        if missing_in_db:
            print(f"❌ Tablas FALTANTES en DB: {', '.join(missing_in_db)}")
            if auto_fix:
                print("🛠️  Creando tablas faltantes...")
                db.create_all()
                print("✅ Tablas sincronizadas.")
        else:
            print("✅ Estructura de tablas: OK")
            
        # --- ANÁLISIS DE COLUMNAS ---
        common_tables = db_tables.intersection(model_tables)
        issues = 0
        
        for table_name in common_tables:
            real_cols = {col['name']: col for col in inspector.get_columns(table_name)}
            model_cols = {col.name: col for col in db.Model.metadata.tables[table_name].columns}
            
            missing_cols = set(model_cols.keys()) - set(real_cols.keys())

            # Una columna que ya existe puede haberse quedado corta respecto al
            # modelo (p. ej. `raw_log` pasó de TEXT a LONGTEXT). Comparar sólo
            # los nombres no lo revela, así que se contrasta también la capacidad.
            #
            # Sólo se reportan ENSANCHAMIENTOS. Estrechar una columna truncaría
            # datos existentes en silencio, y además muchas diferencias de texto
            # son cosméticas (TINYINT(1)/BOOL, el charset que MySQL anexa), así
            # que se comparan capacidades declaradas, no cadenas de tipo.
            widened_cols = []
            for col_name, col_obj in model_cols.items():
                if col_name in missing_cols:
                    continue
                want_cap = _text_capacity(col_obj.type)
                have_cap = _text_capacity(real_cols[col_name]['type'])
                if want_cap is None or have_cap is None or want_cap <= have_cap:
                    continue
                try:
                    want = col_obj.type.compile(db.engine.dialect).upper()
                    have = real_cols[col_name]['type'].compile(db.engine.dialect).upper()
                except Exception:
                    continue
                widened_cols.append((col_name, col_obj, have, want))

            if missing_cols or widened_cols:
                issues += 1
                print(f"\n🔔 Discrepancia en `{table_name}`:")

            if missing_cols:
                for col_name in missing_cols:
                    print(f"   ❌ Columna `{col_name}` no existe en DB.")
                    if auto_fix:
                        col_obj = model_cols[col_name]
                        try:
                            compiled_type = col_obj.type.compile(db.engine.dialect)
                            alter_sql = f"ALTER TABLE `{table_name}` ADD COLUMN `{col_name}` {compiled_type}"
                            db.session.execute(text(alter_sql))
                            db.session.commit()
                            print(f"      🔨 Columna `{col_name}` añadida exitosamente.")
                        except Exception as e:
                            print(f"      ⚠️ Error al añadir columna: {e}")

            for col_name, col_obj, have, want in widened_cols:
                print(f"   ❌ Columna `{col_name}` es {have}, insuficiente para el modelo ({want}).")
                if auto_fix:
                    # SQLite no soporta MODIFY COLUMN, pero tampoco necesita el
                    # cambio: su TEXT no tiene tope práctico.
                    if db.engine.dialect.name != 'mysql':
                        print("      ↩️  Omitido: sólo aplica a MySQL.")
                        continue
                    try:
                        nullable = "NULL" if col_obj.nullable else "NOT NULL"
                        alter_sql = (f"ALTER TABLE `{table_name}` "
                                     f"MODIFY COLUMN `{col_name}` {want} {nullable}")
                        db.session.execute(text(alter_sql))
                        db.session.commit()
                        print(f"      🔨 Columna `{col_name}` migrada a {want}.")
                    except Exception as e:
                        db.session.rollback()
                        print(f"      ⚠️ Error al migrar columna: {e}")
            
        if issues == 0 and not missing_in_db:
            print("✅ Columnas y Tipos: OK")
            print("\n✨ BASE DE DATOS EN SINCRONÍA TOTAL")
        
        print("="*60 + "\n")

if __name__ == '__main__':
    # Fix por defecto si no se especifica --check
    do_fix = '--check' not in sys.argv
    check_database_schema(auto_fix=do_fix)
