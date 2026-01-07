"""
Test de Llamada Saliente (OUTBOUND)

Este script prueba el flujo completo de una llamada saliente:
1. Consulta llamadas pendientes
2. Crea sesión OUTBOUND
3. Simula conversación de confirmación
4. Verifica estado actualizado
5. Consulta estadísticas
"""
import requests
import time
import json
from typing import Dict, Any


# Configuración
API_BASE_URL = "http://localhost:8000/api/v1"
PATIENT_PHONE = "3001234567"  # Cambiar por un teléfono que exista en tu Excel
COMPLAINT_EXAMPLE_PHONE = PATIENT_PHONE  # Default: usa un teléfono válido del Excel/API


class OutboundCallTester:
    """Tester para llamadas salientes"""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session_id = None

    def print_separator(self, title: str):
        """Imprime un separador visual"""
        print("\n" + "=" * 80)
        print(f"  {title}")
        print("=" * 80 + "\n")

    def print_response(self, response: Dict[Any, Any], title: str = "Response"):
        """Imprime una respuesta JSON formateada"""
        print(f"\n{title}:")
        print(json.dumps(response, indent=2, ensure_ascii=False))

    def check_health(self) -> bool:
        """Verifica que el API esté disponible"""
        self.print_separator("1. VERIFICANDO SALUD DEL API")
        try:
            response = requests.get(f"{self.base_url}/health")
            if response.status_code == 200:
                print("✅ API está en línea y funcionando")
                self.print_response(response.json(), "Health Status")
                return True
            else:
                print(f"❌ API respondió con código: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print(f"❌ No se puede conectar al API en {self.base_url}")
            print("   Asegúrate de que el servidor esté corriendo:")
            print("   uvicorn src.presentation.api.main:app --reload")
            return False

    def get_pending_calls(self) -> Dict[Any, Any]:
        """Obtiene lista de llamadas pendientes"""
        self.print_separator("2. CONSULTANDO LLAMADAS PENDIENTES")
        try:
            response = requests.get(f"{self.base_url}/calls/outbound/pending")
            response.raise_for_status()
            data = response.json()
            print(f"✅ Llamadas pendientes encontradas: {data['total_pending']}")

            if data['total_pending'] > 0:
                print("\nPrimeras 3 llamadas:")
                for i, call in enumerate(data['calls'][:3], 1):
                    print(f"\n  {i}. {call['patient_name']}")
                    print(f"     Teléfono: {call['patient_phone']}")
                    print(f"     Servicio: {call['service_type']}")
                    print(f"     Fecha: {call['appointment_date']} {call['appointment_time']}")
                    print(f"     Ciudad: {call['city']}")
            else:
                print("⚠️  No hay llamadas pendientes")
                print("   Verifica que el archivo Excel tenga registros con estado 'Pendiente'")

            return data
        except requests.exceptions.RequestException as e:
            print(f"❌ Error al consultar llamadas pendientes: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   Detalle: {e.response.text}")
            return {"total_pending": 0, "calls": []}

    def create_outbound_session(self, phone: str, agent_name: str = "María") -> bool:
        """Crea una sesión OUTBOUND"""
        self.print_separator("3. CREANDO SESIÓN OUTBOUND")
        print(f"Teléfono del paciente: {phone}")
        print(f"Agente: {agent_name}")

        try:
            response = requests.post(
                f"{self.base_url}/calls/outbound",
                json={
                    "patient_phone": phone,
                    "agent_name": agent_name
                }
            )
            response.raise_for_status()
            data = response.json()

            self.session_id = data['session_id']
            print(f"✅ Sesión creada exitosamente")
            print(f"\nSession ID: {self.session_id}")
            print(f"Paciente: {data['patient_name']}")
            print(f"Servicio: {data['service_type']}")
            print(f"Fecha cita: {data['appointment_date']}")

            return True
        except requests.exceptions.RequestException as e:
            print(f"❌ Error al crear sesión: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    print(f"   Detalle: {error_data.get('detail', 'Error desconocido')}")
                except:
                    print(f"   Detalle: {e.response.text}")
            return False

    def send_message(self, message: str, step_number: int, description: str) -> Dict[Any, Any]:
        """Envía un mensaje en la conversación"""
        self.print_separator(f"{step_number}. {description}")
        print(f"Usuario: {message}")

        try:
            response = requests.post(
                f"{self.base_url}/conversation/message/v2",
                headers={"X-Session-ID": self.session_id},
                json={"message": message}
            )
            response.raise_for_status()
            data = response.json()

            print(f"\n{'María (Agente)'}: {data['agent_response']}")
            print(f"\n📍 Fase: {data['conversation_phase']}")

            if data.get('call_direction'):
                print(f"📞 Tipo de llamada: {data['call_direction']}")

            if data.get('metadata', {}).get('confirmation_status'):
                print(f"✅ Estado: {data['metadata']['confirmation_status']}")

            extracted = (data.get("metadata") or {}).get("extracted") or {}
            if extracted.get("incident_summary"):
                print(f"📝 Incidencia detectada: {extracted['incident_summary']}")
            if extracted.get("appointment_date_changed") is True:
                print(f"📅 Cambio de fecha detectado: {extracted.get('new_appointment_date')}")
            if extracted.get("special_needs"):
                print(f"♿ Necesidad especial detectada: {extracted.get('special_needs')}")
            if extracted.get("coverage_issue") is True:
                print(f"🗺️ Zona sin cobertura detectada: {extracted.get('location')}")
            if extracted.get("patient_away") is True:
                print(f"✈️ Paciente fuera detectado: {extracted.get('return_date')}")

            if data.get('requires_escalation'):
                print(f"⚠️  Requiere escalamiento: {data['metadata'].get('escalation_reason', 'N/A')}")

            time.sleep(1)  # Pausa para legibilidad
            return data
        except requests.exceptions.RequestException as e:
            print(f"❌ Error al enviar mensaje: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    print(f"   Detalle: {error_data.get('detail', 'Error desconocido')}")
                except:
                    print(f"   Detalle: {e.response.text}")
            return {}

    def get_session_details(self) -> Dict[Any, Any]:
        """Obtiene detalles completos de la sesión"""
        self.print_separator("CONSULTANDO DETALLES DE LA SESIÓN")
        try:
            response = requests.get(f"{self.base_url}/calls/{self.session_id}")
            response.raise_for_status()
            data = response.json()

            print("✅ Detalles de la sesión:")
            print(f"\nPaciente: {data.get('patient_name', 'N/A')}")
            print(f"Documento: {data.get('patient_document', 'N/A')}")
            print(f"Servicio: {data.get('service_type', 'N/A')}")
            print(f"Fase actual: {data.get('conversation_phase', 'N/A')}")
            print(f"Estado confirmación: {data.get('confirmation_status', 'N/A')}")
            print(f"Servicio confirmado: {data.get('service_confirmed', False)}")

            return data
        except requests.exceptions.RequestException as e:
            print(f"❌ Error al consultar sesión: {e}")
            return {}

    def get_statistics(self) -> Dict[Any, Any]:
        """Obtiene estadísticas de llamadas"""
        self.print_separator("CONSULTANDO ESTADÍSTICAS GENERALES")
        try:
            response = requests.get(f"{self.base_url}/calls/statistics")
            response.raise_for_status()
            data = response.json()

            print("✅ Estadísticas del sistema:")
            print(f"\nTotal de llamadas: {data['total']}")
            print(f"  - Pendientes: {data['pendiente']}")
            print(f"  - Confirmadas: {data['confirmado']}")
            print(f"  - Reprogramar: {data['reprogramar']}")
            print(f"  - Rechazadas: {data['rechazado']}")
            print(f"  - No contesta: {data['no_contesta']}")
            print(f"  - Sin cobertura: {data['zona_sin_cobertura']}")

            print("\nPor tipo de servicio:")
            for service_type, count in data['by_service_type'].items():
                print(f"  - {service_type}: {count}")

            print("\nPor modalidad:")
            for modality, count in data['by_modality'].items():
                print(f"  - {modality}: {count}")

            return data
        except requests.exceptions.RequestException as e:
            print(f"❌ Error al consultar estadísticas: {e}")
            return {}

    def run_successful_confirmation_flow(self, phone: str):
        """Ejecuta flujo completo de confirmación exitosa"""
        print("\n" + "🚀" * 40)
        print("INICIANDO TEST DE LLAMADA SALIENTE - CONFIRMACIÓN EXITOSA")
        print("🚀" * 40)

        # 1. Verificar salud
        if not self.check_health():
            return False

        # 2. Ver llamadas pendientes
        self.get_pending_calls()

        # 3. Crear sesión
        if not self.create_outbound_session(phone):
            return False

        # 4. Flujo conversacional
        # Saludo inicial
        self.send_message(
            "Hola",
            4,
            "SALUDO INICIAL DEL PACIENTE"
        )

        # Aceptar aviso legal
        self.send_message(
            "Sí, autorizo la grabación",
            5,
            "ACEPTACIÓN AVISO LEGAL"
        )

        # Confirmar servicio
        self.send_message(
            "Sí, confirmo el servicio. Todo está bien",
            6,
            "CONFIRMACIÓN DEL SERVICIO"
        )

        # Despedida
        self.send_message(
            "Muchas gracias. Hasta luego",
            7,
            "DESPEDIDA"
        )

        # 5. Ver detalles finales
        self.get_session_details()

        # 6. Ver estadísticas
        self.get_statistics()

        self.print_separator("✅ TEST COMPLETADO EXITOSAMENTE")
        print("La llamada fue confirmada y el Excel debería estar actualizado")
        print(f"Session ID: {self.session_id}")

        return True

    def run_reschedule_flow(self, phone: str):
        """Ejecuta flujo de reprogramación"""
        print("\n" + "🚀" * 40)
        print("INICIANDO TEST DE LLAMADA SALIENTE - REPROGRAMACIÓN")
        print("🚀" * 40)

        # 1. Verificar salud
        if not self.check_health():
            return False

        # 2. Crear sesión
        if not self.create_outbound_session(phone):
            return False

        # 3. Flujo conversacional
        self.send_message("Hola", 3, "SALUDO INICIAL")
        self.send_message("Sí, autorizo", 4, "ACEPTACIÓN AVISO LEGAL")
        self.send_message(
            "No puedo ese día, necesito cambiar la fecha",
            5,
            "SOLICITUD DE REPROGRAMACIÓN"
        )
        self.send_message(
            "Prefiero el próximo martes a las 10am",
            6,
            "NUEVA FECHA PROPUESTA"
        )
        self.send_message("Gracias, adiós", 7, "DESPEDIDA")

        # 4. Ver detalles finales
        self.get_session_details()

        self.print_separator("✅ TEST DE REPROGRAMACIÓN COMPLETADO")
        return True

    def run_rejection_flow(self, phone: str):
        """Ejecuta flujo de rechazo"""
        print("\n" + "🚀" * 40)
        print("INICIANDO TEST DE LLAMADA SALIENTE - RECHAZO")
        print("🚀" * 40)

        # 1. Verificar salud
        if not self.check_health():
            return False

        # 2. Crear sesión
        if not self.create_outbound_session(phone):
            return False

        # 3. Flujo conversacional
        self.send_message("Hola", 3, "SALUDO INICIAL")
        self.send_message("Sí, autorizo", 4, "ACEPTACIÓN AVISO LEGAL")
        self.send_message(
            "No, ya no necesito el servicio. Cancelo la cita",
            5,
            "RECHAZO DEL SERVICIO"
        )
        self.send_message("Gracias de todas formas. Adiós", 6, "DESPEDIDA")

        # 4. Ver detalles finales
        self.get_session_details()

        self.print_separator("✅ TEST DE RECHAZO COMPLETADO")
        return True

    def run_driver_complaint_flow(self, phone: str):
        """Ejecuta flujo de confirmación con queja (conversación compleja)"""
        print("\n" + "🚨" * 40)
        print("INICIANDO TEST DE LLAMADA SALIENTE - CONFIRMACIÓN CON QUEJA (COMPLEJO)")
        print("🚨" * 40)

        # 1. Verificar salud
        if not self.check_health():
            return False

        # 2. Ver llamadas pendientes
        self.get_pending_calls()

        # 3. Crear sesión
        if not self.create_outbound_session(phone):
            return False

        # 4. Flujo conversacional (mezcla confirmación + queja + aclaraciones)
        self.send_message("Hola", 4, "SALUDO INICIAL")
        self.send_message("Sí, soy el paciente", 5, "CONFIRMACIÓN DE IDENTIDAD")
        self.send_message("Sí, autorizo la grabación", 6, "ACEPTACIÓN AVISO LEGAL")

        self.send_message(
            "Lunes, miércoles y viernes. Correcto... pero tengo una inquietud: yo tenía mi chófer, el señor Juan Carlos. "
            "Ya sabe dónde vivo, pero los chóferes que me han puesto me vienen a buscar muy temprano o llegan demasiado tarde. "
            "La vez pasada casi pierdo la diálisis por la demora.",
            7,
            "QUEJA POR ROTACIÓN DE CONDUCTORES"
        )

        self.send_message(
            "Colabórame, por favor. Ayúdame para ver si me pueden poner a mi chófer Juan Carlos, porque con ese señor no tengo problemas.",
            8,
            "SOLICITUD EXPLÍCITA DE CONDUCTOR"
        )

        self.send_message(
            "Yo confirmo el servicio, pero necesito que respeten el horario y que el conductor me llame antes de llegar. "
            "Si vuelve a pasar, voy a poner la queja formal.",
            9,
            "CONFIRMACIÓN CON CONDICIÓN Y SEGUIMIENTO"
        )

        self.send_message("Gracias, adiós", 10, "CIERRE")

        # Ver detalles finales
        self.get_session_details()

        self.print_separator("✅ TEST DE QUEJA COMPLETADO")
        return True

    def run_wheelchair_special_needs_flow(self, phone: str):
        """Caso complejo: familiar reporta silla de ruedas + queja por vehículo pequeño"""
        print("\n" + "♿" * 40)
        print("INICIANDO TEST DE LLAMADA SALIENTE - SILLA DE RUEDAS / VEHÍCULO GRANDE (COMPLEJO)")
        print("♿" * 40)

        if not self.check_health():
            return False

        self.get_pending_calls()

        if not self.create_outbound_session(phone):
            return False

        self.send_message("Hola", 4, "SALUDO INICIAL")
        self.send_message("Habla Ludíz, soy la mamá y responsable del paciente", 5, "CONFIRMACIÓN (FAMILIAR)")
        self.send_message("Sí, autorizo la grabación", 6, "AVISO LEGAL")

        self.send_message(
            "Sí, es a la 1 de la tarde... pero la última vez tuve un inconveniente: "
            "el conductor llegó en una van pequeña y pretendía que yo me sentara adelante con el niño. "
            "Yo necesito dos asientos disponibles porque el niño lleva silla de ruedas.",
            7,
            "REPORTE DE NECESIDAD ESPECIAL + QUEJA"
        )

        self.send_message(
            "Siempre tengo el mismo inconveniente y siempre que llaman me toca decir lo mismo y lo mismo... ya estoy cansada de repetir.",
            8,
            "FRUSTRACIÓN POR REPETICIÓN"
        )

        self.send_message(
            "Yo confirmo el servicio, pero por favor registren lo del carro grande y los dos asientos. "
            "Si no, no me sirve y me toca llamar a la EPS.",
            9,
            "CONFIRMACIÓN CON CONDICIÓN"
        )

        self.send_message("Gracias, hasta luego", 10, "CIERRE")
        self.get_session_details()
        self.print_separator("✅ TEST SILLA DE RUEDAS COMPLETADO")
        return True

    def run_out_of_coverage_flow(self, phone: str):
        """Caso complejo: usuario reporta zona sin cobertura (Hachaca) + ajuste de fechas"""
        print("\n" + "🗺️" * 40)
        print("INICIANDO TEST DE LLAMADA SALIENTE - ZONA SIN COBERTURA (COMPLEJO)")
        print("🗺️" * 40)

        if not self.check_health():
            return False

        self.get_pending_calls()

        if not self.create_outbound_session(phone):
            return False

        self.send_message("Hola", 4, "SALUDO INICIAL")
        self.send_message("Sí, soy Emilce", 5, "CONFIRMACIÓN DE IDENTIDAD")
        self.send_message("Sí, autorizo la grabación", 6, "AVISO LEGAL")

        self.send_message(
            "Tengo una observación: el centro abre el 7, entonces realmente me recogerían el 8. "
            "Y otra cosa: yo vivo en Hachaca, fuera de Santa Marta.",
            7,
            "AJUSTE DE FECHA + ZONA SIN COBERTURA"
        )

        self.send_message(
            "¿Entonces cómo hacemos? Porque desde Hachaca hasta Santa Marta no tengo cómo bajar.",
            8,
            "PREGUNTA DE SOLUCIÓN"
        )

        self.send_message("Listo, gracias", 9, "CIERRE")
        self.get_session_details()
        self.print_separator("✅ TEST ZONA SIN COBERTURA COMPLETADO")
        return True

    def run_patient_away_flow(self, phone: str):
        """Caso complejo: paciente fuera de la ciudad + reanudación por WhatsApp"""
        print("\n" + "✈️" * 40)
        print("INICIANDO TEST DE LLAMADA SALIENTE - PACIENTE FUERA DE LA CIUDAD (COMPLEJO)")
        print("✈️" * 40)

        if not self.check_health():
            return False

        self.get_pending_calls()

        if not self.create_outbound_session(phone):
            return False

        self.send_message("Hola", 4, "SALUDO INICIAL")
        self.send_message("Sí, habla Lilia", 5, "CONFIRMACIÓN DE IDENTIDAD")
        self.send_message("Sí, autorizo la grabación", 6, "AVISO LEGAL")

        self.send_message(
            "Sí, es correcto, pero yo estoy por fuera todavía esta semana. Estoy en Riohacha, Guajira. "
            "Regreso a la ciudad el viernes.",
            7,
            "PACIENTE FUERA DE LA CIUDAD"
        )

        self.send_message(
            "¿Cómo haría para reiniciar el transporte cuando llegue allá? ¿Me pueden ayudar con eso?",
            8,
            "REANUDACIÓN DEL SERVICIO"
        )

        self.send_message("Bueno, gracias", 9, "CIERRE")
        self.get_session_details()
        self.print_separator("✅ TEST PACIENTE FUERA COMPLETADO")
        return True

    def run_intermunicipal_flow(self, phone: str):
        """Caso complejo: transporte intermunicipal + confirmación de punto/hora"""
        print("\n" + "🚌" * 40)
        print("INICIANDO TEST DE LLAMADA SALIENTE - INTERMUNICIPAL (COMPLEJO)")
        print("🚌" * 40)

        if not self.check_health():
            return False

        self.get_pending_calls()

        if not self.create_outbound_session(phone):
            return False

        self.send_message("Hola", 4, "SALUDO INICIAL")
        self.send_message("Habla Jenis, soy la familiar responsable", 5, "CONFIRMACIÓN (FAMILIAR)")
        self.send_message("Sí, autorizo la grabación", 6, "AVISO LEGAL")

        self.send_message(
            "La cita es a las 9. Solo para confirmar: ¿de verdad el vehículo sale a las 3 de la mañana "
            "desde el parque central? ¿Y me llaman antes de llegar?",
            7,
            "CONFIRMACIÓN DE PUNTO/HORA INTERMUNICIPAL"
        )

        self.send_message("Ok, entendido. Gracias", 8, "CIERRE")
        self.get_session_details()
        self.print_separator("✅ TEST INTERMUNICIPAL COMPLETADO")
        return True


def main():
    """Función principal"""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║              TEST DE LLAMADAS SALIENTES - TRANSFORMAS TRANSPORT              ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)

    # Crear tester
    tester = OutboundCallTester(API_BASE_URL)

    # Menú de opciones
    print("\nSelecciona el tipo de test a ejecutar:\n")
    print("1. Confirmación exitosa (flujo completo)")
    print("2. Reprogramación de cita")
    print("3. Rechazo de servicio")
    print("4. Solo consultar llamadas pendientes")
    print("5. Solo consultar estadísticas")
    print("6. Confirmación con queja de conductor (flujo complejo)")
    print("7. Silla de ruedas / vehículo grande (flujo complejo)")
    print("8. Zona sin cobertura (Hachaca) (flujo complejo)")
    print("9. Paciente fuera de la ciudad (flujo complejo)")
    print("10. Intermunicipal (punto/hora) (flujo complejo)")
    print("\n0. Salir")

    try:
        option = input("\nOpción: ").strip()

        if option == "0":
            print("\n👋 Saliendo...")
            return

        if option in ["1", "2", "3", "6", "7", "8", "9", "10"]:
            # Solicitar teléfono
            default_phone = COMPLAINT_EXAMPLE_PHONE if option == "6" else PATIENT_PHONE
            phone_input = input(f"\nTeléfono del paciente (default: {default_phone}): ").strip()
            phone = phone_input if phone_input else default_phone

            if option == "1":
                tester.run_successful_confirmation_flow(phone)
            elif option == "2":
                tester.run_reschedule_flow(phone)
            elif option == "3":
                tester.run_rejection_flow(phone)
            elif option == "6":
                tester.run_driver_complaint_flow(phone)
            elif option == "7":
                tester.run_wheelchair_special_needs_flow(phone)
            elif option == "8":
                tester.run_out_of_coverage_flow(phone)
            elif option == "9":
                tester.run_patient_away_flow(phone)
            elif option == "10":
                tester.run_intermunicipal_flow(phone)

        elif option == "4":
            tester.check_health()
            tester.get_pending_calls()

        elif option == "5":
            tester.check_health()
            tester.get_statistics()

        else:
            print("❌ Opción no válida")

    except KeyboardInterrupt:
        print("\n\n👋 Test interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
