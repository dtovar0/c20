import os
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.modules.auth.models import User, AuthConfig
from app.modules.auth.services import validate_ldap_connection
from app.modules.audit.services import add_audit_log

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    try:
        # 1. Si ya está logueado, ir al inicio
        if current_user.is_authenticated:
            return redirect(url_for('core.index'))
            
        # --- DEBUG DE CABECERAS (SI ESTÁ HABILITADO) ---
        if os.getenv('DEBUG_AUTH', 'false').lower() == 'true':
            print("\n" + "="*50)
            print("DEBUG AUTH: REVISANDO CABECERAS ENTRANTES")
            for header, value in request.headers.items():
                print(f"  {header}: {value}")
            print("="*50 + "\n")

        # 2. INTENTO DE SSO / AUTHELIA (Soporta GET y POST)
        if os.getenv('AUTHELIA_ENABLED', 'false').lower() == 'true':
            header_user = os.getenv('AUTHELIA_HEADER_USER', 'Remote-Email')
            authelia_user = request.headers.get(header_user)
            
            if authelia_user:
                print(f"DEBUG: Usuario detectado -> {authelia_user}")
                header_name = os.getenv('AUTHELIA_HEADER_NAME', 'Remote-Name')
                header_groups = os.getenv('AUTHELIA_HEADER_GROUPS', 'Remote-Groups')
                
                print("DEBUG: Buscando usuario en DB...")
                user = User.query.filter_by(username=authelia_user).first()
                authelia_name = request.headers.get(header_name, authelia_user)
                authelia_groups = request.headers.get(header_groups, '')
                
                # Lógica de Roles
                inferred_role = 'usuario'
                if authelia_groups and 'administrador' in [g.strip().lower() for g in authelia_groups.split(',')]:
                    inferred_role = 'administrador'

                if not user:
                    print("DEBUG: Usuario nuevo. Creando registro...")
                    user = User(
                        username=authelia_user,
                        nombre=authelia_name,
                        role=inferred_role,
                        auth_source='sso'
                    )
                    db.session.add(user)
                    db.session.commit()
                else:
                    print("DEBUG: Usuario existente. Actualizando metadatos...")
                    user.nombre = authelia_name
                    user.role = inferred_role
                    db.session.commit()
                
                print(f"DEBUG: Procediendo a login_user para {user.username}")
                login_user(user)
                print("DEBUG: Registro en auditoría...")
                add_audit_log("login sso", status="success", detail=f"Usuario {authelia_user} ha iniciado sesión vía SSO")
                print("DEBUG: Redirigiendo a index...")
                return redirect(url_for('core.index'))

        # 3. LOGIN TRADICIONAL (Solo si es POST)
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")
            auth_type = request.form.get("auth_type", "directory")
            
            if auth_type == "directory":
                from app.modules.auth.services import authenticate_user_ldap
                ldap_result = authenticate_user_ldap(username, password)
                if ldap_result.get("status") == "success":
                    user = ldap_result["user"]
                    login_user(user)
                    add_audit_log("login usuario", status="success", detail=f"Usuario {username} vía DIRECTORIO")
                    return redirect(url_for('core.index'))
                else:
                    flash(f"Error: {ldap_result.get('message')}", "error")
            else:
                user = User.query.filter_by(username=username).first()
                if user and user.check_password(password):
                    login_user(user)
                    add_audit_log("login usuario", status="success", detail=f"Usuario {username} ha iniciado sesión LOCALMENTE")
                    return redirect(url_for('core.index'))
                flash("Credenciales incorrectas", "error")

        # 4. FALLBACK: Mostrar formulario de login manual
        return render_template("login.html", sso_enabled=os.getenv('AUTHELIA_ENABLED', 'false').lower() == 'true')

    except Exception as e:
        import traceback
        print("\n" + "!"*50)
        print(f"ERROR CRÍTICO EN LOGIN: {str(e)}")
        traceback.print_exc()
        print("!"*50 + "\n")
        from flask import current_app
        current_app.logger.error(f"Error en login: {e}")
        return render_template("login.html", error="Error en el servicio de autenticación")

