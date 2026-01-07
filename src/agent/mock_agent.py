"""
Mock Conversational Agent

Simple mock agent for testing without full LangGraph implementation.
Simulates the conversation flow based on phases.
"""
from typing import Dict, Any, Optional
from datetime import datetime
import uuid
from ..domain.value_objects.conversation_phase import ConversationPhase


class MockConversationalAgent:
    """
    Mock agent that simulates conversation flow

    For testing and demonstration purposes only.
    Production will use full LangGraph implementation.
    """

    def __init__(self, agent_name: str = "María", company_name: str = "Transformas"):
        self.agent_name = agent_name
        self.company_name = company_name
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def create_session(self, agent_name: Optional[str] = None) -> str:
        """Create a new conversation session"""
        if agent_name:
            self.agent_name = agent_name
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "session_id": session_id,
            "phase": ConversationPhase.GREETING,
            "patient_name": None,
            "patient_document": None,
            "patient_eps": None,
            "service_date": None,
            "service_type": None,
            "messages": [],
            "created_at": datetime.utcnow().isoformat()
        }
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session state"""
        return self.sessions.get(session_id)

    async def process_message(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """
        Process user message and generate response

        Args:
            session_id: Session identifier
            user_message: User's message

        Returns:
            Dict with agent_response, phase, and metadata
        """
        if session_id not in self.sessions:
            raise ValueError(f"Session not found: {session_id}")

        session = self.sessions[session_id]
        current_phase = session["phase"]

        # Add user message to history
        session["messages"].append({
            "role": "user",
            "content": user_message,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Generate response based on current phase
        response = self._generate_response(session, user_message)

        # Add agent response to history
        session["messages"].append({
            "role": "assistant",
            "content": response["agent_response"],
            "timestamp": datetime.utcnow().isoformat()
        })

        # Update phase
        session["phase"] = response["next_phase"]

        return {
            "session_id": session_id,
            "agent_response": response["agent_response"],
            "conversation_phase": str(response["next_phase"]),
            "requires_escalation": response.get("requires_escalation", False),
            "metadata": response.get("metadata", {})
        }

    def _generate_response(self, session: Dict, user_message: str) -> Dict[str, Any]:
        """Generate response based on current phase and user input"""
        current_phase = session["phase"]
        user_lower = user_message.lower()

        # GREETING phase
        if current_phase == ConversationPhase.GREETING:
            return {
                "agent_response": (
                    f"Buenos días, le habla {self.agent_name} de {self.company_name}, "
                    f"empresa autorizada por EPS Cosalud. "
                    f"Le informo que esta llamada está siendo grabada y monitoreada "
                    f"por calidad y seguridad. ¿Es usted el paciente o un familiar responsable?"
                ),
                "next_phase": ConversationPhase.IDENTIFICATION,
                "metadata": {}
            }

        # IDENTIFICATION phase
        elif current_phase == ConversationPhase.IDENTIFICATION:
            # Try to extract information
            if any(word in user_lower for word in ["yo soy", "mi nombre", "me llamo"]):
                # Extract name (simple heuristic)
                if "juan" in user_lower or "maría" in user_lower or "pedro" in user_lower:
                    session["patient_name"] = "Paciente Identificado"

                return {
                    "agent_response": (
                        f"Perfecto. ¿Podría por favor confirmarme su tipo de documento "
                        f"y número de cédula para verificar sus datos?"
                    ),
                    "next_phase": ConversationPhase.IDENTIFICATION,
                    "metadata": {}
                }

            # Check for document info
            if any(char.isdigit() for char in user_message):
                session["patient_document"] = "CC-1234567890"
                session["patient_eps"] = "COSALUD"

                return {
                    "agent_response": (
                        f"Muchas gracias por la información, Sr./Sra. Paciente. "
                        f"He verificado que usted pertenece a EPS Cosalud. "
                        f"Ahora, permítame coordinar el servicio de transporte. "
                        f"¿Para qué fecha y tipo de cita necesita el servicio?"
                    ),
                    "next_phase": ConversationPhase.SERVICE_COORDINATION,
                    "metadata": {"patient_validated": True}
                }

            return {
                "agent_response": (
                    f"Con mucho gusto. ¿Podría indicarme su nombre completo y "
                    f"número de documento por favor?"
                ),
                "next_phase": ConversationPhase.IDENTIFICATION,
                "metadata": {}
            }

        # SERVICE_COORDINATION phase
        elif current_phase == ConversationPhase.SERVICE_COORDINATION:
            # Check for complaints/incidents
            if any(word in user_lower for word in ["queja", "problema", "tarde", "impuntual", "conductor"]):
                return {
                    "agent_response": (
                        f"Comprendo su situación y lamento el inconveniente. "
                        f"Permítame disculparme. Voy a registrar su observación "
                        f"para que sea escalada al coordinador. ¿Puede darme más "
                        f"detalles sobre lo ocurrido?"
                    ),
                    "next_phase": ConversationPhase.INCIDENT_MANAGEMENT,
                    "metadata": {"incident_detected": True}
                }

            # Check for service info
            if any(word in user_lower for word in ["terapia", "diálisis", "dialisis", "consulta"]):
                if "terapia" in user_lower:
                    session["service_type"] = "TERAPIA"
                elif "diálisis" in user_lower or "dialisis" in user_lower:
                    session["service_type"] = "DIALISIS"
                else:
                    session["service_type"] = "CONSULTA_ESPECIALIZADA"

                return {
                    "agent_response": (
                        f"Perfecto, he registrado su servicio de {session['service_type']}. "
                        f"El servicio quedará coordinado en ruta compartida. "
                        f"¿Hay algo más en lo que pueda servirle?"
                    ),
                    "next_phase": ConversationPhase.CLOSING,
                    "metadata": {"service_coordinated": True}
                }

            return {
                "agent_response": (
                    f"Claro que sí. ¿Me puede indicar si es para terapia, diálisis "
                    f"o consulta especializada?"
                ),
                "next_phase": ConversationPhase.SERVICE_COORDINATION,
                "metadata": {}
            }

        # INCIDENT_MANAGEMENT phase
        elif current_phase == ConversationPhase.INCIDENT_MANAGEMENT:
            return {
                "agent_response": (
                    f"Gracias por compartir esta información. He registrado su "
                    f"observación con alta prioridad. El coordinador recibirá "
                    f"una notificación y se comunicará con usted en las próximas "
                    f"24-48 horas. ¿Hay algo más en lo que pueda ayudarle?"
                ),
                "next_phase": ConversationPhase.CLOSING,
                "metadata": {"incident_logged": True}
            }

        # CLOSING phase
        elif current_phase == ConversationPhase.CLOSING:
            if "no" in user_lower or "nada" in user_lower or "gracias" in user_lower:
                return {
                    "agent_response": (
                        f"Muy bien. Ha sido un gusto atenderle. Mi nombre es {self.agent_name} "
                        f"de {self.company_name}. Gracias por su tiempo y que tenga un "
                        f"excelente día. Lo invitamos a permanecer en línea para "
                        f"calificar nuestro servicio del 1 al 5."
                    ),
                    "next_phase": ConversationPhase.SURVEY,
                    "metadata": {}
                }

            return {
                "agent_response": (
                    f"Con mucho gusto. ¿En qué más puedo ayudarle?"
                ),
                "next_phase": ConversationPhase.CLOSING,
                "metadata": {}
            }

        # SURVEY phase
        elif current_phase == ConversationPhase.SURVEY:
            # Check for rating
            if any(char in user_message for char in "12345"):
                return {
                    "agent_response": (
                        f"Muchas gracias por su calificación. Su opinión es muy "
                        f"importante para nosotros. ¡Que tenga un excelente día!"
                    ),
                    "next_phase": ConversationPhase.END,
                    "metadata": {"survey_completed": True}
                }

            return {
                "agent_response": (
                    f"Por favor califique nuestro servicio del 1 al 5, siendo "
                    f"5 muy satisfecho."
                ),
                "next_phase": ConversationPhase.SURVEY,
                "metadata": {}
            }

        # END phase
        elif current_phase == ConversationPhase.END:
            return {
                "agent_response": (
                    f"La conversación ha finalizado. Gracias por contactar a "
                    f"{self.company_name}."
                ),
                "next_phase": ConversationPhase.END,
                "metadata": {"conversation_ended": True}
            }

        # Default
        return {
            "agent_response": "Disculpe, no entendí. ¿Puede repetir por favor?",
            "next_phase": current_phase,
            "metadata": {}
        }
