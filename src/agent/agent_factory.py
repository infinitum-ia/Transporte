from __future__ import annotations

from typing import Any, Union
import logging

from src.agent.llm_agent import LLMConversationalAgent
from src.agent.mock_agent import MockConversationalAgent
from src.infrastructure.config.settings import Settings
from src.infrastructure.persistence.redis.session_store import RedisSessionStore

logger = logging.getLogger(__name__)


def create_agent(*, settings: Settings, store: RedisSessionStore | None = None, llm: Any = None):
    mode = (settings.AGENT_MODE or "mock").strip().lower()
    if mode == "llm":
        if store is None:
            raise ValueError("AGENT_MODE=llm requires a session store (Redis)")
        return LLMConversationalAgent(settings=settings, store=store, llm=llm)
    return MockConversationalAgent(agent_name=settings.AGENT_NAME, company_name=settings.COMPANY_NAME)


def create_orchestrator(settings: Settings) -> Any:
    """
    Create conversation orchestrator based on settings.

    Uses LangGraphOrchestrator if USE_LANGGRAPH=true, otherwise CallOrchestrator.
    Includes automatic fallback to legacy orchestrator if LangGraph fails.

    Args:
        settings: Application settings

    Returns:
        Orchestrator instance (LangGraphOrchestrator or CallOrchestrator)
    """
    if settings.USE_LANGGRAPH:
        try:
            logger.info("Creating LangGraphOrchestrator")
            from src.agent.langgraph_orchestrator import LangGraphOrchestrator
            return LangGraphOrchestrator(settings=settings)
        except Exception as e:
            logger.error(f"Failed to create LangGraphOrchestrator: {e}", exc_info=True)
            logger.warning("Falling back to legacy CallOrchestrator")
            # Fall through to create CallOrchestrator

    # Create legacy orchestrator
    logger.info("Creating legacy CallOrchestrator")
    from src.agent.call_orchestrator import CallOrchestrator
    return CallOrchestrator()
