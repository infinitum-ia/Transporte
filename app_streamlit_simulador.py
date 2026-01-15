"""
Streamlit Chat Application for Testing Medical Transport Agent - OUTBOUND ONLY

Automated LLM-based simulation of outbound confirmation calls.
The LLM simulates patient responses based on real patient data context.

This application uses the UNIFIED ENDPOINT (/conversation/unified) which simplifies
the conversation flow by:
- Automatically creating or continuing sessions based on patient_phone
- No need to manually manage session_id headers
- Single endpoint for all conversation messages
"""
import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, Any, List
import re
import os
from openai import OpenAI
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Configuration
# IMPORTANTE: El prefijo /api/v1 puede variar dependiendo de la configuración del servidor
# Si obtiene errores 404, intente sin el prefijo: "http://localhost:8000"
API_BASE_URL = "http://localhost:8000"

# OpenAI Configuration for Patient Simulation
openai_client = None
try:
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key:
        openai_client = OpenAI(api_key=openai_api_key)
    else:
        print("Warning: OPENAI_API_KEY not found in environment variables")
except Exception as e:
    print(f"Warning: Could not initialize OpenAI client: {e}")

# Sample database based on provided structure
PATIENT_DATABASE = [
    {
        "nombre_paciente": "John Jairo",
        "apellido_paciente": "Mesa",
        "tipo_documento": "CC",
        "numero_documento": "1234567",
        "eps": "Cosalud",
        "departamento": "Magdalena",
        "ciudad": "Santa Marta",
        "nombre_familiar": "Carmen Gamero",
        "parentesco": "Familiar",
        "telefono": "3001234567",
        "tipo_servicio": "Terapia",
        "tipo_tratamiento": "Fisioterapia",
        "frecuencia": "Lunes-Miércoles-Viernes",
        "fecha_servicio": "07/01/2025,08/01/2025",
        "hora_servicio": "7:20",
        "destino_centro_salud": "Fundación Camel",
        "modalidad_transporte": "Ruta",
        "zona_recogida": "Centro",
        "direccion_completa": "Calle 15 #10-20",
        "observaciones_especiales": "",
        "estado_confirmacion": "Pendiente"
    },
    {
        "nombre_paciente": "Valeria",
        "apellido_paciente": "Ballerospina",
        "tipo_documento": "CC",
        "numero_documento": "11275945",
        "eps": "Cosalud",
        "departamento": "Magdalena",
        "ciudad": "Santa Marta",
        "nombre_familiar": "",
        "parentesco": "",
        "telefono": "3009876543",
        "tipo_servicio": "Terapia",
        "tipo_tratamiento": "Fisioterapia",
        "frecuencia": "Semanal",
        "fecha_servicio": "7/01/2025",
        "hora_servicio": "8:00",
        "destino_centro_salud": "Centro de Rehabilitación",
        "modalidad_transporte": "Desembolso",
        "zona_recogida": "Norte",
        "direccion_completa": "Carrera 5 #30-15",
        "observaciones_especiales": "",
        "estado_confirmacion": "Pendiente"
    },
    {
        "nombre_paciente": "Adaluz",
        "apellido_paciente": "Valencia",
        "tipo_documento": "CC",
        "numero_documento": "2345678",
        "eps": "Cosalud",
        "departamento": "Magdalena",
        "ciudad": "Santa Marta",
        "nombre_familiar": "Benedit Carrillo",
        "parentesco": "Familiar",
        "telefono": "3112345678",
        "tipo_servicio": "Cita Especialista",
        "tipo_tratamiento": "Cita con especialista",
        "frecuencia": "Puntual",
        "fecha_servicio": "13/01/2025,14/01/2025,16/01/2025",
        "hora_servicio": "9:00",
        "destino_centro_salud": "Fundación Camel, Unidad San Caway",
        "modalidad_transporte": "Ruta",
        "zona_recogida": "Sur",
        "direccion_completa": "Calle 30 #8-40",
        "observaciones_especiales": "",
        "estado_confirmacion": "Pendiente"
    },
    {
        "nombre_paciente": "Joan",
        "apellido_paciente": "Diaz",
        "tipo_documento": "CC",
        "numero_documento": "3456789",
        "eps": "Cosalud",
        "departamento": "Atlántico",
        "ciudad": "Barranquilla",
        "nombre_familiar": "",
        "parentesco": "",
        "telefono": "3201234567",
        "tipo_servicio": "Dialisis",
        "tipo_tratamiento": "Hemodiálisis",
        "frecuencia": "Lunes-Miércoles-Viernes",
        "fecha_servicio": "08/01/2025,10/01/2025",
        "hora_servicio": "16:00",
        "destino_centro_salud": "Centro de Diálisis Renal",
        "modalidad_transporte": "Ruta",
        "zona_recogida": "Occidente",
        "direccion_completa": "Calle 45 #23-10",
        "observaciones_especiales": "",
        "estado_confirmacion": "Pendiente"
    },
    {
        "nombre_paciente": "Alvaro Jose",
        "apellido_paciente": "Castro",
        "tipo_documento": "TI",
        "numero_documento": "4567890",
        "eps": "Cosalud",
        "departamento": "Magdalena",
        "ciudad": "Santa Marta",
        "nombre_familiar": "Ludíz Castro",
        "parentesco": "Madre",
        "telefono": "3156789012",
        "tipo_servicio": "Cita Especialista",
        "tipo_tratamiento": "Pediatría especializada",
        "frecuencia": "Puntual",
        "fecha_servicio": "7/01/2025",
        "hora_servicio": "13:00",
        "destino_centro_salud": "Promotor de la Salud de la Costa",
        "modalidad_transporte": "Ruta",
        "zona_recogida": "Este",
        "direccion_completa": "Carrera 12 #18-30",
        "observaciones_especiales": "",
        "estado_confirmacion": "Pendiente"
    },
    {
        "nombre_paciente": "Emilce",
        "apellido_paciente": "Rodriguez",
        "tipo_documento": "CC",
        "numero_documento": "5678901",
        "eps": "Cosalud",
        "departamento": "Magdalena",
        "ciudad": "Hachaca",
        "nombre_familiar": "",
        "parentesco": "",
        "telefono": "3187654321",
        "tipo_servicio": "Terapia",
        "tipo_tratamiento": "Fisioterapia",
        "frecuencia": "Martes-Jueves-Sábado",
        "fecha_servicio": "08/01/2025,10/01/2025",
        "hora_servicio": "7:00",
        "destino_centro_salud": "Centro Biolisti",
        "modalidad_transporte": "Ruta",
        "zona_recogida": "Hachaca",
        "direccion_completa": "Vereda El Carmen km 15",
        "observaciones_especiales": "",
        "estado_confirmacion": "Pendiente"
    },
    {
        "nombre_paciente": "Lilia",
        "apellido_paciente": "Valencia",
        "tipo_documento": "CC",
        "numero_documento": "6789012",
        "eps": "Cosalud",
        "departamento": "Atlántico",
        "ciudad": "Barranquilla",
        "nombre_familiar": "",
        "parentesco": "",
        "telefono": "3145678901",
        "tipo_servicio": "Dialisis",
        "tipo_tratamiento": "Hemodiálisis",
        "frecuencia": "Lunes-Miércoles-Viernes",
        "fecha_servicio": "12/01/2025,14/01/2025,17/01/2025",
        "hora_servicio": "17:30",
        "destino_centro_salud": "Clínica de Diálisis Norte",
        "modalidad_transporte": "Ruta",
        "zona_recogida": "Norte",
        "direccion_completa": "Calle 72 #8-15",
        "observaciones_especiales": "",
        "estado_confirmacion": "Pendiente"
    },
    {
        "nombre_paciente": "Kelly Joana",
        "apellido_paciente": "Garcia",
        "tipo_documento": "CC",
        "numero_documento": "7890123",
        "eps": "Cosalud",
        "departamento": "Sucre",
        "ciudad": "Sincelejo",
        "nombre_familiar": "Jenis García",
        "parentesco": "Familiar",
        "telefono": "3098765432",
        "tipo_servicio": "Cita Especialista",
        "tipo_tratamiento": "Consulta especializada",
        "frecuencia": "Puntual",
        "fecha_servicio": "8/01/2025",
        "hora_servicio": "3:00",
        "destino_centro_salud": "Hospital Regional Sincelejo",
        "modalidad_transporte": "Ruta intermunicipal",
        "zona_recogida": "Parque Central Sincelejo",
        "direccion_completa": "Barrio Centro - Parque Principal",
        "observaciones_especiales": "",
        "estado_confirmacion": "Pendiente"
    },
    {
        "nombre_paciente": "Maria del Carmen",
        "apellido_paciente": "Perez",
        "tipo_documento": "CC",
        "numero_documento": "8901234",
        "eps": "Cosalud",
        "departamento": "Magdalena",
        "ciudad": "Santa Marta",
        "nombre_familiar": "",
        "parentesco": "",
        "telefono": "3176543210",
        "tipo_servicio": "Terapia",
        "tipo_tratamiento": "Terapia ocupacional",
        "frecuencia": "Martes-Jueves",
        "fecha_servicio": "07/01/2025,09/01/2025",
        "hora_servicio": "8:30",
        "destino_centro_salud": "Centro de Rehabilitación Integral",
        "modalidad_transporte": "Desembolso",
        "zona_recogida": "Centro",
        "direccion_completa": "Calle 22 #14-30",
        "observaciones_especiales": "",
        "estado_confirmacion": "Pendiente"
    },
    {
        "nombre_paciente": "Jose Luis",
        "apellido_paciente": "martinez",
        "tipo_documento": "CC",
        "numero_documento": "9012345",
        "eps": "Cosalud",
        "departamento": "Atlántico",
        "ciudad": "Barranquilla",
        "nombre_familiar": "Ana Martínez",
        "parentesco": "Esposa",
        "telefono": "3134567890",
        "tipo_servicio": "Dialisis",
        "tipo_tratamiento": "Hemodiálisis",
        "frecuencia": "Lunes-Miércoles-Viernes",
        "fecha_servicio": "06/01/2025,08/01/2025,10/01/2025",
        "hora_servicio": "6:00",
        "destino_centro_salud": "Fundación Renal del Caribe",
        "modalidad_transporte": "Ruta",
        "zona_recogida": "Sur",
        "direccion_completa": "Carrera 38 #50-22",
        "observaciones_especiales": "",
        "estado_confirmacion": "Pendiente"
    }
]

