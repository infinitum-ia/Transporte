# Context builder node - temporary simplified version
from typing import Dict, Any

def context_builder(state: Dict[str, Any]) -> Dict[str, Any]:
    """Build context for LLM prompt (simplified)"""
    # For now, just pass through
    # In Fase 4, this will build compact prompts
    return state
