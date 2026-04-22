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

        # Sanitizar host y puerto
        host = config.ldap_host.strip()
        port = int(config.ldap_port) if config.ldap_port else 389

        server = Server(
            host, 
            port=port, 
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
                # PROTOCOLO DE PURGA: Si el LDAP está arriba pero el usuario no existe, lo borramos localmente
                local_user = User.query.filter_by(username=username).first()
                if local_user:
                    from app.modules.audit.services import add_audit_log
                    db.session.delete(local_user)
                    db.session.commit()
                    add_audit_log("usuario borrado", status="warning", detail=f"Sincronía LDAP: Usuario {username} purgado por no existir en origen")
                    print(f"🗑️ Usuario {username} purgado localmente (Eliminado de LDAP).")
                
                return {"status": "error", "message": "Usuario no encontrado en el directorio corporativo"}
            
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
                        from app.modules.audit.services import add_audit_log
                        add_audit_log("usuario creado", status="success", detail=f"Sincronía LDAP: Shadow user '{username}' generado")
                    else:
                        # Actualizar correo si cambió
                        local_user.email = email
                    
                    # Lógica de Mapeo de Roles Avanzado (JSON + Legacy Fallback)
                    new_role = 'usuario' # Default
                    member_of = [str(g).lower() for g in user_entry.memberOf] if 'memberOf' in user_entry else []

                    # 1. Intentar Mapeo Dinámico (JSON)
                    if config.ldap_role_mappings:
                        import json
                        try:
                            mappings = json.loads(config.ldap_role_mappings)
                            # Mappings es una lista: [{"group": "...", "role": "..."}]
                            for mapping in mappings:
                                m_group = mapping.get('group', '').strip().lower()
                                m_role = mapping.get('role', 'usuario')
                                if any(m_group in group for group in member_of):
                                    new_role = m_role
                                    break
                        except Exception as e:
                            print(f"Error parsing role mappings: {e}")

                    # 2. Fallback a Legacy (si sigue siendo usuario y hay legacy config)
                    if new_role == 'usuario' and config.ldap_group_admin:
                        legacy_groups = [g.strip().lower() for g in config.ldap_group_admin.split(',')]
                        if any(any(lg in group for lg in legacy_groups) for group in member_of):
                            new_role = 'administrador'
                    
                    local_user.role = new_role
                    
                    from app.modules.audit.services import add_audit_log
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
