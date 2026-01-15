"""
State schema for LangGraph-based conversation graph.

This module defines the ConversationState TypedDict that holds all conversation data
throughout the graph execution.
"""

from typing import TypedDict, Annotated, List, Dict, Optional, Any
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages


class ConversationState(TypedDict):
    """
    Complete state schema for conversation graph.
    
    This TypedDict contains all data needed throughout the conversation lifecycle,
    including patient data, service details, policy evaluations, and control flow.
    """
    
    # ========== Identificación ==========
    session_id: str
    """Unique session identifier"""
    
    call_direction: str
    """Call direction: INBOUND | OUTBOUND"""
    
    current_phase: str
    """Current conversation phase (e.g., GREETING, IDENTIFICATION, etc.)"""
    
    llm_system_prompt: str
    """Latest system prompt built for the LLM (persisted across nodes)"""
    
    agent_name: str
    """Agent name (e.g., María, Carlos)"""
    
    company_name: str
    """Company name (e.g., Transpormax)"""
    
    eps_name: str
    """EPS name (e.g., Cosalud)"""
    
    # ========== Mensajes (con append automático) ==========
    messages: Annotated[List[BaseMessage], add_messages]
    """Conversation message history with automatic append"""
    
    # ========== Datos del Paciente ==========
    patient_full_name: Optional[str]
    """Patient full name"""
    
    document_type: Optional[str]
    """Document type (CC, TI, CE, etc.)"""
    
    document_number: Optional[str]
    """Document number"""
    
    eps: Optional[str]
    """EPS name (must be Cosalud)"""
    
    phone: Optional[str]
    """Patient phone number"""

    relationship_to_patient: Optional[str]
    """Relationship of caller to patient (if not the patient)"""

    caller_name: Optional[str]
    """Name of the person calling (if not the patient)"""

    # ========== Contact Data (for outbound calls with family/friends) ==========
    contact_name: Optional[str]
    """Name of contact person (for outbound calls when not speaking with patient directly)"""

    contact_relationship: Optional[str]
    """Relationship of contact to patient (hermano, esposa, hijo, etc.)"""

    contact_age: Optional[str]
    """Age of contact (required if contact_relationship is hijo/nieto to validate >= 18)"""
    
    # ========== Datos del Servicio ==========
    service_type: Optional[str]
    """Service type: Terapia | Diálisis | Cita con Especialista"""
    
    treatment_type: Optional[str]
    """Specific treatment type (e.g., Fisioterapia, Diálisis)"""
    
    appointment_dates: List[str]
    """List of appointment dates (can be multiple for recurring services)"""

    appointment_date: Optional[str]
    """Single appointment date (for simple single-date services)"""

    appointment_time: Optional[str]
    """Appointment time (HH:MM format)"""
    
    pickup_address: Optional[str]
    """Pickup address for transport"""
    
    frequency: Optional[str]
    """Service frequency (daily, weekly, etc.)"""
    
    route_type: Optional[str]
    """Transport route type: ruta | expreso"""
    
    # ========== Políticas ==========
    active_policies: List[str]
    """List of policy IDs that apply to current state"""
    
    policy_violations: List[Dict[str, Any]]
    """List of detected policy violations with details"""
    
    policy_context_injected: str
    """Policy context text injected into prompt"""
    
    # ========== Validaciones pre-LLM ==========
    eligibility_checked: bool
    """Whether eligibility has been checked"""
    
    eligibility_issues: List[str]
    """List of eligibility issues found"""
    
    escalation_required: bool
    """Whether escalation to EPS is required"""
    
    escalation_reasons: List[str]
    """Reasons for escalation"""
    
    # ========== Incidencias ==========
    incidents: List[Dict[str, Any]]
    """
    Structured incidents list. Each incident has:
    - type: str (IMPUNTUALIDAD, CONDUCTOR_ROTACION, etc.)
    - severity: str (LOW, MEDIUM, HIGH)
    - description: str
    - timestamp: str (ISO 8601)
    """
    
    # ========== Confirmación (outbound) ==========
    confirmation_status: Optional[str]
    """Confirmation status: CONFIRMED | REJECTED | RESCHEDULED | UNKNOWN"""
    
    service_confirmed: bool
    """Whether service was confirmed by patient"""
    
    date_change_detected: bool
    """Whether a date/time change was requested"""
    
    new_appointment_date: Optional[str]
    """New appointment date if changed"""
    
    new_appointment_time: Optional[str]
    """New appointment time if changed"""
    
    rejection_reason: Optional[str]
    """Reason for service rejection"""
    
    # ========== Casos Especiales ==========
    special_needs: List[str]
    """Special needs (wheelchair, oxygen, etc.)"""
    
    coverage_issue: bool
    """Whether there's a coverage issue requiring EPS contact"""
    
    patient_away: bool
    """Whether patient is away/traveling"""
    
    patient_return_date: Optional[str]
    """Expected return date if patient is away"""
    
    wrong_number: bool
    """Whether call reached wrong number"""
    
    patient_deceased: bool
    """Whether patient is deceased"""
    
    language_barrier: bool
    """Whether there's a language barrier"""
    
    # ========== Observaciones ==========
    observations: List[str]
    """General observations about the call"""

    special_observation: Optional[str]
    """Special observation or request made during the call (e.g., request different driver, need wheelchair accessible vehicle)"""

    # ========== Análisis Emocional (Integración Ligera) ==========
    emotional_memory: List[Dict[str, Any]]
    """
    Historial de estados emocionales por turno.
    Cada entrada: {
        "turn": int,
        "sentiment": str,  # Frustración | Incertidumbre | Neutro | Euforia
        "conflict_level": str,  # Bajo | Medio | Alto
        "timestamp": str
    }
    """

    current_sentiment: Optional[str]
    """Sentimiento actual del usuario: Frustración | Incertidumbre | Neutro | Euforia"""

    current_conflict_level: Optional[str]
    """Nivel de conflicto actual: Bajo | Medio | Alto"""

    personality_mode: str
    """
    Modo de personalidad del agente: Balanceado (default) | Simplificado | Técnico
    - Balanceado: Conversación natural estándar
    - Simplificado: Lenguaje más simple, evita tecnicismos (se activa con confusión repetida)
    - Técnico: Detalles específicos, respuestas más informativas
    """

    emotional_validation_required: bool
    """Si el usuario requiere validación emocional antes de continuar con datos"""

    validation_attempt_count: int
    """Número de intentos de re-generación de respuesta (límite: 2)"""

    # ========== Supervisor Robusto (Pre-Analyzer + Context Enricher) ==========
    user_emotion: Optional[str]
    """Emoción detectada del usuario: frustración | confusión | neutro | positivo"""

    user_emotion_level: Optional[str]
    """Nivel de emoción: bajo | medio | alto"""

    user_intent: Optional[str]
    """Intención detectada: confirmar | cambiar | queja | pregunta | cancelar | saludo"""

    user_topic: Optional[str]
    """Tema principal: horario | direccion | conductor | fecha | servicio | otro"""

    needs_empathy: bool
    """Si el usuario requiere respuesta empática"""

    policy_keywords: List[str]
    """Keywords de políticas detectadas por el Pre-Analyzer"""

    relevant_policies: List[str]
    """Políticas aplicables inyectadas por el Context Enricher"""

    case_example: Optional[str]
    """Ejemplo de caso similar para Few-Shot prompting"""

    tone_instruction: Optional[str]
    """Instrucción de ajuste de tono según emoción detectada"""

    # ========== Control de Flujo ==========
    agent_response: str
    """Last agent response text"""
    
    next_phase: Optional[str]
    """Next phase to transition to"""
    
    turn_count: int
    """Number of conversation turns"""
    
    requires_human_review: bool
    """Whether conversation requires human review"""
    
    greeting_done: bool
    """Whether the initial greeting/legal notice was already delivered (outbound)"""
    
    # ========== Metadata ==========
    created_at: str
    """Session creation timestamp (ISO 8601)"""
    
    updated_at: str
    """Last update timestamp (ISO 8601)"""
    
    excel_row_index: Optional[int]
    """Row index in Excel file (for outbound calls)"""
