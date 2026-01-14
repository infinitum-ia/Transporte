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
    - `PATIENT_PHONE`: Patient phone number (10 digits) - REQUIRED
    - `MESSAGE`: User's message - REQUIRED
    - `IS_OUTBOUND`: True for outbound (we call patient), False for inbound (patient calls us) - Default: True
    - `AGENT_NAME`: Agent name - Optional (default: "María")

    **Response:**
    - `SESSION_ID`: Session identifier (save for tracking)
    - `AGENT_RESPONSE`: Agent's response message (ready to play/display)
    - `FIN`: True if conversation ended, False if conversation continues

    **Usage Examples:**

    1. **Start outbound call:**
    ```json
    {
        "PATIENT_PHONE": "3001234567",
        "MESSAGE": "START",
        "IS_OUTBOUND": true
    }
    ```

    2. **Continue conversation:**
    ```json
    {
        "PATIENT_PHONE": "3001234567",
        "MESSAGE": "Sí, con él habla",
        "IS_OUTBOUND": true
    }
    ```

    3. **Inbound call:**
    ```json
    {
        "PATIENT_PHONE": "3001234567",
        "MESSAGE": "Buenos días, necesito transporte",
        "IS_OUTBOUND": false
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

        print(f"\n{'='*80}")
        print(f"🎯 [ENDPOINT] MENSAJE RECIBIDO")
        print(f"{'='*80}")
        print(f"   📞 Teléfono: {request.PATIENT_PHONE}")
        print(f"   💬 Mensaje: '{request.MESSAGE}'")
        print(f"   📍 Dirección: {'OUTBOUND (llamamos)' if request.IS_OUTBOUND else 'INBOUND (paciente llama)'}")
        print(f"   👤 Agente: {request.AGENT_NAME}")
        print(f"{'='*80}\n")

        # Get orchestrator from app state
        orchestrator = getattr(http_request.app.state, "call_orchestrator", None)
        if orchestrator is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Call orchestrator not configured. Ensure AGENT_MODE=llm in environment."
            )

        # Process unified message (handles session creation + messaging)
        print(f"🔄 [ENDPOINT] Enviando a LangGraph Orchestrator...")
        response = await orchestrator.process_unified_message(
            patient_phone=request.PATIENT_PHONE,
            user_message=request.MESSAGE,
            is_outbound=request.IS_OUTBOUND,
            agent_name=request.AGENT_NAME
        )

        print(f"\n✅ [ENDPOINT] RESPUESTA LISTA")
        print(f"   🤖 Respuesta: '{response.get('agent_response', '')[:100]}...'")
        print(f"   📊 Fase: {response.get('conversation_phase')}")
        print(f"{'='*80}\n")

        # Map response to new schema (UPPERCASE fields)
        # FIN = True if conversation_phase is "END"
        fin = response.get('conversation_phase') == 'END'

        return UnifiedConversationResponse(
            SESSION_ID=response.get('session_id'),
            AGENT_RESPONSE=response.get('agent_response'),
            FIN=fin
        )

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
