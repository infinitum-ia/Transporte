# State updater node
from typing import Dict, Any
from datetime import datetime

def state_updater(state: Dict[str, Any]) -> Dict[str, Any]:
    """Update state after LLM response"""
    # Update phase if next_phase is set
    if state.get('next_phase'):
        state['current_phase'] = state['next_phase']
    
    # Update timestamp
    state['updated_at'] = datetime.utcnow().isoformat()
    
    return state
