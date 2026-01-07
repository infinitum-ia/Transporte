from __future__ import annotations

from typing import Any, Dict, Optional, Protocol


class ConversationalAgent(Protocol):
    def create_session(self, agent_name: Optional[str] = None) -> str:
        ...

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        ...

    async def process_message(self, session_id: str, user_message: str) -> Dict[str, Any]:
        ...

