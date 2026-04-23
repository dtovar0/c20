import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app
from flask_login import login_user, current_user
from app.modules.auth.models import User

app = create_app()
with app.test_request_context('/'):
    user = User.query.first()
    if user:
        login_user(user)
        print("User logged in in test context.")
        print(f"Flask-Login current_user authenticated? {current_user.is_authenticated}")
        print(f"Session vars: {sys.modules['flask'].session}")
