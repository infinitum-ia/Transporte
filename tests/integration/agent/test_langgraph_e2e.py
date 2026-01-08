import pytest
from src.agent.langgraph_orchestrator import LangGraphOrchestrator

class TestLangGraphE2E:
    """End-to-end tests for LangGraph orchestrator"""
    
    @pytest.mark.asyncio
    async def test_inbound_flow_complete(self):
        """Test complete inbound call flow"""
        orchestrator = LangGraphOrchestrator()

        # Create session
        session_id = orchestrator.create_session(call_direction="INBOUND", agent_name="Maria")

        # First message - greeting
        result1 = await orchestrator.process_message(session_id, "Hola")
        assert result1['agent_response'] is not None
        assert len(result1['agent_response']) > 0

        # Second message - identification
        result2 = await orchestrator.process_message(session_id, "Mi nombre es Juan Perez")
        assert result2['agent_response'] is not None

        # Verify session persists
        session = orchestrator.get_session(session_id)
        assert session is not None
        assert len(session['messages']) >= 4  # 2 user + 2 agent
    
    @pytest.mark.asyncio
    async def test_outbound_flow_complete(self):
        """Test complete outbound call flow"""
        orchestrator = LangGraphOrchestrator()
        
        # Create outbound session
        session_id = orchestrator.create_session(
            call_direction="OUTBOUND",
            agent_name="Carlos",
            excel_row_index=5
        )
        
        # First message
        result = await orchestrator.process_message(session_id, "START")
        assert result['agent_response'] is not None
        assert result['current_phase'] in ['OUTBOUND_GREETING', 'OUTBOUND_SERVICE_CONFIRMATION']
    
    @pytest.mark.asyncio
    async def test_escalation_auto_triggers(self):
        """Test automatic escalation for policy violations"""
        orchestrator = LangGraphOrchestrator()

        session_id = orchestrator.create_session(call_direction="INBOUND")

        # Simulate EPS being set to wrong value
        orchestrator._sessions[session_id]['eps'] = 'Sura'

        # Process message - should trigger escalation
        result = await orchestrator.process_message(session_id, "Confirmo")

        # Check session for escalation (escalation may be detected in state)
        session = orchestrator.get_session(session_id)
        assert len(session.get('eligibility_issues', [])) > 0
    
    @pytest.mark.asyncio
    async def test_policy_violations_detected(self):
        """Test policy violation detection"""
        orchestrator = LangGraphOrchestrator()
        
        session_id = orchestrator.create_session(call_direction="INBOUND")
        
        # Message that violates policy (wants specific driver)
        result = await orchestrator.process_message(
            session_id,
            "Quiero al conductor Juan"
        )
        
        # Should detect policy violation
        assert len(result['policy_violations']) > 0
        assert any(v['policy_id'] == 'CONDUCTOR_001' for v in result['policy_violations'])
    
    @pytest.mark.asyncio
    async def test_geographic_policy_blocks(self):
        """Test geographic coverage policy blocking"""
        orchestrator = LangGraphOrchestrator()
        
        session_id = orchestrator.create_session(call_direction="INBOUND")
        
        # Simulate state with rural address
        orchestrator._sessions[session_id]['pickup_address'] = 'Vereda El Campano'
        
        # Process message
        result = await orchestrator.process_message(session_id, "Confirmo")
        
        # Should escalate due to geography
        session = orchestrator.get_session(session_id)
        assert len(session.get('eligibility_issues', [])) > 0 or session.get('escalation_required', False)
    
    @pytest.mark.asyncio
    async def test_conversation_state_persists(self):
        """Test that conversation state persists across messages"""
        orchestrator = LangGraphOrchestrator()
        
        session_id = orchestrator.create_session()
        
        # Multiple messages
        await orchestrator.process_message(session_id, "Hola")
        await orchestrator.process_message(session_id, "Juan Perez")
        await orchestrator.process_message(session_id, "Confirmo")
        
        # Check state
        session = orchestrator.get_session(session_id)
        assert session['turn_count'] >= 3
        assert len(session['messages']) >= 6  # 3 user + 3 agent
