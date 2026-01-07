"""Script para diagnosticar problemas con EXCEL_PATH"""
import os
from pathlib import Path
from src.infrastructure.config.settings import settings

print("=" * 80)
print("DIAGNÓSTICO DE CONFIGURACIÓN EXCEL")
print("=" * 80)

print(f"\n1. EXCEL_PATH desde settings:")
print(f"   Valor: {repr(settings.EXCEL_PATH)}")
print(f"   Tipo: {type(settings.EXCEL_PATH)}")

if settings.EXCEL_PATH:
    print(f"\n2. Verificando existencia del archivo:")
    print(f"   os.path.exists(): {os.path.exists(settings.EXCEL_PATH)}")
    print(f"   Path.exists(): {Path(settings.EXCEL_PATH).exists()}")

    # Intentar con barras normales
    normalized_path = str(settings.EXCEL_PATH).replace('\\', '/')
    print(f"\n3. Ruta normalizada:")
    print(f"   Valor: {normalized_path}")
    print(f"   Existe: {os.path.exists(normalized_path)}")

    # Intentar ruta raw
    print(f"\n4. Intentando con pathlib:")
    p = Path(settings.EXCEL_PATH)
    print(f"   Path object: {p}")
    print(f"   Absolute: {p.absolute()}")
    print(f"   Exists: {p.exists()}")

    if p.exists():
        print(f"   Size: {p.stat().st_size} bytes")

else:
    print("\n⚠️  EXCEL_PATH no está configurado en settings")
    print("   Verifica que esté en el archivo .env")

print(f"\n5. Archivo .env:")
env_path = Path(".env")
print(f"   Existe: {env_path.exists()}")

if env_path.exists():
    print(f"\n   Contenido relacionado con EXCEL:")
    with open(".env", "r", encoding="utf-8") as f:
        for line in f:
            if "EXCEL" in line:
                print(f"   {line.rstrip()}")

print("\n" + "=" * 80)
