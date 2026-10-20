"""
Valida la cuenta del C20 (C20_USER / C20_PASS) contra el nodo.

Usa el mismo inicio de sesión que el worker (_login de bin/c20_cmd.py), que
reconoce los mensajes con los que el nodo niega el acceso, y muestra el motivo
y lo que respondió el nodo.

Códigos de salida: 0 cuenta válida, 1 acceso rechazado, 2 sin respuesta o sin
configuración.

Uso:
    python utils/test_c20.py           # resultado
    python utils/test_c20.py --debug   # además, el diálogo crudo con el nodo
"""
import argparse
import os
import sys

import pexpect
from dotenv import load_dotenv

# Agrega bin/ para reutilizar el inicio de sesión del motor del C20
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, 'bin'))

from c20_cmd import EXPECT_TIMEOUT, LOGIN_OK, LOGIN_RECHAZADO, _login

OK, RECHAZADO, SIN_RESPUESTA = 0, 1, 2
CODIGOS = {LOGIN_OK: OK, LOGIN_RECHAZADO: RECHAZADO}


class _Captura:
    """Acumula lo que llega del nodo para mostrarlo con --debug."""

    def __init__(self):
        self.texto = ''

    def write(self, s):
        self.texto += s

    def flush(self):
        pass


def _mensajes_del_nodo(texto, password):
    """Líneas no vacías de la respuesta, sin la contraseña por si hubo eco."""
    if password:
        texto = texto.replace(password, '*' * len(password))
    return [linea.strip() for linea in texto.splitlines() if linea.strip()]


def validar_cuenta(captura=None):
    """
    Devuelve (código, mensaje, líneas del nodo).

    captura: objeto con write() que recibe todo lo leído del nodo (--debug).
    """
    host = os.getenv('C20_HOST')
    user = os.getenv('C20_USER')
    password = os.getenv('C20_PASS')
    port = os.getenv('C20_PORT', '23')

    if not all([host, user, password]):
        return SIN_RESPUESTA, "Faltan credenciales del C20 en .env (C20_HOST, C20_USER, C20_PASS)", []

    try:
        session = pexpect.spawn(f'telnet {host} {port}', timeout=EXPECT_TIMEOUT,
                                encoding='utf-8', codec_errors='replace')
        # Mismo ritmo de envío que el worker, para que la prueba lo refleje
        session.delaybeforesend = 0.5
    except Exception as e:
        return SIN_RESPUESTA, f"No se pudo abrir telnet: {e}", []
    if captura is not None:
        session.logfile_read = captura

    try:
        resultado, motivo, texto = _login(session, user, password)
        codigo = CODIGOS.get(resultado, SIN_RESPUESTA)
        if codigo == OK:
            motivo = "Cuenta válida: el nodo aceptó el usuario y la contraseña"
            try:
                session.sendline('exit')
            except Exception:
                pass
        return codigo, motivo, _mensajes_del_nodo(texto, password)
    except Exception as e:
        return SIN_RESPUESTA, str(e), []
    finally:
        session.close()


def test_c20(debug=False):
    load_dotenv(os.path.join(BASE_DIR, '.env'))

    print("\n" + "="*60)
    print("🔐 VALIDACIÓN DE LA CUENTA C20")
    print("="*60)
    print(f"📡 Nodo: {os.getenv('C20_HOST', 'NODE_NOT_SET')}:{os.getenv('C20_PORT', '23')}")
    print(f"👤 Usuario: {os.getenv('C20_USER') or '(vacío)'}")
    print(f"⏳ Iniciando sesión ({EXPECT_TIMEOUT}s de espera por paso)...")

    captura = _Captura() if debug else None
    codigo, mensaje, lineas = validar_cuenta(captura)

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

    if debug:
        password = os.getenv('C20_PASS')
        crudo = captura.texto
        if password:
            crudo = crudo.replace(password, '*' * len(password))
        print("\n🔍 Diálogo crudo con el nodo (\\r y \\n visibles):")
        for linea in crudo.split('\n'):
            print(f"   {linea!r}")

    print("="*60 + "\n")
    return codigo


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Valida la cuenta del C20 contra el nodo.")
    parser.add_argument('--debug', action='store_true',
                        help="Muestra el diálogo crudo con el nodo (contraseña enmascarada)")
    sys.exit(test_c20(debug=parser.parse_args().debug))
