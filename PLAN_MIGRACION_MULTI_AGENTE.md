# Plan de Migración: Arquitectura Multi-Agente con Análisis Emocional

**Fecha:** 2026-01-10
**Objetivo:** Migrar de arquitectura LangGraph mono-agente a multi-agente con análisis emocional, validación de seguridad y memoria emocional persistente.

---

## 1. RESUMEN EJECUTIVO

### Arquitectura Actual (Mono-Agente)
- **1 agente LLM** (`llm_responder`) que genera respuestas basadas en prompts contextuales
- Flujo lineal: validaciones pre-LLM → LLM → procesamiento post-LLM
- Context builder con análisis de políticas y casos similares

### Arquitectura Propuesta (Multi-Agente)
- **3 agentes LLM especializados:**
  1. **Context & Emotion Manager** (Agente Secundario): Analiza sentimiento, conflicto, personalidad
  2. **The Orchestrator** (Agente Principal): Genera respuestas adaptadas al contexto emocional
  3. **The Guardrail** (Agente de Seguridad): Valida respuestas antes de enviarlas al usuario

- **Memoria emocional persistente**: Historial de estados emocionales del usuario
- **Validación en cascada**: El Guardrail puede rechazar y forzar re-generación
- **Adaptación de personalidad dinámica**: Balanceado, Simplificado, Técnico

---

## 2. CAMBIOS EN EL STATE (ConversationState)

### Archivo: `src/agent/graph/state.py`

**AGREGAR CAMPOS NUEVOS:**

```python
# ========== Análisis Emocional y Personalidad ==========
emotional_memory: List[Dict[str, Any]]
"""
Historial de estados emocionales por turno.
Cada entrada: {
    "turn": int,
    "sentiment": str,  # Frustración | Incertidumbre | Neutro | Euforia
    "conflict_level": str,  # Bajo | Medio | Alto
    "timestamp": str
}
"""

current_sentiment: Optional[str]
"""Sentimiento actual del usuario: Frustración | Incertidumbre | Neutro | Euforia"""

current_conflict_level: Optional[str]
"""Nivel de conflicto actual: Bajo | Medio | Alto"""

personality_mode: str
"""
Modo de personalidad del agente: Balanceado (default) | Simplificado | Técnico
- Balanceado: Conversación natural estándar
- Simplificado: Lenguaje más simple, evita tecnicismos (se activa con confusión repetida)
- Técnico: Detalles específicos, respuestas más informativas
"""

sarcasm_detected: bool
"""Si se detectó sarcasmo en el último mensaje del usuario"""

ambiguity_detected: bool
"""Si se detectó ambigüedad en el último mensaje del usuario"""

emotional_validation_required: bool
"""Si el usuario requiere validación emocional antes de continuar con datos"""

# ========== Validación de Seguridad ==========
safety_validation_status: Optional[str]
"""Estado de validación: APPROVED | REJECTED | PENDING"""

safety_rejection_reason: Optional[str]
"""Razón de rechazo por el Guardrail"""

safety_correction_needed: Optional[str]
"""Corrección sugerida por el Guardrail"""

validation_attempt_count: int
"""Número de intentos de validación (límite: 3)"""

safety_issues_detected: List[str]
"""
Lista de problemas detectados por el Guardrail:
- fallo_logico: Datos inconsistentes con Excel
- seguridad: Revelación de datos sensibles
- accesibilidad: Lenguaje demasiado complejo
- consistencia: Falta confirmación de datos antes de despedida
"""
```

**VALORES POR DEFECTO EN INICIALIZACIÓN:**

```python
# En langgraph_orchestrator.py o donde se inicialice el state
"emotional_memory": [],
"current_sentiment": "Neutro",
"current_conflict_level": "Bajo",
"personality_mode": "Balanceado",
"sarcasm_detected": False,
"ambiguity_detected": False,
"emotional_validation_required": False,
"safety_validation_status": None,
"safety_rejection_reason": None,
"safety_correction_needed": None,
"validation_attempt_count": 0,
"safety_issues_detected": [],
```

---

## 3. NUEVOS NODOS DEL GRAFO

### 3.1. Context & Emotion Manager (Agente Secundario)

**Archivo a crear:** `src/agent/graph/nodes/context_emotion_analyzer.py`

**Responsabilidad:**
- Analizar el último mensaje del usuario ANTES de que el Orchestrator genere respuesta
- Clasificar sentimiento (Frustración, Incertidumbre, Neutro, Euforia)
- Evaluar nivel de conflicto (Bajo, Medio, Alto)
- Sugerir adaptación de personalidad (Balanceado, Simplificado, Técnico)
- Detectar expresiones no literales (sarcasmo, ambigüedad)

**Estructura básica:**

