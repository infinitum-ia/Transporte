# LangGraph Orchestrator - compatible with CallOrchestrator interface
from typing import Dict, Any, Optional
import uuid
import logging
from langchain_core.messages import HumanMessage, AIMessage
from src.agent.graph.conversation_graph import create_conversation_graph
from src.agent.graph.state_adapters import create_initial_state, state_to_dict
from src.infrastructure.logging import get_logger
from src.infrastructure.config.settings import settings as app_settings
from src.infrastructure.observability import get_langfuse_handler, get_langfuse_client
from src.infrastructure.observability.langfuse_integration import flush_langfuse

logger = logging.getLogger(__name__)
# Use shared conversation logger for visibility
conv_logger = get_logger().logger


def _calculate_pickup_time(appointment_time: str, offset_minutes: int = 60) -> str:
    """
    Calculate pickup time based on appointment time.

    By default, pickup is 1 hour (60 minutes) before the appointment.

    Args:
        appointment_time: Appointment time in HH:MM format
        offset_minutes: Minutes before appointment for pickup (default 60)

    Returns:
        Pickup time in HH:MM format
    """
    try:
        # Parse appointment time (handle both HH:MM and H:MM formats)
        time_parts = appointment_time.replace('.', ':').split(':')
        hour = int(time_parts[0])
        minute = int(time_parts[1]) if len(time_parts) > 1 else 0

        # Calculate pickup time
        total_minutes = hour * 60 + minute - offset_minutes

        # Handle negative time (would be previous day)
        if total_minutes < 0:
            total_minutes = 0
            logger.warning(f"Pickup time would be negative, setting to 00:00")

        pickup_hour = total_minutes // 60
        pickup_minute = total_minutes % 60

        return f"{pickup_hour:02d}:{pickup_minute:02d}"

    except Exception as e:
        logger.error(f"Error calculating pickup time from '{appointment_time}': {e}")
        return appointment_time  # Return original if error

def _record_langfuse_scores(handler, prev_phase: str, result: Dict[str, Any]):
    """Record custom scores in Langfuse after each conversation turn."""
    if not handler:
        return
    try:
        client = get_langfuse_client()
        if not client:
            return

        if not hasattr(handler, "get_trace_id"):
            return
        trace_id = handler.get_trace_id()
        if not trace_id:
            return

        # Score: escalation triggered
        client.score(
            trace_id=trace_id,
            name="escalation_triggered",
            value=1 if result.get("escalation_required") else 0,
        )

        # Score: phase transition occurred
        next_phase = result.get("next_phase") or result.get("current_phase")
        phase_changed = next_phase != prev_phase
        client.score(
            trace_id=trace_id,
            name="phase_transition",
            value=1 if phase_changed else 0,
            comment=f"{prev_phase} -> {next_phase}" if phase_changed else "no change",
        )

        # Score: data extraction count
        extracted = result.get("extracted_data", {})
        if isinstance(extracted, dict):
            extracted_count = len([v for v in extracted.values() if v])
        else:
            extracted_count = 0
        client.score(
            trace_id=trace_id,
            name="data_extraction_count",
            value=extracted_count,
        )

    except Exception as e:
        logger.warning(f"Failed to record Langfuse scores: {e}")


