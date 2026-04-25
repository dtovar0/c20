from app import create_app, db
from app.modules.psx.models import PSX5KTask, PSX5KDetail
from sqlalchemy import func

app = create_app()
with app.app_context():
    try:
        val = db.session.query(func.sum(PSX5KDetail.total)).join(PSX5KTask).filter(PSX5KTask.estado == 'Completado').scalar()
        print(f"VAL: {val}")
    except Exception as e:
        print(f"ERROR: {e}")
