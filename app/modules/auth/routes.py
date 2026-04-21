from flask import Blueprint, render_template, request, jsonify
from app import db
from app.modules.auth.models import AuthConfig

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

@auth_bp.route("/")
def index():
    config = AuthConfig.query.first()
    return render_template("auth.html", config=config)

@auth_bp.route("/save", methods=["POST"])
def save():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
            
        config = AuthConfig.query.first()
        if not config:
            config = AuthConfig()
            db.session.add(config)
            
        # Update Auth Config
        if "ldap_host" in data: config.ldap_host = data["ldap_host"]
        if "ldap_port" in data: config.ldap_port = data["ldap_port"]
        if "ldap_ssl" in data: config.ldap_ssl = data["ldap_ssl"]
        if "ldap_base_dn" in data: config.ldap_base_dn = data["ldap_base_dn"]
        if "ldap_user" in data: config.ldap_user = data["ldap_user"]
        if "ldap_pass" in data: config.ldap_pass = data["ldap_pass"]
        
        db.session.commit()
        return jsonify({"status": "success", "message": "Configuración de Directorio Guardada"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