```python
from typing import Dict, Any
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from src.infrastructure.config.settings import settings
from src.agent.prompts.emotion_analyzer_prompt import build_emotion_analysis_prompt
import logging

logger = logging.getLogger(__name__)

def context_emotion_analyzer(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Agente Secundario: Analiza contexto emocional antes de la respuesta.

    OUTPUT esperado del LLM (JSON):
    {
        "sentiment": "Frustración | Incertidumbre | Neutro | Euforia",
        "conflict_level": "Bajo | Medio | Alto",
        "personality_adaptation": "Balanceado | Simplificado | Técnico",
        "sarcasm_detected": bool,
        "ambiguity_detected": bool,
        "emotional_validation_required": bool,
        "resolution_strategy": "Validación Emocional | Informativa | Directa"
    }
    """

    print(f"\n{'━'*80}")
    print(f"😊 [AGENTE A] CONTEXT & EMOTION MANAGER - Análisis Emocional")
    print(f"{'━'*80}")

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

    if not last_user_message:
        # Sin mensaje, retornar valores neutros
        state["current_sentiment"] = "Neutro"
        state["current_conflict_level"] = "Bajo"
        state["personality_mode"] = "Balanceado"
        return state

    # Construir prompt de análisis emocional
    emotion_prompt = build_emotion_analysis_prompt(
        last_user_message=last_user_message,
        emotional_history=state.get("emotional_memory", []),
        current_phase=state.get("current_phase", "GREETING")
    )

    # Llamar LLM para análisis
    try:
        llm = ChatOpenAI(
            openai_api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            temperature=0.3,  # Más bajo para análisis objetivo
            max_tokens=500,
            response_format={"type": "json_object"}
        )

        llm_messages = [
            SystemMessage(content=emotion_prompt),
            HumanMessage(content=last_user_message)
        ]

        print(f"🧠 Analizando emoción con {settings.OPENAI_MODEL}...")
        response = llm.invoke(llm_messages)
        analysis = json.loads(response.content)

        # Actualizar state con análisis
        state["current_sentiment"] = analysis.get("sentiment", "Neutro")
        state["current_conflict_level"] = analysis.get("conflict_level", "Bajo")
        state["personality_mode"] = analysis.get("personality_adaptation", "Balanceado")
        state["sarcasm_detected"] = analysis.get("sarcasm_detected", False)
        state["ambiguity_detected"] = analysis.get("ambiguity_detected", False)
        state["emotional_validation_required"] = analysis.get("emotional_validation_required", False)

        # Agregar a memoria emocional
        emotional_entry = {
            "turn": state.get("turn_count", 0),
            "sentiment": state["current_sentiment"],
            "conflict_level": state["current_conflict_level"],
            "timestamp": state.get("updated_at", "")
        }
        emotional_memory = state.get("emotional_memory", [])
        emotional_memory.append(emotional_entry)
        state["emotional_memory"] = emotional_memory

        print(f"✅ Análisis emocional completado:")
        print(f"   😊 Sentimiento: {state['current_sentiment']}")
        print(f"   ⚠️  Nivel conflicto: {state['current_conflict_level']}")
        print(f"   🎭 Modo personalidad: {state['personality_mode']}")
        print(f"   🎪 Sarcasmo: {'Sí' if state['sarcasm_detected'] else 'No'}")
        print(f"   ❓ Ambigüedad: {'Sí' if state['ambiguity_detected'] else 'No'}")
        if state['emotional_validation_required']:
            print(f"   ❤️  REQUIERE VALIDACIÓN EMOCIONAL")
        print(f"{'━'*80}\n")

    except Exception as e:
        logger.error(f"Error en análisis emocional: {e}")
        # Valores por defecto en caso de error
        state["current_sentiment"] = "Neutro"
        state["current_conflict_level"] = "Bajo"
        state["personality_mode"] = "Balanceado"

    return state
```

**Archivo de prompts a crear:** `src/agent/prompts/emotion_analyzer_prompt.py`

```python
from typing import List, Dict, Any

def build_emotion_analysis_prompt(
    last_user_message: str,
    emotional_history: List[Dict[str, Any]],
    current_phase: str
) -> str:
    """Construye prompt para análisis emocional del mensaje del usuario"""

    prompt = f"""Eres un Analista de Contexto y Emociones experto en atención al cliente.

Tu tarea es analizar el mensaje del usuario y clasificar:

1. **Sentimiento**: Clasifica en una de estas categorías:
   - Frustración: Usuario molesto, enojado, impaciente
   - Incertidumbre: Usuario confundido, inseguro, con dudas
   - Neutro: Tono normal, sin emociones marcadas
   - Euforia: Usuario muy contento, agradecido, positivo

2. **Nivel de Conflicto**: Evalúa la intensidad del problema:
   - Bajo: Consulta simple, sin problema grave
   - Medio: Problema que requiere atención, pero manejable
   - Alto: Problema grave, usuario muy molesto o urgente

3. **Adaptación de Personalidad Sugerida**:
   - Modo Simplificado: Si hay confusión repetida, lenguaje complejo dificulta comprensión
   - Modo Técnico: Si el usuario pide detalles específicos, datos precisos
   - Modo Balanceado: Conversación estándar (default)

4. **Expresiones no literales**:
   - Sarcasmo: ¿El usuario usa sarcasmo o ironía?
   - Ambigüedad: ¿El mensaje es ambiguo o poco claro?

5. **Estrategia de Resolución**:
   - Validación Emocional: Si hay enojo/frustración, usar frases empáticas ANTES de dar datos
   - Informativa: Dar información directa y clara
   - Directa: Respuesta breve y concisa

**Fase actual de la conversación:** {current_phase}

**Historial emocional reciente:**
"""

    if emotional_history:
        for entry in emotional_history[-3:]:  # Últimos 3 turnos
            prompt += f"\n- Turno {entry['turn']}: {entry['sentiment']} (Conflicto: {entry['conflict_level']})"
    else:
        prompt += "\n(Sin historial previo)"

    prompt += """

**IMPORTANTE:**
- Si el usuario repite "¿Cómo?" o "¿Qué?" → Sugiere Modo Simplificado
- Si el usuario muestra frustración → Requiere Validación Emocional
- Si el usuario pide detalles técnicos → Sugiere Modo Técnico

**OUTPUT (JSON obligatorio):**
```json
{
  "sentiment": "Frustración | Incertidumbre | Neutro | Euforia",
  "conflict_level": "Bajo | Medio | Alto",
  "personality_adaptation": "Balanceado | Simplificado | Técnico",
  "sarcasm_detected": true/false,
  "ambiguity_detected": true/false,
  "emotional_validation_required": true/false,
  "resolution_strategy": "Validación Emocional | Informativa | Directa"
}
```
"""

    return prompt
```

---

### 3.2. The Orchestrator (Agente Principal)

**Archivo a crear:** `src/agent/graph/nodes/orchestrator.py`

