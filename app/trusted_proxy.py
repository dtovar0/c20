"""
Validación del origen de las cabeceras de identidad del SSO.

Authelia se aplica inyectando cabeceras (`Remote-Email`, `Remote-User`…) en la
petición desde el reverse proxy. El backend deduce de ellas quién eres, así que
solo son fiables si nadie más puede ponerlas: cualquiera que alcance el puerto
de la aplicación podría enviar `Remote-Email: admin@empresa.com` y entrar como
administrador.

`TRUSTED_PROXIES` declara desde qué direcciones se aceptan. Por defecto solo
loopback, que es donde escucha el proxy en un despliegue normal.

    TRUSTED_PROXIES=127.0.0.1,::1
    TRUSTED_PROXIES=10.0.0.0/8,127.0.0.1     # también acepta redes CIDR
    TRUSTED_PROXIES=*                        # desactiva la comprobación
"""

import ipaddress
import os

from flask import request

DEFAULT_TRUSTED = '127.0.0.1,::1'


def _entries():
    raw = os.getenv('TRUSTED_PROXIES', DEFAULT_TRUSTED)
    return [item.strip() for item in raw.split(',') if item.strip()]


def is_trusted_proxy(remote_addr=None):
    """True si la petición viene de un origen autorizado a inyectar cabeceras.

    Acepta direcciones sueltas y redes en notación CIDR. Con `*` se desactiva
    la comprobación, lo que solo tiene sentido si el puerto ya está aislado por
    otros medios.
    """
    entries = _entries()
    if '*' in entries:
        return True

    addr = remote_addr if remote_addr is not None else request.remote_addr
    if not addr:
        return False

    try:
        client = ipaddress.ip_address(addr)
    except ValueError:
        # Un remote_addr no parseable no se considera de confianza.
        return False

    for entry in entries:
        try:
            if '/' in entry:
                if client in ipaddress.ip_network(entry, strict=False):
                    return True
            elif client == ipaddress.ip_address(entry):
                return True
        except ValueError:
            # Una entrada mal escrita se ignora en lugar de tumbar la petición.
            continue
    return False


def sso_identity_headers():
    """Cabeceras de identidad del SSO, o None si el origen no es de confianza.

    Devuelve (email, name, groups). Centraliza la lectura para que ningún punto
    de la aplicación toque `request.headers` del SSO sin pasar por aquí.
    """
    if not is_trusted_proxy():
        return None

    candidates = [
        os.getenv('AUTHELIA_HEADER_USER', 'Remote-Email'),
        'X-Forwarded-Email',
        'Remote-User',
        'X-Forwarded-User',
    ]
    email = None
    for header in candidates:
        value = request.headers.get(header)
        if value:
            email = value.strip()
            break
    if not email:
        return None

    name = request.headers.get(
        os.getenv('AUTHELIA_HEADER_NAME', 'Remote-Name'), email)
    groups = request.headers.get(
        os.getenv('AUTHELIA_HEADER_GROUPS', 'Remote-Groups'), '')
    return email, name, groups


def describe():
    """Resumen legible de la configuración, para diagnóstico."""
    entries = _entries()
    if '*' in entries:
        return 'TRUSTED_PROXIES=* (comprobación desactivada)'
    return 'TRUSTED_PROXIES=' + ','.join(entries)
