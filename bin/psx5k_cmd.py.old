import pexpect
import sys
import re
import os
import datetime
import shutil
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def test_connectivity():
    """
    Verifica si el servidor PSX responde a SSH.
    Retorna (True, message) o (False, error).
    """
    PSX_IP = os.getenv('PSX_IP')
    PSX_USER = os.getenv('PSX_USER')
    PSX_PASS = os.getenv('PSX_PASS')
    PSX_PORT = os.getenv('PSX_PORT', '22')

    if not all([PSX_IP, PSX_USER, PSX_PASS]):
        return False, "Faltan credenciales en .env"

    ssh_path = shutil.which('ssh')
    if not ssh_path:
        return False, "Binario 'ssh' no encontrado en el sistema (PATH)."

    try:
        cmd = pexpect.spawn(f'{ssh_path} -o StrictHostKeyChecking=no -p {PSX_PORT} {PSX_USER}@{PSX_IP}', timeout=10, encoding='utf-8', codec_errors='replace')
        idx = cmd.expect(['Password:', pexpect.EOF, pexpect.TIMEOUT])
        
        if idx == 0: # Password:
            cmd.sendline(PSX_PASS)
            idx2 = cmd.expect(['\r\n>', 'Permission denied', pexpect.TIMEOUT])
            if idx2 == 0:
                cmd.sendline('exit')
                return True, "Conexión exitosa"
            else:
                return False, "Error de autenticación o timeout en password"
        elif idx == 1:
            return False, "Conexión rechazada o cerrada por el host"
        else:
            return False, "Timeout al intentar conectar"
            
    except Exception as e:
        return False, str(e)

DEBUG_PSX_ENABLED = os.getenv('DEBUG_PSX', 'false').lower() == 'true'

class StreamLog:
    def __init__(self):
        self.content = ""
    def write(self, s):
        self.content += s
        if DEBUG_PSX_ENABLED:
            sys.stdout.write(s)
    def flush(self):
        sys.stdout.flush()