class LangGraphOrchestrator:
    """
    LangGraph-based conversation orchestrator.

    Compatible interface with CallOrchestrator for easy migration.

    Uses LLM-based context building with dynamic policy/case injection.
    """

    def __init__(self, settings=None, store=None, excel_service=None):
        """Initialize orchestrator with compiled graph

        Args:
            settings: Application settings
            store: RedisSessionStore for session persistence (optional)
            excel_service: ExcelOutboundService for outbound calls (optional)
        """
        logger.info("Initializing LangGraph with LLM-based context builder")
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
        Carga la sesión 
        Agrega el mensaje del usuario a la lista de mensaje
        Invoca Langgraph que decide la siguiente fase y genera la respuesta
        actualiza el estado
        guarda el estado en redis o memoria
        devuelve el diccionario
        
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

        prev_phase = state.get("current_phase")
        prev_turn = state.get("turn_count", 0)

        # Build Langfuse handler for observability
        langfuse_tags = [
            call_direction.lower(),
            f"phase:{state.get('current_phase', 'GREETING')}",
        ]
        service_type = state.get("service_type")
        if service_type:
            langfuse_tags.append(f"service:{service_type}")

        langfuse_handler = get_langfuse_handler(
            session_id=session_id,
            user_id=state.get("patient_phone", "unknown"),
            tags=langfuse_tags,
            metadata={
                "agent_name": agent_name,
                "turn_count": state.get("turn_count", 0),
                "call_direction": call_direction,
                "patient_full_name": state.get("patient_full_name", ""),
                "service_type": service_type or "",
            },
            trace_name="conversation_turn",
        )
        invoke_config = {"callbacks": [langfuse_handler]} if langfuse_handler else {}

        # Run graph
        result = self.graph.invoke(state, config=invoke_config)

        # Debug log for phase/turn changes
        try:
            conv_logger.info(
                "LANGGRAPH_STEP",
                extra={
                    "event_type": "langgraph_step",
                    "session_id": session_id,
                    "agent_name": agent_name,
                    "call_direction": call_direction,
                    "prev_phase": prev_phase,
                    "next_phase": result.get('next_phase'),
                    "current_phase": result.get('current_phase'),
                    "prev_turn": prev_turn,
                    "new_turn": result.get('turn_count'),
                    "agent_response_preview": (result.get('agent_response') or "")[:200],
                    "user_message_preview": user_message[:200],
                }
            )
            if result.get('current_phase') == prev_phase and prev_turn == result.get('turn_count'):
                conv_logger.warning(
                    "LANGGRAPH_NO_PROGRESS",
                    extra={
                        "event_type": "langgraph_no_progress",
                        "session_id": session_id,
                        "phase": prev_phase,
                        "user_message": user_message[:200],
                    }
                )
        except Exception as e:
            conv_logger.warning(f"Could not log langgraph step: {e}")
        
        # Add agent response to messages
        agent_response = result.get('agent_response', '')
        if agent_response:
            result['messages'].append(AIMessage(content=agent_response))
        
        # Update session
        self._sessions[session_id] = result

        # Langfuse scoring
        _record_langfuse_scores(
            langfuse_handler, prev_phase, result
        )

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
        excel_row_index: int = None,
        patient_phone: str | None = None
    ) -> str:
        """Create a new session and (for outbound) preload data from Excel if available
            Genera un ID unico con uuid4.hex
            Busca los datos del paciente en un excel
            crea un objeto conversaciónstate con el id, telefono y los demas datos
            asocia el numero de telefono a la sesión
            devuelve un id
        
        
        """
        session_id = str(uuid.uuid4())

        state = create_initial_state(
            session_id=session_id,
            call_direction=call_direction,
            agent_name=agent_name,
            excel_row_index=excel_row_index
        )

        # Preload outbound data from Excel to personalize greeting
        if call_direction == "OUTBOUND" and self.excel_service and patient_phone:
            try:
                patient_data = self.excel_service.get_patient_by_phone(patient_phone)
                if patient_data:
                    state["patient_full_name"] = patient_data.nombre_completo
                    state["document_type"] = patient_data.tipo_documento
                    state["document_number"] = patient_data.numero_documento
                    state["eps"] = patient_data.eps
                    state["phone"] = patient_data.telefono
                    state["service_type"] = patient_data.tipo_servicio
                    state["appointment_date"] = patient_data.fecha_servicio
                    state["appointment_time"] = patient_data.hora_servicio
                    state["pickup_address"] = patient_data.direccion_completa
                    # Track excel row to update status later
                    state["excel_row_index"] = patient_data.row_index
                    # Calculate pickup_time (1 hour before appointment)
                    if patient_data.hora_servicio:
                        pickup_time = _calculate_pickup_time(patient_data.hora_servicio)
                        state["pickup_time"] = pickup_time
                        logger.info(f"Calculated pickup_time: {pickup_time} (appointment: {patient_data.hora_servicio})")
            except Exception as e:
                logger.warning(f"Could not preload outbound data from Excel: {e}")

        if patient_phone:
            # Maintain phone on state for lookups
            state["patient_phone"] = patient_phone
            state["phone"] = patient_phone

        self._sessions[session_id] = state

        return session_id

    async def find_session_by_phone(self, patient_phone: str) -> Optional[str]:
        """Find session ID by patient phone number using in-memory map (and log lookup)."""
        # Fallback to in-memory mapping (even if Redis exists, this is our only index right now)
        if not hasattr(self, '_phone_to_session'):
            self._phone_to_session = {}
        session_key = f"phone:{patient_phone}"

        # Try phone->session map
        mapped = self._phone_to_session.get(session_key)
        if mapped:
            conv_logger.info(
                "SESSION_LOOKUP_HIT",
                extra={
                    "event_type": "session_lookup",
                    "patient_phone": patient_phone,
                    "session_id": mapped,
                    "source": "phone_map",
                }
            )
            return mapped

        # Try current in-memory sessions
        try:
            for session_id in list(self._sessions.keys()):
                session_data = self._sessions.get(session_id, {})
                if session_data.get("patient_phone") == patient_phone:
                    conv_logger.info(
                        "SESSION_LOOKUP_HIT",
                        extra={
                            "event_type": "session_lookup",
                            "patient_phone": patient_phone,
                            "session_id": session_id,
                            "source": "in_memory_sessions",
                        }
                    )
                    return session_id
        except Exception as e:
            conv_logger.warning(f"Error finding session by phone: {e}")

        conv_logger.info(
            "SESSION_LOOKUP_MISS",
            extra={
                "event_type": "session_lookup",
                "patient_phone": patient_phone,
                "session_id": None,
                "source": "miss",
            }
        )
        return None

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
        print(f"\n{'▼'*80}")
        print(f"🎬 [ORCHESTRATOR] PROCESANDO MENSAJE")
        print(f"{'▼'*80}")
        logger.info(f"[ORCHESTRATOR] patient_phone={patient_phone}")
        logger.info(f"[ORCHESTRATOR] user_message='{user_message[:100]}...'")
        logger.info(f"[ORCHESTRATOR] is_outbound={is_outbound}")

        session_id = None
        session_created = False

        # Try to find existing session by phone
        print(f"🔍 [ORCHESTRATOR] Buscando sesión existente para {patient_phone}...")
        session_id = await self.find_session_by_phone(patient_phone)

        if not session_id:
            excel_row_index = None
            # If outbound and Excel service available, preload row index for mapping
            if is_outbound and self.excel_service:
                try:
                    patient_data = self.excel_service.get_patient_by_phone(patient_phone)
                    if patient_data:
                        excel_row_index = patient_data.row_index
                except Exception as e:
                    logger.warning(f"Error loading patient from Excel: {e}")

            # Create new session
            session_id = self.create_session(
                call_direction="OUTBOUND" if is_outbound else "INBOUND",
                agent_name=agent_name or (self.settings.AGENT_NAME if self.settings else "María"),
                excel_row_index=excel_row_index,
                patient_phone=patient_phone
            )
            session_created = True
            print(f"✨ [ORCHESTRATOR] Nueva sesión creada: {session_id}")
            # Track phone -> session_id mapping
            if not hasattr(self, '_phone_to_session'):
                self._phone_to_session = {}
            self._phone_to_session[f"phone:{patient_phone}"] = session_id
            conv_logger.info(
                "SESSION_CREATED",
                extra={
                    "event_type": "session_created",
                    "session_id": session_id,
                    "patient_phone": patient_phone,
                    "call_direction": "OUTBOUND" if is_outbound else "INBOUND",
                    "excel_row_index": excel_row_index,
                }
            )
        else:
            print(f"♻️  [ORCHESTRATOR] Sesión existente reutilizada: {session_id}")
            conv_logger.info(
                "SESSION_REUSED",
                extra={
                    "event_type": "session_reused",
                    "session_id": session_id,
                    "patient_phone": patient_phone,
                    "call_direction": "OUTBOUND" if is_outbound else "INBOUND",
                }
            )

        # Get current state
        state = self._sessions.get(session_id)
        if not state:
            # Load from Redis if available
            if self.store:
                try:
                    import asyncio
                    state = await self.store.get(session_id)
                    if state:
                        self._sessions[session_id] = state
                    else:
                        # Shouldn't happen if session_id was found, but create fallback
                        state = create_initial_state(
                            session_id=session_id,
                            call_direction="OUTBOUND" if is_outbound else "INBOUND",
                            agent_name=agent_name or (self.settings.AGENT_NAME if self.settings else "María")
                        )
                        self._sessions[session_id] = state
                except Exception as e:
                    logger.error(f"Error loading session from Redis: {e}")
                    state = self._sessions.get(session_id)
        else:
            state = self._sessions.get(session_id)

        # Store phone in state
        state["patient_phone"] = patient_phone
        # Keep legacy phone field aligned
        if not state.get("phone"):
            state["phone"] = patient_phone
        # Log current session summary
        conv_logger.info(
            "SESSION_STATE",
            extra={
                "event_type": "session_state",
                "session_id": session_id,
                "patient_phone": patient_phone,
                "current_phase": state.get("current_phase"),
                "turn_count": state.get("turn_count"),
                "has_messages": len(state.get("messages", [])),
            }
        )

        # Process the message
        turn_count = state.get('turn_count', 0)
        processed_message = user_message

        # SHORT-CIRCUIT: First outbound turn has a scripted greeting (skip LLM entirely)
        if is_outbound and turn_count == 0 and user_message.upper() in ["START", "INICIO", "COMENZAR", "/START"]:
            patient_name = state.get("patient_full_name", "")
            scripted_response = f"\u00bfTengo el gusto de hablar con {patient_name}?" if patient_name else "\u00bfTengo el gusto de hablar con el paciente?"
            print(f"\n\u26a1 [ORCHESTRATOR] SHORT-CIRCUIT: Primer turno outbound (sin LLM)")
            print(f"   Respuesta directa: '{scripted_response}'")
            logger.info(f"[ORCHESTRATOR] Short-circuit first outbound turn (no LLM call)")

            # Update state manually (same as LangGraph would)
            state['messages'].append(HumanMessage(content="/START"))
            state['messages'].append(AIMessage(content=scripted_response))
            state['turn_count'] = 1
            state['extracted_data'] = {"patient_full_name": patient_name} if patient_name else {}
            self._sessions[session_id] = state

            response = {
                'agent_response': scripted_response,
                'next_phase': 'OUTBOUND_GREETING',
                'current_phase': 'OUTBOUND_GREETING',
                'session_id': session_id,
                'escalation_required': False,
                'escalation_reasons': [],
                'policy_violations': [],
                'state': state_to_dict(state),
            }
        else:
            print(f"\n\U0001F680 [ORCHESTRATOR] Ejecutando LangGraph...")
            print(f"   Session: {session_id[:8]}")
            print(f"   Fase actual: {state.get('current_phase', 'GREETING')}")
            print(f"   Turno: {turn_count}")
            logger.info(f"[ORCHESTRATOR] Procesando mensaje para session_id={session_id[:8] if session_id else 'None'}...")
            try:
                response = await self.process_message(
                    session_id=session_id,
                    user_message=processed_message,
                    call_direction="OUTBOUND" if is_outbound else "INBOUND",
                    agent_name=agent_name or (self.settings.AGENT_NAME if self.settings else "Mar\u00eda")
                )
                print(f"\u2705 [ORCHESTRATOR] LangGraph completado")
                logger.info(f"[ORCHESTRATOR] Mensaje procesado exitosamente")
            except Exception as e:
                logger.error(f"[ORCHESTRATOR] ERROR en process_message: {e}", exc_info=True)
                flush_langfuse()
                raise

        # Save updated state to Redis if store is available
        if self.store:
            try:
                import asyncio
                updated_state = self._sessions.get(session_id, {})
                # Clean state for Redis (remove non-serializable objects)
                clean_state = {k: v for k, v in updated_state.items()
                              if k not in ['messages'] and not callable(v)}
                # Add messages back as dicts
                if 'messages' in updated_state:
                    clean_state['messages'] = [
                        {'role': 'user' if hasattr(m, 'type') and m.type == 'human' else 'assistant',
                         'content': m.content if hasattr(m, 'content') else str(m)}
                        for m in updated_state.get('messages', [])
                    ]
                await self.store.set(session_id, clean_state)
                logger.info(f"Session {session_id[:8]}... saved to Redis")
            except Exception as e:
                logger.error(f"Error saving session to Redis: {e}")

        # Add session management info
        response["session_created"] = session_created
        response["conversation_phase"] = response.get("current_phase")
        response["call_direction"] = "OUTBOUND" if is_outbound else "INBOUND"
        response["requires_escalation"] = response.get("escalation_required", False)
        response["metadata"] = {}

        # Flush Langfuse events before returning response
        flush_langfuse()

        return response
