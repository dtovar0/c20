import os
import sys
import time
import datetime
import pexpect
from app import create_app
from app.modules.notifications.services import send_notification_by_slug
from app.modules.auth.models import User
from psx5k_cmd import test_connectivity

# Configuración
CHECK_INTERVAL = 300  # 5 minutos
MAX_RETRIES = 2       # Reintentos antes de alertar

def monitor():
    app = create_app()
    print(f"🕵️ PSX5K Watchdog iniciado - Intervalo: {CHECK_INTERVAL}s")
    
    last_status_ok = True

    while True:
        try:
            ok, msg = test_connectivity()
            
            if not ok:
                print(f"[{datetime.datetime.now()}] ❌ Fallo de conectividad: {msg}")
                
                # Reintentar una vez más antes de alarmar
                time.sleep(10)
                ok_retry, msg_retry = test_connectivity()
                
                if not ok_retry and last_status_ok:
                    # Solo enviar correo si el estado anterior era OK (para evitar spam)
                    print("🚨 Alarma enviada: Perda de conectividad persistente.")
                    
                    with app.app_context():
                        admin = User.query.filter_by(role='administrador').first()
                        if admin and admin.username:
                            send_notification_by_slug(
                                slug='error', 
                                target_email=admin.username,
                                context={
                                    'usuario': 'SYSTEM_WATCHDOG', 
                                    'ip': os.getenv('PSX_IP', 'DESCONOCIDA'), 
                                    'error': f'CONECTIVIDAD PSX PERDIDA: {msg_retry}'
                                }
                            )
                    last_status_ok = False
            else:
                if not last_status_ok:
                    print(f"[{datetime.datetime.now()}] ✅ Conectividad restaurada.")
                    # Opcional: enviar correo de recuperación
                    last_status_ok = True
                else:
                    print(f"[{datetime.datetime.now()}] ✅ PSX OK")

        except Exception as e:
            print(f"⚠️ Error en monitor: {e}")

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    monitor()
