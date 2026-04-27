import sys
import os
import random

# Agrega la ruta base del proyecto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.modules.psx.models import PSX5KJob, PSX5KTask
from datetime import datetime

def run_load_test(count=100, chunks=5):
    """
    Crea una carga de trabajo sintética para probar el worker y la UI.
    """
    app = create_app()
    with app.app_context():
        print(f"\n🚀 INICIANDO PRUEBA DE CARGA: {count} registros en {chunks} chunks")
        
        # 1. Crear el Job Maestro
        job = PSX5KJob(
            usuario="LOAD_TESTER",
            tarea=random.choice(["add", "delete"]),
            accion_tipo="Manual",
            datos_tipo="Rango",
            routing_label="TEST_ROUTE",
            run_force=False
        )
        db.session.add(job)
        db.session.flush() # Para obtener el ID
        
        # 2. Generar números aleatorios y dividirlos en chunks
        all_numbers = [f"55{random.randint(10000000, 99999999)}" for _ in range(count)]
        chunk_size = count // chunks
        
        for i in range(chunks):
            start = i * chunk_size
            end = start + chunk_size if i < chunks - 1 else count
            chunk_data = ",".join(all_numbers[start:end])
            
            task = PSX5KTask(
                job_id=job.id,
                estado="Pendiente",
                datos=chunk_data,
                chunk_index=i+1,
                chunk_total=chunks,
                tipo="normal"
            )
            db.session.add(task)
            
        db.session.commit()
        print(f"✅ Job #{job.id} creado exitosamente con {chunks} tareas pendientes.")
        print(f"💡 Ahora puedes iniciar el worker (backend_psx5k.py) para procesar esta carga.")
        print("-" * 60 + "\n")

if __name__ == '__main__':
    print("Nexus Load Tester - Generador de carga para PSX5K")
    try:
        n = int(input("¿Cuántos números totales (ANI) generar? [100]: ") or 100)
        c = int(input("¿En cuántos chunks dividir el trabajo? [5]: ") or 5)
        run_load_test(n, c)
    except ValueError:
        print("Entrada inválida. Usa números enteros.")
