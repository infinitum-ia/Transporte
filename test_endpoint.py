"""
Script de prueba rapida para verificar el endpoint unified
"""
import requests
import json

API_BASE_URL = "http://localhost:8000/api/v1"

def test_endpoint():
    """Prueba el endpoint unified"""
    url = f"{API_BASE_URL}/conversation/unified"

    payload = {
        "PATIENT_PHONE": "3001234567",
        "MESSAGE": "START",
        "IS_OUTBOUND": True,
        "AGENT_NAME": "Maria"
    }

    print(f"[TEST] Probando endpoint: {url}")
    print(f"[TEST] Payload: {json.dumps(payload, indent=2)}")
    print("-" * 80)

    try:
        response = requests.post(url, json=payload, timeout=10)

        print(f"[TEST] Status Code: {response.status_code}")
        print(f"[TEST] Response: {json.dumps(response.json(), indent=2)}")

        if response.status_code == 200:
            print("\n[OK] Endpoint funcionando correctamente")
        else:
            print(f"\n[ERROR] Status: {response.status_code}")

    except requests.exceptions.ConnectionError:
        print("[ERROR] No se pudo conectar al servidor")
        print("        Verifique que la API este corriendo en http://localhost:8000")
    except Exception as e:
        print(f"[ERROR] {str(e)}")

if __name__ == "__main__":
    test_endpoint()
