"""
Prompt builders for conversational agent

REFACTORED:
- Unified build_prompt function (replaces build_dynamic_prompt and build_compact_prompt)
- Clean, centralized prompt construction
"""
from src.agent.prompts.prompt_builder import build_prompt

__all__ = [
    "build_prompt",
]
