"""
Response Validator Node - Validación y corrección de respuestas.

Dos capas de validación:
1. Capa A (Regex): Correcciones rápidas y determinísticas
2. Capa B (Fallback): Respuestas predefinidas para errores graves
"""
import re
import logging
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)


# =============================================================================
# CAPA A: REGLAS REGEX PARA CORRECCIÓN AUTOMÁTICA
# =============================================================================
REGEX_CORRECTIONS = [
    # Error: Usar parentesco como nombre
    (r'\bSr\.\s*(hijo|hija|esposo|esposa|mamá|papá|madre|padre|hermano|hermana|abuelo|abuela|nieto|nieta|tío|tía)\b',
     'señor', 'parentesco_como_nombre'),

    (r'\bSra\.\s*(hijo|hija|esposo|esposa|mamá|papá|madre|padre|hermano|hermana|abuelo|abuela|nieto|nieta|tío|tía)\b',
     'señora', 'parentesco_como_nombre'),

    # Error: Presentación duplicada
    (r'(Soy María de Transpormax[^.]*\.)\s*\1',
     r'\1', 'presentacion_duplicada'),

    # Error: "Buenos días/tardes" literal (debería elegir uno)
    (r'Buenos días/tardes',
     'Buenos días', 'saludo_literal'),

    # Error: Día duplicado ("LUNES, LUNES")
    (r'(\b(?:LUNES|MARTES|MIÉRCOLES|MIERCOLES|JUEVES|VIERNES|SÁBADO|SABADO|DOMINGO)\b),?\s*\1',
     r'\1', 'dia_duplicado'),

    # Error: "este LUNES, LUNES" (redundancia de día)
    (r'este\s+(\b(?:LUNES|MARTES|MIÉRCOLES|MIERCOLES|JUEVES|VIERNES|SÁBADO|SABADO|DOMINGO)\b),\s*\1',
     r'\1', 'este_dia_duplicado'),
]


# =============================================================================
# CAPA B: DETECCIÓN DE ERRORES GRAVES Y FALLBACKS
# =============================================================================
GRAVE_ERROR_PATTERNS = {
    # Patrón que indica error grave → respuesta fallback
    'parentesco_como_nombre': {
        'pattern': r'\b(Sr\.|Sra\.)\s*(hijo|hija|esposo|esposa|mamá|papá)\b',
        'fallback': "Perfecto, gracias. Soy María de Transpormax, autorizada por Cosalud. Esta llamada está siendo grabada para garantizar la calidad del servicio. ¿En qué puedo ayudarle?"
    },

    'respuesta_vacia': {
        'pattern': r'^[\s\.\,]*$',
        'fallback': "Disculpe, ¿podría repetir eso? No escuché bien."
    },

    'json_en_respuesta': {
        'pattern': r'\{.*"agent_response".*\}',
        'fallback': None  # Marca para extraer el agent_response del JSON
    },
}


# =============================================================================
# VALIDACIONES DE CONTEXTO (sin regex, lógica)
# =============================================================================
def _check_empathy_missing(response: str, needs_empathy: bool, emotion: str) -> Optional[str]:
    """
    Verifica si falta empatía cuando el usuario está molesto.

    Returns:
        Mensaje de advertencia si falta empatía, None si está OK
    """
    if not needs_empathy or emotion != "frustración":
        return None

    # Palabras que indican empatía
    empathy_words = [
        "entiendo", "lamento", "comprendo", "disculp",
        "tiene razón", "es frustrante", "molestia"
    ]

    response_lower = response.lower()
    has_empathy = any(word in response_lower for word in empathy_words)

    if not has_empathy:
        return "ADVERTENCIA: Usuario frustrado pero respuesta sin empatía"

    return None


def _check_policy_violation(response: str, relevant_policies: list) -> Optional[str]:
    """
    Verifica si la respuesta contradice alguna política.

    Returns:
        Mensaje de advertencia si hay violación, None si está OK
    """
    response_lower = response.lower()

    # Verificaciones específicas
    if "zona" in str(relevant_policies) or "cobertura" in str(relevant_policies):
        # Si hay política de zona y el agente dice "sí podemos ir"
        if "sí podemos" in response_lower or "no hay problema" in response_lower:
            return "ADVERTENCIA: Posible violación de política de cobertura"

    if "conductor" in str(relevant_policies):
        # Si hay política de conductor y el agente promete asignar uno específico
        if "le asignaré" in response_lower or "voy a asignar" in response_lower:
            return "ADVERTENCIA: No se puede prometer conductor específico"

    return None


