# Flujo de Ejecución del Sistema

## 📊 Diagrama de Flujo Completo

```
┌─────────────────────────────────────────────────────────────────┐
│ 🎯 [ENDPOINT] conversation.py                                   │
│ POST /api/v1/conversation/unified                               │
│                                                                  │
│ Recibe:                                                          │
│   - patient_phone: "3001234567"                                  │
│   - message: "Hola, buenos días"                                │
│   - is_outbound: true/false                                      │
│   - agent_name: "María"                                          │
└─────────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 🎬 [ORCHESTRATOR] langgraph_orchestrator.py                     │
│ process_unified_message()                                        │
│                                                                  │
│ 1. Busca sesión existente por teléfono                           │
│ 2. Si no existe: crea nueva sesión                              │
│ 3. Si es OUTBOUND: precarga datos de Excel                      │
│ 4. Llama a process_message() → ejecuta LangGraph                │
└─────────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 🔄 [LANGGRAPH] conversation_graph.py                             │
│ Ejecuta 3 nodos en secuencia:                                    │
│                                                                  │
│   NODO 1 → NODO 2 → NODO 3 → Retorna estado actualizado         │
└─────────────────────────────────────────────────────────────────┘
          │
          ▼
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 📝 [NODO 1/3] CONTEXT BUILDER                                  ┃
┃ src/agent/graph/nodes/context_builder.py                       ┃
┃                                                                 ┃
┃ Responsabilidad: Construir prompt dinámico con contexto        ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
          │
          ├─► 1. Obtiene fase actual y último mensaje usuario
          │
          ├─► 2. 🤖 [AGENT A] ContextBuilderAgent (LLM)
          │   └─ src/agent/context_builder.py
          │      │
          │      ├─► Llama LLM para identificar políticas relevantes
          │      │   Input: mensaje usuario + fase + estado
          │      │   Output: lista de números de políticas relevantes
          │      │
          │      ├─► Llama LLM para identificar casos similares
          │      │   Input: mensaje usuario + fase + estado
          │      │   Output: lista de números de casos relevantes
          │      │
          │      ├─► Formatea fechas/horas de Excel (día de semana, etc)
          │      │
          │      └─► Genera alertas críticas (menor de edad, fuera de cobertura, etc)
          │
          └─► 3. 🛠️ Construye prompt unificado
              └─ src/agent/prompts/prompt_builder.py
                 │
                 ├─► Agrega personalidad del agente
                 ├─► Agrega instrucciones de fase
                 ├─► Inyecta políticas relevantes identificadas por LLM
                 ├─► Inyecta casos similares identificados por LLM
                 ├─► Agrega datos conocidos (nombre, servicio, fecha, etc)
                 ├─► Agrega alertas críticas
                 └─► Agrega esquema de salida JSON

          Resultado: state["llm_system_prompt"] = prompt completo
          │
          ▼
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 🤖 [NODO 2/3] LLM RESPONDER                                     ┃
┃ src/agent/graph/nodes/llm_responder.py                          ┃
┃                                                                  ┃
┃ Responsabilidad: Generar respuesta con OpenAI GPT              ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
          │
          ├─► 1. Recupera system_prompt del estado
          │
          ├─► 2. Recupera último mensaje del usuario
          │
          ├─► 3. 🧠 [AGENT B] OpenAI GPT (gpt-4o-mini / gpt-4-turbo)
          │   │
          │   ├─► Crea mensajes para el LLM:
          │   │   [SystemMessage(system_prompt), HumanMessage(user_message)]
          │   │
          │   ├─► Llama OpenAI con configuración:
          │   │   - Model: gpt-4o-mini / gpt-4-turbo
          │   │   - Temperature: 0.3 (consistente)
          │   │   - Max tokens: 2000
          │   │   - Response format: JSON
          │   │
          │   └─► Recibe respuesta JSON:
          │       {
          │         "agent_response": "Buenos días...",
          │         "next_phase": "OUTBOUND_SERVICE_CONFIRMATION",
          │         "requires_escalation": false,
          │         "extracted": {
          │           "contact_name": "Martha",
          │           "contact_relationship": "esposa",
          │           ...
          │         }
          │       }
          │
          └─► 4. Parsea respuesta y actualiza estado
              ├─► state["agent_response"] = respuesta del agente
              ├─► state["next_phase"] = siguiente fase
              ├─► state["requires_escalation"] = necesita escalación
              └─► state["extracted_data"] = datos extraídos

          Resultado: Estado actualizado con respuesta del LLM
          │
          ▼
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 🔄 [NODO 3/3] RESPONSE PROCESSOR                                ┃
┃ src/agent/graph/nodes/response_processor.py                     ┃
┃                                                                  ┃
┃ Responsabilidad: Procesar y validar respuesta                   ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
          │
          ├─► 1. Extrae datos del LLM output
          │
          ├─► 2. Actualiza estado con datos extraídos
          │   └─► Merge de extracted_data con campos del state
          │
          ├─► 3. Transiciona fase
          │   └─► current_phase = next_phase
          │
          └─► 4. Incrementa contador de turnos

          Resultado: Estado final completo
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│ ✅ [ORCHESTRATOR] Retorna respuesta                             │
│                                                                  │
│ {                                                                │
│   "agent_response": "Buenos días...",                            │
│   "conversation_phase": "OUTBOUND_SERVICE_CONFIRMATION",         │
│   "session_id": "abc123...",                                     │
│   "requires_escalation": false,                                  │
│   "patient_name": "John Jairo Mesa",                             │
│   "service_type": "Terapia",                                     │
│   ...                                                             │
│ }                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 🔍 Detalles de los Agentes

### 🤖 AGENT A: ContextBuilderAgent (LLM-based)
**Archivo:** `src/agent/context_builder.py`

**Función:** Analiza el contexto con LLM para identificar qué políticas y casos son relevantes

**Proceso:**
1. **Identificación de Políticas (LLM)**
   - Input: Mensaje usuario + Fase + Estado
   - Prompt: "Dado este contexto, selecciona las políticas relevantes"
   - Output: `[1, 3, 5]` (números de políticas)
   - Políticas disponibles se cargan desde `politicas.md`

2. **Identificación de Casos (LLM)**
   - Input: Mensaje usuario + Fase + Estado
   - Prompt: "Dado este contexto, selecciona los casos similares"
   - Output: `[2, 7]` (números de casos)
   - Casos disponibles se cargan desde `casos.md`

3. **Formateo de Fechas**
   - Convierte "2025-01-15" → "mañana, MARTES 15 de enero"
   - Usa locale español para nombres de días/meses

4. **Generación de Alertas**
   - Detecta menor de edad
   - Detecta zona fuera de cobertura
   - Detecta falta de datos críticos

### 🧠 AGENT B: OpenAI GPT (Principal)
**Archivo:** Llamada directa a OpenAI API

**Función:** Genera la respuesta conversacional del agente

**Configuración:**
- Model: `gpt-4o-mini` (rápido y económico) o `gpt-4-turbo` (más potente)
- Temperature: `0.3` (respuestas consistentes)
- Max tokens: `2000`
- Response format: `JSON object`

**Input:**
- System Prompt: ~2000-4000 palabras con:
  - Personalidad del agente
  - Instrucciones de fase
  - Políticas relevantes (inyectadas por Agent A)
  - Casos similares (inyectados por Agent A)
  - Datos conocidos
  - Alertas
  - Esquema de salida
- User Message: Último mensaje del usuario

**Output:**
```json
{
  "agent_response": "Perfecto, Sra. Martha. Soy María de Transpormax...",
  "next_phase": "OUTBOUND_SERVICE_CONFIRMATION",
  "requires_escalation": false,
  "extracted": {
    "contact_name": "Martha",
    "contact_relationship": "esposa",
    "contact_age": null,
    ...
  }
}
```

## 📁 Archivos Clave

### Entrada
- `src/presentation/api/v1/endpoints/conversation.py` - Endpoint HTTP

### Orquestación
- `src/agent/langgraph_orchestrator.py` - Orquestador principal
- `src/agent/graph/conversation_graph.py` - Definición del grafo

### Nodos del Grafo
- `src/agent/graph/nodes/context_builder.py` - Nodo 1
- `src/agent/graph/nodes/llm_responder.py` - Nodo 2
- `src/agent/graph/nodes/response_processor.py` - Nodo 3

### Agentes Auxiliares
- `src/agent/context_builder.py` - Agent A (LLM para contexto)
- `src/agent/prompts/prompt_builder.py` - Constructor de prompts
- `src/agent/resources/resource_loader.py` - Cargador de recursos

### Recursos
- `politicas.md` - Políticas de operación
- `casos.md` - Casos de uso y situaciones

## 🎨 Logs Visuales

Cuando ejecutas el sistema, verás logs como:

```
===============================================================================
🎯 [ENDPOINT] MENSAJE RECIBIDO
===============================================================================
   📞 Teléfono: 3001234567
   💬 Mensaje: 'Hola, buenos días'
   📍 Dirección: OUTBOUND (llamamos)
   👤 Agente: María
