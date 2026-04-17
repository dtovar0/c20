from flask import Flask
from flask_compress import Compress
import os

def create_app():
    app = Flask(__name__, 
                template_folder='../templates', 
                static_folder='../static')

    # Inicializar Extensiones
    Compress(app)

    # Registro de Blueprints
    from app.modules.core.routes import core_bp
    app.register_blueprint(core_bp)

    return app
