# Escalation detector node
from typing import Dict, Any

ESCALATION_KEYWORDS = [
    'servicio expreso', 'servicio express', 'urgente ya', 'inmediato',
    'fuera de la ciudad', 'zona rural', 'no autorizado', 'sin autorizacion'
]

def escalation_detector(state: Dict[str, Any]) -> Dict[str, Any]:
    """Detect if escalation to EPS is required"""
    reasons = []
    
    # Check policy violations (BLOCKING)
    violations = state.get('policy_violations', [])
    for v in violations:
        if v.get('severity') == 'BLOCKING':
            reasons.append(f"Politica bloqueante: {v.get('policy_name')}")
    
    # Check eligibility issues
    issues = state.get('eligibility_issues', [])
    if issues:
        reasons.extend(issues)
    
    # Check last message for keywords
    messages = state.get('messages', [])
    if messages:
        last_msg = ''
        for msg in reversed(messages):
            if hasattr(msg, 'type') and msg.type == 'human':
                last_msg = msg.content.lower()
                break
        
        for keyword in ESCALATION_KEYWORDS:
            if keyword in last_msg:
                reasons.append(f'Usuario menciono: {keyword}')
                break
    
    state['escalation_required'] = len(reasons) > 0
    state['escalation_reasons'] = reasons
    
    return state
