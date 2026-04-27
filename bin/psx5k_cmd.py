import pexpect
import sys
import os
import shutil
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuraciones globales desde ENV
DEBUG_PSX_ENABLED = os.getenv('DEBUG_PSX', 'false').lower() == 'true'
EXPECT_PROMPTS = ['Password:', '\r\n>', 'PSXMASTER>', 'PSX>', pexpect.TIMEOUT, pexpect.EOF]

class StreamLog:
    """Wrapper para capturar el flujo de salida sin saturar consola (a menos que se active DEBUG)"""
    def __init__(self):
        self.content = ""
    def write(self, s):
        self.content += s
        if DEBUG_PSX_ENABLED:
            sys.stdout.write(s)
    def flush(self):
        sys.stdout.flush()

def _check_psx_error(output):
    """
    Analiza la salida de PSX en busca de patrones de error comunes.
    Retorna (True, error_msg) si hay error, (False, None) si parece exitoso.
    """
    error_patterns = [
        ('ERR_REC_NOT_FOUND', "Registro no encontrado"),
        ('is not present in table', "Referencia inválida (Foreign Key)"),
        ('already exists', "El registro ya existe"),
        ('syntax error', "Error de sintaxis en comando"),
        ('Permission denied', "Permiso denegado en PSX"),
        ('Invalid command', "Comando no reconocido"),
        ('Database is locked', "Base de datos PSX ocupada/bloqueada")
    ]
    for pattern, msg in error_patterns:
        if pattern in output:
            return True, msg
    return False, None

def _get_psx_connection(timeout=15):
    """
    Helper interno para establecer conexión SSH básica.
    No entra en PSXMASTER, solo el túnel y login.
    """
    PSX_IP = os.getenv('PSX_IP')
    PSX_USER = os.getenv('PSX_USER')
    PSX_PASS = os.getenv('PSX_PASS')
    PSX_PORT = os.getenv('PSX_PORT', '22')

    if not all([PSX_IP, PSX_USER, PSX_PASS]):
        return None, "Faltan credenciales críticas en .env"

    ssh_path = shutil.which('ssh')
    if not ssh_path:
        return None, "Binario 'ssh' no encontrado en el sistema."

    try:
        connection_str = f'{ssh_path} -o StrictHostKeyChecking=no -p {PSX_PORT} {PSX_USER}@{PSX_IP}'
        cmd = pexpect.spawn(connection_str, timeout=timeout, encoding='utf-8', codec_errors='replace')
        cmd.setecho(False)
        cmd.delaybeforesend = 0.5
        
        idx = cmd.expect(EXPECT_PROMPTS)
        
        if idx == 0: # Password:
            cmd.sendline(PSX_PASS)
            idx2 = cmd.expect(EXPECT_PROMPTS)
            if idx2 in [1, 2, 3]: # Alguno de los prompts
                return cmd, "OK"
            else:
                return None, "Fallo de autenticación o Prompt no reconocido"
        elif idx in [1, 2, 3]: # Entró directo (ej. por llaves, aunque pida pass en env)
            return cmd, "OK"
        else:
            return None, "Timeout o Conexión rechazada"
            
    except Exception as e:
        return None, str(e)

def test_connectivity():
    """
    Verifica si el servidor PSX responde a SSH.
    Retorna (True, message) o (False, error).
    """
    cmd, msg = _get_psx_connection()
    if cmd:
        cmd.sendline('exit')
        cmd.close()
        return True, "Conexión exitosa"
    return False, msg

