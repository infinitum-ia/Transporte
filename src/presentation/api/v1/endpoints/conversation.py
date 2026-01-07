"""
Conversation Endpoints
"""
from fastapi import APIRouter, HTTPException, status, Header, Depends, Request
from ..schemas.conversation_schema import (
    ConversationMessageRequest,
    ConversationMessageResponse
)
from ...dependencies import get_agent, get_call_orchestrator
from .....agent.call_orchestrator import CallOrchestrator

router = APIRouter(prefix="/conversation", tags=["conversation"])


@router.post("/message", response_model=ConversationMessageResponse)
async def send_message(
    request: ConversationMessageRequest,
    x_session_id: str = Header(..., description="Session ID"),
    agent=Depends(get_agent),
):
    """
    Send a message in the conversation (legacy endpoint)

    The agent will process the message according to the current conversation phase
    and return an appropriate response.

    This endpoint uses the legacy agent. For both INBOUND and OUTBOUND call support,
    use POST /api/v1/conversation/message/v2 instead.

    **Headers:**
    - `X-Session-ID`: Session identifier (required)

    **Request Body:**
    - `message`: User's message (1-2000 characters)

    **Response:**
    - `agent_response`: Agent's response message
    - `conversation_phase`: Current phase in the conversation flow
    - `requires_escalation`: Whether the request needs EPS escalation
    - `metadata`: Additional context information
    """
    try:
        response = await agent.process_message(x_session_id, request.message)
        return ConversationMessageResponse(**response)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing message: {str(e)}"
        )


@router.post("/message/v2", response_model=ConversationMessageResponse)
async def send_message_v2(
    http_request: Request,
    request: ConversationMessageRequest,
    x_session_id: str = Header(..., description="Session ID")
):
    """
    Send a message in the conversation (v2 - supports both INBOUND and OUTBOUND)

    The CallOrchestrator will automatically detect the call direction from the session
    and route to the appropriate processing logic (inbound or outbound).

    **Headers:**
    - `X-Session-ID`: Session identifier (required)

    **Request Body:**
    - `message`: User's message (1-2000 characters)

    **Response:**
    - `agent_response`: Agent's response message
    - `conversation_phase`: Current phase in the conversation flow
    - `requires_escalation`: Whether the request needs EPS escalation
    - `call_direction`: INBOUND or OUTBOUND
    - `metadata`: Additional context information (including confirmation status for outbound)
    """
    try:
        # Get orchestrator from app state
        orchestrator = getattr(http_request.app.state, "call_orchestrator", None)
        if orchestrator is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Call orchestrator not configured. Ensure AGENT_MODE=llm in environment."
            )

        # Process message
        response = await orchestrator.process_message(x_session_id, request.message)
        return ConversationMessageResponse(**response)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing message: {str(e)}"
        )
