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
    
    # ========== Datos del Servicio ==========
    service_type: Optional[str]
    """Service type: Terapia | Diálisis | Cita con Especialista"""
    
    treatment_type: Optional[str]
    """Specific treatment type (e.g., Fisioterapia, Diálisis)"""
    
    appointment_dates: List[str]
    """List of appointment dates (can be multiple for recurring services)"""
    
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
    
    # ========== Control de Flujo ==========
    agent_response: str
    """Last agent response text"""
    
    next_phase: Optional[str]
    """Next phase to transition to"""
    
    turn_count: int
    """Number of conversation turns"""
    
    requires_human_review: bool
    """Whether conversation requires human review"""
    
    # ========== Metadata ==========
    created_at: str
    """Session creation timestamp (ISO 8601)"""
    
    updated_at: str
    """Last update timestamp (ISO 8601)"""
    
    excel_row_index: Optional[int]
    """Row index in Excel file (for outbound calls)"""
