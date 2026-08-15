"""
Motor de ejecución del C20, compartido por sus secciones (C20 y Teams).

Sustituye a los scripts expect del sistema legado (add/del_SNPANAME, TOFCNAME,
OFC2CODE, DNSCRN, por sección) por una única sesión telnet que recorre las
tablas en orden. El comportamiento frente al nodo es el mismo; lo que cambia es
que antes se abrían cuatro sesiones por tarea —una por script, con las
credenciales escritas en cada archivo— y ahora se abre una sola, con las
credenciales en el .env.

Las secciones comparten nodo, tablas, jerarquía y confirmaciones; lo único que
difiere es cómo se construye el alta en OFC2CODE, que cada una define en
SECTION_PROFILES.

Jerarquía del C20: lada -> serie -> número. El contenedor debe existir antes que
lo contenido, de ahí el orden en las altas. Una baja no retira ladas ni series:
solo se sacan los números de OFC2CODE y DNSCRN.

Semántica de los veredictos, uniforme en las cuatro tablas:
  OK   -> se ejecutó la operación
  FAIL -> no se hizo nada porque el registro no estaba en el estado esperado
          (en 'add' ya existía; en 'del' no existía). No es un error.
  ERROR-> el nodo respondió algo inesperado o no respondió. Sí es un error.
          (El sistema legado no distinguía este caso: los .exp no tenían rama
          por defecto, así que esos números desaparecían del log en silencio.)
"""
import os
import sys
import time

import pexpect
from dotenv import load_dotenv

load_dotenv()

DEBUG_ENABLED = os.getenv('DEBUG_C20', 'false').lower() == 'true'

# Ladas de 2 dígitos (Monterrey, Guadalajara, CDMX). El resto usa 3.
# En ambos casos lada + serie suman 6 dígitos.
LADAS_CORTAS = {'81', '33', '55'}

# Segundos de espera entre tablas, como el flujo original entre scripts.
SLEEP_BETWEEN_TABLES = int(os.getenv('C20_SLEEP_BETWEEN_TABLES', 5))
# Espera tras cada 'pos', que el nodo necesita para responder.
CMD_DELAY = float(os.getenv('C20_CMD_DELAY', 1))
EXPECT_TIMEOUT = int(os.getenv('C20_EXPECT_TIMEOUT', 15))


# --- PERFILES POR SECCIÓN ---
# Lo único que distingue a una sección de otra es cómo construye el alta en
# OFC2CODE. Todo lo demás (SNPANAME, TOFCNAME, DNSCRN, bajas, confirmaciones)
# es idéntico.
#
#   C20   -> zona 900 da terminación; el resto rutea a un destino fijo. En el
#            sistema legado la línea que usaba la zona real estaba comentada y
#            el destino quedó fijo en 504.
#   Teams -> prefijo 100 rutea a DEST 16; el resto inserta el prefijo con
#            traducción a la troncal de Teams.

C20_ZONA_TERMINACION = os.getenv('C20_ZONA_TERMINACION', '900')
C20_DEST = os.getenv('C20_DEST_DEFAULT', '504')
C20_ZONA_DEFAULT = os.getenv('C20_ZONA_DEFAULT', '504')

TEAMS_PREFIJO_DIRECTO = os.getenv('TEAMS_PREFIJO_DIRECTO', '100')
TEAMS_DEST_DIRECTO = os.getenv('TEAMS_DEST_DIRECTO', '16')
TEAMS_XLT = os.getenv('TEAMS_XLT', 'PX2')
TEAMS_TRONCAL = os.getenv('TEAMS_TRONCAL', 'MSTEAMS2')
TEAMS_PREFIJO_DEFAULT = os.getenv('TEAMS_PREFIJO_DEFAULT', '')

def _ofc2code_add_c20(numero, parametro):
    if str(parametro) == C20_ZONA_TERMINACION:
        return f'add LCL_SUB {numero} {numero} TRMT OFC UNDN $'
    return f'add LCL_SUB {numero} {numero} RTE DEST {C20_DEST} $'


def _ofc2code_add_teams(numero, parametro):
    if str(parametro) == TEAMS_PREFIJO_DIRECTO:
        return f'add LCL_SUB {numero} {numero} RTE DEST {TEAMS_DEST_DIRECTO} $'
    return (f'add LCL_SUB {numero} {numero} DMOD INSRT {parametro} '
            f'XLT {TEAMS_XLT} {TEAMS_TRONCAL} $')


