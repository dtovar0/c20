import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app, db
from app.modules.auth.models import User
from datetime import datetime

app = create_app()
with app.app_context():
    username = "mockuser@vivaro.com"
    local_user = User.query.filter_by(username=username).first()
    if not local_user:
        local_user = User(
            username=username,
            nombre="Mock User",
            role='usuario',
            auth_source='ldap',
            is_active=True
        )
        local_user.password_hash = None
        db.session.add(local_user)
        # Flush to check ID
        db.session.flush()
        print(f"ID AFTER FLUSH: {local_user.id}")

    local_user.last_login_at = datetime.utcnow()
    db.session.commit()
    print(f"ID AFTER COMMIT: {local_user.id}")
