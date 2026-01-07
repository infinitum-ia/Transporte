"""
Test Simple de Llamada Saliente (OUTBOUND)

Script automatizado para probar rápidamente una llamada saliente completa.
No requiere interacción del usuario.
"""
import requests
import sys
import time


# Configuración
API_BASE_URL = "http://localhost:8000/api/v1"
PATIENT_PHONE = "3001234567"  # ⚠️ CAMBIAR por un teléfono que exista en tu Excel


def test_outbound_call():
    """Test automatizado de llamada saliente"""

    print("=" * 80)
    print("TEST AUTOMATIZADO DE LLAMADA SALIENTE")
    print("=" * 80)

    try:
        # 1. Verificar que el API esté disponible
        print("\n[1/8] Verificando API...")
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        assert response.status_code == 200, "API no disponible"
        print("✅ API disponible")

        # 2. Consultar llamadas pendientes
        print("\n[2/8] Consultando llamadas pendientes...")
        response = requests.get(f"{API_BASE_URL}/calls/outbound/pending")
        assert response.status_code == 200, "Error al consultar llamadas pendientes"
        pending = response.json()
        print(f"✅ {pending['total_pending']} llamadas pendientes")

        # 3. Crear sesión OUTBOUND
        print(f"\n[3/8] Creando sesión OUTBOUND para teléfono {PATIENT_PHONE}...")
        response = requests.post(
            f"{API_BASE_URL}/calls/outbound",
            json={
                "patient_phone": PATIENT_PHONE,
                "agent_name": "María"
            }
        )

        if response.status_code == 404:
            print(f"\n❌ ERROR: No se encontró paciente con teléfono {PATIENT_PHONE}")
            print("\n💡 SOLUCIÓN:")
            print("   1. Verifica que el archivo Excel esté configurado en EXCEL_PATH")
            print("   2. Asegúrate de que el teléfono existe en el Excel")
            print("   3. El formato debe ser: 10 dígitos sin espacios")
            print(f"\n   Detalle del error: {response.json().get('detail', 'N/A')}")
            return False

        assert response.status_code == 201, f"Error al crear sesión: {response.status_code}"
        session_data = response.json()
        session_id = session_data['session_id']
        print(f"✅ Sesión creada: {session_id}")
        print(f"   Paciente: {session_data['patient_name']}")
        print(f"   Servicio: {session_data['service_type']}")
        print(f"   Fecha: {session_data['appointment_date']}")

        # Función auxiliar para enviar mensajes
        def send_message(message: str, step: str):
            print(f"\n[{step}] Usuario: {message}")
            response = requests.post(
                f"{API_BASE_URL}/conversation/message/v2",
                headers={"X-Session-ID": session_id},
                json={"message": message}
            )
            assert response.status_code == 200, f"Error al enviar mensaje: {response.status_code}"
            data = response.json()
            print(f"   Agente: {data['agent_response'][:100]}...")
            print(f"   Fase: {data['conversation_phase']}")
            if 'confirmation_status' in data.get('metadata', {}):
                print(f"   Estado: {data['metadata']['confirmation_status']}")
            time.sleep(0.5)
            return data

        # 4. Saludo inicial
        send_message("Hola", "4/8")

        # 5. Aceptar aviso legal
        send_message("Sí, autorizo la grabación", "5/8")

        # 6. Confirmar servicio
        send_message("Sí, confirmo el servicio. Todo está correcto", "6/8")

        # 7. Despedida
        result = send_message("Muchas gracias. Hasta luego", "7/8")

        # 8. Verificar detalles finales
        print("\n[8/8] Consultando detalles finales de la sesión...")
        response = requests.get(f"{API_BASE_URL}/calls/{session_id}")
        assert response.status_code == 200, "Error al consultar sesión"
        final_data = response.json()

        print("\n" + "=" * 80)
        print("RESUMEN DE LA LLAMADA")
        print("=" * 80)
        print(f"Session ID: {final_data['session_id']}")
        print(f"Paciente: {final_data['patient_name']}")
        print(f"Tipo llamada: {final_data['call_direction']}")
        print(f"Fase final: {final_data['conversation_phase']}")
        print(f"Estado confirmación: {final_data.get('confirmation_status', 'N/A')}")
        print(f"Servicio confirmado: {final_data.get('service_confirmed', False)}")

        # Verificar que se haya completado correctamente
        assert final_data['conversation_phase'] in ['END', 'OUTBOUND_CLOSING'], \
            f"La conversación no terminó correctamente: {final_data['conversation_phase']}"

        print("\n" + "=" * 80)
        print("✅ TEST COMPLETADO EXITOSAMENTE")
        print("=" * 80)
        print("\n💾 El archivo Excel debería estar actualizado con el estado de la llamada")

        # Mostrar estadísticas finales
        print("\n📊 Consultando estadísticas...")
        response = requests.get(f"{API_BASE_URL}/calls/statistics")
        if response.status_code == 200:
            stats = response.json()
            print(f"\nEstadísticas actuales:")
            print(f"  Total: {stats['total']}")
            print(f"  Pendientes: {stats['pendiente']}")
            print(f"  Confirmadas: {stats['confirmado']}")

        return True

    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: No se puede conectar al API")
        print("\n💡 SOLUCIÓN:")
        print("   Asegúrate de que el servidor esté corriendo:")
        print("   uvicorn src.presentation.api.main:app --reload")
        return False

    except AssertionError as e:
        print(f"\n❌ ERROR EN EL TEST: {e}")
        return False

    except Exception as e:
        print(f"\n❌ ERROR INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Función principal"""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║           TEST SIMPLE DE LLAMADA SALIENTE - TRANSFORMAS TRANSPORT            ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)

    print(f"\nConfigiguración:")
    print(f"  API URL: {API_BASE_URL}")
    print(f"  Teléfono: {PATIENT_PHONE}")
    print(f"\n⚠️  Asegúrate de:")
    print(f"  1. El servidor esté corriendo (uvicorn ...)")
    print(f"  2. Redis esté activo")
    print(f"  3. AGENT_MODE=llm en .env")
    print(f"  4. EXCEL_PATH configurado con un archivo válido")
    print(f"  5. El teléfono {PATIENT_PHONE} exista en el Excel")
    print(f"\n  Presiona ENTER para continuar o Ctrl+C para cancelar...")

    try:
        input()
    except KeyboardInterrupt:
        print("\n\n👋 Test cancelado")
        return

    success = test_outbound_call()

    if success:
        print("\n🎉 ¡Test exitoso!")
        sys.exit(0)
    else:
        print("\n💥 Test falló. Revisa los mensajes de error arriba.")
        sys.exit(1)


if __name__ == "__main__":
    main()
