import os
import sys
from dotenv import load_dotenv

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

from app import create_app, db
from app.modules.psx.models import PSX5KTask, PSX5KJob
from sqlalchemy import text, func

app = create_app()
with app.app_context():
    print("Reparando esquema: Ampliando columna 'estado' a 50 caracteres...")
    db.session.execute(text("ALTER TABLE psx5k_tasks MODIFY COLUMN estado VARCHAR(50)"))
    db.session.commit()
    
    print("Normalizando estados antiguos...")
    
    # Terminada -> Completado
    count_c = PSX5KTask.query.filter_by(estado='Terminada').update({PSX5KTask.estado: 'Completado'})
    
    # Error -> Terminado con Errores
    count_e = PSX5KTask.query.filter_by(estado='Error').update({PSX5KTask.estado: 'Terminado con Errores'})
    
    db.session.commit()
    print(f"Sincronizados: {count_c} completadas, {count_e} errores.")
    
    # Resumen Final
    new_stats = db.session.query(PSX5KTask.estado, func.count(PSX5KTask.id)).group_by(PSX5KTask.estado).all()
    print("\nResumen Final de Estados en la DB:")
    for state, count in new_stats:
        print(f" - {state}: {count}")
