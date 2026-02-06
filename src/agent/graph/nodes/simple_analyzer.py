"""
Simple Analyzer - Análisis basado en reglas (sin LLM).

Reemplaza el pre_analyzer LLM por un análisis rápido basado en patrones.
Reduce la latencia de ~2 segundos a <10ms.
"""
import re
from typing import Dict, Any, List

# Patrones de emoción
EMOTION_PATTERNS = {
    "frustración": [
        r"\b(molest[oa]?|enojad[oa]?|furi[oa]?|hart[oa]?|cansad[oa]?)\b",
        r"\b(increible|increíble|absurdo|ridiculo|ridículo|inaceptable)\b",
        r"\b(no me gusta|estoy molest|que problema|qué problema|siempre lo mismo|ya van varias)\b",
        r"[!]{2,}",  # Múltiples signos de exclamación
        r"\b(mal servicio|pesimo|pésimo|terrible|horrible)\b",
    ],
    "confusión": [
        r"\b(no entiendo|no entendi|no entendí|como asi|cómo así)\b",
        r"\b(que significa|qué significa|puede repetir|no me queda claro)\b",
        r"\b(expliqueme|explíqueme|no se|no sé|cual es|cuál es|que es|qué es)\b",
        r"[?]{2,}",  # Múltiples signos de interrogación
    ],
    "positivo": [
        r"\b(gracias|excelente|perfecto|muy bien|genial|maravilloso|fantastico|fantástico)\b",
        r"\b(agradezco|amable|claro|entendido|listo)\b",
    ],
}

# Patrones de intención
INTENT_PATTERNS = {
    "confirmar": [
        r"^(sí|si|claro|ok|okay|vale|listo|correcto|afirmativo|así es|exacto|eso)$",
        r"\b(confirmo|acepto|de acuerdo|está bien)\b",
    ],
    "negar": [
        r"^(no|nop|nel|negativo)$",
        r"\b(no puedo|no quiero|no me sirve|no asistir)\b",
    ],
    "cambiar": [
        r"\b(cambiar|modificar|actualizar|diferente|otra|otro)\b",
        r"\b(cambio de|quiero cambiar|necesito cambiar)\b",
    ],
    "cancelar": [
        r"\b(cancelar|anular|no voy|no asistir|no puedo ir)\b",
    ],
    "queja": [
        r"\b(queja|reclamo|denunciar|reportar|mal servicio)\b",
        r"\b(el conductor|llegó tarde|no llegó|me dejó)\b",
    ],
    "pregunta": [
        r"^\s*¿",  # Empieza con signo de pregunta
        r"\b(cuando|cuándo|donde|dónde|como|cómo|cual|cuál)\b",
        r"\b(que hora|qué hora|a que|a qué|por que|por qué)\b",
        r"\?$",  # Termina con signo de pregunta
    ],
    "saludo": [
        r"^(hola|buenos dias|buenos días|buenas tardes|buenas noches|alo|aló)[\s,!.]*$",
        r"^(hola|buenos dias|buenos días|buenas tardes|buenas noches)",
    ],
}

# Patrones de tópico
TOPIC_PATTERNS = {
    "horario": [
        r"\b(hora|horario|tiempo|tarde|temprano|puntual|demora)\b",
    ],
    "direccion": [
        r"\b(dirección|direccion|calle|carrera|avenida|barrio|casa|apartamento)\b",
        r"\b(recoger|recogida|paso por)\b",
    ],
    "conductor": [
        r"\b(conductor|chofer|chófer|driver|quien conduce|el que maneja)\b",
    ],
    "fecha": [
        r"\b(fecha|día|dia|mañana|pasado mañana|lunes|martes|miércoles|jueves|viernes)\b",
    ],
    "servicio": [
        r"\b(servicio|transporte|cita|terapia|diálisis|dialisis)\b",
    ],
}

# Keywords que activan políticas
POLICY_KEYWORDS_PATTERNS = {
    "cambio_direccion": [r"\b(cambiar dirección|otra dirección|no es esa|dirección incorrecta)\b"],
    "zona_cobertura": [r"\b(vereda|rural|fuera de|zona|cobertura|lejos)\b"],
    "acompanante": [r"\b(acompañante|acompañar|ir con|familiar|hijo|esposa)\b"],
    "conductor": [r"\b(conductor específico|mismo conductor|prefiero|no quiero ese)\b"],
    "menor_edad": [r"\b(soy el hijo|soy la hija|tengo \d+ años|menor)\b"],
}


