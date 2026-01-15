import pytest
from src.infrastructure.config.settings import Settings

class TestAgentFactory:
    """Tests for agent factory orchestrator creation"""

    def test_create_orchestrator_langgraph_when_enabled(self):
        """Test that LangGraphOrchestrator is created when enabled"""
        # Import here to avoid import issues
        from src.agent.agent_factory import create_orchestrator

        settings = Settings(USE_LANGGRAPH=True)
        orchestrator = create_orchestrator(settings)

        # Should be LangGraphOrchestrator
        assert orchestrator.__class__.__name__ == 'LangGraphOrchestrator'
        assert hasattr(orchestrator, 'process_message')
        assert hasattr(orchestrator, 'create_session')
        assert hasattr(orchestrator, 'get_session')

    def test_settings_has_langgraph_flag(self):
        """Test that settings has USE_LANGGRAPH flag"""
        settings = Settings(USE_LANGGRAPH=True)
        assert hasattr(settings, 'USE_LANGGRAPH')
        assert settings.USE_LANGGRAPH == True

        settings2 = Settings(USE_LANGGRAPH=False)
        assert settings2.USE_LANGGRAPH == False
