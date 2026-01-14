"""
Listar todas las rutas disponibles en la API
"""
import requests

API_BASE_URL = "http://localhost:8000"

def list_routes():
    """Lista todas las rutas de la API"""
    try:
        # Intentar obtener el schema de OpenAPI
        response = requests.get(f"{API_BASE_URL}/openapi.json", timeout=5)

        if response.status_code == 200:
            schema = response.json()
            paths = schema.get("paths", {})

            print("[INFO] Rutas disponibles en la API:")
            print("=" * 80)

            for path, methods in paths.items():
                for method in methods.keys():
                    if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                        print(f"  {method.upper():6} {path}")

            print("=" * 80)
            print(f"[INFO] Total de rutas: {len(paths)}")

            # Buscar rutas que contengan "conversation"
            print("\n[INFO] Rutas relacionadas con 'conversation':")
            for path in paths.keys():
                if "conversation" in path.lower():
                    print(f"  - {path}")

        else:
            print(f"[ERROR] No se pudo obtener el schema: {response.status_code}")

    except requests.exceptions.ConnectionError:
        print("[ERROR] No se pudo conectar al servidor")
        print("        Verifique que la API este corriendo en http://localhost:8000")
    except Exception as e:
        print(f"[ERROR] {str(e)}")

if __name__ == "__main__":
    list_routes()