SECTION_PROFILES = {
    'c20': {
        'ofc2code_add': _ofc2code_add_c20,
        'parametro_default': C20_ZONA_DEFAULT,
    },
    'teams': {
        'ofc2code_add': _ofc2code_add_teams,
        'parametro_default': TEAMS_PREFIJO_DEFAULT,
    },
}

TABLES = ('snpaname', 'tofcname', 'ofc2code', 'dnscrn')

# Orden jerárquico: la lada y la serie deben existir antes que el número.
TABLES_ADD = ('snpaname', 'tofcname', 'ofc2code', 'dnscrn')
# Un 'del' no da de baja ladas ni series: solo se retiran los números.
TABLES_DEL = ('ofc2code', 'dnscrn')

# Respuestas del nodo. 'TUPLE NOT FOUND' y 'KEY NOT FOUND' significan que el
# registro no existe; el prompt a secas significa que sí existe.
NOT_FOUND = ('TUPLE NOT FOUND', 'KEY NOT FOUND')
PROMPT = r'\r\n>'


class StreamLog:
    """Captura el flujo de la sesión sin saturar consola (salvo con DEBUG_C20)."""
    def __init__(self):
        self.content = ""

    def write(self, s):
        self.content += s
        if DEBUG_ENABLED:
            sys.stdout.write(s)

    def flush(self):
        if DEBUG_ENABLED:
            sys.stdout.flush()


def split_number(numero):
    """
    Descompone un número en (lada, serie) según la regla del C20.

    81/33/55 -> lada de 2 dígitos + serie de 4
    resto    -> lada de 3 dígitos + serie de 3

    Devuelve (None, None) si el número es demasiado corto para descomponerlo.
    """
    numero = (numero or '').strip()
    if len(numero) < 6:
        return None, None

    if numero[:2] in LADAS_CORTAS:
        return numero[:2], numero[2:6]
    return numero[:3], numero[3:6]


def build_hierarchy(numeros):
    """
    Deriva las ladas y series únicas de una lista de números, preservando el
    orden de aparición.

    Devuelve (ladas, series) donde cada serie es la tupla (lada, serie): el nodo
    las recibe separadas por espacio, igual que en el archivo c20_serie.exp.
    """
    ladas, series = [], []
    seen_l, seen_s = set(), set()

    for numero in numeros:
        lada, serie = split_number(numero)
        if not lada:
            continue

        if lada not in seen_l:
            seen_l.add(lada)
            ladas.append(lada)

        if (lada, serie) not in seen_s:
            seen_s.add((lada, serie))
            series.append((lada, serie))

    return ladas, series


def _connect(timeout=EXPECT_TIMEOUT):
    """
    Abre la sesión telnet y autentica contra el nodo C20.

    Devuelve (sesión, "OK") o (None, motivo).
    """
    host = os.getenv('C20_HOST')
    user = os.getenv('C20_USER')
    password = os.getenv('C20_PASS')
    port = os.getenv('C20_PORT', '23')

    if not all([host, user, password]):
        return None, "Faltan credenciales del C20 en .env (C20_HOST, C20_USER, C20_PASS)"

    try:
        session = pexpect.spawn(f'telnet {host} {port}', timeout=timeout,
                                encoding='utf-8', codec_errors='replace')
        session.delaybeforesend = 0.5

        # El nodo pide usuario y contraseña con etiqueta; algunos scripts del
        # sistema legado esperaban solo el prompt, así que se aceptan ambos.
        idx = session.expect(['Enter User Name', PROMPT, pexpect.TIMEOUT, pexpect.EOF])
        if idx in (2, 3):
            session.close()
            return None, "El nodo no respondió al inicio de sesión"

        session.sendline(user)
        session.expect(['Enter Password', PROMPT, pexpect.TIMEOUT, pexpect.EOF])
        session.sendline(password)

        idx = session.expect([PROMPT, pexpect.TIMEOUT, pexpect.EOF])
        if idx != 0:
            session.close()
            return None, "Fallo de autenticación o prompt no reconocido"

        return session, "OK"
    except Exception as e:
        return None, str(e)


def test_connectivity():
    """Verifica que el nodo C20 responda y acepte las credenciales."""
    session, msg = _connect(timeout=10)
    if session:
        try:
            session.sendline('exit')
            session.close()
        except Exception:
            pass
        return True, "Conexión exitosa"
    return False, msg


