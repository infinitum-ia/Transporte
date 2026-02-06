# Nodes module - Con Supervisor Robusto (Optimizado)
from src.agent.graph.nodes.input_processor import input_processor
from src.agent.graph.nodes.policy_engine_node import policy_engine_node
from src.agent.graph.nodes.eligibility_checker import eligibility_checker
from src.agent.graph.nodes.escalation_detector import escalation_detector
from src.agent.graph.nodes.context_builder import context_builder
from src.agent.graph.nodes.llm_responder import llm_responder
from src.agent.graph.nodes.response_processor import response_processor
from src.agent.graph.nodes.state_updater import state_updater
from src.agent.graph.nodes.special_case_handler import special_case_handler
from src.agent.graph.nodes.excel_writer import excel_writer

# Supervisor Robusto - Optimizado (sin LLM extra)
from src.agent.graph.nodes.simple_analyzer import simple_analyzer_node  # Reemplaza pre_analyzer (basado en reglas)
from src.agent.graph.nodes.context_enricher import context_enricher_node
from src.agent.graph.nodes.response_validator import response_validator_node

# Mantener pre_analyzer_node como alias para compatibilidad
pre_analyzer_node = simple_analyzer_node

__all__ = [
    'input_processor', 'policy_engine_node', 'eligibility_checker',
    'escalation_detector', 'context_builder',
    'llm_responder', 'response_processor',
    'state_updater', 'special_case_handler', 'excel_writer',
    # Supervisor Robusto (optimizado)
    'simple_analyzer_node', 'pre_analyzer_node', 'context_enricher_node', 'response_validator_node'
]