===============================================================================

🔄 [ENDPOINT] Enviando a LangGraph Orchestrator...

▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
🎬 [ORCHESTRATOR] PROCESANDO MENSAJE
▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
🔍 [ORCHESTRATOR] Buscando sesión existente para 3001234567...
✨ [ORCHESTRATOR] Nueva sesión creada: abc12345

🚀 [ORCHESTRATOR] Ejecutando LangGraph...
   Session: abc12345
   Fase actual: OUTBOUND_GREETING

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 [NODO 1/3] CONTEXT BUILDER - Construcción Inteligente del Contexto
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   📊 Fase actual: OUTBOUND_GREETING
   💬 Mensaje usuario: 'Hola, buenos días'

🤖 [AGENT A] ContextBuilderAgent (LLM) - Analizando contexto...
   ➤ Identificando políticas relevantes con LLM...
   ➤ Identificando casos similares con LLM...

✅ [NODO 1/3] Contexto construido exitosamente
   📏 Tamaño prompt: 1523 palabras (8945 caracteres)
   📋 Políticas inyectadas: 2
   📁 Casos inyectados: 1
   ⚠️  Alertas: 0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 [NODO 2/3] LLM RESPONDER - Generando Respuesta con OpenAI
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🧠 [AGENT B] OpenAI GPT (gpt-4o-mini) - Generando respuesta...
   ➤ Prompt: 8945 caracteres (~1523 palabras)
   ➤ Temperatura: 0.3
   ➤ Max tokens: 2000

