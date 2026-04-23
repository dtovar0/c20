import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.modules.notifications.models import SMTPConfig
from app.modules.notifications.services import send_test_email

def test_smtp():
    app = create_app()

    with app.app_context():
        config = SMTPConfig.query.first()
        if not config:
            print("❌ Error: No hay configuración SMTP guardada en la base de datos.")
            return

        print("====================================")
        print("📧 INICIANDO PRUEBA SMTP")
        print(f"Servidor: {config.server}:{config.port}")
        print(f"Cifrado: {config.encryption}")
        print(f"Usuario: {config.user}")
        print(f"Remitente: {config.sender_name} <{config.sender_email}>")
        print("====================================")

        # Destinatario para prueba
        target = input("Ingresa un correo destinatario de prueba (o presiona Enter para usar el usuario SMTP): ")
        if not target.strip():
            target = config.user

        print(f"Enviando correo de validación a {target} (puede tardar unos segundos)...")
        
        res = send_test_email(
            server=config.server,
            port=config.port,
            encryption=config.encryption,
            user=config.user,
            password=config.password,
            sender_name=config.sender_name,
            sender_email=config.sender_email,
            target_email=target
        )

        print("\n[ RESULTADO ]")
        if res.get("status") == "success":
            print(f"✅ {res['message']}")
        else:
            print(f"❌ {res.get('message')}")

if __name__ == '__main__':
    test_smtp()