@auth_bp.route("/users/purge", methods=["POST"])
@login_required
def purge_users():
    """
    Ruta administrativa para ejecutar la limpieza de inactividad.
    """
    if current_user.role != 'administrador':
        return jsonify({"status": "error", "message": "Acceso denegado"}), 403
        
    try:
        from app.modules.auth.services import purge_inactive_users
        result = purge_inactive_users(days=30)
        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "error", "message": "Ocurrió un error al procesar el usuario."}), 500

@auth_bp.route("/logout")
@login_required
def logout():
    user_name = current_user.username
    logout_user()
    add_audit_log("logout", status="success", detail=f"User {user_name} has logged out")
    
    # --- LOGOUT COORDINADO CON AUTHELIA (SSO) ---
    if os.getenv('AUTHELIA_ENABLED', 'false').lower() == 'true':
        slo_url = os.getenv('AUTHELIA_SLO_URL')
        if slo_url:
            # Redirigimos al login para romper el bucle
            redirect_url = f"{slo_url}?rd={request.host_url}auth/login"
            return redirect(redirect_url)
        
    flash("Has cerrado sesión correctamente.", "info")
    return redirect(url_for('auth.login'))

@auth_bp.route("/")
@login_required
def index():
    try:
        config = AuthConfig.query.first()
        return render_template("auth.html", config=config)
    except Exception as e:
        current_app.logger.error(f"Error en auth.index: {e}")
        return render_template("auth.html", config=None)

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
        return jsonify({"status": "error", "message": "Error al actualizar credenciales."}), 500

@auth_bp.route("/users/list")
@login_required
def list_users():
    search = request.args.get('search', '').lower()
    
    query = User.query
    if search:
        query = query.filter(
            (User.username.ilike(f'%{search}%')) | 
            (User.nombre.ilike(f'%{search}%')) | 
            (User.role.ilike(f'%{search}%')) |
            (User.auth_source.ilike(f'%{search}%'))
        )
    
    users = query.all()
    user_list = []
    for u in users:
        # Map db state to UI status
        status = 'active' if u.is_active else 'inactive'
        
        user_list.append({
            "id": u.id,
            "username": u.username,
            "nombre": u.nombre,
            "role": u.role,
            "source": u.auth_source or 'local',
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
            nombre=data.get('nombre', ''),
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
        return jsonify({"status": "error", "message": "Error del sistema en el entorno LDAP."}), 500

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
        return jsonify({"status": "error", "message": "La conexión LDAP ha fallado temporalmente."}), 500

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
        if "nombre" in data: user.nombre = data["nombre"]
        if "role" in data: user.role = data["role"]
        
        if "password" in data and data["password"]:
            user.set_password(data["password"])
            
        db.session.commit()
        return jsonify({"status": "success", "message": "Usuario actualizado correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": "Autenticación LDAP falló en el controlador."}), 500

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
        return jsonify({"status": "error", "message": "Fallo en la sincronización de roles LDAP."}), 500

@auth_bp.route("/preferences/save", methods=["POST"])
@login_required
def save_preferences():
    """
    Guarda las preferencias de interfaz del usuario actual.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No se recibieron datos"}), 400
            
        if "notifications" in data: current_user.pref_notifications = data["notifications"]
        if "email_notifications" in data: current_user.pref_email_notifications = data["email_notifications"]
        if "refresh_interval" in data: current_user.pref_refresh_interval = data["refresh_interval"]
        if "tour_enabled" in data: current_user.pref_tour_enabled = data["tour_enabled"]
        
        # Save color mapping
        if "status_colors" in data:
            import json
            current_user.pref_status_colors = json.dumps(data["status_colors"])
        
        db.session.commit()
        return jsonify({"status": "success", "message": "Preferencias del sistema actualizadas"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": "Error al guardar preferencias"}), 500