**Responsabilidad:**
- Generar la respuesta del agente basándose en:
  - Análisis emocional del Agente Secundario
  - Contexto de políticas y casos (del context_builder)
  - Fase actual de la conversación
  - Datos ya conocidos del paciente/servicio
- Decidir el cambio de fase (next_phase)
- Aplicar estrategias de resolución según el estado emocional

**Diferencias con `llm_responder` actual:**
- Recibe contexto emocional como input adicional
- Adapta tono y estilo según `personality_mode`
- Aplica validación emocional si `emotional_validation_required = True`
- No repite datos ya confirmados

**Estructura básica:**

```python
from typing import Dict, Any
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from src.infrastructure.config.settings import settings
from src.agent.prompts.orchestrator_prompt import build_orchestrator_prompt
import logging

logger = logging.getLogger(__name__)

def orchestrator(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Agente Principal (The Orchestrator): Genera respuesta adaptada al contexto emocional.

    INPUT del state:
    - llm_system_prompt (del context_builder)
    - current_sentiment, current_conflict_level, personality_mode (del emotion_analyzer)
    - emotional_validation_required

    OUTPUT (JSON):
    {
        "agent_response": str,
        "next_phase": str,
        "requires_escalation": bool,
        "extracted": {...}
    }
    """

    print(f"\n{'━'*80}")
    print(f"🎭 [AGENTE B] THE ORCHESTRATOR - Generando Respuesta Contextual")
    print(f"{'━'*80}")

    # Obtener contexto emocional
    sentiment = state.get("current_sentiment", "Neutro")
    conflict_level = state.get("current_conflict_level", "Bajo")
    personality_mode = state.get("personality_mode", "Balanceado")
    emotional_validation_required = state.get("emotional_validation_required", False)

    print(f"   😊 Sentimiento: {sentiment}")
    print(f"   ⚠️  Conflicto: {conflict_level}")
    print(f"   🎭 Personalidad: {personality_mode}")
    if emotional_validation_required:
        print(f"   ❤️  VALIDACIÓN EMOCIONAL ACTIVADA")

    # Obtener prompt base del context_builder
    base_prompt = state.get("llm_system_prompt", "")

    # Construir prompt enriquecido con contexto emocional
    orchestrator_prompt = build_orchestrator_prompt(
        base_prompt=base_prompt,
        sentiment=sentiment,
        conflict_level=conflict_level,
        personality_mode=personality_mode,
        emotional_validation_required=emotional_validation_required,
        current_phase=state.get("current_phase", "GREETING"),
        safety_correction=state.get("safety_correction_needed")  # Si el Guardrail rechazó
    )

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

    if not last_user_message:
        logger.warning("No user message found")
        state["agent_response"] = "Disculpe, no entendí. ¿Me puede repetir?"
        state["next_phase"] = state.get("current_phase", "GREETING")
        return state

    try:
        # LLM call
        llm = ChatOpenAI(
            openai_api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            temperature=settings.OPENAI_TEMPERATURE,
            max_tokens=settings.OPENAI_MAX_TOKENS,
            response_format={"type": "json_object"}
        )

        llm_messages = [
            SystemMessage(content=orchestrator_prompt),
            HumanMessage(content=last_user_message)
        ]

        print(f"\n🧠 Generando respuesta con {settings.OPENAI_MODEL}...")
        print(f"   Prompt: ~{len(orchestrator_prompt.split())} palabras")

        response = llm.invoke(llm_messages)
        llm_output = json.loads(response.content)

        # Actualizar state
        state["agent_response"] = llm_output.get("agent_response", "")
        state["next_phase"] = llm_output.get("next_phase", state.get("current_phase"))
        state["requires_escalation"] = llm_output.get("requires_escalation", False)
        state["extracted_data"] = llm_output.get("extracted", {})
        state["_llm_raw_output"] = response.content

        print(f"\n✅ [AGENTE B] Respuesta generada:")
        print(f"   💬 '{state['agent_response'][:100]}...'")
        print(f"   🔄 Fase: {state.get('current_phase')} → {state['next_phase']}")
        print(f"{'━'*80}\n")

    except Exception as e:
        logger.error(f"Error en orchestrator: {e}")
        state["agent_response"] = "Disculpe, hubo un problema técnico."
        state["next_phase"] = state.get("current_phase", "GREETING")

    return state
```

**Archivo de prompts a crear:** `src/agent/prompts/orchestrator_prompt.py`

