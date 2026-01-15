• El único endpoint consolidado, POST /api/v1/conversation/unified en src/presentation/api/v1/endpoints/conversation.py:100, toma el número de teléfono y el mensaje del cliente, recupera
  el call_orchestrator cargado durante el inicio (src/presentation/api/main.py:51) y luego lo usa para ejecutar process_unified_message tras haber inicializado los agentes por medio de
  create_agent y create_orchestrator (src/agent/agent_factory.py:14/23) cuando AGENT_MODE=llm.

  - LangGraphOrchestrator (src/agent/langgraph_orchestrator.py:16) elige el grafo tradicional o el ReAct (:40/:43), mantiene ConversationState, añade cada HumanMessage, invoca el grafo en
    process_message (:51) y expone process_unified_message (:247) para que el endpoint cree o rehidrate sesiones con find_session_by_phone (:197), create_session (:152) y un
    RedisSessionStore, serializando el resultado con state_to_dict (src/agent/graph/state_adapters.py:55).
  - El grafo principal (src/agent/graph/conversation_graph.py:18) enlaza input_processor (src/agent/graph/nodes/input_processor.py:6), policy_engine_node (:5), eligibility_checker (:4),
    escalation_detector (:9), context_builder (:10), llm_responder (src/agent/graph/nodes/llm_responder.py:25), response_processor (src/agent/graph/nodes/response_processor.py:10),
    state_updater (src/agent/graph/nodes/state_updater.py:5), special_case_handler (src/agent/graph/nodes/special_case_handler.py:4) y excel_writer (src/agent/graph/nodes/
    excel_writer.py:4), con los condicionales should_escalate y route_after_llm (src/agent/graph/edges/routing.py:4/:10), mientras que la variante ReAct (src/agent/graph/
    conversation_graph_react.py:35) inserta el detector react_context_analyzer (src/agent/graph/nodes/react_context_analyzer.py:17) antes del constructor de prompts para agregar guías
    inteligentes.
  - context_builder (src/agent/graph/nodes/context_builder.py:10) recoge identidad, servicio, políticas y alertas y llama a build_compact_prompt (src/agent/prompts/
    langgraph_prompts.py:1259), donde se inyectan personalidad, instrucciones por fase, datos conocidos, políticas y cualquier react_guidance detectado; llm_responder arma el
    SystemMessage/HumanMessage, llama a OpenAI y parsea el JSON de respuesta para actualizar el estado.
  - Cuando USE_REACT_AGENT está activado, react_context_analyzer usa ContextAnalyzer (src/agent/react/context_analyzer.py:18) y la fábrica get_context_analyzer (:744) para detectar
    situaciones y devolver react_guidance, y luego ReActAgent (src/agent/react/agent.py:23) ejecuta el bucle Think-Act-Observe con build_react_prompt (src/agent/react/prompts.py:154) antes
    de regresar al grafo principal.
  - El esquema completo de estado ConversationState (src/agent/graph/state.py:13) y su inicialización create_initial_state (src/agent/graph/state_adapters.py:95) aseguran que cada turno
    conserve fases, mensajes, escalaciones, incidentes y metadatos que ya se ejercitan en tests/integration/agent/test_langgraph_e2e.py:2-100 y tests/unit/agent/test_agent_factory.py:8-16.

  Siguientes pasos: 1) inspecciona tests/integration/agent/test_langgraph_e2e.py:2-100 y tests/unit/agent/test_agent_factory.py:8-16 para ver cómo se recorre este flujo completo y cuándo
  se activa el ReAct, y 2) ejecuta make test-integration (o el objetivo adecuado) antes de validar cambios para asegurarte de que el grafo, el prompt y la persistencia siguen comportándose
  como esperas.
