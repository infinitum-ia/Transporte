# LLM responder node - temporary mock version
from typing import Dict, Any
from src.shared.utils.time_utils import get_greeting

def llm_responder(state: Dict[str, Any]) -> Dict[str, Any]:
    """Call LLM to generate response (simplified mock)"""
    # Temporary mock response based on phase
    phase = state.get('current_phase', 'GREETING')
    
    if phase == 'GREETING' or phase == 'OUTBOUND_GREETING':
        greeting = get_greeting()
        state['agent_response'] = f"{greeting}, soy {state.get('agent_name', 'Maria')} de {state.get('company_name', 'Transpormax')}. Esta llamada esta siendo grabada."
        state['next_phase'] = 'IDENTIFICATION' if phase == 'GREETING' else 'OUTBOUND_SERVICE_CONFIRMATION'
    
    elif phase == 'IDENTIFICATION':
        state['agent_response'] = "Por favor, podria darme su nombre completo?"
        state['next_phase'] = 'SERVICE_COORDINATION'
    
    elif phase == 'SERVICE_COORDINATION' or phase == 'OUTBOUND_SERVICE_CONFIRMATION':
        state['agent_response'] = "Perfecto, he registrado la informacion."
        state['next_phase'] = 'END'
    
    else:
        state['agent_response'] = "Gracias por su tiempo."
        state['next_phase'] = 'END'
    
    return state
