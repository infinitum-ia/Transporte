"""
Session API Schemas

Schemas for session management endpoints.
"""
from pydantic import BaseModel
from typing import Optional


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
