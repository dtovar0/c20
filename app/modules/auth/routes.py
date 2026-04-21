from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.modules.auth.models import User, AuthConfig

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('core.index'))
        
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('core.index'))
        
        flash("Credenciales inválidas", "error")
        return redirect(url_for('auth.login'))

    return render_template("login.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
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
