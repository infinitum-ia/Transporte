# LangGraph Orchestrator - compatible with CallOrchestrator interface
from typing import Dict, Any, Optional
import uuid
from langchain_core.messages import HumanMessage, AIMessage
from src.agent.graph.conversation_graph import create_conversation_graph
from src.agent.graph.state_adapters import create_initial_state, state_to_dict

class LangGraphOrchestrator:
    """
    LangGraph-based conversation orchestrator.
    
    Compatible interface with CallOrchestrator for easy migration.
    """
    
    def __init__(self, settings=None, store=None, excel_service=None):
        """Initialize orchestrator with compiled graph

        Args:
            settings: Application settings
            store: RedisSessionStore for session persistence (optional)
            excel_service: ExcelOutboundService for outbound calls (optional)
        """
        self.graph = create_conversation_graph()
        self.settings = settings
        self.store = store
        self.excel_service = excel_service
        self._sessions = {}  # In-memory session storage for now
    
    async def process_message(
        self,
        session_id: str,
        user_message: str,
        call_direction: str = "INBOUND",
        agent_name: str = "Maria",
        excel_row_index: int = None
    ) -> Dict[str, Any]:
        """
        Process a user message through the LangGraph.
        
        Args:
            session_id: Unique session identifier
            user_message: User's message
            call_direction: INBOUND or OUTBOUND
            agent_name: Agent name
            excel_row_index: Row index for outbound calls
            
        Returns:
            Response dict with agent_response, next_phase, etc.
        """
        
        # Get or create session state
        if session_id not in self._sessions:
            # Create new session
            state = create_initial_state(
                session_id=session_id,
                call_direction=call_direction,
                agent_name=agent_name,
                excel_row_index=excel_row_index
            )
            self._sessions[session_id] = state
        else:
            state = self._sessions[session_id]
        
        # Add user message to state
        state['messages'].append(HumanMessage(content=user_message))
        
        # Run graph
        result = self.graph.invoke(state)
        
        # Add agent response to messages
        agent_response = result.get('agent_response', '')
        if agent_response:
            result['messages'].append(AIMessage(content=agent_response))
        
        # Update session
        self._sessions[session_id] = result
        
        # Return response in compatible format
        return {
            'agent_response': agent_response,
            'next_phase': result.get('next_phase'),
            'current_phase': result.get('current_phase'),
            'session_id': session_id,
            'escalation_required': result.get('escalation_required', False),
            'escalation_reasons': result.get('escalation_reasons', []),
            'policy_violations': result.get('policy_violations', []),
            'state': state_to_dict(result)
        }
    
    def get_session(self, session_id: str) -> Dict[str, Any]:
        """Get session state"""
        if session_id in self._sessions:
            return state_to_dict(self._sessions[session_id])
        return None
    
    def create_session(
        self,
        call_direction: str = "INBOUND",
        agent_name: str = "Maria",
        excel_row_index: int = None
    ) -> str:
        """Create a new session"""
        session_id = str(uuid.uuid4())

        state = create_initial_state(
            session_id=session_id,
            call_direction=call_direction,
            agent_name=agent_name,
            excel_row_index=excel_row_index
        )
        self._sessions[session_id] = state

        return session_id

    async def process_unified_message(
        self,
        patient_phone: str,
        user_message: str,
        is_outbound: bool = False,
        agent_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process message with automatic session management.

        Compatible with CallOrchestrator.process_unified_message().

        Args:
            patient_phone: Patient phone number
            user_message: User's message
            is_outbound: True for outbound, False for inbound
            agent_name: Agent name (optional)

        Returns:
            Dict with response, session info, and metadata
        """
        # For now, create a simple mapping of patient_phone to session_id
        # In production, this would use Redis or the store
        session_key = f"phone:{patient_phone}"

        # Find or create session
        session_id = None
        session_created = False

        # Simple in-memory phone-to-session mapping
        if not hasattr(self, '_phone_to_session'):
            self._phone_to_session = {}

        if session_key in self._phone_to_session:
            session_id = self._phone_to_session[session_key]
        else:
            # Create new session
            session_id = self.create_session(
                call_direction="OUTBOUND" if is_outbound else "INBOUND",
                agent_name=agent_name or (self.settings.AGENT_NAME if self.settings else "María")
            )
            self._phone_to_session[session_key] = session_id
            session_created = True

        # Process the message
        response = await self.process_message(
            session_id=session_id,
            user_message=user_message,
            call_direction="OUTBOUND" if is_outbound else "INBOUND",
            agent_name=agent_name or (self.settings.AGENT_NAME if self.settings else "María")
        )

        # Add session management info
        response["session_created"] = session_created
        response["conversation_phase"] = response.get("current_phase")
        response["call_direction"] = "OUTBOUND" if is_outbound else "INBOUND"
        response["requires_escalation"] = response.get("escalation_required", False)
        response["metadata"] = {}

        return response
