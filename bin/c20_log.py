"""
Log a archivo del motor C20, compartido por el worker y sus secciones.

Complementa a los dos registros que ya existían, que dejaban un hueco:

  - c20_command_logs (BD) guarda el flujo de una tarea, pero solo al cerrarla:
    si la sesión muere a medias, o el worker se cae, no queda nada.
  - DEBUG_C20 hacía eco a stdout, que bajo systemd va al journal y se pierde si
    el proceso se lanzó redirigido a /dev/null.

Este módulo escribe a logs/c20_worker.log con rotación, de forma continua, así
que el rastro sobrevive a una sesión interrumpida y no depende de cómo se haya
levantado el proceso.

Se controla con dos variables independientes:

  C20_LOG_ENABLED  -> escribir el archivo (por defecto true)
  DEBUG_C20        -> además, eco a stdout (por defecto false)

Nada aquí interrumpe una tarea: si el archivo no se puede abrir o escribir, el
log se degrada a silencio y la sesión con el nodo sigue su curso.
"""
import logging
import logging.handlers
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

LOG_ENABLED = os.getenv('C20_LOG_ENABLED', 'true').lower() == 'true'
LOG_DIR = os.getenv('C20_LOG_DIR', os.path.join(PROJECT_ROOT, 'logs'))
LOG_FILE = os.path.join(LOG_DIR, os.getenv('C20_LOG_FILE', 'c20_worker.log'))
LOG_MAX_BYTES = int(os.getenv('C20_LOG_MAX_BYTES', 10 * 1024 * 1024))
LOG_BACKUPS = int(os.getenv('C20_LOG_BACKUPS', 5))

_logger = None


def get_logger():
    """
    Devuelve el logger del motor, creándolo la primera vez.

    propagate=False lo mantiene fuera del logger raíz: el flujo del nodo es
    ruidoso y no tiene por qué acabar en los handlers de Flask.
    """
    global _logger
    if _logger is not None:
        return _logger

    log = logging.getLogger('c20')
    log.setLevel(logging.DEBUG)
    log.propagate = False

    if LOG_ENABLED and not log.handlers:
        try:
            os.makedirs(LOG_DIR, exist_ok=True)
            handler = logging.handlers.RotatingFileHandler(
                LOG_FILE, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUPS,
                encoding='utf-8')
            handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s %(message)s'))
            log.addHandler(handler)
        except Exception as e:
            # Sin permisos o sin disco: seguimos sin log en archivo.
            print(f"⚠️  C20: no se pudo abrir {LOG_FILE}: {e}")

    if not log.handlers:
        log.addHandler(logging.NullHandler())

    _logger = log
    return _logger


def log_line(message, level=logging.INFO):
    """Registra un evento del worker. Nunca propaga una excepción."""
    try:
        get_logger().log(level, message)
    except Exception:
        pass


def log_stream(text):
    """
    Registra un fragmento crudo de la sesión con el nodo.

    Llega en trozos arbitrarios desde pexpect, así que se parte por líneas para
    que cada una quede con su marca de tiempo. Los fragmentos sin '\\n' se
    escriben tal cual: partirlos más sería inventar límites que no existen.
    """
    if not text:
        return
    try:
        log = get_logger()
        for line in text.splitlines():
            if line.strip():
                log.debug('| %s', line.rstrip())
    except Exception:
        pass
