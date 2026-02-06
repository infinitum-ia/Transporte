# Conversation graph using LangGraph StateGraph - Optimizado (1 sola llamada LLM)
from langgraph.graph import StateGraph, END
from src.agent.graph.state import ConversationState
from src.agent.graph.nodes import (
    input_processor,
    policy_engine_node,
    eligibility_checker,
    escalation_detector,
    context_builder,
    llm_responder,
    response_processor,
    state_updater,
    special_case_handler,
    excel_writer,
    # Supervisor Robusto - Optimizado
    pre_analyzer_node,  # Ahora usa simple_analyzer (basado en reglas, sin LLM)
    context_enricher_node,
    response_validator_node,
)
from src.agent.graph.edges import should_escalate, route_after_llm


def create_conversation_graph():
    """
    Create the LangGraph StateGraph for conversation management.

    ARQUITECTURA OPTIMIZADA (1 LLM call):

    Graph Flow (per turn):
    START -> input_processor
          -> pre_analyzer (análisis basado en REGLAS, ~5ms - antes era LLM ~2000ms)
          -> context_enricher (inyecta políticas/casos)
          -> policy_engine -> eligibility_checker -> escalation_detector
          -> [conditional: escalate?]
              -> YES: special_case_handler -> END
              -> NO: context_builder -> llm_responder (ÚNICA llamada LLM)
                  -> response_validator (validación por reglas)
                  -> response_processor
                  -> [conditional: route_after_llm]
                      -> END: excel_writer -> END
                      -> special: special_case_handler -> END
                      -> continue: state_updater -> END

    OPTIMIZACIÓN: Antes había 2 llamadas LLM (pre_analyzer + llm_responder).
    Ahora pre_analyzer usa regex/reglas, reduciendo latencia de ~6s a ~3s.
    """

    # Create graph
    graph = StateGraph(ConversationState)
    print("===============COMPILANDO GRAFO============")
    # Add all nodes (Supervisor Robusto - Optimizado)
    graph.add_node("input_processor", input_processor)
    graph.add_node("pre_analyzer", pre_analyzer_node)  # OPTIMIZADO: Ahora usa reglas, no LLM (~5ms vs ~2000ms)
    graph.add_node("context_enricher", context_enricher_node)
    graph.add_node("policy_engine", policy_engine_node)
    graph.add_node("eligibility_checker", eligibility_checker)
    graph.add_node("escalation_detector", escalation_detector)
    graph.add_node("context_builder", context_builder)
    graph.add_node("llm_responder", llm_responder)
    graph.add_node("response_validator", response_validator_node)  # NUEVO
    graph.add_node("response_processor", response_processor)
    graph.add_node("state_updater", state_updater)
    graph.add_node("special_case_handler", special_case_handler)
    graph.add_node("excel_writer", excel_writer)

    # Define edges (linear flow con Supervisor Robusto)
    graph.set_entry_point("input_processor")

    # Flujo con Supervisor: pre_analyzer y context_enricher después de input
    graph.add_edge("input_processor", "pre_analyzer")  # NUEVO
    graph.add_edge("pre_analyzer", "context_enricher")  # NUEVO
    graph.add_edge("context_enricher", "policy_engine")  # MODIFICADO
    graph.add_edge("policy_engine", "eligibility_checker")
    graph.add_edge("eligibility_checker", "escalation_detector")

    # Conditional: Check if escalation required
    graph.add_conditional_edges(
        "escalation_detector",
        should_escalate,
        {
            "special_case_handler": "special_case_handler",
            "context_builder": "context_builder"
        }
    )

    # Normal flow continues through LLM
    graph.add_edge("context_builder", "llm_responder")
    graph.add_edge("llm_responder", "response_validator")  # NUEVO: Validar antes de procesar
    graph.add_edge("response_validator", "response_processor")  # MODIFICADO

    # Conditional: Route after LLM
    graph.add_conditional_edges(
        "response_processor",
        route_after_llm,
        {
            "excel_writer": "excel_writer",
            "special_case_handler": "special_case_handler",
            "state_updater": "state_updater"
        }
    )

    # Final: All paths go to END (no loops!)
    graph.add_edge("special_case_handler", END)
    graph.add_edge("excel_writer", END)
    graph.add_edge("state_updater", END)

    # Compile graph
    return graph.compile()
