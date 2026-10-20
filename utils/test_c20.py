"""
Valida la cuenta del C20 (C20_USER / C20_PASS) contra el nodo.

A diferencia de test_connectivity() de bin/c20_cmd.py, que solo espera el prompt
y ante un rechazo termina por timeout, aquí se reconocen los mensajes con los
que el nodo niega el acceso y se informa el motivo.

Códigos de salida: 0 cuenta válida, 1 acceso rechazado, 2 sin respuesta o sin
configuración.
"""
import os
import sys

import pexpect
from dotenv import load_dotenv

# Agrega bin/ para reutilizar las constantes del motor del C20
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, 'bin'))

from c20_cmd import EXPECT_TIMEOUT, PROMPT

PIDE_USUARIO = 'Enter User Name'
PIDE_PASSWORD = 'Enter Password'

# Mensajes del nodo al negar el acceso, del más específico al más general.
# El nodo no distingue contraseña vencida de usuario nuevo: imprime ambos
# casos en el mismo aviso.
RECHAZOS = (
    ('NOT PERMITTED TO LOGON',
     'Cuenta no permitida: la contraseña tiene más de 180 días, o es un usuario '
     'nuevo que no la cambió en el primer acceso. Hay que cambiarla en el nodo.'),
    ('Invalid user name or password', 'Usuario o contraseña incorrectos.'),
)

OK, RECHAZADO, SIN_RESPUESTA = 0, 1, 2


def _mensajes_del_nodo(texto, password):
    """Líneas no vacías de la respuesta, sin la contraseña por si hubo eco."""
    if password:
        texto = texto.replace(password, '*' * len(password))
    return [linea.strip() for linea in texto.splitlines() if linea.strip()]


def validar_cuenta():
    """Devuelve (código, mensaje, líneas del nodo)."""
    host = os.getenv('C20_HOST')
    user = os.getenv('C20_USER')
    password = os.getenv('C20_PASS')
    port = os.getenv('C20_PORT', '23')

    if not all([host, user, password]):
        return SIN_RESPUESTA, "Faltan credenciales del C20 en .env (C20_HOST, C20_USER, C20_PASS)", []

    try:
        session = pexpect.spawn(f'telnet {host} {port}', timeout=EXPECT_TIMEOUT,
                                encoding='utf-8', codec_errors='replace')
    except Exception as e:
        return SIN_RESPUESTA, f"No se pudo abrir telnet: {e}", []

    try:
        if session.expect([PIDE_USUARIO, pexpect.TIMEOUT, pexpect.EOF]) != 0:
            return SIN_RESPUESTA, "El nodo no pidió el usuario", []
        # Tras pedir el usuario el nodo imprime avisos de terminal y luego su
        # prompt; se espera ese prompt para no responder antes de tiempo.
        session.expect([PROMPT, pexpect.TIMEOUT, pexpect.EOF])
        session.sendline(user)

        if session.expect([PIDE_PASSWORD, pexpect.TIMEOUT, pexpect.EOF]) != 0:
            return SIN_RESPUESTA, "El nodo no pidió la contraseña", []
        session.expect([PROMPT, pexpect.TIMEOUT, pexpect.EOF])
        session.sendline(password)

        # Con rechazo el nodo imprime el motivo y vuelve a pedir el usuario;
        # con éxito deja el prompt.
        idx = session.expect([PIDE_USUARIO, PROMPT, pexpect.TIMEOUT, pexpect.EOF])
        texto = session.before or ''
        lineas = _mensajes_del_nodo(texto, password)

        for patron, motivo in RECHAZOS:
            if patron in texto:
                return RECHAZADO, motivo, lineas
        if idx == 0:
            return RECHAZADO, "El nodo rechazó el acceso y volvió a pedir el usuario", lineas
        if idx == 1:
            try:
                session.sendline('exit')
            except Exception:
                pass
            return OK, "Cuenta válida: el nodo aceptó el usuario y la contraseña", lineas
        return SIN_RESPUESTA, "El nodo no respondió tras enviar la contraseña", lineas
    finally:
        session.close()


def test_c20():
    load_dotenv(os.path.join(BASE_DIR, '.env'))

    print("\n" + "="*60)
    print("🔐 VALIDACIÓN DE LA CUENTA C20")
    print("="*60)
    print(f"📡 Nodo: {os.getenv('C20_HOST', 'NODE_NOT_SET')}:{os.getenv('C20_PORT', '23')}")
    print(f"👤 Usuario: {os.getenv('C20_USER') or '(vacío)'}")
    print(f"⏳ Iniciando sesión ({EXPECT_TIMEOUT}s de espera por paso)...")

    codigo, mensaje, lineas = validar_cuenta()

    if codigo == OK:
        print("\n✅ RESULTADO: CUENTA VÁLIDA")
    elif codigo == RECHAZADO:
        print("\n❌ RESULTADO: ACCESO RECHAZADO")
    else:
        print("\n⚠️  RESULTADO: SIN RESPUESTA DEL NODO")
    print(f"📝 {mensaje}")

    if codigo == RECHAZADO and lineas:
        print("\n📄 Respuesta del nodo:")
        for linea in lineas:
            print(f"   {linea}")

    print("="*60 + "\n")
    return codigo


if __name__ == '__main__':
    sys.exit(test_c20())
