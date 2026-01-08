"""
Conversation Endpoints

Unified endpoint for handling both inbound and outbound calls.
"""
from fastapi import APIRouter, HTTPException, status, Request
from src.infrastructure.logging import get_logger

router = APIRouter(prefix="/conversation", tags=["conversation"])
logger = get_logger()


@router.post("/unified", status_code=status.HTTP_200_OK)
async def unified_conversation(
    http_request: Request
):
    """
    Unified conversation endpoint (handles session + messaging in one call)

    **PERFECT FOR EXTERNAL PLATFORM INTEGRATIONS**

    This endpoint automatically:
    - Creates session if it doesn't exist (based on phone number)
    - Continues existing session if found
    - Handles both INBOUND and OUTBOUND calls
    - Returns agent response immediately

    **Request Body:**
    - `patient_phone`: Patient phone number (10 digits) - REQUIRED
    - `message`: User's message - REQUIRED
    - `is_outbound`: True for outbound (we call patient), False for inbound (patient calls us) - Default: True
    - `agent_name`: Agent name - Optional (default: "María")

    **Response:**
    - `session_id`: Session identifier (save for tracking)
    - `agent_response`: Agent's response message (ready to play/display)
    - `conversation_phase`: Current phase
    - `call_direction`: INBOUND or OUTBOUND
    - `session_created`: True if new session, False if continuing
    - `patient_name`: Patient name (if known)
    - `service_type`: Service type (if known)
    - `requires_escalation`: Whether escalation needed
    - `metadata`: Additional info

    **Usage Examples:**

    1. **Start outbound call:**
    ```json
    {
        "patient_phone": "3001234567",
        "message": "START",
        "is_outbound": true
    }
    ```

    2. **Continue conversation:**
    ```json
    {
        "patient_phone": "3001234567",
        "message": "Sí, con él habla",
        "is_outbound": true
    }
    ```

    3. **Inbound call:**
    ```json
    {
        "patient_phone": "3001234567",
        "message": "Buenos días, necesito transporte",
        "is_outbound": false
    }
    ```

    **Benefits:**
    - No need to manage session IDs manually
    - Phone number identifies the conversation thread
    - Works for complete conversation flow
    - Single endpoint for all interactions
    """
    try:
        # Import schemas dynamically to avoid circular import
        from ..schemas.conversation_schema import (
            UnifiedConversationRequest,
            UnifiedConversationResponse
        )

        # Parse request
        body = await http_request.json()
        request = UnifiedConversationRequest(**body)

        # Get orchestrator from app state
        orchestrator = getattr(http_request.app.state, "call_orchestrator", None)
        if orchestrator is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Call orchestrator not configured. Ensure AGENT_MODE=llm in environment."
            )

        # Process unified message (handles session creation + messaging)
        response = await orchestrator.process_unified_message(
            patient_phone=request.patient_phone,
            user_message=request.message,
            is_outbound=request.is_outbound,
            agent_name=request.agent_name
        )

        return UnifiedConversationResponse(**response)

    except ValueError as e:
        # Patient not found or configuration error
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=error_msg
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing unified message: {str(e)}"
        )
