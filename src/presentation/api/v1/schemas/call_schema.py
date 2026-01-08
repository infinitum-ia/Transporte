"""
Call Management API Schemas

Schemas for monitoring and managing calls.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict


# ==========================================
# PENDING CALLS
# ==========================================

class PendingCallItem(BaseModel):
    """Single pending call item"""
    patient_name: str
    patient_phone: str
    service_type: str
    appointment_date: str
    appointment_time: str
    modality: str
    city: str
    observations: Optional[str] = None


class PendingCallsResponse(BaseModel):
    """Response with list of pending calls"""
    total_pending: int = Field(..., description="Total number of pending calls")
    calls: List[PendingCallItem] = Field(..., description="List of pending calls")

    model_config = {
        "json_schema_extra": {
            "example": {
                "total_pending": 2,
                "calls": [
                    {
                        "patient_name": "Juan Pérez García",
                        "patient_phone": "3001234567",
                        "service_type": "Diálisis",
                        "appointment_date": "2024-01-20",
                        "appointment_time": "08:00",
                        "modality": "RUTA",
                        "city": "Bogotá",
                        "observations": "Paciente requiere silla de ruedas"
                    }
                ]
            }
        }
    }


# ==========================================
# CALL STATISTICS
# ==========================================

class CallStatisticsResponse(BaseModel):
    """Response with call statistics"""
    total: int = Field(..., description="Total number of calls")
    pendiente: int = Field(..., description="Pending calls")
    confirmado: int = Field(..., description="Confirmed calls")
    reprogramar: int = Field(..., description="Calls to reschedule")
    rechazado: int = Field(..., description="Rejected calls")
    no_contesta: int = Field(..., description="No answer calls")
    zona_sin_cobertura: int = Field(..., description="No coverage area calls")
    by_service_type: Dict[str, int] = Field(..., description="Calls by service type")
    by_modality: Dict[str, int] = Field(..., description="Calls by modality")

    model_config = {
        "json_schema_extra": {
            "example": {
                "total": 100,
                "pendiente": 25,
                "confirmado": 60,
                "reprogramar": 8,
                "rechazado": 5,
                "no_contesta": 2,
                "zona_sin_cobertura": 0,
                "by_service_type": {
                    "Diálisis": 50,
                    "Terapia": 30,
                    "Cita con Especialista": 20
                },
                "by_modality": {
                    "RUTA": 70,
                    "DESEMBOLSO": 30
                }
            }
        }
    }


# ==========================================
# STATUS UPDATE
# ==========================================

class CallStatusUpdateRequest(BaseModel):
    """Request to update call status"""
    status: str = Field(
        ...,
        description="New status (Confirmado, Reprogramar, Rechazado, No contesta, Zona sin cobertura)"
    )
    observations: Optional[str] = Field(None, description="Additional observations")

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "Confirmado",
                "observations": "Paciente confirma servicio, sin cambios"
            }
        }
    }


class CallStatusUpdateResponse(BaseModel):
    """Response for status update"""
    session_id: str
    status: str
    updated_at: str
    success: bool = True

    model_config = {
        "json_schema_extra": {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "Confirmado",
                "updated_at": "2024-01-15T11:30:00Z",
                "success": True
            }
        }
    }


# ==========================================
# SESSION DETAILS
# ==========================================

class SessionDetailResponse(BaseModel):
    """Detailed session information with call direction"""
    session_id: str
    call_direction: str
    conversation_phase: str
    agent_name: str
    patient_name: Optional[str] = None
    patient_document: Optional[str] = None
    service_type: Optional[str] = None
    confirmation_status: Optional[str] = None
    service_confirmed: Optional[bool] = None
    created_at: str
    updated_at: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "call_direction": "OUTBOUND",
                "conversation_phase": "OUTBOUND_SERVICE_CONFIRMATION",
                "agent_name": "María",
                "patient_name": "Juan Pérez García",
                "patient_document": "CC-1234567890",
                "service_type": "Diálisis",
                "confirmation_status": "Confirmado",
                "service_confirmed": True,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:45:00Z"
            }
        }
    }
