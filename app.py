from flask import Flask
from app.modules.home.routes import home_bp
import os

def create_app():
    app = Flask(__name__, 
                static_url_path='/assets',
                static_folder='assets',
                template_folder='templates')
    
    # Register Blueprints
    app.register_blueprint(home_bp)
    
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
