# Context builder node - build optimized prompts for LLM
from typing import Dict, Any, List
from src.agent.prompts.langgraph_prompts import build_compact_prompt
from src.domain.value_objects.conversation_phase import ConversationPhase


def context_builder(state: Dict[str, Any]) -> Dict[str, Any]:
    """Build compact optimized prompt for LLM with dynamic policy injection"""

    phase_str = state.get("current_phase", "GREETING")

    # Convert phase string to ConversationPhase enum if needed
    try:
        if isinstance(phase_str, str):
            phase = ConversationPhase[phase_str]
        else:
            phase = phase_str
    except KeyError:
        phase = ConversationPhase.GREETING

    # Gather known data from state
    known_data = {
        "patient_full_name": state.get("patient_full_name"),
        "document_type": state.get("patient_document_type"),
        "document_number": state.get("patient_document_number"),
        "eps": state.get("patient_eps"),
        "service_type": state.get("service_type"),
        "appointment_date": state.get("appointment_date"),
        "appointment_time": state.get("appointment_time"),
        "pickup_address": state.get("pickup_address"),
    }

    # Gather active policies for injection
    policies = state.get("policy_violations", [])
    policy_strings = []
    if policies:
        for violation in policies:
            policy_name = violation.get("policy_id", "")
            # Map policy IDs to human-readable restrictions
            policy_map = {
                "CONDUCTOR_001": "Solo puede sugerir conductores, no asignar",
                "SERVICIO_001": f"Solo trabajamos con EPS Cosalud (paciente tiene {violation.get('value')})",
                "GEOGRAFIA_001": "Solo operamos en Santa Marta urbano",
                "MODALIDAD_001": "Estándar es ruta compartida, para otros modos consulte su EPS",
                "PROTOCOLO_001": "Grabación obligatoria",
            }
            policy_text = policy_map.get(policy_name, policy_name)
            policy_strings.append(policy_text)

    # Gather alerts
    alerts: List[str] = []
    if state.get("escalation_required"):
        alerts.append(f"ESCALAMIENTO REQUERIDO: {state.get('escalation_reasons', ['Sin especificar'])[0]}")
    if state.get("eligibility_issues"):
        for issue in state.get("eligibility_issues", []):
            alerts.append(f"PROBLEMA DE ELEGIBILIDAD: {issue}")

    # Build optimized prompt
    system_prompt = build_compact_prompt(
        phase=phase,
        agent_name=state.get("agent_name", "María"),
        company_name=state.get("company_name", "Transpormax"),
        eps_name=state.get("eps_name", "Cosalud"),
        known_data=known_data,
        policies=policy_strings if policy_strings else None,
        alerts=alerts if alerts else None,
    )

    state["llm_system_prompt"] = system_prompt

    return state
