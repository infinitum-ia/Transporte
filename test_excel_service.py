"""Test directo del ExcelOutboundService"""
import os
from pathlib import Path
from src.infrastructure.config.settings import settings
from src.infrastructure.persistence.excel_service import ExcelOutboundService

print("=" * 80)
print("TEST DIRECTO DE EXCEL SERVICE")
print("=" * 80)

print(f"\n1. EXCEL_PATH: {settings.EXCEL_PATH}")
print(f"   Existe: {Path(settings.EXCEL_PATH).exists() if settings.EXCEL_PATH else False}")

if settings.EXCEL_PATH and os.path.exists(settings.EXCEL_PATH):
    print("\n2. Intentando inicializar ExcelOutboundService...")
    try:
        service = ExcelOutboundService(
            excel_path=settings.EXCEL_PATH,
            backup_folder=settings.EXCEL_BACKUP_FOLDER
        )
        print("   OK: Servicio inicializado correctamente")

        print("\n3. Cargando llamadas pendientes...")
        pending = service.get_pending_calls()
        print(f"   OK: {len(pending)} llamadas pendientes encontradas")

        if pending:
            print("\n4. Primera llamada:")
            call = pending[0]
            print(f"   Nombre: {call.nombre_completo}")
            print(f"   Telefono: {call.telefono}")
            print(f"   Servicio: {call.tipo_servicio}")
            print(f"   Fecha: {call.fecha_servicio}")

        print("\n5. Estadisticas:")
        stats = service.get_statistics()
        print(f"   Total: {stats['total']}")
        print(f"   Pendientes: {stats['pendiente']}")

    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback
        traceback.print_exc()
else:
    print("\nERROR: EXCEL_PATH no existe o no esta configurado")
    if settings.EXCEL_PATH:
        print(f"   Ruta configurada: {settings.EXCEL_PATH}")
        print(f"   Existe: {os.path.exists(settings.EXCEL_PATH)}")

print("\n" + "=" * 80)
