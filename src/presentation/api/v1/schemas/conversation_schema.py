"""
Conversation API Schemas

Schemas for the unified conversation endpoint.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class UnifiedConversationRequest(BaseModel):
    """Unified request for conversation (handles session creation + messaging)"""
    patient_phone: str = Field(..., min_length=10, max_length=10, description="Patient phone number (10 digits)")
    message: str = Field(..., min_length=1, max_length=2000, description="User message")
    is_outbound: bool = Field(default=True, description="True for outbound calls (we call patient), False for inbound calls (patient calls us)")
    agent_name: Optional[str] = Field(default="María", description="Agent name")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "patient_phone": "3001234567",
                    "message": "Sí, con él habla",
                    "is_outbound": True,
                    "agent_name": "María"
                },
                {
                    "patient_phone": "3001234567",
                    "message": "Buenos días, necesito transporte",
                    "is_outbound": False,
                    "agent_name": "María"
                }
            ]
        }
    }


class UnifiedConversationResponse(BaseModel):
    """Unified response from conversation (includes session management)"""
    session_id: str = Field(..., description="Session identifier")
    agent_response: str = Field(..., description="Agent's response message")
    conversation_phase: str = Field(..., description="Current conversation phase")
    call_direction: str = Field(..., description="Call direction (INBOUND or OUTBOUND)")
    requires_escalation: bool = Field(default=False, description="Whether escalation to EPS is required")
    session_created: bool = Field(..., description="True if session was created in this request, False if continuing existing session")
    patient_name: Optional[str] = Field(None, description="Patient name (if known)")
    service_type: Optional[str] = Field(None, description="Service type (if known)")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

    model_config = {
        "json_schema_extra": {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "agent_response": "Buenos días, ¿hablo con Juan Pérez García? Le llamo de Transformas...",
                "conversation_phase": "OUTBOUND_GREETING",
                "call_direction": "OUTBOUND",
                "requires_escalation": False,
                "session_created": True,
                "patient_name": "Juan Pérez García",
                "service_type": "Diálisis",
                "metadata": {}
            }
        }
    }