# =============================================================================
# CLASE PRINCIPAL DEL VALIDADOR
# =============================================================================
class ResponseValidator:
    """Valida y corrige respuestas del LLM."""

    def validate_and_correct(
        self,
        response: str,
        state: Dict[str, Any]
    ) -> Tuple[str, bool, list]:
        """
        Valida y corrige una respuesta.

        Args:
            response: Respuesta generada por el LLM
            state: Estado de la conversación

        Returns:
            Tuple de (respuesta_corregida, fue_corregida, lista_de_correcciones)
        """
        corrections = []
        was_corrected = False
        corrected_response = response

        # Capa A: Correcciones Regex
        for pattern, replacement, error_type in REGEX_CORRECTIONS:
            if re.search(pattern, corrected_response, re.IGNORECASE):
                corrected_response = re.sub(
                    pattern,
                    replacement,
                    corrected_response,
                    flags=re.IGNORECASE
                )
                corrections.append(f"REGEX_FIX: {error_type}")
                was_corrected = True
                logger.info(f"[VALIDATOR] Corregido: {error_type}")

        # Capa B: Detección de errores graves → Fallback
        for error_name, config in GRAVE_ERROR_PATTERNS.items():
            if re.search(config['pattern'], corrected_response, re.IGNORECASE):
                if config['fallback']:
                    corrected_response = config['fallback']
                    corrections.append(f"FALLBACK: {error_name}")
                    was_corrected = True
                    logger.warning(f"[VALIDATOR] Error grave, usando fallback: {error_name}")
                elif error_name == 'json_en_respuesta':
                    # Intentar extraer agent_response del JSON
                    extracted = self._extract_from_json(corrected_response)
                    if extracted:
                        corrected_response = extracted
                        corrections.append("EXTRACTED_FROM_JSON")
                        was_corrected = True

        # Validaciones de contexto (solo advertencias, no correcciones automáticas)
        needs_empathy = state.get("needs_empathy", False)
        emotion = state.get("user_emotion", "neutro")
        policies = state.get("relevant_policies", [])

        empathy_warning = _check_empathy_missing(corrected_response, needs_empathy, emotion)
        if empathy_warning:
            corrections.append(empathy_warning)
            logger.warning(f"[VALIDATOR] {empathy_warning}")

        policy_warning = _check_policy_violation(corrected_response, policies)
        if policy_warning:
            corrections.append(policy_warning)
            logger.warning(f"[VALIDATOR] {policy_warning}")

        return corrected_response, was_corrected, corrections

    def _extract_from_json(self, text: str) -> Optional[str]:
        """Intenta extraer agent_response de un JSON mal formateado."""
        import json
        try:
            # Buscar el JSON en el texto
            match = re.search(r'\{[^{}]*"agent_response"\s*:\s*"([^"]+)"[^{}]*\}', text)
            if match:
                return match.group(1)

            # Intentar parsear como JSON completo
            data = json.loads(text)
            if isinstance(data, dict) and "agent_response" in data:
                return data["agent_response"]
        except:
            pass
        return None


# Singleton
_validator_instance = None


def get_response_validator() -> ResponseValidator:
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = ResponseValidator()
    return _validator_instance


def response_validator_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Nodo de LangGraph para validación de respuesta.

    Lee: state["agent_response"]
    Escribe: state["agent_response"] (corregida), state["validation_corrections"]
    """
    response = state.get("agent_response", "")

    if not response:
        return state

    validator = get_response_validator()
    corrected, was_corrected, corrections = validator.validate_and_correct(
        response=response,
        state=state
    )

    state["agent_response"] = corrected
    state["validation_corrections"] = corrections
    state["response_was_corrected"] = was_corrected

    if was_corrected:
        logger.info(f"[VALIDATOR] Respuesta corregida. Correcciones: {corrections}")

    return state