```python
def build_orchestrator_prompt(
    base_prompt: str,
    sentiment: str,
    conflict_level: str,
    personality_mode: str,
    emotional_validation_required: bool,
    current_phase: str,
    safety_correction: str = None
) -> str:
    """Enriquece el prompt base con adaptaciones emocionales"""

    # Comenzar con el prompt base (ya tiene contexto de políticas, casos, datos)
    enriched_prompt = base_prompt

    # Agregar sección de ADAPTACIÓN EMOCIONAL
    enriched_prompt += f"\n\n{'='*80}\n"
    enriched_prompt += "## ADAPTACIÓN EMOCIONAL Y PERSONALIDAD\n"
    enriched_prompt += f"{'='*80}\n\n"

    enriched_prompt += f"**Sentimiento del usuario detectado:** {sentiment}\n"
    enriched_prompt += f"**Nivel de conflicto:** {conflict_level}\n"
    enriched_prompt += f"**Modo de personalidad sugerido:** {personality_mode}\n\n"

    # Instrucciones según sentimiento
    if sentiment == "Frustración":
        enriched_prompt += "⚠️ **USUARIO FRUSTRADO/ENOJADO:**\n"
        enriched_prompt += "- PRIORIDAD: Validación emocional ANTES de dar datos\n"
        enriched_prompt += "- Usa frases empáticas: 'Entiendo su frustración, Sr./Sra. {nombre}...'\n"
        enriched_prompt += "- NO des información técnica de inmediato\n"
        enriched_prompt += "- Primero valida la emoción, luego ofrece solución\n\n"

    elif sentiment == "Incertidumbre":
        enriched_prompt += "❓ **USUARIO CON DUDAS/CONFUSIÓN:**\n"
        enriched_prompt += "- Usa lenguaje claro y simple\n"
        enriched_prompt += "- Confirma comprensión: '¿Le quedó claro?' o '¿Tiene alguna duda?'\n"
        enriched_prompt += "- Repite información importante de forma diferente\n\n"

    elif sentiment == "Euforia":
        enriched_prompt += "😊 **USUARIO POSITIVO/AGRADECIDO:**\n"
        enriched_prompt += "- Mantén tono amable pero profesional\n"
        enriched_prompt += "- Puedes ser más cálido en el trato\n\n"

    # Instrucciones según conflicto
    if conflict_level == "Alto":
        enriched_prompt += "🚨 **CONFLICTO ALTO:**\n"
        enriched_prompt += "- Considera escalación a EPS si el problema está fuera de alcance\n"
        enriched_prompt += "- Ofrece alternativas concretas\n"
        enriched_prompt += "- No prometas lo que no puedes cumplir\n\n"

    # Instrucciones según modo de personalidad
    if personality_mode == "Simplificado":
        enriched_prompt += "🔤 **MODO SIMPLIFICADO ACTIVADO:**\n"
        enriched_prompt += "- Evita tecnicismos\n"
        enriched_prompt += "- Usa frases cortas y directas\n"
        enriched_prompt += "- Explica paso a paso si es necesario\n\n"

    elif personality_mode == "Técnico":
        enriched_prompt += "🔬 **MODO TÉCNICO ACTIVADO:**\n"
        enriched_prompt += "- El usuario quiere detalles específicos\n"
        enriched_prompt += "- Proporciona información precisa (fechas, horas, direcciones exactas)\n"
        enriched_prompt += "- Puedes usar términos más formales\n\n"

    # Si requiere validación emocional
    if emotional_validation_required:
        enriched_prompt += "❤️ **VALIDACIÓN EMOCIONAL REQUERIDA:**\n"
        enriched_prompt += "ANTES de dar cualquier dato, usa una frase de validación:\n"
        enriched_prompt += "Ejemplos:\n"
        enriched_prompt += "- 'Entiendo su preocupación, Sr./Sra. {nombre}, permítame ayudarle...'\n"
        enriched_prompt += "- 'Comprendo lo frustrante que puede ser esto...'\n"
        enriched_prompt += "- 'Tiene toda la razón en sentirse así, vamos a resolverlo...'\n\n"

    # Si el Guardrail rechazó la respuesta anterior
    if safety_correction:
        enriched_prompt += "🛡️ **CORRECCIÓN DE SEGURIDAD:**\n"
        enriched_prompt += f"Tu respuesta anterior fue rechazada por: {safety_correction}\n"
        enriched_prompt += "Por favor, genera una nueva respuesta corrigiendo este problema.\n\n"

    # Recordatorio final
    enriched_prompt += f"{'='*80}\n"
    enriched_prompt += "## REGLAS CRÍTICAS\n"
    enriched_prompt += f"{'='*80}\n\n"
    enriched_prompt += "1. NO repitas datos ya confirmados en turnos anteriores\n"
    enriched_prompt += "2. Si el usuario se identifica correctamente → avanza de fase\n"
    enriched_prompt += "3. Si es menor de edad → activa protocolo 'Persona Autorizada'\n"
    enriched_prompt += f"4. Fase actual: {current_phase}\n"
    enriched_prompt += "5. Tu respuesta debe ser en formato JSON con:\n"
    enriched_prompt += "   - agent_response (str)\n"
    enriched_prompt += "   - next_phase (str)\n"
    enriched_prompt += "   - requires_escalation (bool)\n"
    enriched_prompt += "   - extracted (dict con datos extraídos)\n"

    return enriched_prompt
```

---

### 3.3. The Guardrail (Agente de Seguridad)

**Archivo a crear:** `src/agent/graph/nodes/safety_validator.py`

**Responsabilidad:**
- Revisar la respuesta del Orchestrator ANTES de enviarla al usuario
- Validar 4 aspectos críticos:
  1. **Fallo Lógico**: ¿Cita datos que no están en Excel o state?
  2. **Seguridad**: ¿Revela datos sensibles a personas no autorizadas?
  3. **Accesibilidad**: ¿Lenguaje demasiado complejo para el perfil del usuario?
  4. **Consistencia**: ¿Se despide sin confirmar datos de la cita?
- Retornar "APPROVED" o "REJECTED" con corrección

**Estructura básica:**

