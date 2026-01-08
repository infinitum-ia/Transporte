# Conversation graph using LangGraph StateGraph
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
    excel_writer
)
from src.agent.graph.edges import should_escalate, route_after_llm, should_continue

def create_conversation_graph():
    """
    Create the LangGraph StateGraph for conversation management.
    
    Graph Flow:
    START -> input_processor -> policy_engine -> eligibility_checker -> escalation_detector
        -> [conditional: escalate?]
            -> YES: special_case_handler -> END
            -> NO: context_builder -> llm_responder -> response_processor 
                -> [conditional: route_after_llm]
                    -> END: excel_writer -> END
                    -> special: special_case_handler -> END
                    -> continue: state_updater -> [conditional: should_continue]
                        -> END: END
                        -> continue: input_processor (loop)
    """
    
    # Create graph
    graph = StateGraph(ConversationState)
    
    # Add all nodes
    graph.add_node("input_processor", input_processor)
    graph.add_node("policy_engine", policy_engine_node)
    graph.add_node("eligibility_checker", eligibility_checker)
    graph.add_node("escalation_detector", escalation_detector)
    graph.add_node("context_builder", context_builder)
    graph.add_node("llm_responder", llm_responder)
    graph.add_node("response_processor", response_processor)
    graph.add_node("state_updater", state_updater)
    graph.add_node("special_case_handler", special_case_handler)
    graph.add_node("excel_writer", excel_writer)
    
    # Define edges (linear flow with conditionals)
    graph.set_entry_point("input_processor")
    
    graph.add_edge("input_processor", "policy_engine")
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
    graph.add_edge("llm_responder", "response_processor")
    
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
    
    # Conditional: Check if should continue conversation
    graph.add_conditional_edges(
        "state_updater",
        should_continue,
        {
            "END": END,
            "input_processor": "input_processor"
        }
    )
    
    # End paths
    graph.add_edge("special_case_handler", END)
    graph.add_edge("excel_writer", END)
    
    return graph.compile()
