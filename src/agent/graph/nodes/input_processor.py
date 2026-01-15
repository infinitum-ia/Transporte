# Input processor node
from typing import Dict, Any
from langchain_core.messages import HumanMessage
from datetime import datetime

def input_processor(state: Dict[str, Any]) -> Dict[str, Any]:
    """Process user input and update state"""
    # Get last message
    messages = state.get('messages', [])
    if not messages:
        return state
    
    last_msg = messages[-1] if messages else None
    if not last_msg or not isinstance(last_msg, HumanMessage):
        return state
    
    # Update turn count
    state['turn_count'] = state.get('turn_count', 0) + 1
    
    # Update timestamp
    state['updated_at'] = datetime.utcnow().isoformat()
    
    return state