```python
from typing import Dict, Any
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from src.infrastructure.config.settings import settings
from src.agent.prompts.safety_validator_prompt import build_safety_validation_prompt
import logging

logger = logging.getLogger(__name__)

MAX_VALIDATION_ATTEMPTS = 3

def safety_validator(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Agente de Seguridad (The Guardrail): Valida respuesta antes de enviarla.

    OUTPUT (JSON):
    {
        "status": "APPROVED | REJECTED",
        "issues": [lista de problemas detectados],
        "correction_needed": "Descripción de la corrección" (si REJECTED)
    }
    """

    print(f"\n{'━'*80}")
    print(f"🛡️  [AGENTE C] THE GUARDRAIL - Validación de Seguridad")
    print(f"{'━'*80}")

    # Obtener respuesta del Orchestrator
    agent_response = state.get("agent_response", "")
    next_phase = state.get("next_phase", "")
    current_phase = state.get("current_phase", "")

    # Incrementar contador de intentos
    validation_attempts = state.get("validation_attempt_count", 0) + 1
    state["validation_attempt_count"] = validation_attempts

    print(f"   🔍 Intento de validación: {validation_attempts}/{MAX_VALIDATION_ATTEMPTS}")
    print(f"   💬 Validando respuesta: '{agent_response[:80]}...'")

    # Si ya se agotaron los intentos, aprobar automáticamente
    if validation_attempts > MAX_VALIDATION_ATTEMPTS:
        logger.warning(f"Max validation attempts reached, auto-approving")
        print(f"   ⚠️  Máximo de intentos alcanzado, aprobando automáticamente")
        state["safety_validation_status"] = "APPROVED"
        state["safety_issues_detected"] = []
        return state

    # Construir prompt de validación
    validation_prompt = build_safety_validation_prompt(
        agent_response=agent_response,
        current_phase=current_phase,
        next_phase=next_phase,
        known_data=_extract_known_data(state),
        excel_data=_extract_excel_data(state)
    )

    try:
        # LLM call
        llm = ChatOpenAI(
            openai_api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            temperature=0.1,  # Muy bajo para validación objetiva
            max_tokens=800,
            response_format={"type": "json_object"}
        )

        llm_messages = [
            SystemMessage(content=validation_prompt),
            HumanMessage(content=f"Valida esta respuesta: {agent_response}")
        ]

        print(f"   🧠 Validando con {settings.OPENAI_MODEL}...")
        response = llm.invoke(llm_messages)
        validation_result = json.loads(response.content)

        status = validation_result.get("status", "APPROVED")
        issues = validation_result.get("issues", [])
        correction = validation_result.get("correction_needed", "")

        state["safety_validation_status"] = status
        state["safety_issues_detected"] = issues
        state["safety_rejection_reason"] = correction if status == "REJECTED" else None
        state["safety_correction_needed"] = correction if status == "REJECTED" else None

        if status == "APPROVED":
            print(f"\n✅ [AGENTE C] VALIDACIÓN APROBADA")
            print(f"{'━'*80}\n")
        else:
            print(f"\n❌ [AGENTE C] VALIDACIÓN RECHAZADA")
            print(f"   Problemas detectados:")
            for issue in issues:
                print(f"   ❌ {issue}")
            print(f"\n   💡 Corrección sugerida: {correction}")
            print(f"{'━'*80}\n")

    except Exception as e:
        logger.error(f"Error en safety validation: {e}")
        # En caso de error, aprobar por defecto (fail-open)
        state["safety_validation_status"] = "APPROVED"
        state["safety_issues_detected"] = []

    return state


def _extract_known_data(state: Dict[str, Any]) -> Dict[str, Any]:
    """Extrae datos ya conocidos del state para validación"""
    return {
        "patient_name": state.get("patient_full_name"),
        "document_number": state.get("patient_document_number"),
        "service_type": state.get("service_type"),
        "appointment_date": state.get("appointment_date"),
        "appointment_time": state.get("appointment_time"),
        "pickup_address": state.get("pickup_address"),
        "contact_name": state.get("contact_name"),
        "contact_relationship": state.get("contact_relationship"),
        "contact_age": state.get("contact_age"),
    }


def _extract_excel_data(state: Dict[str, Any]) -> Dict[str, Any]:
    """Extrae datos del Excel (si es outbound call)"""
    # Esta función debería acceder a los datos cargados desde Excel
    # Por ahora retornar los mismos datos conocidos
    return _extract_known_data(state)
```

**Archivo de prompts a crear:** `src/agent/prompts/safety_validator_prompt.py`

```python
from typing import Dict, Any

def build_safety_validation_prompt(
    agent_response: str,
    current_phase: str,
    next_phase: str,
    known_data: Dict[str, Any],
    excel_data: Dict[str, Any]
) -> str:
    """Construye prompt para validación de seguridad"""

    prompt = f"""Eres el Validador de Seguridad y Accesibilidad (The Guardrail).

Tu tarea es revisar la respuesta del agente ANTES de que llegue al usuario final.

**CONTEXTO:**
- Fase actual: {current_phase}
- Próxima fase: {next_phase}

**Datos conocidos del paciente/servicio (del state):**
"""

    for key, value in known_data.items():
        if value:
            prompt += f"- {key}: {value}\n"

    prompt += f"\n**Datos del Excel (para outbound calls):**\n"
    for key, value in excel_data.items():
        if value and value != known_data.get(key):
            prompt += f"- {key}: {value}\n"

    prompt += f"""

**VALIDACIONES OBLIGATORIAS:**

1. **Fallo Lógico:**
   - ¿El agente está citando una fecha/hora que NO está en los datos conocidos o Excel?
   - ¿Menciona un servicio o dirección incorrecta?
   - ¿Hay contradicciones con la información previa?

2. **Seguridad:**
   - ¿Está revelando datos sensibles (documento, dirección) a alguien NO autorizado?
   - Si contact_relationship existe y contact_age < 18, ¿el agente pidió hablar con un adulto?
   - ¿Se está identificando correctamente la persona autorizada?

3. **Accesibilidad:**
   - ¿El lenguaje es demasiado complejo o técnico?
   - ¿Usa términos médicos sin explicar?
   - ¿Las instrucciones son claras y entendibles?

4. **Consistencia:**
   - Si next_phase = "END" o "OUTBOUND_CLOSING": ¿Se confirmaron todos los datos de la cita?
   - ¿El agente dio un resumen final antes de despedirse?
   - ¿Se identificó claramente con su nombre antes de cerrar?

**CRITERIOS DE RECHAZO:**

Devuelve status="REJECTED" si encuentras:
- Fechas/horas que NO coinciden con los datos conocidos
- Revelación de datos sensibles a persona no autorizada
- Lenguaje excesivamente complejo (más de 30 palabras por frase)
- Despedida sin resumen de confirmación

**OUTPUT (JSON obligatorio):**
```json
{{
  "status": "APPROVED | REJECTED",
  "issues": ["lista de problemas detectados"],
  "correction_needed": "Descripción de qué debe corregirse" (solo si REJECTED)
}}
```

**EJEMPLO DE RECHAZO:**

Respuesta del agente: "Su cita es el 15 de enero a las 10:00 AM."
Datos conocidos: appointment_date = "2024-01-20"

Output:
```json
{{
  "status": "REJECTED",
  "issues": ["fallo_logico"],
  "correction_needed": "La fecha citada (15 de enero) no coincide con los datos del Excel (20 de enero). Corregir la fecha en la respuesta."
}}
```

**IMPORTANTE:**
- Si no encuentras problemas, devuelve status="APPROVED" con issues=[]
- Si encuentras problemas, sé específico en la corrección necesaria
- Prioriza la seguridad sobre la cortesía
"""

    return prompt
```