def psx5k_cmd(line_task, line_number, line_type=None, routing_label=None, force=False):
    """
    Motor de ejecución PSX5K optimizado.
    """
    stats = {
        "total": 0, "ok": 0, "dup": 0, "force_ok": 0, "fail": 0,
        "del": 0, "delcheck": 0,
        "logs": [], "full_flow": ""
    }
    stream = StreamLog()
    
    # 1. Establecer Conexión
    cmd, msg = _get_psx_connection(timeout=30)
    if not cmd:
        stats["fail"] = len(line_number)
        stats["logs"].append(f"CRITICAL: {msg}")
        return stats

    try:
        # Activar log para capturar el flujo operativo
        cmd.logfile = stream

        # 2. Entrar a la instancia PSXMASTER
        cmd.sendline('s t i PSXMASTER')
        idx = cmd.expect(EXPECT_PROMPTS)
        if idx != 2: # No llegamos al prompt PSXMASTER>
            raise ConnectionError(f"No se pudo activar instancia PSXMASTER. Prompt actual: {cmd.before}")

        # === TEST WATCHDOG POINT ===
        watchdog_sleep = os.getenv('TEST_WATCHDOG_SLEEP')
        if watchdog_sleep:
            import time
            print(f"DEBUG: [WATCHDOG TEST] Sleeping for {watchdog_sleep}s...")
            time.sleep(int(watchdog_sleep))

        # 3. Procesar Números (ANI)
        for number in line_number:
            stats["total"] += 1
            try:
                # Flags de control
                SURE_CHECK = os.getenv('PSX_SURE_CHECK', 'true').lower() == 'true'
                EXISTENCE_CHECK = os.getenv('PSX_EXISTENCE_CHECK', 'true').lower() == 'true'
                
                # --- PASO 1: VALIDACIÓN DE EXISTENCIA (SHOW) ---
                found = False
                # Siempre validamos si EXISTENCE_CHECK está activo, o si es un ADD sin FORCE
                if EXISTENCE_CHECK or (line_task == 'add' and (SURE_CHECK or not force)):
                    cmd.sendline(f'show subscriber Subscriber_Id {number} Country_Id 52')
                    cmd.expect(EXPECT_PROMPTS)
                    found = 'ERR_REC_NOT_FOUND' not in cmd.before
                else:
                    # Si no hay check de existencia activo (ej. en delete), asumimos que debemos intentar la operación
                    if line_task == 'delete':
                        found = True 

                # --- PASO 2: EJECUCIÓN SEGÚN EL TIPO ---
                
                # CASO A: AÑADIR (ADD)
                if line_task == 'add':
                    if not found or force:
                        is_force = found and force
                        msg_prefix = "[OK]" if not found else "[FORCE-OK]"
                        
                        if line_type == 'call_in':
                            # Registro de Subscriber
                            cmd.sendline(f"put subscriber Subscriber_Id {number} Country_Id 52 Orig_Entity_Routing_Profile_Id 911 Is_Destination 1")
                            cmd.expect(EXPECT_PROMPTS)
                            err, err_msg = _check_psx_error(cmd.before)
                            if err: raise Exception(f"Error Subscriber: {err_msg}")
                            
                            # Registro de Destination
                            cmd.sendline(f"put destination National_Id {number} Country_Id 52 Custom_Script_Id BLOCKING Is_Subscriber 1")
                            cmd.expect(EXPECT_PROMPTS)
                            err, err_msg = _check_psx_error(cmd.before)
                            if err: raise Exception(f"Error Destination: {err_msg}")

                            if is_force: stats["force_ok"] += 1
                            else: stats["ok"] += 1
                            stats["logs"].append(f"{msg_prefix} {number} - call_in")
                            
                        elif line_type == 'call_inout':
                            # Registro de Subscriber
                            cmd.sendline(f"put subscriber Subscriber_Id {number} Country_Id 52 Orig_Entity_Routing_Profile_Id 911 Is_Destination 1")
                            cmd.expect(EXPECT_PROMPTS)
                            err, err_msg = _check_psx_error(cmd.before)
                            if err: raise Exception(f"Error Subscriber: {err_msg}")

                            # Registro de Destination con Routing Label
                            cmd.sendline(f"put destination National_Id {number} Country_Id 52 Custom_Script_Id \"\" Element_Attributes 0x20 Routing_Label_Id {routing_label} Is_Subscriber 1")
                            cmd.expect(EXPECT_PROMPTS)
                            
                            if 'is not present in table "routing_label"' in cmd.before:
                                cmd.sendline(f'delete subscriber Subscriber_Id {number} Country_Id 52')
                                cmd.expect(EXPECT_PROMPTS)
                                stats["fail"] += 1
                                stats["logs"].append(f"[FAIL] {number} - Routing Label Inválido")
                            else:
                                err, err_msg = _check_psx_error(cmd.before)
                                if err: raise Exception(f"Error Destination: {err_msg}")
                                
                                if is_force: stats["force_ok"] += 1
                                else: stats["ok"] += 1
                                stats["logs"].append(f"{msg_prefix} {number} - call_inout")
                    else:
                        stats["dup"] += 1
                        stats["logs"].append(f"[DUP] {number} - Ya existe")

                # CASO B: ELIMINAR (DELETE)
                elif line_task == 'delete':
                    # Intento de borrado
                    cmd.sendline(f'delete subscriber Subscriber_Id {number} Country_Id 52')
                    cmd.expect(EXPECT_PROMPTS)
                    cmd.sendline(f'delete destination National_Id {number} Country_Id 52')
                    cmd.expect(EXPECT_PROMPTS)
                    
                    if found:
                        if EXISTENCE_CHECK:
                            stats["delcheck"] += 1
                            stats["logs"].append(f"[DELCHECK] {number} - Eliminado")
                        else:
                            stats["del"] += 1
                            stats["logs"].append(f"[DEL] {number} - Eliminado")
                    else:
                        stats["del"] += 1
                        stats["logs"].append(f"[DEL] {number} - No encontrado")

            except Exception as e:
                stats["fail"] += 1
                stats["logs"].append(f"[ERROR] {number}: {str(e)}")

        # 4. Cerrar Sesión
        cmd.sendline('exit')
        cmd.expect(pexpect.EOF)
        
    except Exception as e:
        stats["fail"] = stats["total"] - (stats["ok"] + stats["dup"] + stats["force_ok"])
        stats["logs"].append(f"CRITICAL ERROR: {str(e)}")
        if DEBUG_PSX_ENABLED: print(f"❌ Error Crítico: {str(e)}")

    stats["full_flow"] = stream.content
    return stats
