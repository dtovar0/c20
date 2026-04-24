import sys
import os

# Agrega la ruta base del proyecto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from psx5k_cmd import test_connectivity

def test_psx():
    print("\n" + "="*60)
    print("🛰️  PRUEBA DE COMUNICACIÓN PSX5K")
    print("="*60)

    # El host se toma de las variables de entorno cargadas por la app
    from dotenv import load_dotenv
    load_dotenv()
    
    host = os.getenv('PSX_IP', 'NODE_NOT_SET')
    print(f"📡 Intentando conectar con el nodo PSX en: {host}")
    print("⏳ Realizando handshake SSH y validación de prompts (15s timeout)...")

    success, msg = test_connectivity()

    if success:
        print("\n✅ RESULTADO: CONEXIÓN EXITOSA")
        print(f"📝 Respuesta del sistema: {msg}")
    else:
        print("\n❌ RESULTADO: FALLO DE CONEXIÓN")
        print(f"📝 Error reportado: {msg}")
        print("\n💡 Tip: Verifica que la VPN esté activa y que las credenciales PSX_* en .env sean correctas.")

    print("="*60 + "\n")

if __name__ == '__main__':
    test_psx()
