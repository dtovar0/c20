from flask import Flask, send_from_directory
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
    from app.modules.settings.routes import settings_bp
    
    app.register_blueprint(core_bp)
    app.register_blueprint(settings_bp)

    # Servir archivos de /assets (Estructura Obligatoria)
    @app.route('/assets/<path:filename>')
    def serve_assets(filename):
        return send_from_directory(os.path.join(app.root_path, '../assets'), filename)

    return app
