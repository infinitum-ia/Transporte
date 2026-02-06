"""
Pre-Analyzer Node - Clasificación de intención y emoción del usuario.

Ejecuta análisis rápido con gpt-4o-mini para:
1. Detectar estado emocional
2. Clasificar intención
3. Identificar temas/políticas relevantes
"""
import os
import json
import logging
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

# Prompt ultra-compacto para minimizar latencia
ANALYZER_PROMPT = """Analiza este mensaje de usuario en una llamada de transporte médico.

Mensaje: "{message}"
Contexto: Fase={phase}, Paciente={patient_name}

Responde SOLO JSON:
{{
  "emotion": "frustración|confusión|neutro|positivo",
  "emotion_level": "bajo|medio|alto",
  "intent": "confirmar|cambiar|queja|pregunta|cancelar|saludo",
  "topic": "horario|direccion|conductor|fecha|servicio|otro",
  "needs_empathy": true/false,
  "policy_keywords": ["cambio_direccion", "zona_cobertura", "acompanante", "conductor"]
}}

Reglas:
- "frustración" si hay enojo, molestia, quejas de servicio
- "confusión" si no entiende, pide repetir, hace preguntas vagas
- "needs_empathy"=true si emotion_level es "medio" o "alto"
- policy_keywords: solo incluye si el mensaje toca esos temas"""


class PreAnalyzer:
    """Analizador de intención y emoción con LLM pequeño."""

    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            max_tokens=150,  # Respuesta muy corta
            api_key=os.getenv("OPENAI_API_KEY")
        )

    def analyze(self, message: str, phase: str, patient_name: str = "", callbacks=None) -> Dict[str, Any]:
        """
        Analiza mensaje del usuario.

        Args:
            message: Mensaje del usuario
            phase: Fase actual de la conversación
            patient_name: Nombre del paciente (si se conoce)
            callbacks: LangChain callbacks for observability (e.g. Langfuse)

        Returns:
            Dict con análisis: emotion, intent, topic, etc.
        """
        prompt = ANALYZER_PROMPT.format(
            message=message[:200],  # Limitar para reducir tokens
            phase=phase,
            patient_name=patient_name or "desconocido"
        )

        try:
            invoke_kwargs = {}
            if callbacks:
                invoke_kwargs["config"] = {"callbacks": callbacks}
            response = self.llm.invoke(prompt, **invoke_kwargs)
            content = response.content.strip()
            print("Respuesta del analizador ", content)

            # Parsear JSON
            if content.startswith("```"):
                content = content.replace("```json", "").replace("```", "").strip()

            analysis = json.loads(content)

            # Validar campos requeridos
            analysis.setdefault("emotion", "neutro")
            analysis.setdefault("emotion_level", "bajo")
            analysis.setdefault("intent", "otro")
            analysis.setdefault("topic", "otro")
            analysis.setdefault("needs_empathy", False)
            analysis.setdefault("policy_keywords", [])

            logger.info(f"[PRE_ANALYZER] {analysis['emotion']}({analysis['emotion_level']}) | {analysis['intent']} | {analysis['topic']}")
            return analysis

        except Exception as e:
            logger.error(f"[PRE_ANALYZER] Error: {e}")
            # Fallback seguro
            return {
                "emotion": "neutro",
                "emotion_level": "bajo",
                "intent": "otro",
                "topic": "otro",
                "needs_empathy": False,
                "policy_keywords": []
            }


# Singleton
_analyzer_instance = None


def get_pre_analyzer() -> PreAnalyzer:
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = PreAnalyzer()
    return _analyzer_instance


def pre_analyzer_node(state: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Nodo de LangGraph para pre-análisis.

    Agrega al state:
    - user_emotion: estado emocional detectado
    - user_intent: intención clasificada
    - policy_keywords: temas de política relevantes
    - needs_empathy: si requiere respuesta empática
    """
    print("\n" + "="*60)
    print("🔍 [PRE_ANALYZER] INICIANDO ANÁLISIS")
    print("="*60)

    # Obtener último mensaje del usuario
    messages = state.get("messages", [])
    last_message = ""
    for msg in reversed(messages):
        if isinstance(msg, dict) and msg.get("role") == "user":
            last_message = msg.get("content", "")
            break
        elif hasattr(msg, "type") and msg.type == "human":
            last_message = msg.content
            break

    if not last_message:
        return state

    # Extract callbacks from LangGraph config for observability
    callbacks = config.get("callbacks") if config else None

    # Analizar
    analyzer = get_pre_analyzer()
    analysis = analyzer.analyze(
        message=last_message,
        phase=state.get("current_phase", "GREETING"),
        patient_name=state.get("patient_full_name", ""),
        callbacks=callbacks,
    )

    # Agregar al state
    state["user_emotion"] = analysis["emotion"]
    state["user_emotion_level"] = analysis["emotion_level"]
    state["user_intent"] = analysis["intent"]
    state["user_topic"] = analysis["topic"]
    state["needs_empathy"] = analysis["needs_empathy"]
    state["policy_keywords"] = analysis["policy_keywords"]

    print(f"\n📊 [PRE_ANALYZER] RESULTADO:")
    print(f"   • Emoción: {analysis['emotion']} ({analysis['emotion_level']})")
    print(f"   • Intent: {analysis['intent']}")
    print(f"   • Topic: {analysis['topic']}")
    print(f"   • Needs empathy: {analysis['needs_empathy']}")
    print(f"   • Policy keywords: {analysis['policy_keywords']}")
    print("="*60 + "\n")

    return state
