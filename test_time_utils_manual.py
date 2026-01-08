"""
Quick manual test for time_utils to verify it works correctly
"""
from datetime import datetime
from src.shared.utils.time_utils import (
    get_bogota_time,
    get_time_of_day_period,
    get_greeting,
    get_farewell
)

print("=" * 60)
print("TIME UTILS MANUAL TEST")
print("=" * 60)

# Get current time
bogota_time = get_bogota_time()
print(f"\n1. Hora actual en Bogotá: {bogota_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
print(f"   Hora en formato 24h: {bogota_time.hour}:{bogota_time.minute:02d}")

# Get period
period = get_time_of_day_period()
print(f"\n2. Período del día: {period}")

# Get greeting
greeting = get_greeting()
print(f"\n3. Saludo: {greeting}")

# Get farewell
farewell = get_farewell()
print(f"\n4. Despedida: {farewell}")

# Show ranges
print("\n" + "=" * 60)
print("RANGOS ESPERADOS:")
print("=" * 60)
print("06:00 - 11:59 → mañana  → Buenos días / Que tenga un excelente día")
print("12:00 - 18:59 → tarde   → Buenas tardes / Que tenga una excelente tarde")
print("19:00 - 05:59 → noche   → Buenas noches / Que tenga una excelente noche")
print("=" * 60)

# Verify logic
hour = bogota_time.hour
expected_period = None
expected_greeting = None
expected_farewell = None

if 6 <= hour < 12:
    expected_period = "mañana"
    expected_greeting = "Buenos días"
    expected_farewell = "Que tenga un excelente día"
elif 12 <= hour < 19:
    expected_period = "tarde"
    expected_greeting = "Buenas tardes"
    expected_farewell = "Que tenga una excelente tarde"
else:
    expected_period = "noche"
    expected_greeting = "Buenas noches"
    expected_farewell = "Que tenga una excelente noche"

print(f"\n✅ VERIFICACIÓN:")
print(f"   Hora actual: {hour}:00")
print(f"   Período esperado: {expected_period}")
print(f"   Período actual: {period}")
print(f"   Match: {'✅ SÍ' if period == expected_period else '❌ NO'}")
print()
print(f"   Saludo esperado: {expected_greeting}")
print(f"   Saludo actual: {greeting}")
print(f"   Match: {'✅ SÍ' if greeting == expected_greeting else '❌ NO'}")
print()
print(f"   Despedida esperada: {expected_farewell}")
print(f"   Despedida actual: {farewell}")
print(f"   Match: {'✅ SÍ' if farewell == expected_farewell else '❌ NO'}")
print()

if period == expected_period and greeting == expected_greeting and farewell == expected_farewell:
    print("🎉 TODOS LOS TESTS PASARON - El módulo funciona correctamente")
else:
    print("⚠️ HAY PROBLEMAS - El módulo no está funcionando como esperado")
