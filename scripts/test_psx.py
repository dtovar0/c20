import os
import sys
import pexpect
import socket
import subprocess
from dotenv import load_dotenv

# Añadir el raíz del proyecto al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def print_step(msg):
    print(f"\n⏳ {msg}...")

def print_success(msg):
    print(f"  ✅ {msg}")

def print_error(msg):
    print(f"  ❌ {msg}")

def test_psx_connection():
    print("====================================")
    print("🔌 NODO PSX5K - DIAGNÓSTICO MANUAL")
    print("====================================")
    
    # 1. Cargar Variables de Entorno
    print_step("Cargando variables de entorno (.env)")
    load_dotenv()
    
    PSX_IP = os.getenv('PSX_IP')
    PSX_USER = os.getenv('PSX_USER')
    PSX_PASS = os.getenv('PSX_PASS')
    PSX_PORT = int(os.getenv('PSX_PORT', 22))
    
    if not all([PSX_IP, PSX_USER, PSX_PASS]):
        print_error("Faltan credenciales en el archivo .env (Revisa PSX_IP, PSX_USER, PSX_PASS)")
        return
    print_success(f"Variables cargadas (IP: {PSX_IP}, Usuario: {PSX_USER}, Puerto: {PSX_PORT})")

    # 2. Validar Ping (Host UP)
    print_step(f"Verificando disponibilidad de red (Ping a {PSX_IP})")
    try:
        # -c 1 para Linux/Mac, en Windows sería -n 1
        ping_cmd = ['ping', '-c', '1', '-W', '2', PSX_IP]
        result = subprocess.run(ping_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            print_success("El Host responde por red (ICMP Echo Ok).")
        else:
            print_error("El Host NO responde al ping. Verifica que el servidor está encendido y accesible en esta red.")
            # Continuamos de todas formas, algunos servidores bloquean ICMP
    except Exception as e:
        print_error(f"Error al ejecutar ping: {e}")

    # 3. Validar Puerto SSH Socket
    print_step(f"Verificando puerto SSH ({PSX_PORT}) abierto en {PSX_IP}")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((PSX_IP, PSX_PORT))
        if result == 0:
            print_success(f"Puerto {PSX_PORT} accesible.")
        else:
            print_error(f"El puerto {PSX_PORT} está cerrado o bloqueado por firewall.")
            sock.close()
            return # Si el puerto está cerrado, SSH definitivamente fallará
        sock.close()
    except Exception as e:
        print_error(f"Error evaluando el socket remoto: {e}")
        return

    # 4. Validar Autenticación SSH Local
    print_step("Verificando autenticación SSH con Pexpect")
    try:
        cmd_str = f'ssh -o StrictHostKeyChecking=no -p {PSX_PORT} {PSX_USER}@{PSX_IP}'
        cmd = pexpect.spawn(cmd_str, timeout=10, encoding='utf-8')
        
        idx = cmd.expect(['Password:', '[Pp]assword:', pexpect.EOF, pexpect.TIMEOUT])
        
        if idx in [0, 1]:  # Exige Password
            cmd.sendline(PSX_PASS)
            
            # Chequeamos si el comando fue aceptado o nos tiró Permission denied u el prompt de PSX
            idx2 = cmd.expect(['\r\n>', 'PSXMASTER>', 'Permission denied', pexpect.TIMEOUT])
            
            if idx2 == 0 or idx2 == 1:
                print_success("Autenticación SSH Exitosa. Las credenciales son CORRECTAS.")
                # Probar comando básico si gustan (Sino simplemente salimos)
                cmd.sendline('exit')
            elif idx2 == 2:
                print_error("Credenciales SSH INVALIDAS (Permission denied).")
            else:
                print_error("Autenticación SSH hizo Timeout después de enviar la contraseña.")
        elif idx == 2:
            print_error("Conexión rechazada o cerrada prematuramente por el host SSH.")
        elif idx == 3:
            print_error("Timeout esperando el prompt de 'Password:'. Verifica si la IP no filtra conexiones SSH.")
            
    except Exception as e:
        print_error(f"Falla general de SSH: {str(e)}")

    print("\n🏁 Proceso finalizado.")

if __name__ == '__main__':
    test_psx_connection()
