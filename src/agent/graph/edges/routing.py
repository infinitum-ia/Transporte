# Routing functions for conditional edges
from typing import Dict, Any, Literal

def should_escalate(state: Dict[str, Any]) -> Literal['special_case_handler', 'context_builder']:
    """Pre-LLM: Si requiere escalamiento, no llamar al LLM"""
    if state.get('escalation_required', False):
        return 'special_case_handler'
    return 'context_builder'

def route_after_llm(state: Dict[str, Any]) -> Literal['excel_writer', 'special_case_handler', 'state_updater']:
    """Post-LLM: Ruteo segun respuesta"""
    next_phase = state.get('next_phase', '')
    
    if next_phase == 'END':
        return 'excel_writer'
    
    # Check special cases
    if state.get('wrong_number', False) or state.get('patient_deceased', False):
        return 'special_case_handler'
    
    return 'state_updater'

def should_continue(state: Dict[str, Any]) -> Literal['END', 'input_processor']:
    """Check if conversation should continue or end"""
    if state.get('next_phase') == 'END':
        return 'END'
    return 'input_processor'
