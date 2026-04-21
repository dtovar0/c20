from ldap3 import Server, Connection, ALL, Tls
import ssl

def validate_ldap_connection(host, port, use_ssl=False, bind_dn=None, bind_pass=None):
    """
    Realiza una prueba de conexión y bind contra un servidor LDAP.
    """
    try:
        # Configuración de Seguridad
        tls_config = None
        if use_ssl:
            # En configuraciones premium, podrías requerir validación de certificados
            # Por ahora permitimos certificados auto-firmados para la prueba inicial
            tls_config = Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLSv1_2)

        # Definición del Servidor
        server = Server(
            host, 
            port=int(port), 
            use_ssl=use_ssl, 
            tls=tls_config, 
            get_info=ALL,
            connect_timeout=5
        )

        # Intento de Conexión y Bind
        # Si bind_dn es None, intentará una conexión anónima
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
