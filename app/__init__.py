from flask import Flask, send_from_directory
from flask_compress import Compress
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

# Instancia global de DB
db = SQLAlchemy()

def create_app():
    app = Flask(__name__, 
                template_folder='../templates', 
                static_folder='../static')

    # Configuración de base de datos
    db_engine = os.getenv('DB_ENGINE', 'sqlite')
    if db_engine == 'mysql':
        db_uri = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    else:
        db_uri = 'sqlite:///nexus.db'
    
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Inicializar Extensiones
    Compress(app)
    db.init_app(app)

    # Registro de Blueprints
    from app.modules.core.routes import core_bp
    from app.modules.settings.routes import settings_bp
    from app.modules.audit.routes import audit_bp
    from app.modules.notifications.routes import notifications_bp
    from app.modules.auth.routes import auth_bp
    from app.modules.design.routes import design_bp
    
    app.register_blueprint(core_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(audit_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(design_bp)

    # Sincronizar Modelos (Importar antes de crear tablas)
    from app.modules.settings.models import SystemConfig
    from app.modules.audit.models import AuditLog
    from app.modules.notifications.models import SMTPConfig
    from app.modules.auth.models import AuthConfig

    # Crear tablas automáticamente dentro del contexto de la app
    with app.app_context():
        try:
            db.create_all()
            print("🚀 Base de Datos Sincronizada Correctamente")
        except Exception as e:
            print(f"❌ Error al sincronizar base de datos: {e}")

    # Servir archivos de /assets
    @app.route('/assets/<path:filename>')
    def serve_assets(filename):
        return send_from_directory(os.path.join(app.root_path, '../assets'), filename)

    # Inyectar configuración global en todas las vistas
    @app.context_processor
    def inject_system_config():
        from app.modules.settings.models import SystemConfig
        try:
            config = SystemConfig.query.first()
            return dict(sys_config=config)
        except:
            return dict(sys_config=None)

    return app
