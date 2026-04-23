import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app
from flask import render_template

app = create_app()
with app.test_request_context('/auth/login'):
    html = render_template('login.html')
    if "mingote" in html:
        print("SUCCESS! mingote is there.")
    else:
        print("mingote NOT FOUND")
    
    if "var(--color-brand-identity-bg" in html:
        print("bg var is present in html text")
