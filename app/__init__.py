from flask import Flask
import os

def create_app():
    app = Flask(__name__, 
                template_folder='../templates', 
                static_folder='../static')

    # Registro de Blueprints
    from app.modules.core.routes import core_bp
    app.register_blueprint(core_bp)

    return app
