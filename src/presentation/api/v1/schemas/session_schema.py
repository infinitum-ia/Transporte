"""
Session API Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SessionCreateRequest(BaseModel):
    """Request to create a new session"""
    agent_name: str = Field(default="María", description="Agent name")

    model_config = {
        "json_schema_extra": {
            "example": {
                "agent_name": "María"
            }
        }
    }


class SessionCreateResponse(BaseModel):
    """Response with new session"""
    session_id: str = Field(..., description="Session identifier")
    created_at: str = Field(..., description="Session creation timestamp")
    conversation_phase: str = Field(default="GREETING", description="Initial conversation phase")

    model_config = {
        "json_schema_extra": {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "created_at": "2024-01-15T10:30:00Z",
                "conversation_phase": "GREETING"
            }
        }
    }


class SessionStateResponse(BaseModel):
    """Full session state"""
    session_id: str
    conversation_phase: str
    patient_name: Optional[str] = None
    patient_document: Optional[str] = None
    service_type: Optional[str] = None
    created_at: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "conversation_phase": "SERVICE_COORDINATION",
                "patient_name": "Juan Pérez",
                "patient_document": "CC-1234567890",
                "service_type": "TERAPIA",
                "created_at": "2024-01-15T10:30:00Z"
            }
        }
    }
