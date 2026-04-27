import requests
import json

# Configuración
BASE_URL = "http://10.224.2.146" # Cambiar por la IP/URL de tu servidor
API_TOKEN = "nexus_secret_token_2024" # Token definido en el .env
HEADERS = {
    "X-API-TOKEN": API_TOKEN
}

def upload_and_create_task():
    print(f"🚀 Iniciando proceso táctico en {BASE_URL}...")

    # PASO 1: Subir el archivo
    # Supongamos que tenemos un archivo local llamado 'numeros.csv'
    # Creamos uno temporal para este ejemplo
    with open('test_ani.csv', 'w') as f:
        f.write("1141234560\n1141234561\n1141234562-1141234565\n")

    print("📁 Subiendo archivo de registros...")
    with open('test_ani.csv', 'rb') as f:
        files = {'file': f}
        r_upload = requests.post(f"{BASE_URL}/api/v1/tasks/upload", headers=HEADERS, files=files)
    
    if r_upload.status_code != 200:
        print(f"❌ Error al subir: {r_upload.text}")
        return

    filename = r_upload.json().get('filename')
    print(f"✅ Archivo aceptado como: {filename}")

    # PASO 2: Crear la tarea referenciando el archivo
    payload = {
        "tarea": "add",
        "accion_tipo": "bulk",
        "datos_tipo": "Archivo",
        "datos": filename,
        "routing_label": "API_PYTHON_TEST",
        "force": True
    }

    print("⚙️ Programando ejecución masiva...")
    r_create = requests.post(
        f"{BASE_URL}/api/v1/tasks/create", 
        headers=HEADERS, 
        json=payload
    )

    if r_create.status_code == 201:
        res = r_create.json()
        print(f"🎯 ¡Éxito! Job Maestro: {res.get('job_id')}")
        print(f"📦 Fragmentos generados: {res.get('task_ids')}")
    else:
        print(f"❌ Error al crear tarea: {r_create.text}")

if __name__ == "__main__":
    upload_and_create_task()
