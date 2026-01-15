"""
Context Enricher Node - Inyección dinámica de políticas y casos.

Este nodo:
1. Selecciona políticas relevantes según topic/keywords del Pre-Analyzer
2. Busca casos similares para Few-Shot prompting
3. Ajusta instrucciones de tono según emoción detectada
"""
import logging
from typing import Dict, Any, List
from pathlib import Path

logger = logging.getLogger(__name__)


# =============================================================================
# MAPEO DE KEYWORDS A POLÍTICAS
# =============================================================================
POLICY_MAPPING = {
    "cambio_direccion": {
        "policy_id": "6",
        "summary": "El servicio de ruta cubre solo área urbana de Santa Marta. Zonas rurales requieren autorización especial de la EPS."
    },
    "zona_cobertura": {
        "policy_id": "6",
        "summary": "Cobertura limitada a zona urbana. Veredas y zonas rurales están fuera de cobertura."
    },
    "acompanante": {
        "policy_id": "5",
        "summary": "Máximo 1 acompañante. Acompañantes adicionales requieren autorización de la EPS."
    },
    "conductor": {
        "policy_id": "7",
        "summary": "No es posible asignar conductores específicos. Solo se pueden registrar sugerencias para el área de despacho."
    },
    "servicio_expreso": {
        "policy_id": "7",
        "summary": "El servicio estándar es 'ruta' (compartido). El servicio 'expreso' requiere autorización médica de la EPS."
    },
    "menor_edad": {
        "policy_id": "3",
        "summary": "Familiares directos (hijos/nietos) deben ser mayores de 18 años para recibir información sensible."
    },
}


# =============================================================================
# MAPEO DE SITUACIONES A CASOS (Few-Shot)
# =============================================================================
CASE_MAPPING = {
    # Por emoción
    "frustración": "1. Usuario Molesto por Cambio de Horario",
    "confusión": "4. Usuario Confundido o No Entiende",

    # Por intent
    "queja": "5. Queja de Conductor",
    "cambiar": "3. Solicitud de Cambio de Dirección",

    # Por topic
    "conductor": "5. Queja de Conductor",
    "direccion": "3. Solicitud de Cambio de Dirección",

    # Por situación especial
    "familiar": "2. Familiar Responde (No es el Paciente)",
    "transferencia": "9. Transferencia de Llamada",
    "numero_equivocado": "10. Número Equivocado",
    "movilidad_reducida": "6. Paciente con Movilidad Reducida",
    "acompanante": "7. Solicitud de Acompañante Adicional",
    "prisa": "8. Usuario con Prisa",
}


# =============================================================================
# INSTRUCCIONES DE TONO SEGÚN EMOCIÓN
# =============================================================================
TONE_INSTRUCTIONS = {
    "frustración": {
        "alto": """
⚠️ USUARIO MUY MOLESTO - PRIORIDAD MÁXIMA:
1. PRIMERO valida su emoción: "Entiendo completamente su molestia..."
2. SEGUNDO reconoce el problema específico que menciona
3. TERCERO ofrece acción concreta
NO des información hasta que hayas validado su sentimiento.""",

        "medio": """
⚠️ USUARIO MOLESTO:
- Reconoce su frustración antes de dar información
- Usa frases como "Tiene razón...", "Entiendo que esto sea frustrante..."
- No minimices el problema""",

        "bajo": ""  # Sin instrucción especial
    },

    "confusión": {
        "alto": """
⚠️ USUARIO CONFUNDIDO:
- Usa lenguaje MUY simple y directo
- Da información en pasos numerados
- Confirma comprensión: "¿Le queda claro?"
- NO uses tecnicismos ni abreviaturas""",

        "medio": """
- Simplifica tu explicación
- Ofrece repetir si es necesario""",

        "bajo": ""
    },

    "neutro": {"alto": "", "medio": "", "bajo": ""},
    "positivo": {"alto": "", "medio": "", "bajo": ""},
}


