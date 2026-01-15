# Checklist de Implementación: Multi-Agente

## FASE 1: Infraestructura Base (2-3 días)

### State Schema
- [ ] Modificar `src/agent/graph/state.py`
  - [ ] Agregar campos emocionales (emotional_memory, current_sentiment, etc.)
  - [ ] Agregar campos de validación (safety_validation_status, etc.)
  - [ ] Documentar cada campo con docstrings

### Prompts Base
- [ ] Crear `src/agent/prompts/emotion_analyzer_prompt.py`
  - [ ] Función `build_emotion_analysis_prompt()`
  - [ ] Documentar formato de output JSON

- [ ] Crear `src/agent/prompts/orchestrator_prompt.py`
  - [ ] Función `build_orchestrator_prompt()`
  - [ ] Secciones de adaptación emocional
  - [ ] Lógica específica por fase

- [ ] Crear `src/agent/prompts/safety_validator_prompt.py`
  - [ ] Función `build_safety_validation_prompt()`
  - [ ] 4 validaciones críticas documentadas

### Persistencia
- [ ] Modificar `src/agent/langgraph_orchestrator.py`
  - [ ] Asegurar que emotional_memory se guarde en Redis
  - [ ] Asegurar que nuevos campos se persistan correctamente
  - [ ] Configurar thread_id para continuidad de sesiones

### Testing Inicial
- [ ] Crear tests para validar schema
- [ ] Verificar que Redis guarda nuevos campos
- [ ] Probar carga/descarga de emotional_memory

---

## FASE 2: Agentes Individuales (3-4 días)

### Agente A: Context & Emotion Manager
- [ ] Crear `src/agent/graph/nodes/context_emotion_analyzer.py`
  - [ ] Función `context_emotion_analyzer(state)`
  - [ ] Llamada a LLM con prompt de análisis
  - [ ] Parseo de JSON response
  - [ ] Actualización de state con análisis
  - [ ] Agregar a emotional_memory
  - [ ] Logging y prints informativos

- [ ] Crear `tests/unit/agent/graph/nodes/test_context_emotion_analyzer.py`
  - [ ] Test: Usuario frustrado → sentiment="Frustración"
  - [ ] Test: Usuario neutro → valores default
  - [ ] Test: Error en LLM → valores seguros
  - [ ] Test: Memoria emocional se actualiza correctamente

### Agente B: The Orchestrator
- [ ] Crear `src/agent/graph/nodes/orchestrator.py`
  - [ ] Función `orchestrator(state)`
  - [ ] Enriquecer prompt base con contexto emocional
  - [ ] Llamada a LLM con prompt enriquecido
  - [ ] Parseo de JSON response
  - [ ] Actualización de state (agent_response, next_phase, extracted)
  - [ ] Manejo de safety_correction (si Guardrail rechazó)
  - [ ] Logging y prints informativos

- [ ] Crear `tests/unit/agent/graph/nodes/test_orchestrator.py`
  - [ ] Test: Genera respuesta con validación emocional
  - [ ] Test: Adapta tono según personality_mode
  - [ ] Test: Regenera con corrección del Guardrail
  - [ ] Test: Error en LLM → respuesta fallback

### Agente C: The Guardrail
- [ ] Crear `src/agent/graph/nodes/safety_validator.py`
  - [ ] Función `safety_validator(state)`
  - [ ] Función helper `_extract_known_data(state)`
  - [ ] Función helper `_extract_excel_data(state)`
  - [ ] Llamada a LLM con prompt de validación
  - [ ] Parseo de JSON response
  - [ ] Actualización de state (safety_validation_status, issues, correction)
  - [ ] Incrementar validation_attempt_count
  - [ ] Límite de 3 intentos → auto-aprobar
  - [ ] Logging y prints informativos

- [ ] Crear `tests/unit/agent/graph/nodes/test_safety_validator.py`
  - [ ] Test: Detecta fallo lógico (fecha incorrecta)
  - [ ] Test: Detecta revelación de datos sensibles
  - [ ] Test: Detecta lenguaje complejo
  - [ ] Test: Detecta falta de resumen en despedida
  - [ ] Test: Aprueba respuesta correcta
  - [ ] Test: Límite de 3 intentos → auto-aprueba

---

## FASE 3: Integración del Grafo (2-3 días)

### Modificar Grafo
- [ ] Modificar `src/agent/graph/conversation_graph.py`
  - [ ] Importar nuevos nodos (context_emotion_analyzer, orchestrator, safety_validator)
  - [ ] Agregar nodos al grafo con `graph.add_node()`
  - [ ] Modificar edges:
    - [ ] escalation_detector → context_emotion_analyzer (antes iba a context_builder)
    - [ ] context_emotion_analyzer → context_builder (nuevo edge)
    - [ ] context_builder → orchestrator (antes iba a llm_responder)
    - [ ] orchestrator → safety_validator (nuevo edge)
    - [ ] safety_validator → conditional routing (nuevo edge)
  - [ ] Actualizar docstrings con nuevo flujo