# Convert to DataFrame for easier manipulation
df_patients = pd.DataFrame(PATIENT_DATABASE)

# Page configuration
st.set_page_config(
    page_title="Transformas - Agente de Transporte Médico",
    page_icon="🚐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .user-message {
        background-color: #e3f2fd;
        margin-left: 20%;
    }
    .agent-message {
        background-color: #f5f5f5;
        margin-right: 20%;
    }
    .message-label {
        font-weight: bold;
        margin-bottom: 0.5rem;
        font-size: 0.9rem;
    }
    .message-content {
        font-size: 1rem;
    }
    .session-info {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .success-box {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .error-box {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .patient-card {
        background-color: #f8f9fa;
        border-left: 4px solid #1f77b4;
        padding: 1rem;
        margin-bottom: 1rem;
        border-radius: 0.25rem;
    }
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.875rem;
        font-weight: bold;
    }
    .status-pending {
        background-color: #fff3cd;
        color: #856404;
    }
    .status-confirmed {
        background-color: #d4edda;
        color: #155724;
    }
    .status-cancelled {
        background-color: #f8d7da;
        color: #721c24;
    }
    .data-table {
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables"""
    if "session_id" not in st.session_state:
        st.session_state.session_id = None
    if "patient_phone" not in st.session_state:
        st.session_state.patient_phone = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "call_type" not in st.session_state:
        st.session_state.call_type = None
    if "conversation_phase" not in st.session_state:
        st.session_state.conversation_phase = None
    if "patient_info" not in st.session_state:
        st.session_state.patient_info = {}
    if "conversation_ended" not in st.session_state:
        st.session_state.conversation_ended = False
    if "selected_patient" not in st.session_state:
        st.session_state.selected_patient = None
    if "auto_simulation_running" not in st.session_state:
        st.session_state.auto_simulation_running = False
    if "simulation_max_turns" not in st.session_state:
        st.session_state.simulation_max_turns = 10
    if "simulation_delay" not in st.session_state:
        st.session_state.simulation_delay = 2.0


def get_patient_by_phone(phone: str) -> Optional[Dict]:
    """Get patient information by phone number"""
    phone = str(phone).strip()
    for patient in PATIENT_DATABASE:
        if str(patient["telefono"]) == phone:
            return patient
    return None


def get_patient_by_document(document: str) -> Optional[Dict]:
    """Get patient information by document number"""
    document = str(document).strip()
    for patient in PATIENT_DATABASE:
        if str(patient["numero_documento"]) == document:
            return patient
    return None


def get_patient_by_name(name: str) -> List[Dict]:
    """Get patients by name (partial match)"""
    name = name.lower().strip()
    results = []
    for patient in PATIENT_DATABASE:
        full_name = f"{patient['nombre_paciente']} {patient['apellido_paciente']}".lower()
        if name in full_name:
            results.append(patient)
    return results


def simulate_patient_response(agent_message: str, patient_context: Dict, conversation_history: List[Dict]) -> str:
    """
    Simulate a patient's response using LLM based on patient context and conversation history.

    Args:
        agent_message: The message from the agent
        patient_context: Dictionary with patient information
        conversation_history: List of previous messages in the conversation

    Returns:
        Simulated patient response
    """
    if not openai_client:
        return "Lo siento, no puedo simular respuestas sin OpenAI configurado."

    try:
        # Build context for the LLM
        full_name = f"{patient_context['nombre_paciente']} {patient_context['apellido_paciente']}"
        addressee = patient_context['nombre_familiar'] if patient_context['nombre_familiar'] else full_name
        relationship = patient_context['parentesco'] if patient_context['parentesco'] else "Paciente"

        system_prompt = f"""Eres {addressee} ({relationship} del paciente {full_name}).
Estás recibiendo una llamada de confirmación de Transformas para un servicio de transporte médico.

INFORMACIÓN DEL SERVICIO:
- Paciente: {full_name}
- Documento: {patient_context['tipo_documento']} {patient_context['numero_documento']}
- Tipo de servicio: {patient_context['tipo_servicio']} - {patient_context['tipo_tratamiento']}
- Fechas: {patient_context['fecha_servicio']}
- Horario: {patient_context['hora_servicio']}
- Destino: {patient_context['destino_centro_salud']}
- Modalidad: {patient_context['modalidad_transporte']}
- Dirección de recogida: {patient_context['direccion_completa']} ({patient_context['zona_recogida']})
- Frecuencia: {patient_context['frecuencia']}
- Ciudad: {patient_context['ciudad']}, {patient_context['departamento']}

INSTRUCCIONES DE COMPORTAMIENTO:
1. Responde de manera natural y realista como lo haría una persona colombiana
2. Sé cortés y educado
3. Confirma la información cuando el agente te la mencione
4. Si el agente pregunta por confirmar el servicio, acepta (di "Sí, confirmado" o similar)
5. Usa expresiones coloquiales colombianas naturales (ejemplo: "Listo", "Vale", "Perfecto", "Claro que sí")
6. Mantén las respuestas cortas y naturales (1-2 oraciones máximo)
7. Si te preguntan por cambios, di que todo está bien
8. Al despedirte, sé cordial y agradece
9. No inventes información que no esté en el contexto
10. Si no entiendes algo, pide que te lo repitan de forma natural

EJEMPLOS DE RESPUESTAS NATURALES:
- "Buenas, ¿quién habla?"
- "Sí, soy yo"
- "Listo, todo confirmado"
- "Perfecto, nos vemos ese día"
- "Claro que sí, muchas gracias"
- "Todo bien, no hay cambios"
- "Vale, adiós"
"""

        # Build conversation history for context
        messages = [{"role": "system", "content": system_prompt}]

        # Add previous conversation
        for msg in conversation_history[-6:]:  # Last 6 messages for context
            if msg["role"] == "agent":
                messages.append({"role": "assistant", "content": f"[AGENTE DIJO]: {msg['content']}"})
            elif msg["role"] == "user":
                messages.append({"role": "user", "content": msg["content"]})

        # Add current agent message
        messages.append({"role": "assistant", "content": f"[AGENTE DICE]: {agent_message}"})
        messages.append({"role": "user", "content": "Responde de forma breve y natural como el paciente/familiar:"})

        # Call OpenAI
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.8,
            max_tokens=150
        )

        simulated_response = response.choices[0].message.content.strip()

        # Clean up response (remove quotes if present)
        simulated_response = simulated_response.strip('"').strip("'")

        return simulated_response

    except Exception as e:
        return f"[ERROR EN SIMULACIÓN: {str(e)}]"


def send_message_unified(patient_phone: str, message: str, is_outbound: bool, agent_name: str = "María") -> Dict[str, Any]:
    """Send a message using the unified endpoint"""
    try:
        payload = {
            "PATIENT_PHONE": patient_phone,
            "MESSAGE": message,
            "IS_OUTBOUND": is_outbound,
            "AGENT_NAME": agent_name
        }

        response = requests.post(
            f"{API_BASE_URL}/conversation/unified",
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            error_detail = response.json().get("detail", "Unknown error")
            return {"success": False, "error": error_detail}

    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"Connection error: {str(e)}"}


def display_chat_message(role: str, content: str, timestamp: str = None):
    """Display a chat message"""
    if role == "user":
        st.markdown(f"""
        <div class="chat-message user-message">
            <div class="message-label">👤 Usuario {f'- {timestamp}' if timestamp else ''}</div>
            <div class="message-content">{content}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="chat-message agent-message">
            <div class="message-label">🤖 Agente María {f'- {timestamp}' if timestamp else ''}</div>
            <div class="message-content">{content}</div>
        </div>
        """, unsafe_allow_html=True)


def run_automated_simulation(patient_context: Dict, agent_name: str, max_turns: int = 10, delay: float = 2.0):
    """
    Run an automated conversation simulation.

    Args:
        patient_context: Dictionary with patient information
        agent_name: Name of the agent
        max_turns: Maximum number of conversation turns
        delay: Delay in seconds between turns
    """
    patient_phone = patient_context['telefono']

    # Initialize conversation with START message
    with st.spinner("Iniciando conversación automática..."):
        initial_result = send_message_unified(patient_phone, "START", is_outbound=True, agent_name=agent_name)

        if not initial_result["success"]:
            st.error(f"❌ Error al iniciar: {initial_result['error']}")
            return

        response_data = initial_result["data"]
        st.session_state.session_id = response_data["SESSION_ID"]
        st.session_state.patient_phone = patient_phone
        st.session_state.call_type = "OUTBOUND"
        st.session_state.messages = []
        st.session_state.conversation_ended = response_data.get("FIN", False)

        # Add agent's initial greeting
        agent_response = response_data.get("AGENT_RESPONSE", "")
        if agent_response:
            st.session_state.messages.append({
                "role": "agent",
                "content": agent_response,
                "timestamp": datetime.now().strftime("%H:%M:%S")
            })

    st.success(f"✅ Conversación iniciada: {response_data['SESSION_ID'][:8]}...")
    st.rerun()


def continue_automated_simulation(patient_context: Dict, agent_name: str, max_turns: int = 10, delay: float = 2.0):
    """Continue the automated simulation for one turn"""

    if st.session_state.conversation_ended:
        st.session_state.auto_simulation_running = False
        st.success("✅ Simulación completada - Conversación finalizada")
        return

    if len(st.session_state.messages) >= max_turns * 2:
        st.session_state.auto_simulation_running = False
        st.warning(f"⚠️ Simulación detenida - Máximo de {max_turns} turnos alcanzado")
        return

    # Get last agent message
    agent_messages = [msg for msg in st.session_state.messages if msg["role"] == "agent"]
    if not agent_messages:
        st.session_state.auto_simulation_running = False
        st.error("❌ No hay mensaje del agente para responder")
        return

    last_agent_message = agent_messages[-1]["content"]

    # Simulate patient response
    with st.spinner("🤖 Paciente simulado está pensando..."):
        time.sleep(delay * 0.5)  # Half delay for thinking
        simulated_response = simulate_patient_response(
            last_agent_message,
            patient_context,
            st.session_state.messages
        )

    # Add simulated response to history
    st.session_state.messages.append({
        "role": "user",
        "content": simulated_response,
        "timestamp": datetime.now().strftime("%H:%M:%S")
    })

    # Send to API
    with st.spinner("📤 Enviando respuesta al agente..."):
        time.sleep(delay * 0.5)  # Half delay for sending
        result = send_message_unified(
            st.session_state.patient_phone,
            simulated_response,
            is_outbound=True,
            agent_name=agent_name
        )

    if result["success"]:
        response_data = result["data"]
        agent_response = response_data.get("AGENT_RESPONSE", "")

        # Add agent response to history
        if agent_response:
            st.session_state.messages.append({
                "role": "agent",
                "content": agent_response,
                "timestamp": datetime.now().strftime("%H:%M:%S")
            })

        # Check if conversation ended
        if response_data.get("FIN", False):
            st.session_state.conversation_ended = True
            st.session_state.auto_simulation_running = False

        st.rerun()
    else:
        st.error(f"❌ Error: {result['error']}")
        st.session_state.auto_simulation_running = False


def display_patient_info(patient: Dict):
    """Display patient information in a formatted card"""
    if not patient:
        return
    
    full_name = f"{patient['nombre_paciente']} {patient['apellido_paciente']}"
    document = f"{patient['tipo_documento']}: {patient['numero_documento']}"
    
    # Parse multiple dates
    dates = patient['fecha_servicio'].split(',')
    formatted_dates = []
    for date_str in dates:
        try:
            # Try to parse date in format dd/mm/yyyy
            date_obj = datetime.strptime(date_str.strip(), '%d/%m/%Y')
            formatted_dates.append(date_obj.strftime('%d de %B de %Y'))
        except:
            formatted_dates.append(date_str.strip())
    
    dates_display = ", ".join(formatted_dates)
    
    # Determine who to address
    if patient['nombre_familiar']:
        addressee = f"{patient['nombre_familiar']} ({patient['parentesco']})"
    else:
        addressee = full_name
    
    st.markdown(f"""
    <div class="patient-card">
        <h4>👤 {full_name}</h4>
        <div class="data-table">
            <table style="width:100%">
                <tr>
                    <td style="width:30%"><strong>📞 Teléfono:</strong></td>
                    <td>{patient['telefono']}</td>
                </tr>
                <tr>
                    <td><strong>📄 Documento:</strong></td>
                    <td>{document}</td>
                </tr>
                <tr>
                    <td><strong>🏥 EPS:</strong></td>
                    <td>{patient['eps']}</td>
                </tr>
                <tr>
                    <td><strong>📍 Ubicación:</strong></td>
                    <td>{patient['ciudad']}, {patient['departamento']}</td>
                </tr>
                <tr>
                    <td><strong>🏠 Dirección:</strong></td>
                    <td>{patient['direccion_completa']} ({patient['zona_recogida']})</td>
                </tr>
                <tr>
                    <td><strong>🚑 Servicio:</strong></td>
                    <td>{patient['tipo_servicio']} - {patient['tipo_tratamiento']}</td>
                </tr>
                <tr>
                    <td><strong>📅 Fechas:</strong></td>
                    <td>{dates_display}</td>
                </tr>
                <tr>
                    <td><strong>🕐 Horario:</strong></td>
                    <td>{patient['hora_servicio']}</td>
                </tr>
                <tr>
                    <td><strong>🎯 Destino:</strong></td>
                    <td>{patient['destino_centro_salud']}</td>
                </tr>
                <tr>
                    <td><strong>🚐 Transporte:</strong></td>
                    <td>{patient['modalidad_transporte']}</td>
                </tr>
                <tr>
                    <td><strong>👥 Dirigirse a:</strong></td>
                    <td>{addressee}</td>
                </tr>
            </table>
        </div>
    </div>
    """, unsafe_allow_html=True)


def main():
    """Main application"""
    init_session_state()

    # Header
    st.markdown('<h1 class="main-header">🚐 Transformas - Simulador Automático (Llamadas Salientes)</h1>', unsafe_allow_html=True)
    
    # Database info
    st.caption(f"📊 Base de datos: {len(PATIENT_DATABASE)} pacientes registrados")

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuración")

        # Check OpenAI availability
        if not openai_client:
            st.error("⚠️ OpenAI no configurado. Configure la variable de entorno OPENAI_API_KEY")
            st.stop()

        # Agent name
        agent_name = st.text_input("Nombre del Agente", value="María", key="agent_name_input")

        st.divider()

        # Database Search Section
        st.subheader("🔍 Buscar Paciente")

        search_option = st.radio(
            "Buscar por:",
            ["Teléfono", "Nombre", "Documento"],
            key="search_option"
        )

        search_query = st.text_input(
            "Ingrese búsqueda:",
            placeholder="Ej: 3001234567 o John Jairo o 1234567",
            key="search_input"
        )

        search_results = []

        if search_query:
            if search_option == "Teléfono":
                patient = get_patient_by_phone(search_query)
                if patient:
                    search_results.append(patient)
            elif search_option == "Nombre":
                search_results = get_patient_by_name(search_query)
            elif search_option == "Documento":
                patient = get_patient_by_document(search_query)
                if patient:
                    search_results.append(patient)

        if search_results:
            st.success(f"✅ Encontrados: {len(search_results)} paciente(s)")

            for idx, patient in enumerate(search_results):
                with st.expander(f"👤 {patient['nombre_paciente']} {patient['apellido_paciente']}", expanded=idx==0):
                    st.write(f"📞: {patient['telefono']}")
                    st.write(f"📄: {patient['tipo_documento']} {patient['numero_documento']}")
                    st.write(f"🏥: {patient['tipo_servicio']} - {patient['tipo_tratamiento']}")

                    if st.button(f"Seleccionar este paciente", key=f"select_{patient['telefono']}"):
                        st.session_state.selected_patient = patient
                        st.session_state.patient_phone = patient['telefono']
                        st.rerun()

        st.divider()

        # Simulation Configuration
        st.subheader("🤖 Configuración de Simulación")

        # Use selected patient
        if st.session_state.selected_patient:
            st.info(f"✅ Paciente: {st.session_state.selected_patient['nombre_paciente']} {st.session_state.selected_patient['apellido_paciente']}")
        else:
            st.warning("⚠️ Seleccione un paciente de la base de datos")

        # Simulation parameters
        max_turns = st.slider("Máximo de turnos", min_value=5, max_value=20, value=10, key="max_turns_slider")
        delay = st.slider("Delay entre mensajes (seg)", min_value=0.5, max_value=5.0, value=2.0, step=0.5, key="delay_slider")

        st.session_state.simulation_max_turns = max_turns
        st.session_state.simulation_delay = delay

        st.divider()

        # Start automated simulation button
        if not st.session_state.session_id:
            if st.button("🚀 Iniciar Simulación Automática", type="primary", use_container_width=True):
                if not st.session_state.selected_patient:
                    st.error("⚠️ Debe seleccionar un paciente")
                else:
                    run_automated_simulation(
                        st.session_state.selected_patient,
                        agent_name,
                        max_turns,
                        delay
                    )

        # Continue simulation controls
        if st.session_state.session_id and not st.session_state.conversation_ended:
            st.divider()

            col1, col2 = st.columns(2)

            with col1:
                if st.button("▶️ Continuar", use_container_width=True, type="primary"):
                    st.session_state.auto_simulation_running = True
                    st.rerun()

            with col2:
                if st.button("⏸️ Pausar", use_container_width=True):
                    st.session_state.auto_simulation_running = False
                    st.rerun()

        # End conversation button
        if st.session_state.session_id:
            st.divider()
            if st.button("🔴 Terminar Conversación", use_container_width=True):
                st.session_state.session_id = None
                st.session_state.patient_phone = None
                st.session_state.messages = []
                st.session_state.call_type = None
                st.session_state.conversation_phase = None
                st.session_state.patient_info = {}
                st.session_state.selected_patient = None
                st.session_state.conversation_ended = False
                st.session_state.auto_simulation_running = False
                st.rerun()

        # Session info
        if st.session_state.session_id:
            st.divider()
            st.subheader("📊 Información de Sesión")

            st.write(f"**Session ID:** `{st.session_state.session_id[:16]}...`")
            st.write(f"**Teléfono:** {st.session_state.patient_phone or 'N/A'}")
            st.write(f"**Tipo:** {st.session_state.call_type or 'N/A'}")

            # Show conversation status
            if st.session_state.conversation_ended:
                st.write("**Estado:** 🔴 FINALIZADA")
            else:
                st.write("**Estado:** 🟢 ACTIVA")
        
        # Database summary
        st.divider()
        st.subheader("📋 Resumen Base de Datos")
        
        therapy_count = len([p for p in PATIENT_DATABASE if p['tipo_servicio'] == 'Terapia'])
        dialysis_count = len([p for p in PATIENT_DATABASE if p['tipo_servicio'] == 'Dialisis'])
        specialist_count = len([p for p in PATIENT_DATABASE if p['tipo_servicio'] == 'Cita Especialista'])
        
        st.write(f"• Terapias: {therapy_count}")
        st.write(f"• Diálisis: {dialysis_count}")
        st.write(f"• Especialistas: {specialist_count}")
        st.write(f"• Total: {len(PATIENT_DATABASE)}")

    # Main chat area
    if not st.session_state.session_id:
        # Display selected patient info if any
        if st.session_state.selected_patient:
            st.subheader("👤 Información del Paciente Seleccionado")
            display_patient_info(st.session_state.selected_patient)
        
        st.info("👈 Por favor, inicie una nueva conversación desde el panel lateral")

        # Database View Tabs
        tab1, tab2, tab3 = st.tabs(["📋 Todos los Pacientes", "📊 Estadísticas", "🔍 Búsqueda Avanzada"])
        
        with tab1:
            st.subheader("Base de Datos de Pacientes")
            
            # Create a simplified DataFrame for display
            display_df = df_patients[['nombre_paciente', 'apellido_paciente', 'telefono', 
                                    'tipo_servicio', 'tipo_tratamiento', 'fecha_servicio', 
                                    'hora_servicio', 'estado_confirmacion']].copy()
            display_df['Paciente'] = display_df['nombre_paciente'] + ' ' + display_df['apellido_paciente']
            display_df = display_df[['Paciente', 'telefono', 'tipo_servicio', 'tipo_tratamiento', 
                                   'fecha_servicio', 'hora_servicio', 'estado_confirmacion']]
            
            st.dataframe(
                display_df,
                column_config={
                    "estado_confirmacion": st.column_config.SelectboxColumn(
                        "Estado",
                        help="Estado de confirmación",
                        options=["Pendiente", "Confirmado", "Cancelado"],
                        default="Pendiente"
                    )
                },
                use_container_width=True,
                hide_index=True
            )
            
            # Export option
            if st.button("📤 Exportar a CSV"):
                csv = display_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Descargar CSV",
                    data=csv,
                    file_name="pacientes_transformas.csv",
                    mime="text/csv"
                )
        
        with tab2:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Pacientes", len(PATIENT_DATABASE))
            
            with col2:
                st.metric("Llamadas Pendientes", len([p for p in PATIENT_DATABASE if p['estado_confirmacion'] == 'Pendiente']))
            
            with col3:
                cities = df_patients['ciudad'].unique()
                st.metric("Ciudades", len(cities))
            
            # Service type distribution
            st.subheader("Distribución por Tipo de Servicio")
            service_counts = df_patients['tipo_servicio'].value_counts()
            st.bar_chart(service_counts)
            
            # City distribution
            st.subheader("Pacientes por Ciudad")
            city_counts = df_patients['ciudad'].value_counts()
            st.dataframe(city_counts)
        
        with tab3:
            st.subheader("Búsqueda por Filtros")
            
            col1, col2 = st.columns(2)
            
            with col1:
                service_filter = st.multiselect(
                    "Tipo de Servicio",
                    options=df_patients['tipo_servicio'].unique(),
                    default=[]
                )
                
                city_filter = st.multiselect(
                    "Ciudad",
                    options=df_patients['ciudad'].unique(),
                    default=[]
                )
            
            with col2:
                transport_filter = st.multiselect(
                    "Modalidad Transporte",
                    options=df_patients['modalidad_transporte'].unique(),
                    default=[]
                )
                
                eps_filter = st.multiselect(
                    "EPS",
                    options=df_patients['eps'].unique(),
                    default=[]
                )
            
            # Apply filters
            filtered_df = df_patients.copy()
            
            if service_filter:
                filtered_df = filtered_df[filtered_df['tipo_servicio'].isin(service_filter)]
            
            if city_filter:
                filtered_df = filtered_df[filtered_df['ciudad'].isin(city_filter)]
            
            if transport_filter:
                filtered_df = filtered_df[filtered_df['modalidad_transporte'].isin(transport_filter)]
            
            if eps_filter:
                filtered_df = filtered_df[filtered_df['eps'].isin(eps_filter)]
            
            st.write(f"**Resultados:** {len(filtered_df)} pacientes encontrados")
            
            if not filtered_df.empty:
                st.dataframe(
                    filtered_df[['nombre_paciente', 'apellido_paciente', 'telefono', 
                               'tipo_servicio', 'ciudad', 'modalidad_transporte']],
                    use_container_width=True
                )

    else:
        # Display session banner
        status_display = "🔴 FINALIZADA" if st.session_state.conversation_ended else "🟢 ACTIVA"
        sim_status = "▶️ EN EJECUCIÓN" if st.session_state.auto_simulation_running else "⏸️ PAUSADA"

        # Show patient info if available
        patient_info = get_patient_by_phone(st.session_state.patient_phone)
        if patient_info:
            st.subheader("👤 Información del Paciente")
            display_patient_info(patient_info)

        # Show different banner if conversation ended
        if st.session_state.conversation_ended:
            st.markdown(f"""
            <div class="success-box">
                <strong>✅ Conversación Finalizada</strong><br>
                La simulación ha completado la llamada de confirmación.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="session-info">
                <strong>Sesión:</strong> {st.session_state.session_id[:16]}... |
                <strong>Tipo:</strong> 📱 SALIENTE |
                <strong>Estado:</strong> {status_display} |
                <strong>Simulación:</strong> {sim_status}
            </div>
            """, unsafe_allow_html=True)

        # Display conversation history
        chat_container = st.container()

        with chat_container:
            for msg in st.session_state.messages:
                display_chat_message(
                    msg["role"],
                    msg["content"],
                    msg.get("timestamp")
                )

        # Info message
        st.divider()

        if st.session_state.conversation_ended:
            st.info("💡 Simulación completada. Inicie una nueva simulación desde el panel lateral.")

            # Show summary
            user_messages = [msg for msg in st.session_state.messages if msg["role"] == "user"]
            agent_messages = [msg for msg in st.session_state.messages if msg["role"] == "agent"]

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Turnos totales", len(user_messages))
            with col2:
                st.metric("Mensajes del agente", len(agent_messages))
            with col3:
                st.metric("Respuestas simuladas", len(user_messages))
        else:
            if st.session_state.auto_simulation_running:
                st.info("🤖 Simulación en ejecución automática... Use el botón '⏸️ Pausar' para detener.")
            else:
                st.info("⏸️ Simulación pausada. Use el botón '▶️ Continuar' para avanzar un turno.")

        # Auto-continue simulation if running
        if st.session_state.auto_simulation_running and not st.session_state.conversation_ended and patient_info:
            continue_automated_simulation(
                patient_info,
                agent_name,
                st.session_state.simulation_max_turns,
                st.session_state.simulation_delay
            )


if __name__ == "__main__":
    main()