"""
Call Management Endpoints

Provides monitoring, statistics, and management capabilities for calls.
Call initiation is handled by the unified conversation endpoint.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime

from ..schemas.call_schema import (
    PendingCallsResponse,
    PendingCallItem,
    CallStatisticsResponse,
    CallStatusUpdateRequest,
    CallStatusUpdateResponse,
    SessionDetailResponse
)
from ...dependencies import get_call_orchestrator, get_excel_service
from .....agent.call_orchestrator import CallOrchestrator
from .....infrastructure.persistence.excel_service import ExcelOutboundService

router = APIRouter(prefix="/calls", tags=["calls"])


# ==========================================
# CALL MONITORING & STATISTICS
# ==========================================

@router.get("/outbound/pending", response_model=PendingCallsResponse)
async def get_pending_calls(
    excel_service: ExcelOutboundService = Depends(get_excel_service)
):
    """
    Get list of pending outbound calls

    Returns all calls with status "Pendiente" from the Excel file.

    **Response:**
    - List of pending calls with patient and service information
    """
    try:
        pending_calls = excel_service.get_pending_calls()

        call_items = [
            PendingCallItem(
                patient_name=call.nombre_completo,
                patient_phone=call.telefono,
                service_type=call.tipo_servicio,
                appointment_date=call.fecha_servicio,
                appointment_time=call.hora_servicio,
                modality=call.modalidad_transporte,
                city=call.ciudad,
                observations=call.observaciones_especiales
            )
            for call in pending_calls
        ]

        return PendingCallsResponse(
            total_pending=len(call_items),
            calls=call_items
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving pending calls: {str(e)}"
        )


# ==========================================
# STATISTICS
# ==========================================

@router.get("/statistics", response_model=CallStatisticsResponse)
async def get_call_statistics(
    excel_service: ExcelOutboundService = Depends(get_excel_service)
):
    """
    Get call statistics

    Returns comprehensive statistics about all calls including:
    - Total calls and breakdown by status
    - Distribution by service type
    - Distribution by modality

    **Response:**
    - Detailed statistics from Excel data
    """
    try:
        stats = excel_service.get_statistics()

        return CallStatisticsResponse(**stats)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving statistics: {str(e)}"
        )


# ==========================================
# SESSION DETAILS
# ==========================================

@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_call_session_details(
    session_id: str,
    orchestrator: CallOrchestrator = Depends(get_call_orchestrator)
):
    """
    Get detailed call session information

    Returns complete session state including call direction, phase, patient info,
    and confirmation status (for outbound calls).

    **Parameters:**
    - `session_id`: Session identifier

    **Response:**
    - Complete session details
    """
    try:
        session = await orchestrator.get_session_async(session_id)

        if session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session not found: {session_id}"
            )

        patient = session.get("patient", {}) or {}
        service = session.get("service", {}) or {}

        patient_name = patient.get("patient_full_name")
        patient_document = None
        if patient.get("document_type") and patient.get("document_number"):
            patient_document = f"{patient.get('document_type')}-{patient.get('document_number')}"

        return SessionDetailResponse(
            session_id=session_id,
            call_direction=session.get("call_direction", "INBOUND"),
            conversation_phase=session.get("phase", "GREETING"),
            agent_name=session.get("agent_name", "María"),
            patient_name=patient_name,
            patient_document=patient_document,
            service_type=service.get("service_type"),
            confirmation_status=session.get("confirmation_status"),
            service_confirmed=session.get("service_confirmed"),
            created_at=session.get("created_at", datetime.utcnow().isoformat()),
            updated_at=session.get("updated_at", datetime.utcnow().isoformat())
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving session: {str(e)}"
        )


# ==========================================
# STATUS UPDATE
# ==========================================

@router.put("/{session_id}/status", response_model=CallStatusUpdateResponse)
async def update_call_status(
    session_id: str,
    request: CallStatusUpdateRequest,
    orchestrator: CallOrchestrator = Depends(get_call_orchestrator),
    excel_service: ExcelOutboundService = Depends(get_excel_service)
):
    """
    Update call confirmation status

    Manually updates the confirmation status for an outbound call session
    and syncs it to the Excel file.

    **Parameters:**
    - `session_id`: Session identifier

    **Request:**
    - `status`: New status (Confirmado, Reprogramar, Rechazado, No contesta, Zona sin cobertura)
    - `observations`: Optional additional observations

    **Response:**
    - Updated status confirmation
    """
    try:
        # Validate status
        valid_statuses = [
            "Confirmado", "Reprogramar", "Rechazado",
            "No contesta", "Zona sin cobertura"
        ]
        if request.status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )

        # Get session
        session = await orchestrator.get_session_async(session_id)

        if session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session not found: {session_id}"
            )

        # Verify this is an outbound call
        if session.get("call_direction") != "OUTBOUND":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Status update only available for outbound calls"
            )

        # Get Excel row index
        row_index = session.get("excel_row_index")
        if row_index is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session not linked to Excel data"
            )

        # Update Excel
        success = excel_service.update_call_status(
            row_index=row_index,
            new_status=request.status,
            observations=request.observations
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update Excel file"
            )

        # Update session state
        session["confirmation_status"] = request.status
        session["updated_at"] = datetime.utcnow().isoformat()

        # Save session
        await orchestrator._store.set(session_id, session)

        return CallStatusUpdateResponse(
            session_id=session_id,
            status=request.status,
            updated_at=session["updated_at"],
            success=True
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating status: {str(e)}"
        )
