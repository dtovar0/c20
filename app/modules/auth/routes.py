from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.modules.auth.models import User, AuthConfig
from app.modules.auth.services import validate_ldap_connection
from app.modules.audit.services import add_audit_log

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('core.index'))
        
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        auth_type = request.form.get("auth_type", "directory")
        
        # --- MODO DIRECTORIO (LDAP) ---
        if auth_type == "directory":
            from app.modules.auth.services import authenticate_user_ldap
            ldap_result = authenticate_user_ldap(username, password)
            
            if ldap_result.get("status") == "success":
                user = ldap_result["user"]
                login_user(user)
                add_audit_log("login usuario", status="success", detail=f"Usuario {username} ha iniciado sesión vía DIRECTORIO")
                return redirect(url_for('core.index'))
            else:
                flash(f"Error de Directorio: {ldap_result.get('message')}", "error")
                return redirect(url_for('auth.login'))
            
        # --- MODO LOCAL ---
        else:
            user = User.query.filter_by(username=username).first()
            
            if user and user.check_password(password):
                login_user(user)
                add_audit_log("login usuario", status="success", detail=f"Usuario {username} ha iniciado sesión LOCALMENTE")
                return redirect(url_for('core.index'))
            
            flash("Credenciales locales incorrectas", "error")
            return redirect(url_for('auth.login'))

    return render_template("login.html")

@auth_bp.route("/logout")
@login_required
def logout():
    username = current_user.username
    logout_user()
    add_audit_log("logout usuario", status="info", user_override=username)
    return render_template("logout.html")

@auth_bp.route("/")
@login_required
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
        if "ldap_user_attr" in data: config.ldap_user_attr = data["ldap_user_attr"]
        if "ldap_group_admin" in data: config.ldap_group_admin = data["ldap_group_admin"]
        if "ldap_group_user" in data: config.ldap_group_user = data["ldap_group_user"]
        if "ldap_role_mappings" in data: config.ldap_role_mappings = data["ldap_role_mappings"]
        
        db.session.commit()
        return jsonify({"status": "success", "message": "Configuración de Directorio Guardada"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@auth_bp.route("/users/list")
@login_required
def list_users():
    search = request.args.get('search', '').lower()
    
    query = User.query
    if search:
        query = query.filter(
            (User.username.ilike(f'%{search}%')) | 
            (User.email.ilike(f'%{search}%')) | 
            (User.role.ilike(f'%{search}%'))
        )
    
    users = query.all()
    user_list = []
    for u in users:
        # Map db state to UI status
        status = 'active' if u.is_active else 'inactive'
        # Check suspended logic if needed, for now using binary state
        
        user_list.append({
            "id": u.id,
            "name": u.username,
            "email": u.email,
            "role": u.role,
            "status": status
        })
        
    return jsonify(user_list)

@auth_bp.route("/users/create", methods=["POST"])
@login_required
def create_user():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Faltan datos"}), 400
            
        # Validar si ya existe
        if User.query.filter_by(username=data['username']).first():
            return jsonify({"status": "error", "message": "El nombre de usuario ya existe"}), 400
            
        new_user = User(
            username=data['username'],
            email=data['email'],
            role=data['role'],
            is_active=True
        )
        new_user.set_password(data['password'])
        
        db.session.add(new_user)
        db.session.commit()
        
        add_audit_log("usuario creado", status="success", detail=f"Se creó el usuario: {data['username']}")
        
        return jsonify({"status": "success", "message": "Usuario creado"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@auth_bp.route("/users/delete", methods=["POST"])
@login_required
def delete_users():
    try:
        data = request.get_json()
        ids = data.get('ids', [])
        
        if not ids:
            return jsonify({"status": "error", "message": "No se proporcionaron IDs"}), 400
            
        User.query.filter(User.id.in_(ids)).delete(synchronize_session=False)
        db.session.commit()
        
        return jsonify({"status": "success", "message": f"{len(ids)} usuarios eliminados"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@auth_bp.route("/users/update", methods=["POST"])
@login_required
def update_user():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({"status": "error", "message": "Usuario no encontrado"}), 404
            
        if "username" in data: user.username = data["username"]
        if "email" in data: user.email = data["email"]
        if "role" in data: user.role = data["role"]
        
        if "password" in data and data["password"]:
            user.set_password(data["password"])
            
        db.session.commit()
        return jsonify({"status": "success", "message": "Usuario actualizado correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@auth_bp.route("/test_ldap", methods=["POST"])
@login_required
def test_ldap():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No se recibieron datos"}), 400
            
        result = validate_ldap_connection(
            host=data.get("ldap_host"),
            port=data.get("ldap_port"),
            use_ssl=data.get("ldap_ssl", False),
            bind_dn=data.get("ldap_user"),
            bind_pass=data.get("ldap_pass")
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