def psx5k_cmd(line_task, line_number, line_type=None, routing_label=None, force=False):
    """
    Función de ejecución para nodo PSX5K (Standalone para validación).
    
    line_task     = str ('add'/'del')
    line_number   = list [8147777000, ...]
    line_type     = str ('call_in'/'call_inout')
    routing_label = str (opcional)
    force         = bool (True para sobreescribir registros existentes)
    """
    
    # Obtener credenciales del entorno (Obligatorios en .env)
    PSX_IP = os.getenv('PSX_IP')
    PSX_USER = os.getenv('PSX_USER')
    PSX_PASS = os.getenv('PSX_PASS')
    PSX_PORT = os.getenv('PSX_PORT', '22')

    if not all([PSX_IP, PSX_USER, PSX_PASS]):
        raise EnvironmentError("Faltan configuraciones críticas de PSX en el archivo .env (PSX_IP, PSX_USER, PSX_PASS)")

    EXPECT = ['Password:', '\r\n>', 'PSXMASTER>']
    
    # Acumuladores de estado para reporte
    stats = {
        "total": 0,
        "ok": 0,
        "dup": 0,
        "force_ok": 0,
        "fail": 0,
        "logs": [],
        "full_flow": ""
    }

    stream = StreamLog()

    try:
        print(f"🚀 Conectando a PSX ({PSX_IP}) para tarea: {line_task.upper()} (Force: {force})...")
        
        ssh_path = shutil.which('ssh')
        if not ssh_path:
            raise FileNotFoundError("El ejecutable 'ssh' no fue encontrado. Asegúrate de que OpenSSH esté instalado y en el PATH.")

        # 1. Establecer Conexión SSH
        cmd = pexpect.spawn(f'{ssh_path} -o StrictHostKeyChecking=no -p {PSX_PORT} {PSX_USER}@{PSX_IP}', timeout=30, encoding='utf-8', codec_errors='replace')
        cmd.setecho(False)
        cmd.delaybeforesend = 0.8
        
        # Flujo de Login (Sin loggear para proteger credenciales)
        idx = cmd.expect(EXPECT)
        if idx == 0: # Password:
            cmd.sendline(PSX_PASS)
            cmd.expect(EXPECT)
            
        # ACTIVAR LOG después del login exitoso
        cmd.logfile = stream

        # Entrar a la instancia PSXMASTER
        cmd.sendline('s t i PSXMASTER')
        cmd.expect(EXPECT)
        
        # 2. Procesar Números (ANI)
        for number in line_number:
            if DEBUG_PSX_ENABLED:
                print(f"\n🔍 [DEBUG] Procesando ANI: {number}")
            stats["total"] += 1
            try:
                if line_task == 'add':
                    # Control de validación previa de existencia
                    SURE_CHECK = os.getenv('PSX_SURE_CHECK', 'true').lower() == 'true'
                    EXISTENCE_CHECK = os.getenv('PSX_EXISTENCE_CHECK', 'true').lower() == 'true'
                    
                    found = False
                    if EXISTENCE_CHECK or (SURE_CHECK or not force):
                        cmd.sendline(f'show subscriber Subscriber_Id {number} Country_Id 52')
                        cmd.expect(EXPECT)
                        result = cmd.before
                        found = 'ERR_REC_NOT_FOUND' not in result
                    else:
                        # Si se deshabilita el check de existencia, asumimos que no está o que no importa
                        found = False

                    if not found or force:
                        # Modo Inserción o Sobreescritura Forzada
                        is_force = found and force
                        msg_prefix = "[OK]" if not found else "[FORCE-OK]"
                        
                        if line_type == 'call_in':
                            cmd.sendline(f"put subscriber Subscriber_Id {number} Country_Id 52 Orig_Entity_Routing_Profile_Id 911 Is_Destination 1")
                            cmd.expect(EXPECT)
                            cmd.sendline(f"put destination National_Id {number} Country_Id 52 Custom_Script_Id BLOCKING Is_Subscriber 1")
                            cmd.expect(EXPECT)
                            if is_force: stats["force_ok"] += 1
                            else: stats["ok"] += 1
                            stats["logs"].append(f"{msg_prefix} {number} - call_in")
                            
                        elif line_type == 'call_inout':
                            cmd.sendline(f"put subscriber Subscriber_Id {number} Country_Id 52 Orig_Entity_Routing_Profile_Id 911 Is_Destination 1")
                            cmd.expect(EXPECT)
                            cmd.sendline(f"put destination National_Id {number} Country_Id 52 Custom_Script_Id \"\" Element_Attributes 0x20 Routing_Label_Id {routing_label} Is_Subscriber 1")
                            cmd.expect(EXPECT)
                            
                            # Validar si el routing_label era válido
                            if 'is not present in table "routing_label"' in cmd.before:
                                # Rollback si falló el label
                                cmd.sendline(f'delete subscriber Subscriber_Id {number} Country_Id 52')
                                cmd.expect(EXPECT)
                                cmd.sendline(f'delete destination National_Id {number} Country_Id 52')
                                cmd.expect(EXPECT)
                                stats["fail"] += 1
                                stats["logs"].append(f"[FAIL] {number} - Routing Label Inválido")
                            else:
                                if is_force: stats["force_ok"] += 1
                                else: stats["ok"] += 1
                                stats["logs"].append(f"{msg_prefix} {number} - call_inout")
                    else:
                        # Registro existente y no se pidió forzar
                        stats["dup"] += 1
                        stats["logs"].append(f"[DUP] {number} - Registro ya existente")

                elif line_task == 'delete':
                    # Para borrar no validamos previo, solo enviamos y si no hay excepción, es OK
                    cmd.sendline(f'delete subscriber Subscriber_Id {number} Country_Id 52')
                    cmd.expect(EXPECT)
                    cmd.sendline(f'delete destination National_Id {number} Country_Id 52')
                    cmd.expect(EXPECT)
                    
                    stats["ok"] += 1
                    stats["logs"].append(f"[DEL] {number} - Procesado")

            except Exception as e:
                stats["fail"] += 1
                stats["logs"].append(f"[ERROR] {number}: {str(e)}")

        # 3. Cerrar Sesión
        cmd.sendline('exit')
        cmd.expect(pexpect.EOF)
        print("\n✅ Sesión PSX finalizada.")
        
    except Exception as e:
        stats["fail"] = stats["total"] - stats["ok"] - stats["dup"] - stats["force_ok"]
        stats["logs"].append(f"CRITICAL ERROR: {str(e)}")
        print(f"\n❌ Error Crítico: {str(e)}")

    stats["full_flow"] = stream.content
    return stats
