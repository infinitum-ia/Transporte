# LLM responder node - call OpenAI with optimized prompt
import json
import logging
import os
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from src.infrastructure.logging import get_logger
from src.agent.graph.nodes.context_builder import context_builder as build_context_prompt
from src.infrastructure.config.settings import settings

logger = logging.getLogger(__name__)


def _truncate_preview(value: str | None, limit: int) -> str:
    """Return a single-line, truncated version of the prompt or message."""
    if not value:
        return ""
    cleaned = value.replace("\n", " ").strip()
    if len(cleaned) <= limit:
        return cleaned
    return f"{cleaned[:limit-3]}..."


def llm_responder(state: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
    """Call LLM to generate response using optimized prompt"""

    print(f"\n{'━'*80}")
    print(f"🤖 [NODO 2/3] LLM RESPONDER - Generando Respuesta con OpenAI")
    print(f"{'━'*80}")

    # Get system prompt from context_builder
    system_prompt = state.get("llm_system_prompt", "")
    if not system_prompt:
        logger.warning("No system prompt in state, re-running context_builder")
        state = build_context_prompt(state)
        system_prompt = state.get("llm_system_prompt", "")
    if not system_prompt:
        logger.warning("No system prompt after rebuild, using fallback")
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
        # Initialize LLM (force JSON output when model supports it)
        llm_kwargs = {
            "openai_api_key": settings.OPENAI_API_KEY,
            "model": settings.OPENAI_MODEL,
            "temperature": settings.OPENAI_TEMPERATURE,
            "max_tokens": settings.OPENAI_MAX_TOKENS,
        }
        model_name = (settings.OPENAI_MODEL or "").lower()
        if "gpt-4o" in model_name or "gpt-4" in model_name:
            llm_kwargs["response_format"] = {"type": "json_object"}

        llm = ChatOpenAI(**llm_kwargs)

        # Build messages for LLM with full conversation history
        llm_messages = [SystemMessage(content=system_prompt)]

        # Add conversation history (all messages)
        for msg in messages:
            if isinstance(msg, dict):
                # Dict format (from Redis)
                role = msg.get("role")
                content = msg.get("content", "")
                if role == "user":
                    llm_messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    from langchain_core.messages import AIMessage
                    llm_messages.append(AIMessage(content=content))
            elif hasattr(msg, "type"):
                # LangChain message format
                llm_messages.append(msg)

        policy_ids = [
            violation.get("policy_id") or violation.get("policy_name") or "desconocida"
            for violation in state.get("policy_violations", [])
            if isinstance(violation, dict)
        ]
        logger_preview = get_logger()
        logger_preview.log_langgraph_state(
            session_id=state.get("session_id", "unknown"),
            current_phase=str(state.get("current_phase", "N/A")),
            call_direction=str(state.get("call_direction", "N/A")),
            agent_name=state.get("agent_name"),
            patient_name=state.get("patient_full_name") or state.get("caller_name"),
            prompt_preview=_truncate_preview(system_prompt, 280),
            user_message_preview=_truncate_preview(last_user_message, 200),
            policy_ids=policy_ids,
            escalation_required=bool(state.get("escalation_required")),
            message_count=len(messages)
        )

        # Call LLM
        print(f"\n🧠 [AGENT B] OpenAI GPT ({settings.OPENAI_MODEL}) - Generando respuesta...")
        print(f"   ➤ Prompt: {len(system_prompt)} caracteres (~{len(system_prompt.split())} palabras)")
        print(f"   ➤ Historial: {len(messages)} mensajes")
        print(f"   ➤ Temperatura: {settings.OPENAI_TEMPERATURE}")
        print(f"   ➤ Max tokens: {settings.OPENAI_MAX_TOKENS}")
        logger.info(f"Calling LLM for phase: {state.get('current_phase')}")

        # ALWAYS print prompts for debugging (truncated in console, full in file)
        print(f"\n{'─'*80}")
        print("📄 PROMPT PREVIEW (primeras 500 caracteres):")
        print(f"{'─'*80}")
        print(system_prompt)
        print(f"\n{'─'*80}")
        print(f"💬 HISTORIAL DE CONVERSACIÓN ({len(messages)} mensajes):")
        for i, msg in enumerate(messages[-5:], 1):  # Show last 5 messages
            if isinstance(msg, dict):
                role = msg.get("role", "unknown")
                content = msg.get("content", "")[:100]
            elif hasattr(msg, "type"):
                role = msg.type
                content = msg.content[:100] if hasattr(msg, "content") else ""
            else:
                role = "unknown"
                content = str(msg)[:100]
            print(f"   {i}. [{role}]: {content}...")
        print(f"{'─'*80}\n")

        print(f"⏳ Esperando respuesta del LLM...")

        # Propagate Langfuse callbacks from LangGraph config
        llm_invoke_kwargs = {}
        if config and config.get("callbacks"):
            llm_invoke_kwargs["config"] = {"callbacks": config["callbacks"]}

        #print("==========LO QUE SE MANDA==========================",llm_messages)
        response = llm.invoke(llm_messages, **llm_invoke_kwargs)
        llm_output = response.content
        print("=======================LO QUE DEVUELVE=======================", llm_output)
        state["_llm_raw_output"] = llm_output
        print(f"✅ Respuesta recibida del LLM\n")

        # Parse JSON response
        try:
            parsed = json.loads(llm_output)
            state["agent_response"] = parsed.get("agent_response", "")
            state["next_phase"] = parsed.get("next_phase", state.get("current_phase", "GREETING"))
            state["requires_escalation"] = parsed.get("requires_escalation", False)
            state["extracted_data"] = parsed.get("extracted", {})

            # Validate response with rules (log-only, no retry)
            validation_result = _validate_response_rules(state["agent_response"], state)

            if validation_result['has_critical_error']:
                logger.warning(f"Validation issues (log-only): {validation_result['errors']}")
                print(f"⚠️  [VALIDACIÓN] Problemas detectados (solo log, sin retry):")
                for err in validation_result['errors']:
                    print(f"   → {err}")
            else:
                print(f"✅ [VALIDACIÓN] Respuesta aprobada")

            print(f"✅ [NODO 2/3] LLM completado exitosamente")
            print(f"   💬 Respuesta: '{state['agent_response'][:80]}...'")
            print(f"   🔄 Próxima fase: {state.get('current_phase')} → {state['next_phase']}")
            extracted_count = len([v for v in state['extracted_data'].values() if v])
            print(f"   📊 Datos extraídos: {extracted_count} campos")
            for key, value in state['extracted_data'].items():
                if value:
                    print(f"      → {key}: {value}")
            if state['requires_escalation']:
                print(f"   ⚠️  Requiere escalación: SÍ")
            print(f"{'━'*80}\n")

            # Log successful LLM response
            logger_preview.log_llm_response(
                session_id=state.get("session_id", "unknown"),
                current_phase=state.get("current_phase", "N/A"),
                agent_response=state["agent_response"],
                next_phase=state["next_phase"],
                extracted_data=state["extracted_data"],
                requires_escalation=state["requires_escalation"]
            )
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {llm_output}")
            logger_preview.log_llm_error(
                session_id=state.get("session_id", "unknown"),
                error_type="JSONDecodeError",
                error_message=f"Failed to parse: {str(e)}",
                current_phase=state.get("current_phase", "N/A")
            )
            # If LLM didn't return JSON, try to use it as response anyway
            state["agent_response"] = llm_output
            state["next_phase"] = state.get("current_phase", "GREETING")

    except Exception as e:
        logger.error(f"LLM call failed: {str(e)}")
        state["agent_response"] = "Disculpe, hubo un problema técnico. ¿Puede intentar más tarde?"
        state["next_phase"] = state.get("current_phase", "GREETING")

    return state


def _validate_response_rules(response: str, state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate LLM response using RULES (not LLM) to detect critical errors.

    This lightweight validation catches common issues without additional LLM cost:
    1. Logical failures (wrong dates/times)
    2. Security issues (revealing data to minors)
    3. Accessibility issues (overly complex language)
    4. Consistency issues (closing without summary)

    Args:
        response: Agent response text to validate
        state: Current conversation state

    Returns:
        Dict with: {
            "has_critical_error": bool,
            "errors": list of error strings,
            "error": first error (for correction prompt) or None
        }
    """
    import re
    from datetime import datetime

    errors = []

    # 1. LOGICAL FAILURE: Incorrect dates mentioned
    appointment_date = state.get('appointment_date')
    if appointment_date:
        # Extract dates mentioned in response (simple regex for common formats)
        # Patterns: "15 de enero", "20/01", "01-20", etc.
        date_patterns = [
            r'\b(\d{1,2})\s+de\s+(\w+)',  # "15 de enero"
            r'\b(\d{1,2})/(\d{1,2})',      # "15/01"
            r'\b(\d{1,2})-(\d{1,2})'       # "15-01"
        ]

        mentioned_dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, response, re.IGNORECASE)
            mentioned_dates.extend(matches)

        # Simple check: if appointment_date contains a day number,
        # verify it's mentioned in the response
        if mentioned_dates:
            # Extract day from appointment_date
            try:
                if '-' in appointment_date:
                    # YYYY-MM-DD format
                    date_obj = datetime.strptime(appointment_date, '%Y-%m-%d')
                elif '/' in appointment_date:
                    # DD/MM/YYYY format
                    date_obj = datetime.strptime(appointment_date, '%d/%m/%Y')
                else:
                    date_obj = None

                if date_obj:
                    correct_day = date_obj.day
                    # Check if correct_day is in any mentioned date
                    found_correct_date = False
                    for match in mentioned_dates:
                        if str(correct_day) in str(match[0]) if isinstance(match, tuple) else str(match):
                            found_correct_date = True
                            break

                    if not found_correct_date and mentioned_dates:
                        errors.append(f"Fecha mencionada no coincide con appointment_date={appointment_date}")

            except Exception:
                pass  # Date parsing failed, skip validation

    # 2. SECURITY: Revealing data to minors
    contact_age = state.get('contact_age')
    if contact_age:
        try:
            age_int = int(contact_age)
            if age_int < 18:
                # Check if response contains sensitive data
                sensitive_keywords = ['documento', 'dirección', 'cita', 'servicio', 'fecha', 'hora']
                if any(keyword in response.lower() for keyword in sensitive_keywords):
                    errors.append("Revelando datos sensibles a menor de edad (age<18)")
        except (ValueError, TypeError):
            pass

    # 3. ACCESSIBILITY: Sentences too long (>35 words)
    sentences = [s.strip() for s in response.split('.') if s.strip()]
    long_sentences = [s for s in sentences if len(s.split()) > 35]
    if len(long_sentences) > 2:  # Allow up to 2 long sentences
        errors.append(f"Lenguaje demasiado complejo ({len(long_sentences)} frases >35 palabras)")

    # 4. CONSISTENCY: Closing without summary
    next_phase = state.get('next_phase', '')
    if next_phase in ['END', 'OUTBOUND_CLOSING']:
        # Check if response includes confirmation/summary keywords
        summary_keywords = ['confirmar', 'queda registrado', 'resumen', 'para confirmar', 'entonces']
        has_summary = any(keyword in response.lower() for keyword in summary_keywords)

        # Also check if it includes critical data (date, time, service)
        has_date_ref = any(word in response.lower() for word in ['fecha', 'día', 'enero', 'febrero', 'marzo', 'lunes', 'martes'])
        has_time_ref = any(word in response.lower() for word in ['hora', ':'])
        has_service_ref = any(word in response.lower() for word in ['terapia', 'diálisis', 'cita', 'servicio'])

        # If closing, should have either summary keyword OR all three references
        if not (has_summary or (has_date_ref and has_time_ref and has_service_ref)):
            errors.append("Despedida sin resumen de confirmación")

    return {
        'has_critical_error': len(errors) > 0,
        'errors': errors,
        'error': errors[0] if errors else None
    }