---

## 4. MODIFICACIÓN DEL FLUJO DEL GRAFO

### Archivo: `src/agent/graph/conversation_graph.py`

**CAMBIOS:**

1. **Importar nuevos nodos:**

```python
from src.agent.graph.nodes import (
    input_processor,
    policy_engine_node,
    eligibility_checker,
    escalation_detector,
    context_emotion_analyzer,  # NUEVO
    context_builder,
    orchestrator,  # NUEVO (reemplaza llm_responder)
    safety_validator,  # NUEVO
    response_processor,
    state_updater,
    special_case_handler,
    excel_writer
)
```

2. **Agregar nodos al grafo:**

```python
# Después de escalation_detector, ANTES de context_builder
graph.add_node("context_emotion_analyzer", context_emotion_analyzer)

# Reemplazar llm_responder con orchestrator
graph.add_node("orchestrator", orchestrator)

# Después de orchestrator, ANTES de response_processor
graph.add_node("safety_validator", safety_validator)
```

3. **Modificar edges:**

```python
# Flujo normal después de no-escalación:
graph.add_conditional_edges(
    "escalation_detector",
    should_escalate,
    {
        "special_case_handler": "special_case_handler",
        "context_emotion_analyzer": "context_emotion_analyzer"  # CAMBIO: antes iba a context_builder
    }
)

# Después de emotion analyzer → context builder
graph.add_edge("context_emotion_analyzer", "context_builder")

# Después de context builder → orchestrator (antes era llm_responder)
graph.add_edge("context_builder", "orchestrator")

# Después de orchestrator → safety validator (NUEVO)
graph.add_edge("orchestrator", "safety_validator")

# Después de safety validator → conditional routing
graph.add_conditional_edges(
    "safety_validator",
    route_after_safety_validation,  # NUEVA función de routing
    {
        "orchestrator": "orchestrator",  # Si REJECTED, loop back
        "response_processor": "response_processor"  # Si APPROVED, continuar
    }
)

# El resto del flujo sigue igual
graph.add_conditional_edges(
    "response_processor",
    route_after_llm,
    {
        "excel_writer": "excel_writer",
        "special_case_handler": "special_case_handler",
        "state_updater": "state_updater"
    }
)
```

---

### Archivo: `src/agent/graph/edges/routing.py`

**AGREGAR NUEVA FUNCIÓN:**

```python
def route_after_safety_validation(state: Dict[str, Any]) -> Literal['orchestrator', 'response_processor']:
    """
    Post-Safety Validation: Si REJECTED, volver a orchestrator. Si APPROVED, continuar.
    """
    validation_status = state.get('safety_validation_status', 'APPROVED')

    if validation_status == 'REJECTED':
        # Volver al orchestrator para regenerar respuesta
        return 'orchestrator'

    # Continuar con response_processor
    # Resetear contador de validación
    state['validation_attempt_count'] = 0
    return 'response_processor'
```

---

## 5. MODIFICACIÓN DE NODOS EXISTENTES

### 5.1. Context Builder

**Archivo:** `src/agent/graph/nodes/context_builder.py`

**CAMBIOS MENORES:**
- Ya no necesita hacer análisis emocional (lo hace el nuevo nodo)
- Solo construir el prompt base con políticas y casos
- El orchestrator enriquecerá el prompt con adaptaciones emocionales

**NO REQUIERE CAMBIOS SIGNIFICATIVOS** - El nodo actual ya funciona bien.

---

### 5.2. Response Processor

**Archivo:** `src/agent/graph/nodes/response_processor.py`

**AGREGAR:**

```python
# Al inicio de la función, después de obtener extracted
print(f"\n{'━'*80}")
print(f"📊 [NODO 3/3] RESPONSE PROCESSOR - Procesando y Extrayendo Datos")
print(f"{'━'*80}")

# Al final, antes del return
# Resetear validación si la fase cambió exitosamente
if state.get("current_phase") != prev_phase:
    state["validation_attempt_count"] = 0
    state["safety_validation_status"] = None
    state["safety_correction_needed"] = None

print(f"✅ [NODO 3/3] Datos procesados y fase actualizada")
print(f"   🔄 {prev_phase} → {state['current_phase']}")
print(f"{'━'*80}\n")
```

---

## 6. MODIFICACIÓN DE ARCHIVOS DE EXPORTACIÓN

### Archivo: `src/agent/graph/nodes/__init__.py`

**AGREGAR NUEVOS NODOS:**

```python
from src.agent.graph.nodes.context_emotion_analyzer import context_emotion_analyzer
from src.agent.graph.nodes.orchestrator import orchestrator
from src.agent.graph.nodes.safety_validator import safety_validator

__all__ = [
    # ... existentes ...
    "context_emotion_analyzer",
    "orchestrator",
    "safety_validator",
]
```

---

## 7. LÓGICA DE NEGOCIO ESPECÍFICA POR FASE

### Implementación en `orchestrator_prompt.py`

**AGREGAR SECCIÓN ESPECÍFICA POR FASE:**

