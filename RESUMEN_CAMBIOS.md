# Resumen Ejecutivo: Cambios para Multi-Agente

## Arquitectura Actual vs Propuesta

### ACTUAL (Mono-Agente)
```
input_processor → policy_engine → eligibility_checker → escalation_detector
    → context_builder → llm_responder → response_processor → END
```

### PROPUESTA (Multi-Agente con Validación)
```
input_processor → policy_engine → eligibility_checker → escalation_detector
    → context_emotion_analyzer (NUEVO - Agente A)
    → context_builder
    → orchestrator (NUEVO - Agente B, reemplaza llm_responder)
    → safety_validator (NUEVO - Agente C)
    → [loop back si REJECTED]
    → response_processor → END
```

---

## Los 3 Agentes Especializados

### 🤖 Agente A: Context & Emotion Manager
**Archivo:** `src/agent/graph/nodes/context_emotion_analyzer.py`

**Función:** Analiza el mensaje del usuario ANTES de generar respuesta

**Output:**
- `sentiment`: Frustración | Incertidumbre | Neutro | Euforia
- `conflict_level`: Bajo | Medio | Alto
- `personality_mode`: Balanceado | Simplificado | Técnico
- `sarcasm_detected`, `ambiguity_detected`
- `emotional_validation_required`: bool

**Ejemplo:**
```
Usuario: "¡Ya llamé 3 veces y nadie me soluciona nada!"
→ sentiment: Frustración
→ conflict_level: Alto
→ emotional_validation_required: True
```

---

### 🎭 Agente B: The Orchestrator
**Archivo:** `src/agent/graph/nodes/orchestrator.py`

**Función:** Genera respuesta ADAPTADA al contexto emocional

**Input:**
- Prompt base (del context_builder)
- Análisis emocional (del Agente A)
- Datos conocidos, políticas, casos

**Adaptaciones:**
- Si `Frustración` → Validación emocional primero: "Entiendo su frustración..."
- Si `Incertidumbre` → Lenguaje simple, confirmar comprensión
- Si `Modo Simplificado` → Frases cortas, sin tecnicismos
- Si `Modo Técnico` → Datos precisos y detallados

**Ejemplo:**
```
Sin adaptación:
"Su cita es el 20/01 a las 10:00."

Con adaptación emocional:
"Entiendo su frustración, Sr. Pérez. Permítame ayudarle de inmediato.
He revisado su cita y confirmo que es el 20 de enero a las 10:00 AM."
```

---

### 🛡️ Agente C: The Guardrail
**Archivo:** `src/agent/graph/nodes/safety_validator.py`

**Función:** Valida respuesta ANTES de enviarla al usuario

**Validaciones:**
1. **Fallo Lógico:** ¿Cita fechas que NO están en Excel?
2. **Seguridad:** ¿Revela datos a persona no autorizada?
3. **Accesibilidad:** ¿Lenguaje demasiado complejo?
4. **Consistencia:** ¿Se despide sin confirmar datos?

**Output:**
- `status`: APPROVED | REJECTED
- `issues`: Lista de problemas
- `correction_needed`: Qué corregir

**Ejemplo de rechazo:**
```
Orchestrator generó:
"Su cita es el 15 de enero a las 10:00."

Excel dice: appointment_date = "2024-01-20"

Guardrail:
{
  "status": "REJECTED",
  "issues": ["fallo_logico"],
  "correction_needed": "Fecha incorrecta. Debe decir 20 de enero, no 15."
}

→ Orchestrator REGENERA con la corrección
```

---

## Cambios en el State

### Campos NUEVOS en `src/agent/graph/state.py`:

```python
# Análisis Emocional
emotional_memory: List[Dict]  # Historial de emociones por turno
current_sentiment: str  # Frustración | Incertidumbre | Neutro | Euforia
current_conflict_level: str  # Bajo | Medio | Alto
personality_mode: str  # Balanceado | Simplificado | Técnico
sarcasm_detected: bool
ambiguity_detected: bool
emotional_validation_required: bool

# Validación de Seguridad
safety_validation_status: str  # APPROVED | REJECTED
safety_rejection_reason: str
safety_correction_needed: str
validation_attempt_count: int  # Límite: 3 intentos
safety_issues_detected: List[str]
```

---

## Archivos a CREAR (6 nuevos archivos principales)

### Nodos:
1. ✅ `src/agent/graph/nodes/context_emotion_analyzer.py`
2. ✅ `src/agent/graph/nodes/orchestrator.py`
3. ✅ `src/agent/graph/nodes/safety_validator.py`

### Prompts:
4. ✅ `src/agent/prompts/emotion_analyzer_prompt.py`
5. ✅ `src/agent/prompts/orchestrator_prompt.py`
6. ✅ `src/agent/prompts/safety_validator_prompt.py`

---

## Archivos a MODIFICAR (7 archivos)

1. ✅ `src/agent/graph/state.py`
   - Agregar campos emocionales y de validación

2. ✅ `src/agent/graph/conversation_graph.py`
   - Modificar flujo: agregar 3 nodos nuevos
   - Cambiar edges para validación en cascada

3. ✅ `src/agent/graph/edges/routing.py`
   - Agregar `route_after_safety_validation()`

4. ✅ `src/agent/graph/nodes/__init__.py`
   - Exportar nuevos nodos

5. ✅ `src/agent/graph/nodes/response_processor.py`
   - Resetear validación cuando fase cambia

