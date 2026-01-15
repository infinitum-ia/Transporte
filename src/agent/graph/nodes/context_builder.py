# Context builder node - Versión con Supervisor Robusto
from typing import Dict, Any
import logging
from src.agent.prompts.prompt_builder import build_prompt
from src.agent.context_builder import get_context_builder
from src.domain.value_objects.conversation_phase import ConversationPhase

logger = logging.getLogger(__name__)


def context_builder(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Construye el prompt del sistema para el LLM.

    Integra datos del Pre-Analyzer y Context Enricher:
    - tone_instruction: Ajuste de tono según emoción
    - relevant_policies: Políticas aplicables
    - case_example: Ejemplo para Few-Shot
    """
    print("\n" + "="*60)
    print("🔧 [CONTEXT_BUILDER] INICIANDO")
    print("="*60)

    phase_str = state.get("current_phase", "GREETING")

    # Convertir fase a enum
    try:
        phase = ConversationPhase[phase_str] if isinstance(phase_str, str) else phase_str
    except KeyError:
        phase = ConversationPhase.GREETING

    # Obtener último mensaje del usuario
    messages = state.get("messages", [])
    last_user_message = ""
    for msg in reversed(messages):
        if isinstance(msg, dict) and msg.get("role") == "user":
            last_user_message = msg.get("content", "")
            break
        elif hasattr(msg, "type") and msg.type == "human":
            last_user_message = msg.content
            break

    # Construir contexto base (formateo de fechas + alertas)
    context_agent = get_context_builder()
    dynamic_context = context_agent.build_context(
        state=state,
        last_user_message=last_user_message,
        current_phase=phase_str
    )

    # Extraer datos del contexto
    contexto_excel = dynamic_context.get("contexto_excel", {})
    alertas = dynamic_context.get("alertas", [])

    # Preparar datos conocidos
    known_data = {
        "patient_full_name": contexto_excel.get("patient_name") or state.get("patient_full_name"),
        "document_type": state.get("document_type"),
        "document_number": state.get("document_number"),
        "eps": state.get("eps"),
        "service_type": contexto_excel.get("service_type") or state.get("service_type"),
        "appointment_date": contexto_excel.get("appointment_date_full") or state.get("appointment_date"),
        "appointment_time": contexto_excel.get("appointment_time") or state.get("appointment_time"),
        "pickup_address": contexto_excel.get("pickup_address") or state.get("pickup_address"),
        "contact_name": state.get("contact_name"),
        "contact_relationship": state.get("contact_relationship"),
    }

    # DEBUG: Verificar qué hay en el state del Supervisor
    print(f"\n📊 [CONTEXT_BUILDER] DATOS DEL SUPERVISOR EN STATE:")
    print(f"   • user_emotion: {state.get('user_emotion', 'NO ENCONTRADO')}")
    print(f"   • user_emotion_level: {state.get('user_emotion_level', 'NO ENCONTRADO')}")
    print(f"   • user_intent: {state.get('user_intent', 'NO ENCONTRADO')}")
    print(f"   • tone_instruction: {state.get('tone_instruction', 'NO ENCONTRADO')[:50] if state.get('tone_instruction') else 'VACÍO'}")
    print(f"   • relevant_policies: {state.get('relevant_policies', 'NO ENCONTRADO')}")
    print(f"   • case_example: {'SÍ (' + str(len(state.get('case_example', ''))) + ' chars)' if state.get('case_example') else 'NO'}")

    # Obtener datos del Supervisor (Pre-Analyzer + Context Enricher)
    tone_instruction = state.get("tone_instruction", "")
    relevant_policies = state.get("relevant_policies", [])
    case_example = state.get("case_example", "")
    user_emotion = state.get("user_emotion", "neutro")
    user_intent = state.get("user_intent", "otro")

    # Construir prompt con contexto enriquecido
    system_prompt = build_prompt(
        phase=phase,
        agent_name=state.get("agent_name", "María"),
        company_name=state.get("company_name", "Transpormax"),
        eps_name=state.get("eps_name", "Cosalud"),
        known_data=known_data,
        alertas=alertas,
        greeting_done=bool(state.get("greeting_done", False)),
        # Datos del Supervisor
        tone_instruction=tone_instruction,
        relevant_policies=relevant_policies,
        case_example=case_example,
        user_emotion=user_emotion,
        user_intent=user_intent,
    )

    state["llm_system_prompt"] = system_prompt

    # DEBUG: Verificar qué se inyectó al prompt
    print(f"\n📝 [CONTEXT_BUILDER] PROMPT CONSTRUIDO:")
    print(f"   • Longitud: ~{len(system_prompt.split())} palabras")
    print(f"   • Contiene 'POLÍTICAS APLICABLES': {'SÍ' if 'POLÍTICAS APLICABLES' in system_prompt else 'NO'}")
    print(f"   • Contiene 'EJEMPLO DE REFERENCIA': {'SÍ' if 'EJEMPLO DE REFERENCIA' in system_prompt else 'NO'}")
    has_tone = bool(tone_instruction) and tone_instruction in system_prompt
    print(f"   • Contiene instrucción de tono: {'SÍ' if has_tone else 'NO'}")
    print("="*60 + "\n")

    logger.info(
        f"[CONTEXT_BUILDER] Fase: {phase_str} | "
        f"Emoción: {user_emotion} | "
        f"Intent: {user_intent} | "
        f"Políticas: {len(relevant_policies)} | "
        f"Prompt: ~{len(system_prompt.split())} palabras"
    )

    return state