────────────────────────────────────────────────────────────────────────────────
📄 PROMPT PREVIEW (primeras 500 caracteres):
────────────────────────────────────────────────────────────────────────────────
Eres María, agente profesional de Transpormax.
Estás autorizado por EPS Cosalud para coordinar transporte médico...

────────────────────────────────────────────────────────────────────────────────
💬 MENSAJE USUARIO: 'Hola, buenos días'
────────────────────────────────────────────────────────────────────────────────

⏳ Esperando respuesta del LLM...
✅ Respuesta recibida del LLM

✅ [NODO 2/3] LLM completado exitosamente
   💬 Respuesta: 'Buenos días, ¿tengo el gusto de hablar con John Jairo Mesa?'
   🔄 Próxima fase: OUTBOUND_GREETING → OUTBOUND_GREETING
   📊 Datos extraídos: 0 campos
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ [ORCHESTRATOR] LangGraph completado

✅ [ENDPOINT] RESPUESTA LISTA
   🤖 Respuesta: 'Buenos días, ¿tengo el gusto de hablar con John Jairo Mesa?'
   📊 Fase: OUTBOUND_GREETING
===============================================================================
```

## 💡 Notas Importantes

1. **Dos LLMs trabajando juntos:**
   - **Agent A** (ContextBuilder): Analiza contexto y selecciona recursos
   - **Agent B** (OpenAI GPT): Genera la respuesta conversacional

2. **Sin keywords hardcoded:**
   - El sistema NO usa búsqueda por palabras clave
   - Todo es dinámico y basado en LLM

3. **Prompts guardados:**
   - Cada llamada guarda el prompt completo en `prompt_debug_HHMMSS.txt`
   - Útil para debugging y optimización

4. **Recursos centralizados:**
   - Políticas en `politicas.md`
   - Casos en `casos.md`
   - ResourceLoader los carga una vez al inicio
