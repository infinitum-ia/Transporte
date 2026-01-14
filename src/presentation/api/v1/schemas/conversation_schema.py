"""
Conversation API Schemas

Schemas for the unified conversation endpoint.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class UnifiedConversationRequest(BaseModel):
    """Unified request for conversation (handles session creation + messaging)"""
    PATIENT_PHONE: str = Field(..., min_length=10, max_length=10, description="Patient phone number (10 digits)")
    MESSAGE: str = Field(..., min_length=1, max_length=2000, description="User message")
    IS_OUTBOUND: bool = Field(default=True, description="True for outbound calls (we call patient), False for inbound calls (patient calls us)")
    AGENT_NAME: Optional[str] = Field(default="María", description="Agent name")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "PATIENT_PHONE": "3001234567",
                    "MESSAGE": "Sí, con él habla",
                    "IS_OUTBOUND": True,
                    "AGENT_NAME": "María"
                },
                {
                    "PATIENT_PHONE": "3001234567",
                    "MESSAGE": "Buenos días, necesito transporte",
                    "IS_OUTBOUND": False,
                    "AGENT_NAME": "María"
                }
            ]
        }
    }


class UnifiedConversationResponse(BaseModel):
    """Unified response from conversation (includes session management)"""
    SESSION_ID: str = Field(..., description="Session identifier")
    AGENT_RESPONSE: str = Field(..., description="Agent's response message")
    FIN: bool = Field(..., description="True if conversation ended, False if conversation continues")

    model_config = {
        "json_schema_extra": {
            "example": {
                "SESSION_ID": "550e8400-e29b-41d4-a716-446655440000",
                "AGENT_RESPONSE": "Buenos días, ¿hablo con Juan Pérez García? Le llamo de Transformas...",
                "FIN": False
            }
        }
    }
