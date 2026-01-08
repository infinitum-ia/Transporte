# Eligibility checker node
from typing import Dict, Any

def eligibility_checker(state: Dict[str, Any]) -> Dict[str, Any]:
    """Check if patient/service is eligible"""
    issues = []

    # Check EPS
    eps = state.get('eps')
    if eps:
        eps = eps.lower()
        if eps != 'cosalud':
            issues.append(f'EPS {eps} no valida, solo Cosalud')
    
    # Check appointment dates
    dates = state.get('appointment_dates', [])
    if dates:
        # Basic validation - dates should exist
        if not all(dates):
            issues.append('Fechas de cita invalidas')
    
    state['eligibility_checked'] = True
    state['eligibility_issues'] = issues
    
    return state
