"""
Langfuse integration module for LLM observability.

Provides callback handlers for LangChain/LangGraph and direct client access
for custom scoring and metadata enrichment.

Usage:
    from src.infrastructure.observability import get_langfuse_handler, get_langfuse_client

    # Get a callback handler for LangChain/LangGraph
    handler = get_langfuse_handler(session_id="abc", user_id="phone:123")
    result = graph.invoke(state, config={"callbacks": [handler]})

    # Get direct client for scoring
    client = get_langfuse_client()
    if client:
        client.score(trace_id=handler.get_trace_id(), name="escalation", value=1)
"""
import logging
import threading
from typing import Optional, List, Dict, Any

from src.infrastructure.config.settings import settings

logger = logging.getLogger(__name__)

# Thread-safe lazy-initialized singleton
_langfuse_client = None
_langfuse_initialized = False
_init_lock = threading.Lock()


def _is_langfuse_available() -> bool:
    """Check if Langfuse is enabled and properly configured."""
    if not settings.LANGFUSE_ENABLED:
        return False
    if not settings.LANGFUSE_PUBLIC_KEY or not settings.LANGFUSE_SECRET_KEY:
        return False
    return True


def get_langfuse_client():
    """
    Get or create the Langfuse client singleton.

    Thread-safe via double-checked locking.
    Returns None if Langfuse is disabled or not configured.
    """
    global _langfuse_client, _langfuse_initialized

    if _langfuse_initialized:
        return _langfuse_client

    with _init_lock:
        if _langfuse_initialized:
            return _langfuse_client

        if not _is_langfuse_available():
            _langfuse_initialized = True
            logger.info("Langfuse disabled or not configured, skipping initialization")
            return None

        try:
            from langfuse import Langfuse

            _langfuse_client = Langfuse(
                public_key=settings.LANGFUSE_PUBLIC_KEY,
                secret_key=settings.LANGFUSE_SECRET_KEY,
                host=settings.LANGFUSE_HOST,
            )
            _langfuse_initialized = True
            logger.info(f"Langfuse client initialized (host={settings.LANGFUSE_HOST})")
            return _langfuse_client
        except Exception as e:
            logger.error(f"Failed to initialize Langfuse client: {e}; will retry on next call")
            _langfuse_client = None
            return None


def get_langfuse_handler(
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    trace_name: Optional[str] = None,
):
    """
    Create a Langfuse CallbackHandler for LangChain/LangGraph.

    This handler automatically captures:
    - LLM generations (prompts, completions, tokens, latency)
    - Chain/graph execution spans
    - Metadata and tags for filtering in dashboard

    Args:
        session_id: Groups multiple traces under one session in Langfuse
        user_id: Identifies the user (e.g., patient phone number)
        tags: List of tags for filtering (e.g., ["inbound", "phase:GREETING"])
        metadata: Additional metadata dict (e.g., {"agent_name": "Maria"})
        trace_name: Name for the trace (defaults to "conversation_turn")

    Returns:
        CallbackHandler instance, or None if Langfuse is not available.
    """
    if not _is_langfuse_available():
        return None

    try:
        from langfuse.callback import CallbackHandler

        handler = CallbackHandler(
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            secret_key=settings.LANGFUSE_SECRET_KEY,
            host=settings.LANGFUSE_HOST,
            session_id=session_id,
            user_id=user_id,
            tags=tags or [],
            metadata=metadata or {},
            trace_name=trace_name or "conversation_turn",
        )
        return handler
    except Exception as e:
        logger.warning(f"Failed to create Langfuse handler: {e}")
        return None


def flush_langfuse():
    """
    Flush pending Langfuse events.

    Call this at the end of each request to ensure data is sent
    before the response is returned.
    """
    client = get_langfuse_client()
    if client:
        try:
            client.flush()
        except Exception as e:
            logger.warning(f"Failed to flush Langfuse: {e}")
