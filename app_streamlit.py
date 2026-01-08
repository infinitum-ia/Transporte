"""
Streamlit Chat Application for Testing Medical Transport Agent

Test both INBOUND and OUTBOUND calls through an interactive chat interface.

This application uses the UNIFIED ENDPOINT (/conversation/unified) which simplifies
the conversation flow by:
- Automatically creating or continuing sessions based on patient_phone
- No need to manually manage session_id headers
- Single endpoint for all conversation messages
"""
import streamlit as st
import requests
import json
from datetime import datetime
from typing import Optional, Dict, Any

# API Configuration
API_BASE_URL = "http://localhost:8000/api/v1"

# Page configuration
st.set_page_config(
    page_title="Transpormax - Agente de Transporte Médico",
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


def send_message_unified(patient_phone: str, message: str, is_outbound: bool, agent_name: str = "María") -> Dict[str, Any]:
    """Send a message using the unified endpoint"""
    try:
        payload = {
            "patient_phone": patient_phone,
            "message": message,
            "is_outbound": is_outbound,
            "agent_name": agent_name
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


def main():
    """Main application"""
    init_session_state()

    # Header
    st.markdown('<h1 class="main-header">🚐 Transformas - Agente de Transporte Médico</h1>', unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuración")

        # Agent name
        agent_name = st.text_input("Nombre del Agente", value="María", key="agent_name_input")

        st.divider()

        # Call type selection
        st.subheader("Tipo de Llamada")

        call_type_option = st.radio(
            "Seleccione el tipo de llamada:",
            ["📞 ENTRANTE (Cliente llama)", "📱 SALIENTE (Confirmación)"],
            key="call_type_radio"
        )

        is_outbound = "SALIENTE" in call_type_option

        # Patient phone (required for unified endpoint)
        if is_outbound:
            st.info("💡 Para llamadas salientes, el teléfono debe existir en el archivo Excel del sistema")
        else:
            st.info("💡 Para llamadas entrantes, ingrese cualquier teléfono como identificador de la conversación")

        patient_phone = st.text_input(
            "Teléfono del Paciente",
            placeholder="3001234567",
            max_chars=10,
            key="patient_phone_input",
            help="El teléfono identifica la conversación de manera única"
        )

        st.divider()

        # Start new conversation button
        if st.button("🆕 Iniciar Nueva Conversación", type="primary", use_container_width=True):
            if not patient_phone:
                st.error("⚠️ Debe ingresar el teléfono del paciente")
            else:
                with st.spinner("Iniciando conversación..."):
                    # Use "START" message to initiate the conversation
                    initial_message = "START" if is_outbound else "Buenos días"
                    result = send_message_unified(patient_phone, initial_message, is_outbound, agent_name)

                    if result["success"]:
                        response_data = result["data"]
                        st.session_state.session_id = response_data["session_id"]
                        st.session_state.patient_phone = patient_phone
                        st.session_state.call_type = "OUTBOUND" if is_outbound else "INBOUND"
                        st.session_state.conversation_phase = response_data.get("conversation_phase")
                        st.session_state.messages = []

                        # Add the agent's initial response
                        agent_response = response_data.get("agent_response", "")
                        if agent_response:
                            st.session_state.messages.append({
                                "role": "agent",
                                "content": agent_response,
                                "timestamp": datetime.now().strftime("%H:%M:%S")
                            })

                        st.session_state.patient_info = {
                            "patient_name": response_data.get("patient_name"),
                            "service_type": response_data.get("service_type")
                        }

                        st.success(f"✅ Conversación iniciada: {response_data['session_id'][:8]}...")
                        st.rerun()
                    else:
                        st.error(f"❌ Error: {result['error']}")

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
                st.rerun()

        # Session info
        if st.session_state.session_id:
            st.divider()
            st.subheader("📊 Información de Sesión")

            st.write(f"**Session ID:** `{st.session_state.session_id[:16]}...`")
            st.write(f"**Teléfono:** {st.session_state.patient_phone or 'N/A'}")
            st.write(f"**Tipo:** {st.session_state.call_type or 'N/A'}")
            st.write(f"**Fase:** {st.session_state.conversation_phase or 'N/A'}")

            if st.session_state.patient_info.get('patient_name'):
                st.write(f"**Paciente:** {st.session_state.patient_info['patient_name']}")

            if st.session_state.patient_info.get('service_type'):
                st.write(f"**Servicio:** {st.session_state.patient_info['service_type']}")

    # Main chat area
    if not st.session_state.session_id:
        st.info("👈 Por favor, inicie una nueva conversación desde el panel lateral")

        # Show instructions
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📞 Llamadas Entrantes")
            st.markdown("""
            El cliente llama a la empresa:
            - **Saludo inicial**
            - **Identificación del paciente**
            - **Aviso legal de grabación**
            - **Coordinación del servicio**
            - **Gestión de incidencias** (opcional)
            - **Cierre y encuesta**

            **Nota:** Ingrese el teléfono del paciente para identificar la conversación.
            """)

        with col2:
            st.subheader("📱 Llamadas Salientes")
            st.markdown("""
            La empresa llama al cliente:
            - **Saludo y verificación**
            - **Aviso legal de grabación**
            - **Confirmación del servicio programado**
            - **Casos especiales** (cambios, quejas)
            - **Cierre**

            **Nota:** Requiere que el teléfono esté registrado en el archivo Excel del sistema.
            """)

    else:
        # Display session banner
        call_type_display = "📱 SALIENTE" if st.session_state.call_type == "OUTBOUND" else "📞 ENTRANTE"
        st.markdown(f"""
        <div class="session-info">
            <strong>Sesión Activa:</strong> {st.session_state.session_id[:16]}... |
            <strong>Tipo:</strong> {call_type_display} |
            <strong>Fase:</strong> {st.session_state.conversation_phase or 'N/A'}
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

        # Message input
        st.divider()

        col1, col2 = st.columns([5, 1])

        with col1:
            user_input = st.text_input(
                "Mensaje",
                placeholder="Escribe tu mensaje aquí...",
                key="user_input",
                label_visibility="collapsed"
            )

        with col2:
            send_button = st.button("📤 Enviar", use_container_width=True, type="primary")

        # Send message
        if send_button and user_input.strip():
            # Add user message to history
            st.session_state.messages.append({
                "role": "user",
                "content": user_input,
                "timestamp": datetime.now().strftime("%H:%M:%S")
            })

            # Send to API using unified endpoint
            with st.spinner("Pensando..."):
                is_outbound = st.session_state.call_type == "OUTBOUND"
                result = send_message_unified(
                    st.session_state.patient_phone,
                    user_input,
                    is_outbound,
                    agent_name
                )

                if result["success"]:
                    response_data = result["data"]
                    agent_response = response_data.get("agent_response", "")

                    # Add agent response to history
                    st.session_state.messages.append({
                        "role": "agent",
                        "content": agent_response,
                        "timestamp": datetime.now().strftime("%H:%M:%S")
                    })

                    # Update conversation phase
                    st.session_state.conversation_phase = response_data.get("conversation_phase")

                    # Update patient info if available
                    if response_data.get("patient_name"):
                        st.session_state.patient_info["patient_name"] = response_data["patient_name"]
                    if response_data.get("service_type"):
                        st.session_state.patient_info["service_type"] = response_data["service_type"]

                    # Check for escalation
                    if response_data.get("requires_escalation"):
                        st.warning(f"⚠️ Escalamiento requerido: {response_data.get('metadata', {}).get('escalation_reason', 'N/A')}")

                    st.rerun()
                else:
                    st.error(f"❌ Error: {result['error']}")

        # Quick actions
        if st.session_state.call_type == "INBOUND":
            st.divider()
            st.caption("💡 Ejemplos de mensajes:")

            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("👋 Buenos días"):
                    st.session_state.messages.append({
                        "role": "user",
                        "content": "Buenos días",
                        "timestamp": datetime.now().strftime("%H:%M:%S")
                    })
                    st.rerun()

            with col2:
                if st.button("🆔 Soy Juan Pérez"):
                    st.session_state.messages.append({
                        "role": "user",
                        "content": "Mi nombre es Juan Pérez, cédula 12345678",
                        "timestamp": datetime.now().strftime("%H:%M:%S")
                    })
                    st.rerun()

            with col3:
                if st.button("✅ Acepto grabación"):
                    st.session_state.messages.append({
                        "role": "user",
                        "content": "Sí, acepto que se grabe la llamada",
                        "timestamp": datetime.now().strftime("%H:%M:%S")
                    })
                    st.rerun()


if __name__ == "__main__":
    main()
