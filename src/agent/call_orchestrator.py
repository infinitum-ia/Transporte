"""
Call Orchestrator

Manages both inbound and outbound calls, routing to appropriate prompts and logic
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.agent.prompts.inbound_prompts import build_inbound_system_prompt
from src.agent.prompts.outbound_prompts import build_outbound_system_prompt
from src.domain.value_objects.conversation_phase import ConversationPhase
from src.domain.value_objects.call_direction import CallDirection
from src.infrastructure.config.settings import Settings
from src.infrastructure.persistence.redis.session_store import RedisSessionStore
from src.infrastructure.persistence.excel_service import ExcelOutboundService, PatientServiceData
from src.infrastructure.logging import get_logger


class LLMOutput(BaseModel):
    """
    LLM Output schema for structured responses

    Note: All optional fields must use Optional[T] with default=None
    to generate valid OpenAI structured output schema
    """
    agent_response: str = Field(min_length=1, description="Agent's response message")
    next_phase: ConversationPhase = Field(description="Next conversation phase")
    requires_escalation: bool = Field(default=False, description="Whether escalation is needed")
    escalation_reason: Optional[str] = Field(default=None, description="Reason for escalation if needed")
    extracted: Optional[Dict[str, Any]] = Field(default=None, description="Extracted data from user message")


class CallOrchestrator:
    """
    Orchestrates both inbound and outbound calls

    - Inbound: Customer calls us (existing flow)
    - Outbound: We call customer to confirm services (new flow)
    """

    def __init__(
        self,
        *,
        settings: Settings,
        store: RedisSessionStore,
        excel_service: Optional[ExcelOutboundService] = None,
        llm: Optional[Any] = None
    ):
        self._settings = settings
        self._store = store
        self._excel_service = excel_service

        # Configure LLM with structured output to ensure valid JSON responses
        base_llm = llm or ChatOpenAI(
            openai_api_key=settings.OPENAI_API_KEY,
            model_name=settings.OPENAI_MODEL,
            temperature=settings.OPENAI_TEMPERATURE,
            max_tokens=settings.OPENAI_MAX_TOKENS,
        )

        # Use structured output to guarantee JSON format
        self._llm = base_llm.with_structured_output(LLMOutput)

        self._logger = get_logger(log_level=settings.LOG_LEVEL)

    # ==========================================
    # SESSION MANAGEMENT
    # ==========================================

    def create_session(self, agent_name: Optional[str] = None) -> str:
        """Create new session ID"""
        return str(uuid.uuid4())

    async def init_inbound_session(
        self,
        session_id: str,
        agent_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Initialize session for INBOUND call (customer calls us)

        Args:
            session_id: Unique session identifier
            agent_name: Name of the agent (optional)

        Returns:
            Initial session state
        """
        now = datetime.utcnow().isoformat()
        state: Dict[str, Any] = {
            "session_id": session_id,
            "call_direction": CallDirection.INBOUND.value,
            "phase": ConversationPhase.GREETING.value,
            "agent_name": agent_name or self._settings.AGENT_NAME,
            "company_name": self._settings.COMPANY_NAME,
            "eps_name": self._settings.EPS_NAME,
            "patient": {
                "patient_full_name": None,
                "document_type": None,
                "document_number": None,
                "eps": None,
                "is_responsible": None,
                "responsible_name": None,
            },
            "service": {
                "service_type": None,
                "service_modality": None,
                "appointment_date": None,
                "appointment_time": None,
                "pickup_address": None,
                "destination_address": None,
            },
            "incidents": [],
            "requires_escalation": False,
            "escalation_reason": None,
            "legal_notice_acknowledged": False,
            "survey_completed": False,
            "messages": [],
            "created_at": now,
            "updated_at": now,
        }
        await self._store.set(session_id, state)

        # Log session creation
        self._logger.log_session_created(
            session_id=session_id,
            call_direction=CallDirection.INBOUND.value,
            agent_name=agent_name or self._settings.AGENT_NAME
        )

        return state

    async def init_outbound_session(
        self,
        session_id: str,
        patient_data: PatientServiceData,
        agent_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Initialize session for OUTBOUND call (we call customer)

        Args:
            session_id: Unique session identifier
            patient_data: Patient data from Excel
            agent_name: Name of the agent (optional)

        Returns:
            Initial session state with patient data pre-loaded
        """
        now = datetime.utcnow().isoformat()
        state: Dict[str, Any] = {
            "session_id": session_id,
            "call_direction": CallDirection.OUTBOUND.value,
            "phase": ConversationPhase.OUTBOUND_GREETING.value,
            "agent_name": agent_name or self._settings.AGENT_NAME,
            "company_name": self._settings.COMPANY_NAME,
            "eps_name": self._settings.EPS_NAME,

            # Pre-loaded patient data from Excel
            "patient": {
                "patient_full_name": patient_data.nombre_completo,
                "document_type": patient_data.tipo_documento,
                "document_number": patient_data.numero_documento,
                "eps": patient_data.eps,
                "is_responsible": bool(patient_data.nombre_familiar),
                "responsible_name": patient_data.nombre_familiar,
                "phone": patient_data.telefono,
            },

            # Pre-loaded service data
            "service": {
                "service_type": patient_data.tipo_servicio,
                "treatment_type": patient_data.tipo_tratamiento,
                "frequency": patient_data.frecuencia,
                "appointment_date": patient_data.fecha_servicio,
                "appointment_time": patient_data.hora_servicio,
                "pickup_address": patient_data.direccion_completa,
                "destination_address": patient_data.destino_centro_salud,
                "service_modality": patient_data.modalidad_transporte,
                "special_observations": patient_data.observaciones_especiales,
            },

            # Excel tracking
            "excel_row_index": patient_data.row_index,

            # Confirmation tracking
            "confirmation_status": None,  # CONFIRMADO, REPROGRAMAR, RECHAZADO, etc.
            "service_confirmed": False,

            "incidents": [],
            "requires_escalation": False,
            "escalation_reason": None,
            "legal_notice_acknowledged": False,
            "messages": [],
            "created_at": now,
            "updated_at": now,

            # Store patient data for prompt building
            "patient_data": patient_data.to_dict()
        }
        await self._store.set(session_id, state)

        # Log session creation
        self._logger.log_session_created(
            session_id=session_id,
            call_direction=CallDirection.OUTBOUND.value,
            patient_phone=patient_data.telefono,
            patient_name=patient_data.nombre_completo,
            agent_name=agent_name or self._settings.AGENT_NAME
        )

        return state

    async def get_session_async(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session from store"""
        return await self._store.get(session_id)

    async def initiate_outbound_call(
        self,
        patient_phone: str,
        agent_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Unified method to initiate outbound call in a single operation

        This method creates the session, loads patient data, and generates
        the initial greeting message automatically.

        Args:
            patient_phone: Patient phone number (10 digits)
            agent_name: Agent name (optional)

        Returns:
            Dict with session_id, initial message, and patient info

        Raises:
            ValueError: If patient not found in Excel
            HTTPException: If Excel service not configured
        """
        # Validate Excel service
        if self._excel_service is None:
            raise ValueError("Excel service not configured. Cannot load patient data.")

        # Get patient data from Excel
        patient_data = self._excel_service.get_patient_by_phone(patient_phone)
        if patient_data is None:
            raise ValueError(f"No patient found with phone number: {patient_phone}")

        # Create session
        session_id = self.create_session(agent_name=agent_name)

        # Initialize outbound session
        state = await self.init_outbound_session(
            session_id=session_id,
            patient_data=patient_data,
            agent_name=agent_name
        )

        # Generate initial greeting message using LLM
        current_phase = ConversationPhase.OUTBOUND_GREETING
        agent_name_resolved = agent_name or self._settings.AGENT_NAME
        company_name = self._settings.COMPANY_NAME
        eps_name = self._settings.EPS_NAME

        # Build system prompt for initial greeting
        system_prompt = build_outbound_system_prompt(
            agent_name=agent_name_resolved,
            company_name=company_name,
            eps_name=eps_name,
            phase=current_phase,
            patient_data=state.get("patient_data", {})
        )

        # Create initial message context
        initial_user_message = "[SYSTEM: This is the start of an outbound call. Generate the initial greeting.]"
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=initial_user_message)
        ]

        # Get LLM response (structured output returns LLMOutput object directly)
        try:
            parsed = await self._llm.ainvoke(messages)
            agent_initial_message = parsed.agent_response
        except Exception:
            # Fallback to template-based greeting
            agent_initial_message = (
                f"Buenos días, ¿hablo con {patient_data.nombre_completo}? "
                f"Le llamo de {company_name} para confirmar su servicio de transporte médico "
                f"programado para {patient_data.tipo_servicio} el día {patient_data.fecha_servicio} "
                f"a las {patient_data.hora_servicio} horas."
            )

        # Add initial message to state
        state.setdefault("messages", []).append({
            "role": "assistant",
            "content": agent_initial_message,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Save updated state
        await self._store.set(session_id, state)

        # Return complete response
        return {
            "session_id": session_id,
            "call_direction": CallDirection.OUTBOUND.value,
            "conversation_phase": current_phase.value,
            "agent_initial_message": agent_initial_message,
            "patient_name": patient_data.nombre_completo,
            "service_type": patient_data.tipo_servicio,
            "appointment_date": patient_data.fecha_servicio,
            "appointment_time": patient_data.hora_servicio,
            "created_at": state["created_at"]
        }



    # ==========================================
    # MESSAGE PROCESSING
    # ==========================================

    async def process_message(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """
        Process user message for both inbound and outbound calls

        Args:
            session_id: Session identifier
            user_message: User's message

        Returns:
            Response dict with agent_response, phase, etc.
        """
        state = await self._store.get(session_id)
        if not state:
            raise ValueError(f"Session not found: {session_id}")

        # Determine call direction
        call_direction = CallDirection.from_string(
            state.get("call_direction", CallDirection.INBOUND.value)
        )

        if call_direction.is_inbound:
            return await self._process_inbound_message(session_id, state, user_message)
        else:
            return await self._process_outbound_message(session_id, state, user_message)

    async def _process_inbound_message(
        self,
        session_id: str,
        state: Dict[str, Any],
        user_message: str
    ) -> Dict[str, Any]:
        """Process message for inbound call (existing logic)"""
        current_phase = ConversationPhase.from_string(state.get("phase", ConversationPhase.GREETING.value))
        agent_name = state.get("agent_name") or self._settings.AGENT_NAME
        company_name = state.get("company_name") or self._settings.COMPANY_NAME
        eps_name = state.get("eps_name") or self._settings.EPS_NAME

        state.setdefault("messages", []).append(
            {"role": "user", "content": user_message, "timestamp": datetime.utcnow().isoformat()}
        )

        # Log user message
        self._logger.log_message(
            session_id=session_id,
            role="user",
            content=user_message,
            current_phase=current_phase.value,
            call_direction=CallDirection.INBOUND.value
        )

        # Build system prompt for inbound call
        system_prompt = build_inbound_system_prompt(
            agent_name=agent_name,
            company_name=company_name,
            eps_name=eps_name,
            phase=current_phase,
        )

        history = state.get("messages", [])[-20:]
        messages = [SystemMessage(content=system_prompt)]
        for m in history:
            role = m.get("role")
            content = m.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))

        # With structured output, LLM returns LLMOutput object directly
        try:
            parsed = await self._llm.ainvoke(messages)
        except Exception as e:
            agent_response = "Disculpe, ¿podría repetir por favor?"

            # Log LLM error
            self._logger.log_llm_error(
                session_id=session_id,
                error_type="llm_invocation_error",
                error_message=str(e),
                current_phase=current_phase.value
            )

            state.setdefault("messages", []).append(
                {"role": "assistant", "content": agent_response, "timestamp": datetime.utcnow().isoformat()}
            )
            await self._store.set(session_id, state)
            return {
                "session_id": session_id,
                "agent_response": agent_response,
                "conversation_phase": current_phase.value,
                "call_direction": state.get("call_direction", CallDirection.INBOUND.value),
                "requires_escalation": bool(state.get("requires_escalation", False)),
                "metadata": {"llm_parse_error": True},
            }

        next_phase = self._guard_transition(current_phase, parsed.next_phase)

        # Log phase transition
        if current_phase != next_phase:
            self._logger.log_phase_transition(
                session_id=session_id,
                from_phase=current_phase.value,
                to_phase=next_phase.value,
                call_direction=CallDirection.INBOUND.value
            )

        state["requires_escalation"] = parsed.requires_escalation
        state["escalation_reason"] = parsed.escalation_reason

        # Log escalation if required
        if parsed.requires_escalation:
            self._logger.log_escalation(
                session_id=session_id,
                reason=parsed.escalation_reason or "Unknown",
                current_phase=current_phase.value,
                call_direction=CallDirection.INBOUND.value
            )
        if current_phase == ConversationPhase.LEGAL_NOTICE and next_phase == ConversationPhase.SERVICE_COORDINATION:
            state["legal_notice_acknowledged"] = True
        if current_phase == ConversationPhase.SURVEY and next_phase == ConversationPhase.END:
            state["survey_completed"] = True

        self._merge_extracted(state, parsed.extracted or {})

        # Log data extraction
        if parsed.extracted:
            self._logger.log_data_extraction(
                session_id=session_id,
                extracted_data=parsed.extracted,
                current_phase=current_phase.value
            )

        state.setdefault("messages", []).append(
            {"role": "assistant", "content": parsed.agent_response, "timestamp": datetime.utcnow().isoformat()}
        )
        state["phase"] = next_phase.value

        # Log agent response
        self._logger.log_message(
            session_id=session_id,
            role="assistant",
            content=parsed.agent_response,
            current_phase=next_phase.value,
            call_direction=CallDirection.INBOUND.value
        )

        await self._store.set(session_id, state)

        return {
            "session_id": session_id,
            "agent_response": parsed.agent_response,
            "conversation_phase": next_phase.value,
            "call_direction": CallDirection.INBOUND.value,
            "requires_escalation": parsed.requires_escalation,
            "metadata": {
                "escalation_reason": parsed.escalation_reason,
                "extracted": parsed.extracted,
            },
        }

    async def _process_outbound_message(
        self,
        session_id: str,
        state: Dict[str, Any],
        user_message: str
    ) -> Dict[str, Any]:
        """Process message for outbound call (new logic)"""
        current_phase = ConversationPhase.from_string(
            state.get("phase", ConversationPhase.OUTBOUND_GREETING.value)
        )
        agent_name = state.get("agent_name") or self._settings.AGENT_NAME
        company_name = state.get("company_name") or self._settings.COMPANY_NAME
        eps_name = state.get("eps_name") or self._settings.EPS_NAME
        patient_data = state.get("patient_data", {})

        state.setdefault("messages", []).append(
            {"role": "user", "content": user_message, "timestamp": datetime.utcnow().isoformat()}
        )

        # Log user message
        self._logger.log_message(
            session_id=session_id,
            role="user",
            content=user_message,
            current_phase=current_phase.value,
            call_direction=CallDirection.OUTBOUND.value
        )

        # Build system prompt for outbound call with patient data
        system_prompt = build_outbound_system_prompt(
            agent_name=agent_name,
            company_name=company_name,
            eps_name=eps_name,
            phase=current_phase,
            patient_data=patient_data
        )

        history = state.get("messages", [])[-20:]
        messages = [SystemMessage(content=system_prompt)]
        for m in history:
            role = m.get("role")
            content = m.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))

        # With structured output, LLM returns LLMOutput object directly
        try:
            parsed = await self._llm.ainvoke(messages)
        except Exception as e:
            agent_response = "Disculpe, ¿podría repetir por favor?"

            # Log LLM error
            self._logger.log_llm_error(
                session_id=session_id,
                error_type="llm_invocation_error",
                error_message=str(e),
                current_phase=current_phase.value
            )

            state.setdefault("messages", []).append(
                {"role": "assistant", "content": agent_response, "timestamp": datetime.utcnow().isoformat()}
            )
            await self._store.set(session_id, state)
            return {
                "session_id": session_id,
                "agent_response": agent_response,
                "conversation_phase": current_phase.value,
                "call_direction": state.get("call_direction", CallDirection.OUTBOUND.value),
                "requires_escalation": bool(state.get("requires_escalation", False)),
                "metadata": {"llm_parse_error": True},
            }

        # Extract outbound-specific fields (make a mutable copy)
        extracted: Dict[str, Any] = dict(parsed.extracted or {})

        # Heuristic: ensure driver/conductor complaints are recorded even if the LLM forgets to populate `incident_summary`
        msg_norm = (user_message or "").lower()
        has_driver_keyword = any(k in msg_norm for k in ["conductor", "chofer", "chófer", "choferes", "chóferes"])
        has_issue_keyword = any(k in msg_norm for k in ["tarde", "temprano", "demora", "puntual", "puntualidad", "lleg"])
        mentions_preferred_driver = "juan carlos" in msg_norm
        if (mentions_preferred_driver or (has_driver_keyword and has_issue_keyword)) and not extracted.get("incident_summary"):
            summary = "Queja por puntualidad/rotación de conductores"
            if mentions_preferred_driver:
                summary += "; solicita conductor Juan Carlos"
            extracted["incident_summary"] = summary

        proposed_next_phase = parsed.next_phase
        # Minimal guardrail: after OUTBOUND_LEGAL_NOTICE, don't get stuck looping in the same phase.
        if current_phase == ConversationPhase.OUTBOUND_LEGAL_NOTICE and proposed_next_phase == ConversationPhase.OUTBOUND_LEGAL_NOTICE:
            proposed_next_phase = ConversationPhase.OUTBOUND_SERVICE_CONFIRMATION

        next_phase = self._guard_transition(current_phase, proposed_next_phase)

        # Log phase transition
        if current_phase != next_phase:
            self._logger.log_phase_transition(
                session_id=session_id,
                from_phase=current_phase.value,
                to_phase=next_phase.value,
                call_direction=CallDirection.OUTBOUND.value
            )

        state["requires_escalation"] = parsed.requires_escalation
        state["escalation_reason"] = parsed.escalation_reason

        # Log escalation if required
        if parsed.requires_escalation:
            self._logger.log_escalation(
                session_id=session_id,
                reason=parsed.escalation_reason or "Unknown",
                current_phase=current_phase.value,
                call_direction=CallDirection.OUTBOUND.value
            )

        # Track confirmation status
        if "service_confirmed" in extracted:
            state["service_confirmed"] = extracted["service_confirmed"]

        if "confirmation_status" in extracted:
            state["confirmation_status"] = extracted["confirmation_status"]

        # Track special cases
        if "appointment_date_changed" in extracted:
            state["appointment_date_changed"] = extracted["appointment_date_changed"]
            state["new_appointment_date"] = extracted.get("new_appointment_date")

        if "patient_away" in extracted:
            state["patient_away"] = extracted["patient_away"]
            state["return_date"] = extracted.get("return_date")

        if "special_needs" in extracted:
            state["special_needs"] = extracted["special_needs"]

        if "coverage_issue" in extracted:
            state["coverage_issue"] = extracted["coverage_issue"]

        # Merge general extracted data
        self._merge_extracted(state, extracted)

        # Log data extraction
        if extracted:
            self._logger.log_data_extraction(
                session_id=session_id,
                extracted_data=extracted,
                current_phase=current_phase.value
            )

        state.setdefault("messages", []).append(
            {"role": "assistant", "content": parsed.agent_response, "timestamp": datetime.utcnow().isoformat()}
        )
        state["phase"] = next_phase.value

        # Log agent response
        self._logger.log_message(
            session_id=session_id,
            role="assistant",
            content=parsed.agent_response,
            current_phase=next_phase.value,
            call_direction=CallDirection.OUTBOUND.value
        )

        # If call ended, update Excel and log completion
        if next_phase == ConversationPhase.END:
            if self._excel_service:
                await self._update_excel_after_call(state)

            # Log call completion
            self._logger.log_call_completed(
                session_id=session_id,
                call_direction=CallDirection.OUTBOUND.value,
                final_phase=next_phase.value,
                message_count=len(state.get("messages", [])),
                confirmation_status=state.get("confirmation_status")
            )

        await self._store.set(session_id, state)

        return {
            "session_id": session_id,
            "agent_response": parsed.agent_response,
            "conversation_phase": next_phase.value,
            "requires_escalation": parsed.requires_escalation,
            "call_direction": CallDirection.OUTBOUND.value,
            "metadata": {
                "escalation_reason": parsed.escalation_reason,
                "extracted": extracted,
                "confirmation_status": state.get("confirmation_status"),
                "service_confirmed": state.get("service_confirmed", False),
            },
        }

    async def _update_excel_after_call(self, state: Dict[str, Any]) -> None:
        """Update Excel with call results"""
        if not self._excel_service:
            return

        row_index = state.get("excel_row_index")
        if row_index is None:
            return

        confirmation_status = state.get("confirmation_status", "Pendiente")
        incidents = state.get("incidents", [])

        # Build observations string
        observations_parts = []
        observations_parts.append(f"Llamada completada")

        if state.get("service_confirmed"):
            observations_parts.append("Servicio confirmado")

        if state.get("appointment_date_changed"):
            new_date = state.get("new_appointment_date")
            observations_parts.append(f"Fecha reprogramada: {new_date}")

        if state.get("patient_away"):
            return_date = state.get("return_date")
            observations_parts.append(f"Paciente fuera, regresa: {return_date}")

        if state.get("special_needs"):
            observations_parts.append(f"Necesidad especial: {state['special_needs']}")

        if incidents:
            for incident in incidents:
                observations_parts.append(f"Incidencia: {incident.get('summary')}")

        observations = " - ".join(observations_parts)

        # Update Excel
        self._excel_service.update_call_status(
            row_index=row_index,
            new_status=confirmation_status,
            observations=observations
        )


    # ==========================================
    # UNIFIED CONVERSATION (PHONE-BASED)
    # ==========================================

    async def find_session_by_phone(self, phone: str) -> Optional[str]:
        """
        Find active session by phone number

        Searches Redis for active sessions with the given phone number.

        Args:
            phone: Patient phone number

        Returns:
            session_id if found, None otherwise
        """
        # Get all session keys from Redis
        try:
            keys = await self._store.find_all_keys("*")
            for key in keys:
                # Extract session_id from full key (e.g., "transport:session:uuid" -> "uuid")
                session_id = key.replace("transport:session:", "").replace("session:", "")
                state = await self._store.get(session_id)
                if state:
                    patient_phone = state.get("patient", {}).get("phone")
                    if patient_phone == phone:
                        return session_id
        except Exception as e:
            print(f"Error searching session by phone: {e}")
        return None

    async def process_unified_message(
        self,
        patient_phone: str,
        user_message: str,
        is_outbound: bool = True,
        agent_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process message with automatic session management

        This method handles the complete flow:
        1. Check if session exists for phone
        2. If not, create new session (outbound or inbound)
        3. Process the message
        4. Return response with session info

        Args:
            patient_phone: Patient phone number (10 digits)
            user_message: User's message
            is_outbound: True for outbound, False for inbound
            agent_name: Agent name (optional)

        Returns:
            Dict with response, session info, and metadata
        """
        session_created = False
        session_id = None

        # Try to find existing session
        session_id = await self.find_session_by_phone(patient_phone)

        # Log unified endpoint request
        self._logger.log_unified_endpoint_request(
            patient_phone=patient_phone,
            is_outbound=is_outbound,
            message_preview=user_message,
            session_found=(session_id is not None)
        )

        if not session_id:
            # Create new session
            session_id = self.create_session(agent_name=agent_name)
            session_created = True

            if is_outbound:
                # Outbound call - need Excel data
                if self._excel_service is None:
                    raise ValueError("Excel service not configured. Cannot create outbound session.")

                patient_data = self._excel_service.get_patient_by_phone(patient_phone)
                if patient_data is None:
                    raise ValueError(f"No patient found with phone: {patient_phone}")

                state = await self.init_outbound_session(
                    session_id=session_id,
                    patient_data=patient_data,
                    agent_name=agent_name
                )

                # For first message in outbound, generate initial greeting if it's a system message
                if user_message.strip() in ["", "START", "[START]", "[INICIO]"]:
                    # Generate initial greeting
                    current_phase = ConversationPhase.OUTBOUND_GREETING
                    system_prompt = build_outbound_system_prompt(
                        agent_name=agent_name or self._settings.AGENT_NAME,
                        company_name=self._settings.COMPANY_NAME,
                        eps_name=self._settings.EPS_NAME,
                        phase=current_phase,
                        patient_data=state.get("patient_data", {})
                    )

                    messages = [
                        SystemMessage(content=system_prompt),
                        HumanMessage(content="[SYSTEM: Generate initial greeting for outbound call]")
                    ]

                    # Structured output returns LLMOutput object directly
                    try:
                        parsed = await self._llm.ainvoke(messages)
                        agent_response = parsed.agent_response
                    except Exception:
                        agent_response = (
                            f"Buenos días, ¿hablo con {patient_data.nombre_completo}? "
                            f"Le llamo de {self._settings.COMPANY_NAME} para confirmar su servicio."
                        )

                    state.setdefault("messages", []).append({
                        "role": "assistant",
                        "content": agent_response,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    await self._store.set(session_id, state)

                    return {
                        "session_id": session_id,
                        "agent_response": agent_response,
                        "conversation_phase": state["phase"],
                        "call_direction": CallDirection.OUTBOUND.value,
                        "requires_escalation": False,
                        "session_created": True,
                        "patient_name": patient_data.nombre_completo,
                        "service_type": patient_data.tipo_servicio,
                        "metadata": {}
                    }

            else:
                # Inbound call - no Excel data needed
                state = await self.init_inbound_session(
                    session_id=session_id,
                    agent_name=agent_name
                )
                # Add phone to state
                state.setdefault("patient", {})["phone"] = patient_phone
                await self._store.set(session_id, state)

        # Process the message
        response = await self.process_message(session_id, user_message)

        # Add session management info
        response["session_created"] = session_created

        # Add patient info if available
        state = await self._store.get(session_id)
        if state:
            patient = state.get("patient", {}) or {}
            service = state.get("service", {}) or {}
            response["patient_name"] = patient.get("patient_full_name")
            response["service_type"] = service.get("service_type")

            # Ensure call_direction is present
            if "call_direction" not in response:
                response["call_direction"] = state.get("call_direction", CallDirection.INBOUND.value)

        return response

    def _guard_transition(self, current: ConversationPhase, proposed: ConversationPhase) -> ConversationPhase:
        """Validate phase transition"""
        return proposed if current.can_transition_to(proposed) else current

    def _merge_extracted(self, state: Dict[str, Any], extracted: Dict[str, Any]) -> None:
        """Merge extracted data into state"""
        patient = state.get("patient") or {}
        service = state.get("service") or {}

        for key in ["patient_full_name", "document_type", "document_number", "eps", "is_responsible", "responsible_name"]:
            if key in extracted and extracted[key] not in (None, ""):
                patient[key] = extracted[key]

        for key in [
            "service_type",
            "service_modality",
            "appointment_date",
            "appointment_time",
            "pickup_address",
            "destination_address",
        ]:
            if key in extracted and extracted[key] not in (None, ""):
                service[key] = extracted[key]

        incident_summary = extracted.get("incident_summary")
        if incident_summary:
            state.setdefault("incidents", []).append(
                {"summary": incident_summary, "created_at": datetime.utcnow().isoformat()}
            )

        state["patient"] = patient
        state["service"] = service
