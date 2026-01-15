"""
Prompt Builder - Versión con Supervisor Robusto
Integra políticas, casos (Few-Shot) y ajustes de tono.
"""
import logging
from typing import Dict, Any, List, Optional
from src.domain.value_objects.conversation_phase import ConversationPhase
from src.agent.prompts.langgraph_prompts import (
    AGENT_PERSONALITY,
    PHASE_INSTRUCTIONS,
    KNOWN_DATA_TEMPLATE,
    ALERTS_TEMPLATE,
    EXTRACTION_RULES,
    OUTPUT_SCHEMA_TEMPLATE,
    get_valid_next_phases,
)

logger = logging.getLogger(__name__)


def build_prompt(
    phase: ConversationPhase,
    agent_name: str,
    company_name: str,
    eps_name: str,
    known_data: Dict[str, Any],
    alertas: List[str] = None,
    greeting_done: bool = False,
    # Nuevos parámetros del Supervisor
    tone_instruction: str = None,
    relevant_policies: List[str] = None,
    case_example: str = None,
    user_emotion: str = None,
    user_intent: str = None,
    # Deprecados (mantener por compatibilidad)
    politicas_relevantes: List[str] = None,
    casos_similares: List[str] = None,
    analisis_emocional: Dict[str, Any] = None,
) -> str:
    """
    Construye prompt unificado para el LLM con contexto enriquecido.

    Args:
        phase: Fase actual de la conversación
        agent_name: Nombre del agente
        company_name: Nombre de la empresa
        eps_name: Nombre de la EPS
        known_data: Datos ya extraídos
        alertas: Alertas críticas
        greeting_done: Si ya se hizo el saludo
        tone_instruction: Instrucción de ajuste de tono (del Supervisor)
        relevant_policies: Políticas aplicables (del Supervisor)
        case_example: Ejemplo de caso similar para Few-Shot (del Supervisor)
        user_emotion: Emoción detectada del usuario
        user_intent: Intención detectada del usuario

    Returns:
        Prompt completo para el LLM
    """
    logger.info(f"[PROMPT_BUILDER] Construyendo prompt para fase={phase}")
    logger.info(
        "[PROMPT_BUILDER] Datos conocidos para prompt | phase=%s | known_data=%s | alertas=%s",
        phase,
        {k: v for k, v in (known_data or {}).items() if v},
        alertas or [],
    )

    prompt_parts = []

    # 1. Personalidad del agente
    prompt_parts.append(AGENT_PERSONALITY.format(
        agent_name=agent_name,
        company_name=company_name,
        eps_name=eps_name
    ))

    # 2. NUEVO: Instrucción de tono (si hay emoción fuerte)
    if tone_instruction:
        prompt_parts.append(tone_instruction)

    # 3. Instrucciones de la fase actual
    phase_instruction = PHASE_INSTRUCTIONS.get(phase, "")
    if phase_instruction:
        patient_name = known_data.get("patient_full_name") or ""
        service_type = known_data.get("service_type") or ""
        service_date = known_data.get("appointment_date") or ""
        service_time = known_data.get("appointment_time") or ""

        try:
            formatted = phase_instruction.format(
                agent_name=agent_name,
                company_name=company_name,
                eps_name=eps_name,
                patient_name=patient_name,
                service_type=service_type,
                service_date=service_date,
                service_time=service_time,
                contact_name=known_data.get("contact_name") or "",
                contact_relationship=known_data.get("contact_relationship") or "",
                pickup_address=known_data.get("pickup_address") or "",
            )
            prompt_parts.append(formatted)
        except KeyError as e:
            logger.warning(f"Variable faltante en instrucción de fase: {e}")
            prompt_parts.append(phase_instruction)

    # 4. NUEVO: Políticas relevantes (del Supervisor)
    if relevant_policies:
        policies_str = "\n".join(f"• {p}" for p in relevant_policies)
        prompt_parts.append(f"""
POLÍTICAS APLICABLES (DEBES CUMPLIR):
{policies_str}
""")

    # 5. NUEVO: Ejemplo de caso similar (Few-Shot)
    if case_example:
        # Limitar a 500 caracteres para no inflar demasiado
        example_truncated = case_example[:500] + "..." if len(case_example) > 500 else case_example
        prompt_parts.append(f"""
EJEMPLO DE REFERENCIA:
{example_truncated}
""")

    # 6. Datos conocidos (filtrados por fase)
    known_data_str = _format_known_data_for_phase(known_data, phase)
    if known_data_str:
        prompt_parts.append(KNOWN_DATA_TEMPLATE.format(known_data=known_data_str))

    # 7. Alertas críticas
    if alertas:
        alertas_str = "\n".join(f"• {a}" for a in alertas)
        prompt_parts.append(ALERTS_TEMPLATE.format(alerts=alertas_str))

    # 8. Estado de saludo
    if greeting_done:
        prompt_parts.append("""
ESTADO: Ya diste saludo y aviso de grabación. NO los repitas.
""")

    # 9. Reglas de extracción
    prompt_parts.append(EXTRACTION_RULES)

    # 10. Formato de salida
    valid_phases = get_valid_next_phases(phase)
    prompt_parts.append("\nRESPONDE CON JSON VÁLIDO:")
    prompt_parts.append(OUTPUT_SCHEMA_TEMPLATE.format(valid_phases=valid_phases))

    prompt = "\n".join(prompt_parts)

    # Log de métricas
    word_count = len(prompt.split())
    has_tone = bool(tone_instruction)
    has_policy = bool(relevant_policies)
    has_case = bool(case_example)
    logger.info(f"[PROMPT_BUILDER] ~{word_count} palabras | tono={has_tone} | políticas={has_policy} | caso={has_case}")

    return prompt


def _format_known_data_for_phase(known_data: Dict[str, Any], phase: ConversationPhase) -> str:
    """
    Formatea datos conocidos relevantes para la fase actual.
    """
    always_relevant = ["patient_full_name", "contact_name", "contact_relationship"]

    phase_relevant = {
        ConversationPhase.OUTBOUND_GREETING: ["patient_full_name"],
        ConversationPhase.OUTBOUND_SERVICE_CONFIRMATION: [
            "patient_full_name", "service_type", "appointment_date",
            "appointment_time", "pickup_address", "contact_name"
        ],
        ConversationPhase.OUTBOUND_SPECIAL_CASES: [
            "patient_full_name", "service_type", "appointment_date",
            "appointment_time", "contact_name"
        ],
        ConversationPhase.OUTBOUND_CLOSING: [
            "patient_full_name", "service_type", "appointment_date",
            "appointment_time", "contact_name"
        ],
        ConversationPhase.IDENTIFICATION: [
            "patient_full_name", "document_type", "document_number", "eps"
        ],
        ConversationPhase.SERVICE_COORDINATION: [
            "patient_full_name", "service_type", "appointment_date",
            "appointment_time", "pickup_address"
        ],
    }

    relevant_keys = phase_relevant.get(phase, always_relevant + [
        "service_type", "appointment_date", "appointment_time", "pickup_address"
    ])

    formatted = []
    for key in relevant_keys:
        value = known_data.get(key)
        if value and value not in (None, "", "null"):
            readable = key.replace("_", " ").title()
            formatted.append(f"• {readable}: {value}")

    return "\n".join(formatted) if formatted else ""
