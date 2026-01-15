"""
Adapters for serializing/deserializing ConversationState to/from Redis.

These adapters handle the conversion between the TypedDict state and JSON
for Redis storage, including special handling for LangChain message objects.
"""

from typing import Dict, Any
from datetime import datetime
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from src.agent.graph.state import ConversationState


def serialize_message(message: BaseMessage) -> Dict[str, Any]:
    """
    Serialize a LangChain message to a dictionary.
    
    Args:
        message: LangChain BaseMessage
        
    Returns:
        Dictionary representation of the message
    """
    return {
        "role": message.__class__.__name__.replace("Message", "").lower(),
        "content": message.content,
        "type": message.__class__.__name__
    }


def deserialize_message(message_dict: Dict[str, Any]) -> BaseMessage:
    """
    Deserialize a dictionary to a LangChain message.
    
    Args:
        message_dict: Dictionary with message data
        
    Returns:
        LangChain BaseMessage object
    """
    message_type = message_dict.get("type", "HumanMessage")
    content = message_dict.get("content", "")
    
    if message_type == "HumanMessage":
        return HumanMessage(content=content)
    elif message_type == "AIMessage":
        return AIMessage(content=content)
    elif message_type == "SystemMessage":
        return SystemMessage(content=content)
    else:
        # Default to HumanMessage
        return HumanMessage(content=content)


def state_to_dict(state: ConversationState) -> Dict[str, Any]:
    """
    Convert ConversationState to a JSON-serializable dictionary.
    
    Args:
        state: ConversationState TypedDict
        
    Returns:
        Dictionary that can be serialized to JSON for Redis
    """
    serialized = dict(state)
    
    # Serialize messages
    if "messages" in serialized and serialized["messages"]:
        serialized["messages"] = [
            serialize_message(msg) for msg in serialized["messages"]
        ]
    
    return serialized


def dict_to_state(data: Dict[str, Any]) -> ConversationState:
    """
    Convert a dictionary from Redis to ConversationState.
    
    Args:
        data: Dictionary from Redis
        
    Returns:
        ConversationState TypedDict
    """
    # Deserialize messages
    if "messages" in data and data["messages"]:
        data["messages"] = [
            deserialize_message(msg_dict) for msg_dict in data["messages"]
        ]
    
    return data  # type: ignore


def create_initial_state(
    session_id: str,
    call_direction: str,
    agent_name: str = "María",
    company_name: str = "Transpormax",
    eps_name: str = "Cosalud",
    excel_row_index: int = None
) -> ConversationState:
    """
    Create an initial ConversationState with default values.
    
    Args:
        session_id: Unique session identifier
        call_direction: INBOUND or OUTBOUND
        agent_name: Agent name
        company_name: Company name
        eps_name: EPS name
        excel_row_index: Excel row index (for outbound calls)
        
    Returns:
        Initialized ConversationState
    """
    now = datetime.utcnow().isoformat()
    
    # Determine initial phase based on call direction
    if call_direction == "OUTBOUND":
        initial_phase = "OUTBOUND_GREETING"
    else:
        initial_phase = "GREETING"
    
    return {
        # Identificación
        "session_id": session_id,
        "call_direction": call_direction,
        "current_phase": initial_phase,
        "llm_system_prompt": "",
        "agent_name": agent_name,
        "company_name": company_name,
        "eps_name": eps_name,
        
        # Mensajes
        "messages": [],
        
        # Datos del paciente
        "patient_full_name": None,
        "document_type": None,
        "document_number": None,
        "eps": None,
        "phone": None,
        "relationship_to_patient": None,
        "caller_name": None,

        # Contact data (for outbound calls)
        "contact_name": None,
        "contact_relationship": None,
        "contact_age": None,
        
        # Datos del servicio
        "service_type": None,
        "treatment_type": None,
        "appointment_dates": [],
        "appointment_date": None,
        "appointment_time": None,
        "pickup_address": None,
        "frequency": None,
        "route_type": None,
        
        # Políticas
        "active_policies": [],
        "policy_violations": [],
        "policy_context_injected": "",
        
        # Validaciones pre-LLM
        "eligibility_checked": False,
        "eligibility_issues": [],
        "escalation_required": False,
        "escalation_reasons": [],
        
        # Incidencias
        "incidents": [],
        
        # Confirmación (outbound)
        "confirmation_status": None,
        "service_confirmed": False,
        "date_change_detected": False,
        "new_appointment_date": None,
        "new_appointment_time": None,
        "rejection_reason": None,
        
        # Casos especiales
        "special_needs": [],
        "coverage_issue": False,
        "patient_away": False,
        "patient_return_date": None,
        "wrong_number": False,
        "patient_deceased": False,
        "language_barrier": False,
        
        # Observaciones
        "observations": [],
        "special_observation": None,

        # Análisis Emocional (Integración Ligera)
        "emotional_memory": [],
        "current_sentiment": "Neutro",
        "current_conflict_level": "Bajo",
        "personality_mode": "Balanceado",
        "emotional_validation_required": False,
        "validation_attempt_count": 0,

        # Supervisor Robusto (Pre-Analyzer + Context Enricher)
        "user_emotion": "neutro",
        "user_emotion_level": "bajo",
        "user_intent": "otro",
        "user_topic": "otro",
        "needs_empathy": False,
        "policy_keywords": [],
        "relevant_policies": [],
        "case_example": None,
        "tone_instruction": "",

        # Control de flujo
        "agent_response": "",
        "next_phase": None,
        "turn_count": 0,
        "requires_human_review": False,
        "greeting_done": False,

        # Metadata
        "created_at": now,
        "updated_at": now,
        "excel_row_index": excel_row_index
    }
