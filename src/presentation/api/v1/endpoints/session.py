"""
Session Management Endpoints

Provides endpoints for retrieving and managing conversation sessions.
Session creation is handled automatically by the unified conversation endpoint.
"""
from fastapi import APIRouter, HTTPException, status, Depends, Request
from datetime import datetime
from ..schemas.session_schema import SessionStateResponse
from ...dependencies import get_agent
from .....agent.llm_agent import LLMConversationalAgent

router = APIRouter(prefix="/session", tags=["session"])


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
