import sys
import os

# Agrega la ruta base del proyecto explícitamente para asegurar que los módulos de app se puedan importar
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.modules.auth.models import AuthConfig
from app.modules.auth.services import validate_ldap_connection

def test_ldap():
    app = create_app()

    with app.app_context():
        config = AuthConfig.query.first()
        if not config:
            print("❌ Error: No hay configuración LDAP guardada en la base de datos.")
            return

        print("====================================")
        print("🔍 INICIANDO PRUEBA LDAP")
        print(f"Host: {config.ldap_host}")
        print(f"Puerto: {config.ldap_port}")
        print(f"SSL Activo: {config.ldap_ssl}")
        print(f"Base DN: {config.ldap_base_dn}")
        print(f"Usuario Bind: {config.ldap_user}")
        print("====================================")

        res = validate_ldap_connection(
            host=config.ldap_host,
            port=config.ldap_port,
            use_ssl=config.ldap_ssl,
            bind_dn=config.ldap_user,
            bind_pass=config.ldap_pass
        )

        print("\n[ RESULTADO ]")
        if res.get("status") == "success":
            print(f"✅ {res['message']}")
            print(f"INFO: {res.get('info', 'N/A')}")
        else:
            print(f"❌ {res.get('message')}")

if __name__ == '__main__':
    test_ldap()