6. ✅ `src/agent/langgraph_orchestrator.py`
   - Persistir `emotional_memory` en Redis

7. ⚠️ `src/agent/graph/nodes/llm_responder.py`
   - DEPRECAR (reemplazado por orchestrator)

---

## Lógicas de Negocio Específicas

### Protocolo de Menores de Edad
```
Si contact_age < 18:
  → "Por favor, ¿me comunicas con un adulto responsable?"
  → NO continuar hasta hablar con adulto
  → Extraer: contact_name, contact_age, contact_relationship
```

### Protocolo de Persona Autorizada
```
Si contact_name != patient_name:
  → Verificar si es persona autorizada en Excel
  → Si NO: "Por seguridad, debo hablar con [Paciente]. ¿Se encuentra?"
  → Si NO está: Agendar "Llamar luego" y cerrar
```

### Resumen Final Obligatorio
```
Si next_phase = "END" o "OUTBOUND_CLOSING":
  → Guardrail valida que haya resumen:
    "Para confirmar: su cita de {tipo} es el {fecha} a las {hora}.
     Pasaremos a recogerle en {dirección}. ¿La información es clara?
     Habló con {agente}. ¡Buen día!"
  → Si NO hay resumen → REJECTED
```

---

## Flujo de Validación en Cascada

```
┌─────────────────┐
│  Orchestrator   │ Genera respuesta
└────────┬────────┘
         ↓
┌─────────────────┐
│ Safety Validator│ Valida
└────────┬────────┘
         ↓
    ¿APPROVED?
         ├─ SÍ → Response Processor → Continuar
         │
         └─ NO → ¿Intentos < 3?
                  ├─ SÍ → Orchestrator (regenerar con correction)
                  └─ NO → Auto-aprobar (evitar loop infinito)
```

**Límite:** Máximo 3 intentos de validación por turno

---

## Memoria Emocional Persistente

```python
emotional_memory = [
  {
    "turn": 1,
    "sentiment": "Neutro",
    "conflict_level": "Bajo",
    "timestamp": "2024-01-20T10:00:00"
  },
  {
    "turn": 2,
    "sentiment": "Frustración",
    "conflict_level": "Alto",
    "timestamp": "2024-01-20T10:01:30"
  },
  {
    "turn": 3,
    "sentiment": "Incertidumbre",  # Usuario se calmó pero aún confuso
    "conflict_level": "Medio",
    "timestamp": "2024-01-20T10:03:00"
  }
]
```

**Uso:**
- Si en turno 2 el usuario estaba enojado
- En turno 5 el agente SIGUE siendo extra-cordial
- Incluso si el usuario ya se calmó
- La memoria emocional persiste toda la conversación

---

## Costos y Performance

### Llamadas LLM por Turno:
- **ANTES:** 1 LLM call (llm_responder)
- **AHORA:** 3 LLM calls:
  1. Emotion Analyzer (rápido, barato)
  2. Orchestrator (principal)
  3. Safety Validator (rápido, barato)

### Estimación de Costos:
- **Incremento:** ~2.5x costo actual
- **Mitigación:**
  - Usar `gpt-4o-mini` para Analyzer y Validator
  - Usar `gpt-4-turbo` solo para Orchestrator

### Latencia:
- **Incremento:** ~1-2 segundos por turno
- **Aceptable:** Para llamadas telefónicas (no es chat en tiempo real)

---

## Plan de Implementación (Fases)

### Fase 1: Infraestructura (2-3 días)
- Modificar State
- Crear prompts base
- Actualizar persistencia

### Fase 2: Agentes (3-4 días)
- Implementar 3 agentes
- Tests unitarios

### Fase 3: Integración (2-3 días)
- Modificar grafo
- Routing de validación
- Tests de integración

### Fase 4: Lógica de Negocio (2-3 días)
- Protocolos específicos
- Validaciones por fase

### Fase 5: Testing (3-4 días)
- Tests E2E
- Ajuste de prompts
- Pruebas reales

**TOTAL:** 12-17 días

---

## Beneficios Clave

### ✅ Empatía Mejorada
- Detecta frustración y adapta tono
- Validación emocional automática
- Memoria de estados emocionales

### ✅ Seguridad Mejorada
- Validación automática de respuestas
- Protección de datos sensibles
- Verificación de persona autorizada

### ✅ Calidad Mejorada
- Resumen final obligatorio
- Consistencia con datos de Excel
- Lenguaje adaptado al usuario

### ✅ Cumplimiento Normativo
- Protocolo de menores
- Grabación de llamadas (aviso legal)
- Identificación clara del agente

---

## Riesgos y Mitigaciones

| Riesgo | Mitigación |
|--------|-----------|
| Costo 2.5x mayor | Usar gpt-4o-mini para Analyzer/Validator |
| Latencia +1-2s | Aceptable para llamadas (no es chat) |
| Loop infinito en validación | Límite de 3 intentos + auto-aprobar |
| Complejidad mayor | Testing exhaustivo + documentación |
| LLM falla en análisis emocional | Defaults seguros (Neutro, Balanceado) |

---

## Próximos Pasos Inmediatos

1. ✅ Revisar y aprobar este plan
2. ⏳ Crear rama `feature/multi-agent-architecture`
3. ⏳ Implementar Fase 1 (State + prompts base)
4. ⏳ Testing unitario de cada agente
5. ⏳ Integración del grafo completo
6. ⏳ Pruebas E2E con escenarios reales
