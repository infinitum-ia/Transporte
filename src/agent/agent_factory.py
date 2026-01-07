from __future__ import annotations

from typing import Any

from src.agent.llm_agent import LLMConversationalAgent
from src.agent.mock_agent import MockConversationalAgent
from src.infrastructure.config.settings import Settings
from src.infrastructure.persistence.redis.session_store import RedisSessionStore


def create_agent(*, settings: Settings, store: RedisSessionStore | None = None, llm: Any = None):
    mode = (settings.AGENT_MODE or "mock").strip().lower()
    if mode == "llm":
        if store is None:
            raise ValueError("AGENT_MODE=llm requires a session store (Redis)")
        return LLMConversationalAgent(settings=settings, store=store, llm=llm)
    return MockConversationalAgent(agent_name=settings.AGENT_NAME, company_name=settings.COMPANY_NAME)
