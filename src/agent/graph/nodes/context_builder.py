# Context builder node - build optimized prompts for LLM (REFACTORED)
from typing import Dict, Any
import logging
from src.agent.prompts.prompt_builder import build_prompt
from src.agent.context_builder import get_context_builder
from src.domain.value_objects.conversation_phase import ConversationPhase

logger = logging.getLogger(__name__)


def context_builder(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build dynamic optimized prompt with LLM-identified policies and cases.

    REFACTORED:
    - Uses ContextBuilderAgent with LLM-based analysis (no keyword matching)
    - Uses unified prompt_builder module (no duplicated logic)
    - Clean, simple orchestration
    """

    print(f"\n{'━'*80}")
    print(f"📝 [NODO 1/3] CONTEXT BUILDER - Construcción Inteligente del Contexto")
    print(f"{'━'*80}")

    phase_str = state.get("current_phase", "GREETING")
    print(f"   📊 Fase actual: {phase_str}")

    # Convert phase string to ConversationPhase enum if needed
    try:
        if isinstance(phase_str, str):
            phase = ConversationPhase[phase_str]
        else:
            phase = phase_str
    except KeyError:
        phase = ConversationPhase.GREETING

    # Get last user message
    messages = state.get("messages", [])
    last_user_message = ""
    if messages:
        for msg in reversed(messages):
            if isinstance(msg, dict):
                if msg.get("role") == "user":
                    last_user_message = msg.get("content", "")
                    break
            elif hasattr(msg, "type"):
                if msg.type == "human":
                    last_user_message = msg.content
                    break

    print(f"   💬 Mensaje usuario: '{last_user_message[:60]}...'")
    print(f"\n🤖 [AGENT A] ContextBuilderAgent (LLM) - Analizando contexto...")
    print(f"   ➤ Identificando políticas relevantes con LLM...")
    print(f"   ➤ Identificando casos similares con LLM...")

    # Use ContextBuilderAgent to build dynamic context
    context_builder_agent = get_context_builder()
    dynamic_context = context_builder_agent.build_context(
        state=state,
        last_user_message=last_user_message,
        current_phase=phase_str
    )

    # Extract dynamic sections
    politicas_relevantes = dynamic_context.get("politicas_relevantes", [])
    casos_similares = dynamic_context.get("casos_similares", [])
    contexto_excel = dynamic_context.get("contexto_excel", {})
    alertas = dynamic_context.get("alertas", [])

    logger.info(f"📋 Políticas: {len(politicas_relevantes)}")
    logger.info(f"📁 Casos: {len(casos_similares)}")
    logger.info(f"⚠️  Alertas: {len(alertas)}")

    # Gather known data from state (including formatted Excel context)
    known_data = {
        "patient_full_name": contexto_excel.get("patient_name") or state.get("patient_full_name"),
        "document_type": state.get("document_type"),
        "document_number": state.get("document_number"),
        "eps": state.get("eps"),
        "service_type": contexto_excel.get("service_type") or state.get("service_type"),
        "appointment_date": contexto_excel.get("appointment_date_full") or state.get("appointment_date"),
        "appointment_date_raw": contexto_excel.get("appointment_date_raw"),
        "appointment_time": contexto_excel.get("appointment_time") or state.get("appointment_time"),
        "pickup_address": contexto_excel.get("pickup_address") or state.get("pickup_address"),
        "contact_name": state.get("contact_name"),
        "contact_relationship": state.get("contact_relationship"),
        "contact_age": state.get("contact_age"),
    }

    # Build unified prompt using prompt_builder
    logger.info(f"📝 Context Builder: Building prompt with prompt_builder")

    try:
        system_prompt = build_prompt(
            phase=phase,
            agent_name=state.get("agent_name", "María"),
            company_name=state.get("company_name", "Transpormax"),
            eps_name=state.get("eps_name", "Cosalud"),
            known_data=known_data,
            politicas_relevantes=politicas_relevantes,
            casos_similares=casos_similares,
            alertas=alertas,
            greeting_done=bool(state.get("greeting_done", False)),
            analisis_emocional=dynamic_context.get("analisis_emocional")  # NEW
        )
        logger.info(f"📝 Context Builder: Prompt built successfully, length={len(system_prompt)}")
    except Exception as e:
        logger.error(f"📝 Context Builder: ERROR building prompt: {e}", exc_info=True)
        raise

    state["llm_system_prompt"] = system_prompt

    # NEW: Update state with emotional analysis
    analisis_emocional = dynamic_context.get("analisis_emocional", {})
    if analisis_emocional:
        state["current_sentiment"] = analisis_emocional.get("sentiment", "Neutro")
        state["current_conflict_level"] = analisis_emocional.get("conflict_level", "Bajo")
        state["personality_mode"] = analisis_emocional.get("personality_mode", "Balanceado")
        state["emotional_validation_required"] = analisis_emocional.get("emotional_validation_required", False)

        # Add to emotional memory
        emotional_memory = state.get("emotional_memory", [])
        emotional_entry = {
            "turn": state.get("turn_count", 0),
            "sentiment": state["current_sentiment"],
            "conflict_level": state["current_conflict_level"],
            "timestamp": state.get("updated_at", "")
        }
        emotional_memory.append(emotional_entry)
        state["emotional_memory"] = emotional_memory

    print(f"\n✅ [NODO 1/3] Contexto construido exitosamente")
    print(f"   📏 Tamaño prompt: ~{len(system_prompt.split())} palabras (~{len(system_prompt)} caracteres)")
    print(f"   📋 Políticas inyectadas: {len(politicas_relevantes)}")
    print(f"   📁 Casos inyectados: {len(casos_similares)}")
    print(f"   ⚠️  Alertas: {len(alertas)}")
    if alertas:
        for alerta in alertas:
            print(f"      → {alerta}")
    if analisis_emocional:
        print(f"   😊 Análisis emocional:")
        print(f"      → Sentimiento: {state.get('current_sentiment')}")
        print(f"      → Nivel conflicto: {state.get('current_conflict_level')}")
        print(f"      → Modo personalidad: {state.get('personality_mode')}")
        if state.get('emotional_validation_required'):
            print(f"      ❤️  VALIDACIÓN EMOCIONAL REQUERIDA")
    print(f"{'━'*80}\n")

    return state
