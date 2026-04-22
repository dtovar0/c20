import pexpect
import sys
import re
import os
import datetime

def s5k_cmd(line_task, line_number, line_type=None, routing_label=None, force=False):
    """
    Función de ejecución para nodo PSX5K (Standalone para validación).
    
    line_task     = str ('add'/'del')
    line_number   = list [8147777000, ...]
    line_type     = str ('call_in'/'call_inout')
    routing_label = str (opcional)
    force         = bool (True para sobreescribir registros existentes)
    """
    
    EXPECT = ['Password:', '\r\n>', 'PSXMASTER>']
    
    # Acumuladores de estado para reporte
    stats = {
        "total": 0,
        "ok": 0,
        "dup": 0,
        "fail": 0,
        "logs": []
    }

    try:
        print(f"🚀 Conectando a PSX (10.133.39.5) para tarea: {line_task.upper()} (Force: {force})...")
        
        # 1. Establecer Conexión SSH
        cmd = pexpect.spawn('ssh -o StrictHostKeyChecking=no -p 8122 admin@10.133.39.5', timeout=30, encoding='utf-8')
        cmd.logfile = sys.stdout # Mantenemos logfile activado para validación del usuario
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
                    
                    found = 'ERR_REC_NOT_FOUND' not in result
                    
                    if not found or force:
                        # Modo Inserción o Sobreescritura Forzada
                        msg_prefix = "[OK]" if not found else "[FORCE-OK]"
                        
                        if line_type == 'call_in':
                            cmd.sendline(f"put subscriber Subscriber_Id {number} Country_Id 52 Orig_Entity_Routing_Profile_Id 911 Is_Destination 1")
                            cmd.expect(EXPECT)
                            cmd.sendline(f"put destination National_Id {number} Country_Id 52 Custom_Script_Id BLOCKING Is_Subscriber 1")
                            cmd.expect(EXPECT)
                            stats["ok"] += 1
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
                                stats["ok"] += 1
                                stats["logs"].append(f"{msg_prefix} {number} - call_inout")
                    else:
                        # Registro existente y no se pidió forzar
                        stats["dup"] += 1
                        stats["logs"].append(f"[DUP] {number} - Registro ya existente")

                elif line_task == 'del':
                    cmd.sendline(f'delete subscriber Subscriber_Id {number} Country_Id 52')
                    cmd.expect(EXPECT)
                    cmd.sendline(f'delete destination National_Id {number} Country_Id 52')
                    cmd.expect(EXPECT)
                    stats["ok"] += 1
                    stats["logs"].append(f"[DEL] {number} - Eliminado")

            except Exception as e:
                stats["fail"] += 1
                stats["logs"].append(f"[ERROR] {number}: {str(e)}")

        # 3. Cerrar Sesión
        cmd.sendline('exit')
        cmd.expect(pexpect.EOF)
        print("\n✅ Sesión PSX finalizada.")
        
    except Exception as e:
        stats["fail"] = stats["total"] - stats["ok"] - stats["dup"]
        stats["logs"].append(f"CRITICAL ERROR: {str(e)}")
        print(f"\n❌ Error Crítico: {str(e)}")

    return stats

if __name__ == "__main__":
    # Bloque de prueba rápida
    print("--- INICIO VALIDACIÓN STANDALONE ---")
    test_anis = ["8147777000"]
    # Prueba con force=True para validar la nueva lógica
    res = s5k_cmd('add', test_anis, 'call_in', force=True)
    print("\n--- RESUMEN FINAL ---")
    print(f"Total: {res['total']} | OK: {res['ok']} | DUP: {res['dup']} | FAIL: {res['fail']}")
    for log in res['logs']:
        print(log)