def analyze_message(message: str) -> Dict[str, Any]:
    """
    Analiza un mensaje usando patrones regex.

    Retorna el mismo formato que el pre_analyzer LLM pero sin latencia.

    Args:
        message: Mensaje del usuario

    Returns:
        Dict con: emotion, emotion_level, intent, topic, needs_empathy, policy_keywords
    """
    msg_lower = message.lower().strip()

    # Detectar emoción
    emotion = "neutro"
    emotion_level = "bajo"

    for emo, patterns in EMOTION_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, msg_lower, re.IGNORECASE):
                emotion = emo
                # Determinar nivel
                matches = sum(1 for p in patterns if re.search(p, msg_lower, re.IGNORECASE))
                if matches >= 3:
                    emotion_level = "alto"
                elif matches >= 2:
                    emotion_level = "medio"
                else:
                    emotion_level = "bajo"
                break
        if emotion != "neutro":
            break

    # Detectar intención
    intent = "otro"
    for int_name, patterns in INTENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, msg_lower, re.IGNORECASE):
                intent = int_name
                break
        if intent != "otro":
            break

    # Detectar tópico
    topic = "otro"
    for top_name, patterns in TOPIC_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, msg_lower, re.IGNORECASE):
                topic = top_name
                break
        if topic != "otro":
            break

    # Detectar keywords de política
    policy_keywords = []
    for keyword, patterns in POLICY_KEYWORDS_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, msg_lower, re.IGNORECASE):
                policy_keywords.append(keyword)
                break

    # Determinar si necesita empatía
    needs_empathy = emotion in ["frustración", "confusión"] and emotion_level in ["medio", "alto"]

    return {
        "emotion": emotion,
        "emotion_level": emotion_level,
        "intent": intent,
        "topic": topic,
        "needs_empathy": needs_empathy,
        "policy_keywords": policy_keywords,
    }


def simple_analyzer_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Nodo de LangGraph para análisis simple basado en reglas.

    Reemplaza pre_analyzer_node pero sin llamada LLM.
    Latencia: <10ms en lugar de ~2000ms.
    """
    import time
    import logging
    logger = logging.getLogger(__name__)

    start_time = time.perf_counter()

    print("\n" + "="*60)
    print("⚡ [SIMPLE_ANALYZER] ANÁLISIS RÁPIDO (sin LLM)")
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
        # Sin mensaje, valores por defecto
        state["user_emotion"] = "neutro"
        state["user_emotion_level"] = "bajo"
        state["user_intent"] = "otro"
        state["user_topic"] = "otro"
        state["needs_empathy"] = False
        state["policy_keywords"] = []
        print("   (sin mensaje de usuario)")
        print("="*60 + "\n")
        return state

    # Analizar con reglas
    analysis = analyze_message(last_message)

    # Agregar al state
    state["user_emotion"] = analysis["emotion"]
    state["user_emotion_level"] = analysis["emotion_level"]
    state["user_intent"] = analysis["intent"]
    state["user_topic"] = analysis["topic"]
    state["needs_empathy"] = analysis["needs_empathy"]
    state["policy_keywords"] = analysis["policy_keywords"]

    # Calcular tiempo
    elapsed_ms = (time.perf_counter() - start_time) * 1000

    logger.info(f"[SIMPLE_ANALYZER] {analysis['emotion']}({analysis['emotion_level']}) | {analysis['intent']} | {analysis['topic']} | {elapsed_ms:.1f}ms")

    print(f"\n📊 [SIMPLE_ANALYZER] RESULTADO:")
    print(f"   • Emoción: {analysis['emotion']} ({analysis['emotion_level']})")
    print(f"   • Intent: {analysis['intent']}")
    print(f"   • Topic: {analysis['topic']}")
    print(f"   • Needs empathy: {analysis['needs_empathy']}")
    print(f"   • Policy keywords: {analysis['policy_keywords']}")
    print(f"   ⏱️  Tiempo: {elapsed_ms:.1f}ms (antes ~2000ms con LLM)")
    print("="*60 + "\n")

    return state
