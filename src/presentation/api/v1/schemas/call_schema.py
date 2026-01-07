"""
Call Management API Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ==========================================
# OUTBOUND CALL CREATION
# ==========================================

class OutboundCallCreateRequest(BaseModel):
    """Request to create outbound call session"""
    patient_phone: str = Field(..., description="Patient phone number (10 digits)")
    agent_name: Optional[str] = Field(default="María", description="Agent name")

    model_config = {
        "json_schema_extra": {
            "example": {
                "patient_phone": "3001234567",
                "agent_name": "María"
            }
        }
    }


class OutboundCallCreateResponse(BaseModel):
    """Response with outbound call session"""
    session_id: str = Field(..., description="Session identifier")
    call_direction: str = Field(default="OUTBOUND", description="Call direction")
    patient_name: str = Field(..., description="Patient full name")
    service_type: str = Field(..., description="Service type")
    appointment_date: str = Field(..., description="Appointment date")
    created_at: str = Field(..., description="Session creation timestamp")

    model_config = {
        "json_schema_extra": {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "call_direction": "OUTBOUND",
                "patient_name": "Juan Pérez García",
                "service_type": "Diálisis",
                "appointment_date": "2024-01-20",
                "created_at": "2024-01-15T10:30:00Z"
            }
        }
    }


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
# SESSION WITH CALL DIRECTION
# ==========================================

class SessionCreateWithDirectionRequest(BaseModel):
    """Request to create session with specific call direction (DEPRECATED - use is_outbound)"""
    call_direction: str = Field(
        default="INBOUND",
        description="Call direction: INBOUND or OUTBOUND"
    )
    agent_name: Optional[str] = Field(default="María", description="Agent name")
    patient_phone: Optional[str] = Field(
        None,
        description="Patient phone (required for OUTBOUND calls)"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "call_direction": "INBOUND",
                    "agent_name": "María"
                },
                {
                    "call_direction": "OUTBOUND",
                    "agent_name": "María",
                    "patient_phone": "3001234567"
                }
            ]
        }
    }


class SessionCreateSimpleRequest(BaseModel):
    """Request to create session with boolean call direction (SIMPLIFIED)"""
    is_outbound: bool = Field(
        default=False,
        description="True for outbound calls (we call customer), False for inbound calls (customer calls us)"
    )
    agent_name: Optional[str] = Field(default="María", description="Agent name")
    patient_phone: Optional[str] = Field(
        None,
        description="Patient phone (required when is_outbound=True)"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "is_outbound": False,
                    "agent_name": "María"
                },
                {
                    "is_outbound": True,
                    "agent_name": "María",
                    "patient_phone": "3001234567"
                }
            ]
        }
    }


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


# ==========================================
# OUTBOUND CALL INITIATION (UNIFIED)
# ==========================================

class OutboundCallInitiateResponse(BaseModel):
    """Response for unified outbound call initiation (session + initial message)"""
    session_id: str = Field(..., description="Session identifier")
    call_direction: str = Field(default="OUTBOUND", description="Call direction")
    conversation_phase: str = Field(..., description="Current conversation phase")
    agent_initial_message: str = Field(..., description="Agent's initial greeting message")
    patient_name: str = Field(..., description="Patient full name")
    service_type: str = Field(..., description="Service type")
    appointment_date: str = Field(..., description="Appointment date")
    appointment_time: Optional[str] = Field(None, description="Appointment time")
    created_at: str = Field(..., description="Session creation timestamp")

    model_config = {
        "json_schema_extra": {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "call_direction": "OUTBOUND",
                "conversation_phase": "OUTBOUND_GREETING",
                "agent_initial_message": "Buenos días, ¿hablo con Juan Pérez García? Le llamo de Transformas para confirmar su servicio de transporte médico programado para Diálisis el día 20 de enero a las 08:00 horas.",
                "patient_name": "Juan Pérez García",
                "service_type": "Diálisis",
                "appointment_date": "2024-01-20",
                "appointment_time": "08:00",
                "created_at": "2024-01-15T10:30:00Z"
            }
        }
    }
