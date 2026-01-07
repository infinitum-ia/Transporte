"""Test para verificar qué ve settings al importarse"""
import sys
import os

# Forzar recarga de settings
if 'src.infrastructure.config.settings' in sys.modules:
    del sys.modules['src.infrastructure.config.settings']

from src.infrastructure.config.settings import settings

print("=" * 80)
print("VALORES DE SETTINGS AL MOMENTO DE IMPORTACIÓN")
print("=" * 80)

print(f"\nAGENT_MODE: {settings.AGENT_MODE}")
print(f"EXCEL_PATH: {repr(settings.EXCEL_PATH)}")
print(f"EXCEL_BACKUP_FOLDER: {repr(settings.EXCEL_BACKUP_FOLDER)}")

if settings.EXCEL_PATH:
    from pathlib import Path
    p = Path(settings.EXCEL_PATH)
    print(f"\nArchivo existe: {p.exists()}")
    if p.exists():
        print(f"Tamaño: {p.stat().st_size} bytes")
else:
    print("\n⚠️  EXCEL_PATH es None o vacío!")

print("\n" + "=" * 80)