```python
def build_orchestrator_prompt(...):
    # ... código existente ...

    # Agregar lógica específica por fase
    enriched_prompt += f"\n\n{'='*80}\n"
    enriched_prompt += f"## LÓGICA DE NEGOCIO PARA FASE: {current_phase}\n"
    enriched_prompt += f"{'='*80}\n\n"

    if current_phase == "OUTBOUND_GREETING":
        enriched_prompt += """
**FASE 1: Identificación e Identidad (Prioridad Máxima)**

1. Comparar nombre de quien habla con "Persona Autorizada" en Excel:
   - Si contact_age < 18 (menor de edad):
     → "Por favor, ¿me comunicas con un adulto responsable?"
     → NO continuar hasta hablar con adulto

   - Si contact_name != patient_name y no es persona autorizada:
     → "Por seguridad, debo hablar con [Nombre del Paciente]. ¿Se encuentra?"
     → Si NO está: Agendar nota "Llamar luego" y cerrar (next_phase = "OUTBOUND_CLOSING")

   - Si es persona autorizada:
     → Continuar a next_phase = "OUTBOUND_LEGAL_NOTICE"

2. Extraer datos:
   - contact_name (nombre de quien habla)
   - contact_relationship (parentesco)
   - contact_age (edad) - CRÍTICO para detectar menores
"""

    elif current_phase == "OUTBOUND_LEGAL_NOTICE":
        enriched_prompt += """
**FASE 2: Presentación Institucional**

Script dinámico OBLIGATORIO:
"Habla {agent_name} de {company_name}. Le informo que por su seguridad esta llamada es grabada."

- Solo tras confirmar identidad
- Continuar a next_phase = "OUTBOUND_SERVICE_CONFIRMATION"
"""

    elif current_phase == "OUTBOUND_SERVICE_CONFIRMATION":
        enriched_prompt += """
**FASE 3: Motivo y Gestión de Cita**

1. Extraer fecha, hora, lugar del Excel (ya en el contexto)
2. Confirmar datos:
   "Le confirmo su cita de {service_type} el {appointment_date} a las {appointment_time}.
   Pasaremos a recogerle en {pickup_address}."

3. Detección de Cambios:
   - Si usuario dice "ya no puedo ir", "necesito cambiar", "tengo que cancelar":
     → Clasificar como "Cambio/Cancelación"
     → Extraer: special_observation con el motivo
     → next_phase = "OUTBOUND_SPECIAL_CASES"

   - Si confirma sin problemas:
     → next_phase = "OUTBOUND_CLOSING"
"""

    elif current_phase == "INCIDENT_MANAGEMENT" or "queja" in last_user_message.lower():
        enriched_prompt += """
**FASE 4: Manejo de Quejas (Empatía Activa)**

Si el Agente Secundario detectó Ira o Ansiedad:

1. PAUSAR el flujo de datos
2. Usar frase de validación emocional:
   "Entiendo su frustración, Sr./Sra. {nombre}, permítame ver cómo podemos solucionar esto..."

3. Escuchar el problema sin interrumpir
4. Registrar queja:
   - extracted["incident_summary"] = "resumen de la queja"

5. Ofrecer solución o escalación si no está en tu alcance
"""

    elif current_phase == "OUTBOUND_CLOSING" or next_phase == "END":
        enriched_prompt += """
**FASE 5: Despedida y Cierre (Garantía de Conformidad)**

🚨 REGLA CRÍTICA: NO cerrar sin Resumen Final

Script OBLIGATORIO:
"Para confirmar: su cita de {service_type} es el {appointment_date} a las {appointment_time}.
Pasaremos a recogerle en {pickup_address}. ¿La información es clara?
Habló con {agent_name} de {company_name}. ¡Que tenga buen día!"

- Verificar que TODOS los datos estén confirmados
- Identificarte con tu nombre
- Despedida cordial
- next_phase = "END"
"""

    return enriched_prompt
```

---

## 8. MEMORIA EMOCIONAL Y THREAD_ID

### 8.1. Persistencia de Emotional Memory

**Archivo:** `src/agent/langgraph_orchestrator.py` (o donde se maneje la persistencia)

**MODIFICAR:** Asegurar que `emotional_memory` se guarde en Redis junto con el resto del state.

```python
# Cuando se guarde el state en Redis:
state_to_save = {
    # ... campos existentes ...
    "emotional_memory": state.get("emotional_memory", []),
    "current_sentiment": state.get("current_sentiment"),
    "current_conflict_level": state.get("current_conflict_level"),
    "personality_mode": state.get("personality_mode", "Balanceado"),
    # ... etc
}
```

### 8.2. Thread_id para Sesiones Interrumpidas

**IDEA:** LangGraph ya soporta `thread_id` para persistencia de conversaciones. Si la llamada se corta y se retoma:

1. Usar el mismo `session_id` como `thread_id`
2. LangGraph cargará automáticamente el estado completo (incluido emotional_memory)
3. El agente sabrá exactamente en qué fase se quedó

**IMPLEMENTACIÓN:**

En `langgraph_orchestrator.py`:

```python
# Al invocar el grafo
config = {
    "configurable": {
        "thread_id": session_id  # Usar session_id como thread_id
    }
}

result = graph.invoke(input_state, config=config)
```

Esto permitirá:
- Si la llamada se corta en OUTBOUND_SERVICE_CONFIRMATION
- El usuario vuelve a llamar con el mismo `session_id`
- El grafo retoma desde OUTBOUND_SERVICE_CONFIRMATION
- Mantiene el historial emocional completo

---

## 9. VALIDACIÓN EN CASCADA

### Flujo de Validación con Límite de Intentos

```
Orchestrator (genera respuesta)
    ↓
Safety Validator (valida)
    ↓
¿APPROVED?
    ├─ SÍ → Response Processor → Continuar
    └─ NO → ¿Intentos < 3?
            ├─ SÍ → Orchestrator (regenerar con correction)
            └─ NO → Auto-aprobar y continuar (evitar loop infinito)
```

