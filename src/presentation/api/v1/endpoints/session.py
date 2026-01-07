"""
Session Endpoints
"""
from fastapi import APIRouter, HTTPException, status, Depends, Request
from datetime import datetime
from typing import Optional
from ..schemas.session_schema import (
    SessionCreateRequest,
    SessionCreateResponse,
    SessionStateResponse
)
from ..schemas.call_schema import (
    SessionCreateWithDirectionRequest,
    SessionCreateSimpleRequest,
    OutboundCallCreateRequest,
    OutboundCallCreateResponse
)
from ...dependencies import get_agent, get_call_orchestrator, get_excel_service
from .....agent.llm_agent import LLMConversationalAgent
from .....agent.call_orchestrator import CallOrchestrator
from .....domain.value_objects.call_direction import CallDirection

router = APIRouter(prefix="/session", tags=["session"])


@router.post("", response_model=SessionCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_session(request: SessionCreateRequest, agent=Depends(get_agent)):
    """
    Create a new INBOUND conversation session (legacy endpoint)

    Returns a unique session ID that must be used for all subsequent messages.
    This endpoint creates INBOUND sessions (patient calls us).

    For creating OUTBOUND sessions, use POST /api/v1/calls/outbound instead.
    """
    session_id = agent.create_session(agent_name=request.agent_name)

    if isinstance(agent, LLMConversationalAgent):
        await agent.init_session(session_id, agent_name=request.agent_name)

    return SessionCreateResponse(
        session_id=session_id,
        created_at=datetime.utcnow().isoformat(),
        conversation_phase="GREETING"
    )


@router.post("/v2", response_model=SessionCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_session_v2(
    request: SessionCreateWithDirectionRequest,
    http_request: Request
):
    """
    Create a new conversation session with specific call direction (v2)

    Supports both INBOUND and OUTBOUND call directions.

    **Request:**
    - `call_direction`: "INBOUND" or "OUTBOUND"
    - `agent_name`: Optional agent name
    - `patient_phone`: Required for OUTBOUND calls

    **Response:**
    - Session ID and initial conversation phase
    """
    try:
        # Validate call direction
        try:
            call_direction = CallDirection.from_string(request.call_direction)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        # Get orchestrator from app state
        orchestrator = getattr(http_request.app.state, "call_orchestrator", None)
        if orchestrator is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Call orchestrator not configured. Ensure AGENT_MODE=llm in environment."
            )

        # Create session
        session_id = orchestrator.create_session(agent_name=request.agent_name)

        if call_direction.is_inbound:
            # Create inbound session
            state = await orchestrator.init_inbound_session(
                session_id=session_id,
                agent_name=request.agent_name
            )
            return SessionCreateResponse(
                session_id=session_id,
                created_at=state["created_at"],
                conversation_phase=state["phase"]
            )

        else:
            # Outbound call requires patient phone
            if not request.patient_phone:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="patient_phone is required for OUTBOUND calls"
                )

            # Get Excel service
            excel_service = getattr(http_request.app.state, "excel_service", None)
            if excel_service is None:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Excel service not configured. Ensure EXCEL_PATH is set in environment."
                )

            # Get patient data
            patient_data = excel_service.get_patient_by_phone(request.patient_phone)
            if patient_data is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No patient found with phone: {request.patient_phone}"
                )

            # Create outbound session
            state = await orchestrator.init_outbound_session(
                session_id=session_id,
                patient_data=patient_data,
                agent_name=request.agent_name
            )
            return SessionCreateResponse(
                session_id=session_id,
                created_at=state["created_at"],
                conversation_phase=state["phase"]
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating session: {str(e)}"
        )


@router.post("/create", response_model=SessionCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_session_simple(
    request: SessionCreateSimpleRequest,
    http_request: Request
):
    """
    Create a new conversation session with boolean call direction (SIMPLIFIED)

    This is the simplified version using a boolean parameter to determine call direction.

    **Request:**
    - `is_outbound`: True for outbound calls (we call customer), False for inbound (customer calls us)
    - `agent_name`: Optional agent name (default: María)
    - `patient_phone`: Required when is_outbound=True

    **Response:**
    - Session ID and initial conversation phase

    **Examples:**
    - Inbound call: `{"is_outbound": false, "agent_name": "María"}`
    - Outbound call: `{"is_outbound": true, "agent_name": "María", "patient_phone": "3001234567"}`
    """
    try:
        # Get orchestrator from app state
        orchestrator = getattr(http_request.app.state, "call_orchestrator", None)
        if orchestrator is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Call orchestrator not configured. Ensure AGENT_MODE=llm in environment."
            )

        # Create session
        session_id = orchestrator.create_session(agent_name=request.agent_name)

        if not request.is_outbound:
            # Create INBOUND session
            state = await orchestrator.init_inbound_session(
                session_id=session_id,
                agent_name=request.agent_name
            )
            return SessionCreateResponse(
                session_id=session_id,
                created_at=state["created_at"],
                conversation_phase=state["phase"]
            )

        else:
            # Create OUTBOUND session
            if not request.patient_phone:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="patient_phone is required when is_outbound=True"
                )

            # Get Excel service
            excel_service = getattr(http_request.app.state, "excel_service", None)
            if excel_service is None:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Excel service not configured. Ensure EXCEL_PATH is set in environment."
                )

            # Get patient data
            patient_data = excel_service.get_patient_by_phone(request.patient_phone)
            if patient_data is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No patient found with phone: {request.patient_phone}"
                )

            # Create outbound session
            state = await orchestrator.init_outbound_session(
                session_id=session_id,
                patient_data=patient_data,
                agent_name=request.agent_name
            )
            return SessionCreateResponse(
                session_id=session_id,
                created_at=state["created_at"],
                conversation_phase=state["phase"]
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating session: {str(e)}"
        )


@router.get("/{session_id}", response_model=SessionStateResponse)
async def get_session(session_id: str, agent=Depends(get_agent)):
    """
    Get session state

    Returns the current state of the conversation session.
    """
    if isinstance(agent, LLMConversationalAgent):
        session = await agent.get_session_async(session_id)
    else:
        session = agent.get_session(session_id)

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}"
        )

    phase = session.get("phase") or session.get("conversation_phase") or "GREETING"
    patient = session.get("patient", {}) or {}
    service = session.get("service", {}) or {}
    patient_name = session.get("patient_name") or patient.get("patient_full_name")
    patient_document = session.get("patient_document")
    if not patient_document and patient.get("document_type") and patient.get("document_number"):
        patient_document = f"{patient.get('document_type')}-{patient.get('document_number')}"

    return SessionStateResponse(
        session_id=session.get("session_id", session_id),
        conversation_phase=str(phase),
        patient_name=patient_name,
        patient_document=patient_document,
        service_type=session.get("service_type") or service.get("service_type"),
        created_at=session.get("created_at", datetime.utcnow().isoformat())
    )


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(session_id: str, http_request: Request, agent=Depends(get_agent)):
    """
    Delete a conversation session

    Removes the session from memory.
    """
    if isinstance(agent, LLMConversationalAgent):
        store = getattr(http_request.app.state, "session_store", None)
        if store is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Session store not configured")
        await store.delete(session_id)
        return

    if hasattr(agent, "sessions") and session_id in getattr(agent, "sessions"):
        del getattr(agent, "sessions")[session_id]
        return

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Session not found: {session_id}"
    )
