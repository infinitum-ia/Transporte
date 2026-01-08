# LLM responder node - call OpenAI with optimized prompt
import json
import logging
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)


def llm_responder(state: Dict[str, Any]) -> Dict[str, Any]:
    """Call LLM to generate response using optimized prompt"""

    # Get system prompt from context_builder
    system_prompt = state.get("llm_system_prompt", "")
    if not system_prompt:
        # Fallback if context_builder didn't run
        logger.warning("No system prompt in state, using fallback")
        state["agent_response"] = "Disculpe, hubo un problema técnico. ¿Puede repetir, por favor?"
        state["next_phase"] = state.get("current_phase", "GREETING")
        return state

    # Get conversation history (last few messages)
    messages = state.get("messages", [])
    last_user_message = None
    for msg in reversed(messages):
        if isinstance(msg, dict):
            if msg.get("role") == "user":
                last_user_message = msg.get("content", "")
                break
        elif hasattr(msg, "type") and msg.type == "human":
            last_user_message = msg.content
            break

    if not last_user_message:
        logger.warning("No user message found in state")
        state["agent_response"] = "Disculpe, no entendí. ¿Me puede repetir?"
        state["next_phase"] = state.get("current_phase", "GREETING")
        return state

    try:
        # Initialize LLM
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            max_tokens=2000,
        )

        # Build messages for LLM
        llm_messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=last_user_message),
        ]

        # Call LLM
        logger.info(f"Calling LLM for phase: {state.get('current_phase')}")
        response = llm.invoke(llm_messages)
        llm_output = response.content

        # Parse JSON response
        try:
            parsed = json.loads(llm_output)
            state["agent_response"] = parsed.get("agent_response", "")
            state["next_phase"] = parsed.get("next_phase", state.get("current_phase", "GREETING"))
            state["requires_escalation"] = parsed.get("requires_escalation", False)
            state["extracted_data"] = parsed.get("extracted", {})
        except json.JSONDecodeError:
            logger.error(f"Failed to parse LLM response: {llm_output}")
            # If LLM didn't return JSON, try to use it as response anyway
            state["agent_response"] = llm_output
            state["next_phase"] = state.get("current_phase", "GREETING")

    except Exception as e:
        logger.error(f"LLM call failed: {str(e)}")
        state["agent_response"] = "Disculpe, hubo un problema técnico. ¿Puede intentar más tarde?"
        state["next_phase"] = state.get("current_phase", "GREETING")

    return state
