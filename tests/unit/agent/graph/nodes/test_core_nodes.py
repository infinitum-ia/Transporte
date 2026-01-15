import pytest
from langchain_core.messages import HumanMessage
from src.agent.graph.nodes import input_processor, policy_engine_node, eligibility_checker, escalation_detector

class TestCoreNodes:
    def test_input_processor_updates_turn_count(self):
        state = {'messages': [HumanMessage(content='Test')], 'turn_count': 0}
        result = input_processor(state)
        assert result['turn_count'] == 1
    
    def test_policy_engine_node_evaluates_policies(self):
        state = {
            'messages': [HumanMessage(content='Quiero al conductor Juan')],
            'current_phase': 'SERVICE_COORDINATION',
            'call_direction': 'INBOUND'
        }
        result = policy_engine_node(state)
        assert 'policy_violations' in result
        assert len(result['policy_violations']) > 0
    
    def test_eligibility_checker_detects_wrong_eps(self):
        state = {'eps': 'Sura'}
        result = eligibility_checker(state)
        assert result['eligibility_checked'] == True
        assert len(result['eligibility_issues']) > 0
    
    def test_escalation_detector_flags_blocking_violation(self):
        state = {
            'policy_violations': [
                {'severity': 'BLOCKING', 'policy_name': 'Test Policy'}
            ],
            'eligibility_issues': [],
            'messages': []
        }
        result = escalation_detector(state)
        assert result['escalation_required'] == True
        assert len(result['escalation_reasons']) > 0
    
    def test_escalation_detector_detects_keywords(self):
        state = {
            'policy_violations': [],
            'eligibility_issues': [],
            'messages': [HumanMessage(content='Necesito servicio expreso')]
        }
        result = escalation_detector(state)
        assert result['escalation_required'] == True