def _drain(session):
    """
    Descarta lo que quede en el buffer.

    Necesario antes de cada consulta: el nodo hace eco de los comandos y deja su
    prompt pendiente, así que sin vaciar primero el siguiente expect() casaría
    con la respuesta anterior en vez de la nueva.
    """
    try:
        while True:
            session.expect([PROMPT, pexpect.TIMEOUT, pexpect.EOF], timeout=0.2)
            if session.after in (pexpect.TIMEOUT, pexpect.EOF):
                break
    except Exception:
        pass


def _select_table(session, tabla):
    """Posiciona la sesión en una tabla del nodo."""
    _drain(session)
    session.sendline(f'Table {tabla.upper()}')
    session.expect([tabla.upper(), pexpect.TIMEOUT, pexpect.EOF])
    _drain(session)


def _exists(session, pos_cmd):
    """
    Ejecuta un 'pos' y determina si el registro existe.

    Se espera el patrón discriminante ('TUPLE/KEY NOT FOUND' frente a cualquier
    otra respuesta), no el prompt: el prompt aparece en ambos casos y no
    distingue nada.

    Devuelve (existe, ok) donde ok es False si el nodo no respondió: ese caso se
    reporta como ERROR en vez de asumirse, que es lo que hacía el sistema legado
    (sus scripts no tenían rama por defecto y perdían esos números en silencio).
    """
    _drain(session)
    session.sendline(pos_cmd)
    if CMD_DELAY:
        time.sleep(CMD_DELAY)

    idx = session.expect(['TUPLE NOT FOUND', 'KEY NOT FOUND', PROMPT,
                          pexpect.TIMEOUT, pexpect.EOF])
    if idx in (0, 1):
        return False, True
    if idx == 2:
        return True, True
    return None, False


def _confirm(session, doble=True):
    """
    Responde a las confirmaciones del nodo tras un add/del.

    La mayoría de tablas piden dos ('CONTINUE PROCESSING' y luego 'CONFIRM');
    SNPANAME solo pide la segunda.
    """
    if doble:
        idx = session.expect(['ENTER Y TO CONTINUE PROCESSING', 'ENTER Y TO CONFIRM',
                              pexpect.TIMEOUT, pexpect.EOF])
        if idx == 0:
            session.sendline('Y')
            if session.expect(['ENTER Y TO CONFIRM', pexpect.TIMEOUT, pexpect.EOF]) != 0:
                return False
            session.sendline('Y')
        elif idx == 1:
            session.sendline('Y')
        else:
            return False
    else:
        if session.expect(['ENTER Y TO CONFIRM', pexpect.TIMEOUT, pexpect.EOF]) != 0:
            return False
        session.sendline('Y')

    _drain(session)
    return True


def _process_snpaname(session, ladas, accion):
    """Altas de lada. Confirmación simple; no interviene en bajas."""
    entries = []
    for lada in ladas:
        existe, ok = _exists(session, f'pos {lada}')
        if not ok:
            entries.append((lada, 'error'))
            continue
        if existe:
            entries.append((lada, 'fail'))
            continue
        session.sendline(f'add {lada} $')
        entries.append((lada, 'ok' if _confirm(session, doble=False) else 'error'))
    return entries


def _process_tofcname(session, series, accion):
    """Altas de serie. El nodo las recibe como 'LADA SERIE'."""
    entries = []
    for lada, serie in series:
        clave = f'{lada} {serie}'
        existe, ok = _exists(session, f'pos {clave}')
        if not ok:
            entries.append((clave, 'error'))
            continue
        if existe:
            entries.append((clave, 'fail'))
            continue
        session.sendline(f'add {clave} $')
        entries.append((clave, 'ok' if _confirm(session) else 'error'))
    return entries


def _process_ofc2code(session, numeros, accion, parametro, build_add):
    """
    Altas y bajas de número en OFC2CODE.

    Es la única tabla cuyo comando de alta depende de la sección: `build_add`
    lo construye según el perfil (ver SECTION_PROFILES). La baja es idéntica
    en todas.
    """
    entries = []
    for numero in numeros:
        existe, ok = _exists(session, f'pos LCL_SUB {numero} {numero}')
        if not ok:
            entries.append((numero, 'error'))
            continue

        if accion == 'add':
            if existe:
                entries.append((numero, 'fail'))
                continue
            session.sendline(build_add(numero, parametro))
            entries.append((numero, 'ok' if _confirm(session) else 'error'))
        else:
            if not existe:
                entries.append((numero, 'fail'))
                continue
            session.sendline(f'del LCL_SUB {numero} {numero} $')
            entries.append((numero, 'ok' if _confirm(session) else 'error'))
    return entries


