# Policy engine node
from typing import Dict, Any
from src.agent.policies import PolicyEngine

def policy_engine_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate policies against current state"""
    engine = PolicyEngine()
    
    phase = state.get('current_phase', 'GREETING')
    direction = state.get('call_direction', 'INBOUND')
    
    result = engine.evaluate(state, phase, direction)
    
    state['active_policies'] = result.applicable_policies
    state['policy_violations'] = [
        {
            'policy_id': v.policy_id,
            'policy_name': v.policy_name,
            'severity': v.severity.value,
            'description': v.description,
            'detected_value': v.detected_value,
            'response_template': v.response_template
        }
        for v in result.violations
    ]
    state['policy_context_injected'] = result.prompt_injection
    
    return state
