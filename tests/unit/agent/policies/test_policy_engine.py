import pytest
from langchain_core.messages import HumanMessage
from src.agent.policies import PolicyEngine, PolicySeverity

class TestPolicyEngine:
    def test_conductor_policy_detects_request(self):
        engine = PolicyEngine()
        state = {
            'messages': [HumanMessage(content='Quiero al conductor Juan')],
            'current_phase': 'SERVICE_COORDINATION',
            'call_direction': 'INBOUND'
        }
        result = engine.evaluate(state, 'SERVICE_COORDINATION', 'INBOUND')
        assert len(result.violations) == 1
        assert result.violations[0].policy_id == 'CONDUCTOR_001'
    
    def test_eps_policy_blocks_non_cosalud(self):
        engine = PolicyEngine()
        state = {
            'eps': 'Sura',
            'messages': [],
            'current_phase': 'IDENTIFICATION',
            'call_direction': 'INBOUND'
        }
        result = engine.evaluate(state, 'IDENTIFICATION', 'INBOUND')
        assert len(result.violations) == 1
        assert result.violations[0].policy_id == 'SERVICIO_001'
        assert result.violations[0].severity == PolicySeverity.BLOCKING
    
    def test_geographic_policy_detects_rural(self):
        engine = PolicyEngine()
        state = {
            'pickup_address': 'Vereda El Campano',
            'messages': [],
            'current_phase': 'SERVICE_COORDINATION',
            'call_direction': 'INBOUND'
        }
        result = engine.evaluate(state, 'SERVICE_COORDINATION', 'INBOUND')
        assert len(result.violations) == 1
        assert result.violations[0].policy_id == 'GEOGRAFIA_001'
    
    def test_modality_policy_detects_expreso(self):
        engine = PolicyEngine()
        state = {
            'messages': [HumanMessage(content='Necesito servicio expreso')],
            'current_phase': 'SERVICE_COORDINATION',
            'call_direction': 'INBOUND'
        }
        result = engine.evaluate(state, 'SERVICE_COORDINATION', 'INBOUND')
        assert len(result.violations) == 1
        assert result.violations[0].policy_id == 'MODALIDAD_001'
    
    def test_no_violations_clean_state(self):
        engine = PolicyEngine()
        state = {
            'eps': 'cosalud',
            'pickup_address': 'Calle 10 # 5-20, Santa Marta',
            'messages': [HumanMessage(content='Confirmo el servicio')],
            'current_phase': 'SERVICE_COORDINATION',
            'call_direction': 'INBOUND'
        }
        result = engine.evaluate(state, 'SERVICE_COORDINATION', 'INBOUND')
        assert len(result.violations) == 0
    
    def test_prompt_injection_generated(self):
        engine = PolicyEngine()
        state = {'messages': [], 'current_phase': 'GREETING', 'call_direction': 'INBOUND'}
        result = engine.evaluate(state, 'GREETING', 'INBOUND')
        assert len(result.prompt_injection) > 0