def _process_dnscrn(session, numeros, accion):
    """Altas y bajas de número en DNSCRN."""
    entries = []
    for numero in numeros:
        existe, ok = _exists(session, f'pos {numero}')
        if not ok:
            entries.append((numero, 'error'))
            continue

        if accion == 'add':
            if existe:
                entries.append((numero, 'fail'))
                continue
            session.sendline(f'add {numero} CLISERV 1 $')
            entries.append((numero, 'ok' if _confirm(session) else 'error'))
        else:
            if not existe:
                entries.append((numero, 'fail'))
                continue
            session.sendline(f'del {numero} $')
            entries.append((numero, 'ok' if _confirm(session) else 'error'))
    return entries


def _tally(entries):
    """Convierte una lista de veredictos en contadores."""
    return {
        "total": len(entries),
        "ok": sum(1 for _, v in entries if v == 'ok'),
        "fail": sum(1 for _, v in entries if v == 'fail'),
        "error": sum(1 for _, v in entries if v == 'error'),
        "entries": entries,
    }


def c20_cmd(line_task, line_number, parametro=None, seccion='c20'):
    """
    Ejecuta una tarea completa contra el C20 en una sola sesión.

    line_task: 'add' o 'del' ('delete' también se acepta: es la etiqueta de la UI)
    line_number: lista de números
    parametro: zona (C20) o prefijo (Teams); por defecto el del perfil
    seccion: 'c20' o 'teams' — determina cómo se construye el alta en OFC2CODE

    Devuelve un dict con los contadores por tabla, más 'ladas'/'series' para
    sincronizar el espejo, 'errors' y 'full_flow' con la sesión cruda.
    """
    perfil = SECTION_PROFILES.get(seccion)
    if not perfil:
        raise ValueError(f"Sección desconocida: {seccion}")

    accion = 'del' if line_task in ('del', 'delete') else 'add'
    if parametro in (None, ''):
        parametro = perfil['parametro_default']
    tablas = TABLES_ADD if accion == 'add' else TABLES_DEL

    results = {t: _tally([]) for t in TABLES}
    results.update({"accion": accion, "seccion": seccion, "errors": [],
                    "full_flow": "", "ladas": [], "series": []})

    if not line_number:
        results["errors"].append("Lote vacío: no hay números que procesar")
        return results

    ladas, series = build_hierarchy(line_number)
    results["ladas"] = ladas
    results["series"] = [f"{l} {s}" for l, s in series]

    if DEBUG_ENABLED:
        print(f"🔍 {seccion.upper()} [{accion}] números={len(line_number)} "
              f"ladas={len(ladas)} series={len(series)} parametro={parametro}")

    session, msg = _connect()
    if not session:
        results["errors"].append(f"Conexión: {msg}")
        return results

    stream = StreamLog()
    session.logfile = stream

    build_add = perfil['ofc2code_add']
    handlers = {
        'snpaname': lambda: _process_snpaname(session, ladas, accion),
        'tofcname': lambda: _process_tofcname(session, series, accion),
        'ofc2code': lambda: _process_ofc2code(session, line_number, accion, parametro, build_add),
        'dnscrn':   lambda: _process_dnscrn(session, line_number, accion),
    }

    try:
        for idx, tabla in enumerate(tablas):
            print(f"▶️  Corriendo {tabla.upper()}")
            try:
                _select_table(session, tabla)
                results[tabla] = _tally(handlers[tabla]())
            except Exception as e:
                print(f"❌ {tabla.upper()}: {e}")
                results["errors"].append(f"{tabla}: {e}")

            # El nodo necesita margen entre tablas; se omite tras la última.
            if idx < len(tablas) - 1 and SLEEP_BETWEEN_TABLES:
                time.sleep(SLEEP_BETWEEN_TABLES)

        try:
            session.sendline('exit')
            session.expect([pexpect.EOF, pexpect.TIMEOUT])
        except Exception:
            pass
    except Exception as e:
        results["errors"].append(f"Sesión interrumpida: {e}")
    finally:
        try:
            session.close()
        except Exception:
            pass
        results["full_flow"] = stream.content

    return results
