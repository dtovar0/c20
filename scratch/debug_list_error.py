import sys, os
sys.path.append(os.getcwd())
from app import create_app, db
from app.modules.psx.models import PSX5KTask, PSX5KJob

app = create_app()
with app.app_context():
    try:
        tasks = PSX5KTask.query.join(PSX5KJob).all()
        print(f"Found {len(tasks)} tasks")
        for i, t in enumerate(tasks):
            try:
                t.to_dict()
            except Exception as item_err:
                print(f"Error in task index {i} (ID: {t.id}): {item_err}")
                # Print attributes to see what's missing
                print(f"  job: {t.job}")
                print(f"  fecha_inicio: {t.fecha_inicio}")
                print(f"  resumen: {t.resumen}")
        print("Test finished.")
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
