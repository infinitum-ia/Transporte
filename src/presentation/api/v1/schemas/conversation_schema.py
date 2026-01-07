"""
Conversation API Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class ConversationMessageRequest(BaseModel):
    """Request to send a message"""
    message: str = Field(..., min_length=1, max_length=2000, description="User message")

    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "Hola, buenos días"
            }
        }
    }


class ConversationMessageResponse(BaseModel):
    """Response from agent"""
    session_id: str = Field(..., description="Session identifier")
    agent_response: str = Field(..., description="Agent's response message")
    conversation_phase: str = Field(..., description="Current conversation phase")
    requires_escalation: bool = Field(default=False, description="Whether escalation to EPS is required")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

    model_config = {
        "json_schema_extra": {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "agent_response": "Buenos días, le habla María de Transformas...",
                "conversation_phase": "GREETING",
                "requires_escalation": False,
                "metadata": {}
            }
        }
    }
