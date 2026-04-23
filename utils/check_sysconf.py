import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app, db
from app.modules.settings.models import SystemConfig

app = create_app()
with app.app_context():
    config = SystemConfig.query.first()
    if config:
        print(config.to_dict())
    else:
        print("NO SYSTEM CONFIG EXISTS!")