**YA IMPLEMENTADO EN:** `safety_validator.py` (ver sección 3.3)

---

## 10. TESTING Y VALIDACIÓN

### Tests a Crear/Modificar

1. **Tests unitarios para nuevos nodos:**
   - `tests/unit/agent/graph/nodes/test_context_emotion_analyzer.py`
   - `tests/unit/agent/graph/nodes/test_orchestrator.py`
   - `tests/unit/agent/graph/nodes/test_safety_validator.py`

2. **Tests de integración:**
   - `tests/integration/test_multi_agent_flow.py`: Validar flujo completo con 3 agentes
   - `tests/integration/test_emotional_memory_persistence.py`: Validar persistencia de memoria emocional
   - `tests/integration/test_validation_cascade.py`: Validar loop de rechazo/aprobación

3. **Tests E2E:**
   - Escenario 1: Usuario frustrado → Validación emocional activada
   - Escenario 2: Menor de edad contesta → Protocolo de persona autorizada
   - Escenario 3: Guardrail rechaza respuesta → Re-generación exitosa
   - Escenario 4: Usuario confundido → Modo simplificado activado

---

## 11. PLAN DE IMPLEMENTACIÓN (Fases)

### Fase 1: Infraestructura Base (2-3 días)
1. Modificar `ConversationState` con nuevos campos
2. Crear prompts base para los 3 agentes
3. Actualizar persistencia en Redis

### Fase 2: Agentes Individuales (3-4 días)
1. Implementar Context & Emotion Manager
2. Implementar The Orchestrator (refactorizar llm_responder)
3. Implementar The Guardrail
4. Tests unitarios de cada agente

### Fase 3: Integración del Grafo (2-3 días)
1. Modificar `conversation_graph.py` con nuevo flujo
2. Agregar routing para validación en cascada
3. Tests de integración del flujo completo

### Fase 4: Lógica de Negocio (2-3 días)
1. Implementar lógica específica por fase
2. Protocolo de menores de edad
3. Validación de persona autorizada
4. Resumen final obligatorio

### Fase 5: Testing y Ajustes (3-4 días)
1. Tests E2E con escenarios complejos
2. Ajuste de prompts según resultados
3. Validación de memoria emocional
4. Pruebas con llamadas reales simuladas

**TIEMPO ESTIMADO TOTAL:** 12-17 días de desarrollo

---

## 12. ARCHIVOS RESUMEN

### Archivos a CREAR:
1. `src/agent/graph/nodes/context_emotion_analyzer.py`
2. `src/agent/graph/nodes/orchestrator.py`
3. `src/agent/graph/nodes/safety_validator.py`
4. `src/agent/prompts/emotion_analyzer_prompt.py`
5. `src/agent/prompts/orchestrator_prompt.py`
6. `src/agent/prompts/safety_validator_prompt.py`
7. `tests/unit/agent/graph/nodes/test_context_emotion_analyzer.py`
8. `tests/unit/agent/graph/nodes/test_orchestrator.py`
9. `tests/unit/agent/graph/nodes/test_safety_validator.py`
10. `tests/integration/test_multi_agent_flow.py`
11. `tests/integration/test_emotional_memory_persistence.py`
12. `tests/integration/test_validation_cascade.py`

### Archivos a MODIFICAR:
1. `src/agent/graph/state.py` - Agregar campos emocionales y de validación
2. `src/agent/graph/conversation_graph.py` - Modificar flujo del grafo
3. `src/agent/graph/edges/routing.py` - Agregar routing de validación
4. `src/agent/graph/nodes/__init__.py` - Exportar nuevos nodos
5. `src/agent/graph/nodes/response_processor.py` - Resetear validación
6. `src/agent/langgraph_orchestrator.py` - Persistencia de emotional_memory
7. `src/infrastructure/persistence/redis/session_store.py` - Guardar nuevos campos (si es necesario)

---

## 13. DEPENDENCIAS Y CONSIDERACIONES

### Dependencias Nuevas:
- **Ninguna nueva**: Usamos las mismas bibliotecas (LangChain, OpenAI, LangGraph)

### Consideraciones de Costos:
- **3 llamadas LLM por turno** (emotion_analyzer + orchestrator + safety_validator)
- Mitigación:
  - emotion_analyzer: temperatura 0.3, max_tokens 500 (rápido y barato)
  - safety_validator: temperatura 0.1, max_tokens 800 (barato)
  - orchestrator: temperatura normal, max_tokens 1500 (más costoso pero es el principal)
- **Estimación:** ~2.5x costo actual por turno

### Consideraciones de Latencia:
- **Latencia adicional:** ~1-2 segundos por turno (2 LLM calls extra)
- Mitigación:
  - Usar `gpt-4o-mini` para emotion_analyzer y safety_validator (más rápido)
  - Usar `gpt-4-turbo` solo para orchestrator

---

## 14. MÉTRICAS DE ÉXITO

### KPIs para Validar la Migración:
1. **Adaptación emocional:**
   - % de usuarios frustrados que recibieron validación emocional
   - Tiempo promedio de resolución de quejas

2. **Seguridad:**
   - % de respuestas rechazadas por el Guardrail
   - % de datos sensibles protegidos correctamente

3. **Calidad de respuestas:**
   - % de despedidas con resumen final
   - % de protocolos de menores aplicados correctamente

4. **Performance:**
   - Latencia promedio por turno
   - Costo promedio por conversación

---

## CONCLUSIÓN

Esta migración transforma el sistema de mono-agente a multi-agente con:
- **Análisis emocional inteligente** (Context & Emotion Manager)
- **Respuestas adaptadas al contexto** (The Orchestrator)
- **Validación de seguridad automática** (The Guardrail)
- **Memoria emocional persistente**
- **Validación en cascada con auto-corrección**

El resultado será un agente más empático, seguro y consistente, alineado con las mejores prácticas de atención al cliente y cumplimiento normativo.
