"""
Prompt Builder - Unified module for building LLM prompts

This module centralizes all prompt construction logic.
"""
import logging
from typing import Dict, Any, List
from src.domain.value_objects.conversation_phase import ConversationPhase
from src.agent.prompts.langgraph_prompts import (
    AGENT_PERSONALITY_ULTRA_COMPACT,
    PHASE_INSTRUCTIONS_COMPACT,
    PHASE_INSTRUCTIONS,
    KNOWN_DATA_TEMPLATE,
    POLICIES_TEMPLATE,
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
    politicas_relevantes: List[str] = None,
    casos_similares: List[str] = None,
    alertas: List[str] = None,
    greeting_done: bool = False,
    analisis_emocional: Dict[str, Any] = None  # NEW parameter
) -> str:
    """
    Build unified LLM prompt with dynamic context injection.

    Args:
        phase: Current conversation phase
        agent_name: Agent name
        company_name: Company name
        eps_name: EPS name
        known_data: Already extracted data
        politicas_relevantes: Relevant policies to inject
        casos_similares: Relevant cases to inject
        alertas: Critical alerts for the agent
        greeting_done: Whether greeting was already done
        analisis_emocional: Emotional analysis (sentiment, conflict, personality mode)

    Returns:
        Complete prompt string for LLM
    """
    logger.info(f"[PROMPT_BUILDER] Building prompt for phase={phase}")

    prompt = ""

    # 1. Personality section (ULTRA COMPACT para reducir tokens)
    logger.info("[PROMPT_BUILDER] Using ULTRA_COMPACT personality")
    prompt += AGENT_PERSONALITY_ULTRA_COMPACT.format(
        agent_name=agent_name,
        company_name=company_name,
        eps_name=eps_name
    )

    prompt += "\n- RESPONDE SOLO con JSON válido exactamente con el esquema indicado.\n\n"

    # 2. Phase instructions (COMPACT cuando disponible)
    phase_instruction = PHASE_INSTRUCTIONS_COMPACT.get(phase) or PHASE_INSTRUCTIONS.get(phase, "")
    logger.info(f"[PROMPT_BUILDER] Using {'COMPACT' if phase in PHASE_INSTRUCTIONS_COMPACT else 'FULL'} phase instructions")

    if phase_instruction:
        # Extract variables from known_data
        patient_name = known_data.get("patient_full_name") or ""
        contact_name = known_data.get("contact_name") or ""
        service_type = known_data.get("service_type") or ""
        service_date = known_data.get("appointment_date") or ""
        service_time = known_data.get("appointment_time") or ""
        pickup_address = known_data.get("pickup_address") or ""

        try:
            formatted_instruction = phase_instruction.format(
                agent_name=agent_name,
                company_name=company_name,
                eps_name=eps_name,
                patient_name=patient_name,
                contact_name=contact_name,
                service_type=service_type,
                service_date=service_date,
                service_time=service_time,
                pickup_address=pickup_address,
            )
            prompt += formatted_instruction
            prompt += "\n\n"
        except KeyError as e:
            logger.error(f"[PROMPT_BUILDER] Missing variable in phase_instruction: {e}")
            raise

    # 3. Relevant policies (dynamic injection)
    if politicas_relevantes:
        logger.info(f"[PROMPT_BUILDER] Injecting {len(politicas_relevantes)} relevant policies")
        prompt += "╔═══════════════════════════════════════════════════════════════╗\n"
        prompt += "║ POLÍTICAS APLICABLES AL CONTEXTO ACTUAL                       ║\n"
        prompt += "╚═══════════════════════════════════════════════════════════════╝\n\n"

        for politica in politicas_relevantes:
            prompt += f"{politica}\n\n"

        prompt += "═══════════════════════════════════════════════════════════════\n\n"

    # 4. Relevant cases (dynamic injection)
    if casos_similares:
        logger.info(f"[PROMPT_BUILDER] Injecting {len(casos_similares)} relevant cases")
        prompt += "╔═══════════════════════════════════════════════════════════════╗\n"
        prompt += "║ CASOS SIMILARES A LA SITUACIÓN ACTUAL                         ║\n"
        prompt += "╚═══════════════════════════════════════════════════════════════╝\n\n"

        for caso in casos_similares:
            # Limit to first 15 lines to avoid context bloat
            caso_lines = caso.split('\n')[:15]
            prompt += '\n'.join(caso_lines) + "\n\n"

        prompt += "═══════════════════════════════════════════════════════════════\n\n"

    # 5. Known data
    known_data_str = _format_known_data(known_data)
    if known_data_str:
        prompt += KNOWN_DATA_TEMPLATE.format(known_data=known_data_str)
        prompt += "\n"

    # 6. Critical alerts
    if alertas:
        logger.info(f"[PROMPT_BUILDER] Adding {len(alertas)} alerts")
        alertas_str = "\n".join(f"- {a}" for a in alertas)
        prompt += ALERTS_TEMPLATE.format(alerts=alertas_str)
        prompt += "\n"

    # 7. NEW: Emotional adaptation (if analysis available)
    if analisis_emocional:
        sentiment = analisis_emocional.get("sentiment", "Neutro")
        conflict_level = analisis_emocional.get("conflict_level", "Bajo")
        personality_mode = analisis_emocional.get("personality_mode", "Balanceado")
        emotional_validation_required = analisis_emocional.get("emotional_validation_required", False)

        logger.info(f"[PROMPT_BUILDER] Adding emotional adaptation: {sentiment}, {conflict_level}, {personality_mode}")

        prompt += """
╔═══════════════════════════════════════════════════════════════╗
║ ADAPTACIÓN EMOCIONAL Y PERSONALIDAD                           ║
╚═══════════════════════════════════════════════════════════════╝

"""
        prompt += f"**Usuario detectado como:** {sentiment}\n"
        prompt += f"**Nivel de conflicto:** {conflict_level}\n"
        prompt += f"**Modo de personalidad sugerido:** {personality_mode}\n\n"

        # Adaptation based on sentiment
        if sentiment == "Frustración":
            prompt += """⚠️ **USUARIO FRUSTRADO/ENOJADO:**
- PRIORIDAD: Validación emocional ANTES de dar datos
- Usa frases empáticas: "Entiendo su frustración, Sr./Sra. {nombre}..."
- NO des información técnica de inmediato
- Primero valida la emoción, luego ofrece solución

"""
        elif sentiment == "Incertidumbre":
            prompt += """❓ **USUARIO CON DUDAS/CONFUSIÓN:**
- Usa lenguaje claro y simple
- Confirma comprensión: "¿Le quedó claro?" o "¿Tiene alguna duda?"
- Repite información importante de forma diferente

"""
        elif sentiment == "Euforia":
            prompt += """😊 **USUARIO POSITIVO/AGRADECIDO:**
- Mantén tono amable pero profesional
- Puedes ser más cálido en el trato

"""

        # Adaptation based on conflict level
        if conflict_level == "Alto":
            prompt += """🚨 **CONFLICTO ALTO:**
- Considera escalación a EPS si el problema está fuera de alcance
- Ofrece alternativas concretas
- No prometas lo que no puedes cumplir

"""

        # Adaptation based on personality mode
        if personality_mode == "Simplificado":
            prompt += """🔤 **MODO SIMPLIFICADO ACTIVADO:**
- Evita tecnicismos
- Usa frases cortas y directas
- Explica paso a paso si es necesario

"""
        elif personality_mode == "Técnico":
            prompt += """🔬 **MODO TÉCNICO ACTIVADO:**
- El usuario quiere detalles específicos
- Proporciona información precisa (fechas, horas, direcciones exactas)
- Puedes usar términos más formales

"""

        # Emotional validation requirement
        if emotional_validation_required:
            prompt += """❤️ **VALIDACIÓN EMOCIONAL REQUERIDA:**
ANTES de dar cualquier dato, usa una frase de validación:
Ejemplos:
- "Entiendo su preocupación, Sr./Sra. {nombre}, permítame ayudarle..."
- "Comprendo lo frustrante que puede ser esto..."
- "Tiene toda la razón en sentirse así, vamos a resolverlo..."

"""

        prompt += "═══════════════════════════════════════════════════════════════\n\n"

    # 8. Greeting context (REFORZADO)
    if greeting_done:
        prompt += """
⚠️ CRÍTICO - ESTADO DE CONVERSACIÓN:
Ya diste el saludo y aviso de grabación en un turno anterior.
NO LOS REPITAS bajo ninguna circunstancia.
Si lo haces, el usuario pensará que no lo escuchaste.
Continúa desde donde quedaste.

"""

    # 9. Extraction rules (CRITICAL for data capture from history)
    prompt += EXTRACTION_RULES
    prompt += "\n"

    # 10. Output format (DINÁMICO según fase actual)
    valid_phases = get_valid_next_phases(phase)
    prompt += "\nRESPONDE CON JSON VÁLIDO:\n"
    prompt += OUTPUT_SCHEMA_TEMPLATE.format(valid_phases=valid_phases)

    logger.info(f"[PROMPT_BUILDER] Prompt completed: ~{len(prompt.split())} words")
    return prompt


def _format_known_data(known_data: Dict[str, Any]) -> str:
    """
    Format known data for prompt injection.

    Args:
        known_data: Dictionary of extracted data

    Returns:
        Formatted string with known data
    """
    relevant_keys = [
        "patient_full_name",
        "document_type",
        "document_number",
        "eps",
        "service_type",
        "appointment_date",
        "appointment_time",
        "pickup_address",
        "contact_name",
        "contact_relationship",
        "contact_age",
    ]

    formatted = []
    for key in relevant_keys:
        value = known_data.get(key)
        if value and value not in (None, "", "null"):
            # Convert key to readable format
            readable = key.replace("_", " ").title()
            formatted.append(f"- {readable}: {value}")

    return "\n".join(formatted) if formatted else ""
