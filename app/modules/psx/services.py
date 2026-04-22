import pexpect
import sys
import re
from datetime import datetime

def run_psx_task(line_task, line_number, line_type=None, routing_label=None):
    """
    Ejecuta comandos en el nodo PSX5K mediante SSH interactivo (pexpect).
    
    line_task     = str ('add'/'del')
    line_number   = list [8147777000, ...]
    line_type     = str ('call_in'/'call_inout')
    routing_label = str (opcional)
    """
    
    EXPECT = ['Password:', '\r\n>', 'PSXMASTER>']
    
    # Acumuladores de estado
    stats = {
        "total": 0,
        "ok": 0,
        "dup": 0,
        "fail": 0,
        "logs": []
    }

    try:
        # 1. Establecer Conexión SSH
        cmd = pexpect.spawn('ssh -o StrictHostKeyChecking=no -p 8122 admin@10.133.39.5', timeout=30, encoding='utf-8')
        # cmd.logfile = sys.stdout # Activar para depuración en consola del backend
        cmd.setecho(False)
        cmd.delaybeforesend = 0.8
        
        # Flujo de Login
        idx = cmd.expect(EXPECT)
        if idx == 0: # Password:
            cmd.sendline('M4rc4t3l#2012')
            cmd.expect(EXPECT)
            
        # Entrar a la instancia PSXMASTER
        cmd.sendline('s t i PSXMASTER')
        cmd.expect(EXPECT)
        
        # 2. Procesar Números (ANI)
        for number in line_number:
            stats["total"] += 1
            try:
                if line_task == 'add':
                    # Verificar existencia previa
                    cmd.sendline(f'show subscriber Subscriber_Id {number} Country_Id 52')
                    cmd.expect(EXPECT)
                    result = cmd.before
                    
                    if 'ERR_REC_NOT_FOUND' in result:
                        if line_type == 'call_in':
                            cmd.sendline(f"put subscriber Subscriber_Id {number} Country_Id 52 Orig_Entity_Routing_Profile_Id 911 Is_Destination 1")
                            cmd.expect(EXPECT)
                            cmd.sendline(f"put destination National_Id {number} Country_Id 52 Custom_Script_Id BLOCKING Is_Subscriber 1")
                            cmd.expect(EXPECT)
                            stats["ok"] += 1
                            stats["logs"].append(f"[OK] {number} - call_in")
                            
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
                                stats["ok"] += 1
                                stats["logs"].append(f"[OK] {number} - call_inout")
                    else:
                        stats["dup"] += 1
                        stats["logs"].append(f"[DUP] {number} - Ya existe")

                elif line_task == 'del':
                    cmd.sendline(f'delete subscriber Subscriber_Id {number} Country_Id 52')
                    cmd.expect(EXPECT)
                    cmd.sendline(f'delete destination National_Id {number} Country_Id 52')
                    cmd.expect(EXPECT)
                    stats["ok"] += 1
                    stats["logs"].append(f"[DEL] {number}")

            except Exception as e:
                stats["fail"] += 1
                stats["logs"].append(f"[ERROR] {number}: {str(e)}")

        # 3. Cerrar Sesión
        cmd.sendline('exit')
        cmd.expect(pexpect.EOF)
        
    except Exception as e:
        stats["fail"] = stats["total"] - stats["ok"] - stats["dup"]
        stats["logs"].append(f"CRITICAL ERROR: {str(e)}")

    return stats