### Routing de Validación
- [ ] Modificar `src/agent/graph/edges/routing.py`
  - [ ] Crear función `route_after_safety_validation(state)`
  - [ ] Si REJECTED → return 'orchestrator'
  - [ ] Si APPROVED → return 'response_processor'
  - [ ] Resetear validation_attempt_count cuando APPROVED

### Exportar Nodos
- [ ] Modificar `src/agent/graph/nodes/__init__.py`
  - [ ] Importar context_emotion_analyzer
  - [ ] Importar orchestrator
  - [ ] Importar safety_validator
  - [ ] Agregar a __all__

### Deprecar llm_responder
- [ ] Marcar `src/agent/graph/nodes/llm_responder.py` como DEPRECATED
- [ ] Agregar comentario: "DEPRECATED: Reemplazado por orchestrator.py"
- [ ] NO eliminar aún (mantener para rollback si es necesario)

### Testing de Integración
- [ ] Crear `tests/integration/test_multi_agent_flow.py`
  - [ ] Test: Flujo completo con 3 agentes (sin rechazo)
  - [ ] Test: Flujo con rechazo del Guardrail → re-generación
  - [ ] Test: Flujo con escalación → skip agentes
  - [ ] Test: Verificar orden de ejecución de nodos

- [ ] Crear `tests/integration/test_emotional_memory_persistence.py`
  - [ ] Test: Memoria emocional se guarda en Redis
  - [ ] Test: Memoria emocional se carga correctamente
  - [ ] Test: Historial emocional persiste entre turnos

- [ ] Crear `tests/integration/test_validation_cascade.py`
  - [ ] Test: Guardrail rechaza 1 vez → regenera → aprueba
  - [ ] Test: Guardrail rechaza 3 veces → auto-aprueba
  - [ ] Test: Validación exitosa en primer intento

---

## FASE 4: Lógica de Negocio Específica (2-3 días)

### Protocolo de Menores
- [ ] En `orchestrator_prompt.py`, fase OUTBOUND_GREETING:
  - [ ] Detectar contact_age < 18
  - [ ] Pedir hablar con adulto
  - [ ] NO continuar hasta hablar con adulto autorizado
  - [ ] Extraer contact_name, contact_age, contact_relationship

- [ ] Test E2E: Menor contesta → pide adulto → adulto autoriza → continúa

### Protocolo de Persona Autorizada
- [ ] En `orchestrator_prompt.py`, fase OUTBOUND_GREETING:
  - [ ] Verificar contact_name vs patient_name
  - [ ] Si no es el paciente, verificar si está autorizado
  - [ ] Si no está autorizado, pedir hablar con paciente
  - [ ] Si paciente no está, agendar "Llamar luego" y cerrar

- [ ] Test E2E: Persona no autorizada → pide paciente → no está → cierra

### Validación Emocional
- [ ] En `orchestrator_prompt.py`:
  - [ ] Si emotional_validation_required = True:
    - [ ] PRIMERO validar emoción
    - [ ] LUEGO dar información
  - [ ] Frases de validación según sentimiento

- [ ] Test E2E: Usuario frustrado → recibe validación emocional → se calma

### Resumen Final Obligatorio
- [ ] En `safety_validator_prompt.py`:
  - [ ] Si next_phase = "END" o "OUTBOUND_CLOSING":
    - [ ] Validar que haya resumen completo:
      - [ ] Tipo de servicio
      - [ ] Fecha
      - [ ] Hora
      - [ ] Dirección
      - [ ] Confirmación con usuario
      - [ ] Identificación del agente
    - [ ] Si falta algo → REJECTED

- [ ] Test E2E: Despedida sin resumen → rechazada → regenera con resumen

### Adaptación de Personalidad
- [ ] En `orchestrator_prompt.py`:
  - [ ] Modo Simplificado: Frases cortas, sin tecnicismos
  - [ ] Modo Técnico: Detalles precisos, lenguaje formal
  - [ ] Modo Balanceado: Conversación estándar

- [ ] Test E2E: Usuario confundido → modo simplificado activado

---

## FASE 5: Testing y Ajustes (3-4 días)

### Tests E2E por Escenario

#### Escenario 1: Usuario Frustrado
- [ ] Crear test E2E
- [ ] Usuario expresa frustración ("¡Ya llamé 3 veces!")
- [ ] Emotion Analyzer detecta: Frustración, Alto conflicto
- [ ] Orchestrator usa validación emocional
- [ ] Guardrail aprueba
- [ ] Respuesta empática y resolutiva

#### Escenario 2: Menor de Edad
- [ ] Crear test E2E
- [ ] Menor contesta (contact_age = 15)
- [ ] Orchestrator pide hablar con adulto
- [ ] Adulto autoriza
- [ ] Conversación continúa normalmente

