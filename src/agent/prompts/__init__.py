"""
Prompt builders for conversational agent

Exports:
- build_inbound_system_prompt: For incoming calls (customer calls us)
- build_outbound_system_prompt: For outgoing calls (we call customer)
"""
from src.agent.prompts.inbound_prompts import build_inbound_system_prompt
from src.agent.prompts.outbound_prompts import build_outbound_system_prompt

__all__ = [
    "build_inbound_system_prompt",
    "build_outbound_system_prompt",
]
