# Special case handler node
from typing import Dict, Any

def special_case_handler(state: Dict[str, Any]) -> Dict[str, Any]:
    """Handle special cases like escalations"""
    escalation_reasons = state.get('escalation_reasons', [])
    
    if escalation_reasons:
        # Generate escalation response
        state['agent_response'] = f"Entiendo la situacion. Debo escalar esto con la EPS Cosalud. Razon: {escalation_reasons[0]}"
    
    elif state.get('wrong_number'):
        state['agent_response'] = "Disculpe, parece que es numero equivocado."
    
    elif state.get('patient_deceased'):
        state['agent_response'] = "Lamento mucho su perdida. Voy a actualizar la informacion."
    
    else:
        state['agent_response'] = "Gracias por su tiempo."
    
    state['next_phase'] = 'END'
    state['requires_human_review'] = True
    
    return state