#### Escenario 3: Guardrail Rechaza
- [ ] Crear test E2E
- [ ] Orchestrator genera respuesta con fecha incorrecta
- [ ] Guardrail detecta fallo lógico → REJECTED
- [ ] Orchestrator regenera con corrección
- [ ] Guardrail aprueba
- [ ] Respuesta correcta enviada

#### Escenario 4: Usuario Confundido
- [ ] Crear test E2E
- [ ] Usuario pregunta "¿Cómo?" repetidamente
- [ ] Emotion Analyzer sugiere Modo Simplificado
- [ ] Orchestrator adapta lenguaje
- [ ] Respuesta simple y clara

#### Escenario 5: Despedida sin Resumen
- [ ] Crear test E2E
- [ ] Orchestrator intenta cerrar sin resumen
- [ ] Guardrail detecta falta de resumen → REJECTED
- [ ] Orchestrator regenera con resumen completo
- [ ] Guardrail aprueba
- [ ] Cierre correcto

### Ajuste de Prompts
- [ ] Revisar logs de tests E2E
- [ ] Identificar prompts que generan respuestas subóptimas
- [ ] Ajustar wording de prompts
- [ ] Re-ejecutar tests
- [ ] Iterar hasta calidad óptima

### Pruebas con Llamadas Reales Simuladas
- [ ] Cargar datos reales de Excel
- [ ] Simular 10 llamadas completas
- [ ] Validar que:
  - [ ] Análisis emocional es preciso
  - [ ] Adaptaciones son apropiadas
  - [ ] Guardrail detecta errores correctamente
  - [ ] Resúmenes finales son completos
  - [ ] No hay loops infinitos

### Métricas y Logs
- [ ] Implementar logging de métricas:
  - [ ] % de respuestas rechazadas por Guardrail
  - [ ] % de validaciones emocionales activadas
  - [ ] Promedio de intentos de validación por turno
  - [ ] Latencia promedio por agente
  - [ ] Costo estimado por conversación

- [ ] Crear dashboard simple para visualizar métricas
- [ ] Validar que métricas están dentro de rangos esperados

---

## FASE 6: Documentación y Deployment (1-2 días)

### Documentación
- [ ] Actualizar CLAUDE.md con nueva arquitectura
- [ ] Documentar los 3 agentes en README.md
- [ ] Crear diagrama visual del flujo multi-agente
- [ ] Documentar nuevos campos del state
- [ ] Actualizar guías de testing

### Configuración
- [ ] Actualizar .env.example con nuevas variables (si aplica)
- [ ] Documentar configuración de temperaturas por agente
- [ ] Documentar límites de validación (MAX_VALIDATION_ATTEMPTS)

### Rollback Plan
- [ ] Documentar proceso de rollback a mono-agente
- [ ] Mantener llm_responder.py como fallback
- [ ] Crear feature flag ENABLE_MULTI_AGENT en settings

### Deployment
- [ ] Merge a rama main
- [ ] Deploy a staging
- [ ] Pruebas de smoke test en staging
- [ ] Deploy a producción
- [ ] Monitoreo de métricas en producción (primeras 24h)

---

## Checklist de Validación Final

### Funcionalidad
- [ ] Emotion Analyzer funciona correctamente
- [ ] Orchestrator genera respuestas adaptadas
- [ ] Guardrail valida correctamente
- [ ] Loop de validación funciona sin bloqueos
- [ ] Memoria emocional persiste correctamente
- [ ] Thread_id permite continuidad de sesiones

### Calidad
- [ ] Coverage >80% en tests
- [ ] Tests E2E pasan todos los escenarios
- [ ] Prompts generan respuestas naturales
- [ ] No hay hardcoded strings en código

### Performance
- [ ] Latencia <3s por turno
- [ ] Sin loops infinitos
- [ ] Sin memory leaks en Redis

### Seguridad
- [ ] Guardrail detecta datos sensibles
- [ ] Protocolo de menores funciona
- [ ] Protocolo de persona autorizada funciona
- [ ] Resumen final siempre presente

### Documentación
- [ ] Código documentado con docstrings
- [ ] README actualizado
- [ ] CLAUDE.md actualizado
- [ ] Diagramas de flujo creados

---

## Notas de Implementación

### Prioridades
1. **CRÍTICO**: Guardrail (seguridad)
2. **ALTA**: Emotion Analyzer (calidad de servicio)
3. **MEDIA**: Orchestrator (ya funciona bien con llm_responder)

### Recomendaciones
- Implementar en rama separada `feature/multi-agent-architecture`
- Hacer commits pequeños y frecuentes
- Ejecutar tests después de cada cambio
- No eliminar llm_responder hasta validar que orchestrator funciona 100%
- Monitorear costos de OpenAI durante desarrollo

### Dependencias Externas
- Ninguna nueva (usar bibliotecas actuales)

### Riesgos Conocidos
- Costo 2.5x mayor → Mitigar con gpt-4o-mini
- Latencia +1-2s → Aceptable para llamadas
- Complejidad → Testing exhaustivo