class ContextEnricher:
    """Enriquece el contexto con políticas, casos y ajustes de tono."""

    def __init__(self, base_path: str = None):
        if base_path is None:
            current_file = Path(__file__)
            base_path = str(current_file.parent.parent.parent.parent.parent)

        self.base_path = Path(base_path)
        self.casos_content = self._load_casos()

    def _load_casos(self) -> Dict[str, str]:
        """Carga y parsea casos.md"""
        casos_path = self.base_path / "casos.md"
        if not casos_path.exists():
            logger.warning(f"casos.md no encontrado en {casos_path}")
            return {}

        with open(casos_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parsear por secciones (## N. Título)
        casos = {}
        current_title = None
        current_content = []

        for line in content.split('\n'):
            if line.startswith('## '):
                if current_title:
                    casos[current_title] = '\n'.join(current_content).strip()
                current_title = line[3:].strip()
                current_content = []
            elif current_title:
                current_content.append(line)

        if current_title:
            casos[current_title] = '\n'.join(current_content).strip()

        logger.info(f"[CONTEXT_ENRICHER] Cargados {len(casos)} casos")
        return casos

    def enrich(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enriquece el contexto basándose en el análisis previo.

        Args:
            state: Estado con campos del Pre-Analyzer

        Returns:
            Dict con políticas, casos y ajustes de tono
        """
        emotion = state.get("user_emotion", "neutro")
        emotion_level = state.get("user_emotion_level", "bajo")
        intent = state.get("user_intent", "otro")
        topic = state.get("user_topic", "otro")
        policy_keywords = state.get("policy_keywords", [])

        enrichment = {
            "policies": [],
            "case_example": None,
            "tone_instruction": "",
        }

        # 1. Seleccionar políticas relevantes
        for keyword in policy_keywords:
            if keyword in POLICY_MAPPING:
                policy = POLICY_MAPPING[keyword]
                enrichment["policies"].append(policy["summary"])

        # 2. Buscar caso similar para Few-Shot
        case_key = None

        # Prioridad: emoción fuerte > intent > topic
        if emotion in ["frustración", "confusión"] and emotion_level in ["medio", "alto"]:
            case_key = CASE_MAPPING.get(emotion)
        elif intent in CASE_MAPPING:
            case_key = CASE_MAPPING.get(intent)
        elif topic in CASE_MAPPING:
            case_key = CASE_MAPPING.get(topic)

        if case_key and case_key in self.casos_content:
            enrichment["case_example"] = self.casos_content[case_key]

        # 3. Ajustar instrucción de tono
        tone_config = TONE_INSTRUCTIONS.get(emotion, {})
        enrichment["tone_instruction"] = tone_config.get(emotion_level, "")

        logger.info(f"[CONTEXT_ENRICHER] Políticas: {len(enrichment['policies'])}, Caso: {bool(enrichment['case_example'])}, Tono: {bool(enrichment['tone_instruction'])}")

        return enrichment


# Singleton
_enricher_instance = None


def get_context_enricher() -> ContextEnricher:
    global _enricher_instance
    if _enricher_instance is None:
        _enricher_instance = ContextEnricher()
    return _enricher_instance


def context_enricher_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Nodo de LangGraph para enriquecimiento de contexto.

    Agrega al state:
    - relevant_policies: lista de políticas aplicables
    - case_example: ejemplo de caso similar (Few-Shot)
    - tone_instruction: instrucción de ajuste de tono
    """
    print("\n" + "="*60)
    print("📚 [CONTEXT_ENRICHER] ENRIQUECIENDO CONTEXTO")
    print("="*60)
    print(f"   • Input - user_emotion: {state.get('user_emotion', 'NO DEFINIDO')}")
    print(f"   • Input - user_emotion_level: {state.get('user_emotion_level', 'NO DEFINIDO')}")
    print(f"   • Input - user_intent: {state.get('user_intent', 'NO DEFINIDO')}")
    print(f"   • Input - policy_keywords: {state.get('policy_keywords', [])}")

    enricher = get_context_enricher()
    enrichment = enricher.enrich(state)

    state["relevant_policies"] = enrichment["policies"]
    state["case_example"] = enrichment["case_example"]
    state["tone_instruction"] = enrichment["tone_instruction"]

    print(f"\n📤 [CONTEXT_ENRICHER] RESULTADO:")
    print(f"   • Políticas: {len(enrichment['policies'])} encontradas")
    for p in enrichment['policies']:
        print(f"     - {p[:60]}...")
    print(f"   • Caso ejemplo: {'SÍ (' + str(len(enrichment['case_example'])) + ' chars)' if enrichment['case_example'] else 'NO'}")
    print(f"   • Tone instruction: {'SÍ' if enrichment['tone_instruction'] else 'NO'}")
    if enrichment['tone_instruction']:
        print(f"     → {enrichment['tone_instruction'][:80]}...")
    print("="*60 + "\n")

    return state
