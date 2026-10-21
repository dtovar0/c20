"""
Valida que la plataforma pueda enviar correos, paso por paso.

Usa la misma configuración SMTP que los envíos reales (get_smtp_settings: base
de datos o .env) y prueba por separado la conexión, el cifrado, el login y el
envío, para decir en qué paso falla y con qué error. Las funciones de envío de
la plataforma ocultan la excepción; este script no.

Uso:
    python utils/test_smtp.py                          # a NOTIFICATION_ADMIN_EMAIL
    python utils/test_smtp.py otro@dominio.com         # a otro destino
    python utils/test_smtp.py --plantilla conexion_c20 # además, con una plantilla

Códigos de salida: 0 todo bien, 1 falló algún paso.
"""
import argparse
import os
import smtplib
import sys
from email.mime.text import MIMEText

# Agrega la ruta base del proyecto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app

# Segundos de espera por cada operación con el servidor SMTP, igual que los
# envíos reales.
TIMEOUT_SMTP = 10

# Valores de ejemplo para los huecos de las plantillas en la prueba con
# --plantilla: dejan ver cómo queda el correo real.
CONTEXTO_EJEMPLO = {
    'usuario': 'SYSTEM_TEST', 'ip': 'NODO_DE_PRUEBA', 'seccion': 'C20', 'tarea': 0,
    'operacion': 'PRUEBA', 'resultado': 'PRUEBA DE ENVÍO',
    'error': 'Correo de prueba enviado con utils/test_smtp.py; no hay ninguna falla real.',
    'hora': '00:00:00', 'registros': 0, 'parametro': '-',
}


def _paso(nombre, funcion):
    """Ejecuta un paso; devuelve True si salió bien e imprime el resultado."""
    try:
        funcion()
        print(f"   ✅ {nombre}")
        return True
    except Exception as e:
        print(f"   ❌ {nombre}: {type(e).__name__}: {e}")
        return False


def probar_smtp(config, destino):
    """Conecta, cifra, autentica y envía un correo simple. Devuelve True si todo salió bien."""
    estado = {}

    def conectar():
        if config.encryption == 'ssl':
            estado['smtp'] = smtplib.SMTP_SSL(config.server, config.port, timeout=TIMEOUT_SMTP)
        else:
            estado['smtp'] = smtplib.SMTP(config.server, config.port, timeout=TIMEOUT_SMTP)

    def enviar():
        msg = MIMEText("Correo de prueba de Nexus: la configuración SMTP funciona.")
        msg['From'] = f"{config.sender_name} <{config.username}>"
        msg['To'] = destino
        msg['Subject'] = "Nexus: prueba de envío SMTP"
        estado['smtp'].send_message(msg)

    print("\n🔌 Pasos:")
    if not _paso(f"Conexión a {config.server}:{config.port}", conectar):
        return False
    smtp = estado['smtp']
    try:
        if config.encryption == 'starttls' and not _paso("Cifrado STARTTLS", smtp.starttls):
            return False
        if config.auth_enabled and config.username and config.password:
            if not _paso(f"Login como {config.username}",
                         lambda: smtp.login(config.username, config.password)):
                return False
        elif config.auth_enabled:
            print("   ⚠️  Autenticación activada pero sin usuario o contraseña: se envía sin login")
        return _paso(f"Envío a {destino}", enviar)
    finally:
        try:
            smtp.quit()
        except Exception:
            pass


def probar_plantilla(slug, destino):
    """Envía con la plantilla indicada, por el mismo camino que la plataforma."""
    from app.modules.notifications.models import NotificationTemplate
    from app.modules.notifications.services import send_notification_by_slug

    print(f"\n🧩 Plantilla '{slug}':")
    if not NotificationTemplate.query.filter_by(slug=slug).first():
        print(f"   ❌ No existe en la base. Abre la sección Notificaciones o reinicia el worker para crearla.")
        return False
    resultado = send_notification_by_slug(slug=slug, target_email=destino,
                                          context=CONTEXTO_EJEMPLO) or {}
    mensaje = resultado.get('message', 'sin respuesta')
    if 'disabled' in mensaje:
        print("   ❌ No se envió: ENABLE_NOTIFICATIONS no está en 'true'")
        return False
    if resultado.get('status') == 'success':
        print(f"   ✅ Enviada a {destino}")
        return True
    print(f"   ❌ {mensaje}")
    print("      (la plataforma oculta el detalle; si los pasos SMTP de arriba salieron bien,")
    print("       el problema está en la plantilla o en sus datos)")
    return False


def test_smtp(destino=None, plantilla=None):
    app = create_app()

    with app.app_context():
        print("\n" + "="*60)
        print("📧 PRUEBA DE ENVÍO SMTP")
        print("="*60)

        from app.modules.notifications.services import get_smtp_settings
        config = get_smtp_settings()
        if not config:
            print("❌ No hay configuración SMTP (ni en la base de datos ni en el .env).")
            print("="*60 + "\n")
            return 1

        destino = destino or os.getenv('NOTIFICATION_ADMIN_EMAIL')
        if not destino:
            print("❌ Indica un destino o define NOTIFICATION_ADMIN_EMAIL en el .env.")
            print("="*60 + "\n")
            return 1

        print(f"🗂  Origen     : {config.origen}")
        print(f"📡 Servidor   : {config.server}:{config.port}")
        print(f"🔐 Cifrado    : {config.encryption}")
        print(f"👤 Remitente  : {config.sender_name} <{config.username}>")
        print(f"🔑 Login      : {'sí' if config.auth_enabled else 'no'}"
              f"{'' if not config.auth_enabled or config.password else ' (falta la contraseña)'}")
        print(f"📬 Destino    : {destino}")
        print(f"🔔 ENABLE_NOTIFICATIONS: {os.getenv('ENABLE_NOTIFICATIONS', 'true')}")

        ok = probar_smtp(config, destino)
        if ok and plantilla:
            ok = probar_plantilla(plantilla, destino)

        if ok:
            print("\n✅ RESULTADO: CORREO ENVIADO. Revisa la bandeja (y spam) de", destino)
        else:
            print("\n❌ RESULTADO: FALLO EN EL ENVÍO (ver el paso marcado arriba)")
            print("💡 Puertos habituales: 587 con starttls, 465 con ssl, 25 sin cifrado.")
        print("="*60 + "\n")
        return 0 if ok else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Valida el envío de correos paso por paso.")
    parser.add_argument('destino', nargs='?', help="Correo de destino (por defecto NOTIFICATION_ADMIN_EMAIL)")
    parser.add_argument('--plantilla', metavar='SLUG',
                        help="Envía además con esta plantilla (p. ej. conexion_c20, error)")
    args = parser.parse_args()
    sys.exit(test_smtp(args.destino, args.plantilla))
