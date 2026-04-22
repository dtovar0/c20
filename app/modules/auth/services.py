from ldap3 import Server, Connection, ALL, Tls
import ssl

def authenticate_user_ldap(username, password):
    """
    Autentica un usuario contra LDAP y sincroniza su perfil local.
    """
    from app.modules.auth.models import AuthConfig, User
    from app import db

    config = AuthConfig.query.first()
    if not config or not config.ldap_host:
        return {"status": "error", "message": "LDAP no configurado"}

    try:
        # 1. Configurar Servidor
        tls_config = None
        if config.ldap_ssl:
            tls_config = Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLSv1_2)

        server = Server(
            config.ldap_host, 
            port=int(config.ldap_port), 
            use_ssl=config.ldap_ssl, 
            tls=tls_config,
            connect_timeout=5
        )

        # 2. Construir el User DN para el Bind
        # Algunos servidores requieren el DN completo, otros solo el CN/UID
        # Para AD suele ser: DOMAIN\username o username@domain.com
        # Aquí usaremos el atributo configurado (ej: sAMAccountName={username})
        user_filter = f"({config.ldap_user_attr}={username})"
        
        # 3. Conexión de búsqueda (usando el usuario de servicio configurado)
        with Connection(server, user=config.ldap_user, password=config.ldap_pass, auto_bind=True) as conn:
            conn.search(config.ldap_base_dn, user_filter, attributes=['mail', 'displayName', 'cn', 'memberOf'])
            
            if not conn.entries:
                return {"status": "error", "message": "Usuario no encontrado en LDAP"}
            
            user_entry = conn.entries[0]
            user_dn = user_entry.entry_dn
            
            # 4. Validar contraseña intentando un nuevo Bind con las credenciales del usuario
            try:
                with Connection(server, user=user_dn, password=password, auto_bind=True):
                    # Login Exitoso en LDAP -> Sincronizar Localmente
                    
                    email = str(user_entry.mail) if 'mail' in user_entry else f"{username}@local.nexus"
                    # Si no hay correo, generamos uno ficticio para cumplir la DB
                    
                    local_user = User.query.filter_by(username=username).first()
                    
                    if not local_user:
                        # Crear Usuario Sombra
                        local_user = User(
                            username=username,
                            email=email,
                            role='usuario' # Por defecto usuario
                        )
                        # Le ponemos una clave local aleatoria inútil ya que usará LDAP
                        local_user.set_password('LDAP_AUTH_DISABLED_LOCAL_PASS')
                        db.session.add(local_user)
                    else:
                        # Actualizar correo si cambió
                        local_user.email = email
                    
                    # Lógica de Mapeo de Roles por Grupos LDAP (opcional)
                    if config.ldap_group_admin:
                        member_of = [str(g) for g in user_entry.memberOf] if 'memberOf' in user_entry else []
                        if any(config.ldap_group_admin in group for group in member_of):
                            local_user.role = 'administrador'
                    
                    db.session.commit()
                    return {"status": "success", "user": local_user}
                    
            except Exception as bind_err:
                return {"status": "error", "message": "Contraseña LDAP incorrecta"}

    except Exception as e:
        return {"status": "error", "message": f"Error LDAP: {str(e)}"}

def validate_ldap_connection(host, port, use_ssl=False, bind_dn=None, bind_pass=None):
    """
    Realiza una prueba de conexión y bind contra un servidor LDAP.
    """
    try:
        tls_config = None
        if use_ssl:
            tls_config = Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLSv1_2)

        server = Server(
            host, 
            port=int(port), 
            use_ssl=use_ssl, 
            tls=tls_config, 
            get_info=ALL,
            connect_timeout=5
        )

        with Connection(server, user=bind_dn, password=bind_pass, auto_bind=True) as conn:
            return {
                "status": "success",
                "message": "Conexión establecida correctamente",
                "info": str(server.info) if server.info else "Anonimo"
            }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Fallo de conexión: {str(e)}"
        }
