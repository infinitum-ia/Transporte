# LangGraph Orchestrator - compatible with CallOrchestrator interface
from typing import Dict, Any
from langchain_core.messages import HumanMessage, AIMessage
from src.agent.graph.conversation_graph import create_conversation_graph
from src.agent.graph.state_adapters import create_initial_state, state_to_dict

class LangGraphOrchestrator:
    """
    LangGraph-based conversation orchestrator.
    
    Compatible interface with CallOrchestrator for easy migration.
    """
    
    def __init__(self, settings=None):
        """Initialize orchestrator with compiled graph"""
        self.graph = create_conversation_graph()
        self.settings = settings
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
        import uuid
        session_id = str(uuid.uuid4())
        
        state = create_initial_state(
            session_id=session_id,
            call_direction=call_direction,
            agent_name=agent_name,
            excel_row_index=excel_row_index
        )
        self._sessions[session_id] = state
        
        return session_id
