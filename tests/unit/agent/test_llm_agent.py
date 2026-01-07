import json
import pytest

from src.agent.llm_agent import LLMConversationalAgent
from src.domain.value_objects.conversation_phase import ConversationPhase
from src.infrastructure.config.settings import Settings


class DummyStore:
    def __init__(self):
        self.data = {}

    async def get(self, session_id: str):
        return self.data.get(session_id)

    async def set(self, session_id: str, state):
        self.data[session_id] = state

    async def delete(self, session_id: str):
        self.data.pop(session_id, None)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_llm_agent_process_message_parses_json(mock_llm):
    settings = Settings()
    store = DummyStore()
    agent = LLMConversationalAgent(settings=settings, store=store, llm=mock_llm)

    session_id = agent.create_session()
    await agent.init_session(session_id, agent_name="María")

    mock_llm.ainvoke.return_value.content = json.dumps(
        {
            "agent_response": "Hola, ¿habla el paciente o un familiar responsable?",
            "next_phase": "IDENTIFICATION",
            "requires_escalation": False,
            "escalation_reason": None,
            "extracted": {"patient_full_name": None},
        }
    )

    result = await agent.process_message(session_id, "Hola")
    assert result["session_id"] == session_id
    assert result["conversation_phase"] == ConversationPhase.IDENTIFICATION.value
    assert "Hola" in result["agent_response"]

