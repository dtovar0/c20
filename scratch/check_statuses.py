from app import create_app, db
from app.modules.psx.models import PSX5KTask

app = create_app()
with app.app_context():
    for t in PSX5KTask.query.all():
        print(f"Task ID {t.id}: '{t.estado}'")
