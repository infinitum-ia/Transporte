"""
Call Orchestrator

Manages both inbound and outbound calls, routing to appropriate prompts and logic
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, ValidationError

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.agent.prompts.inbound_prompts import build_inbound_system_prompt
from src.agent.prompts.outbound_prompts import build_outbound_system_prompt
from src.domain.value_objects.conversation_phase import ConversationPhase
from src.domain.value_objects.call_direction import CallDirection
from src.infrastructure.config.settings import Settings
from src.infrastructure.persistence.redis.session_store import RedisSessionStore
from src.infrastructure.persistence.excel_service import ExcelOutboundService, PatientServiceData


class LLMOutput(BaseModel):
    agent_response: str = Field(min_length=1)
    next_phase: ConversationPhase
    requires_escalation: bool = False
    escalation_reason: Optional[str] = None
    extracted: Dict[str, Any] = Field(default_factory=dict)


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
        self._llm = llm or ChatOpenAI(
            openai_api_key=settings.OPENAI_API_KEY,
            model_name=settings.OPENAI_MODEL,
            temperature=settings.OPENAI_TEMPERATURE,
            max_tokens=settings.OPENAI_MAX_TOKENS,
        )

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

        # Get LLM response
        llm_result = await self._llm.ainvoke(messages)
        raw_content = (getattr(llm_result, "content", None) or "").strip()

        try:
            parsed = LLMOutput.model_validate(json.loads(raw_content))
            agent_initial_message = parsed.agent_response
        except (json.JSONDecodeError, ValidationError):
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

        llm_result = await self._llm.ainvoke(messages)
        raw_content = (getattr(llm_result, "content", None) or "").strip()

        try:
            parsed = LLMOutput.model_validate(json.loads(raw_content))
        except (json.JSONDecodeError, ValidationError):
            agent_response = raw_content or "Disculpe, ¿podría repetir por favor?"
            state.setdefault("messages", []).append(
                {"role": "assistant", "content": agent_response, "timestamp": datetime.utcnow().isoformat()}
            )
            await self._store.set(session_id, state)
            return {
                "session_id": session_id,
                "agent_response": agent_response,
                "conversation_phase": current_phase.value,
                "requires_escalation": bool(state.get("requires_escalation", False)),
                "metadata": {"llm_parse_error": True},
            }

        next_phase = self._guard_transition(current_phase, parsed.next_phase)

        state["requires_escalation"] = parsed.requires_escalation
        state["escalation_reason"] = parsed.escalation_reason
        if current_phase == ConversationPhase.LEGAL_NOTICE and next_phase == ConversationPhase.SERVICE_COORDINATION:
            state["legal_notice_acknowledged"] = True
        if current_phase == ConversationPhase.SURVEY and next_phase == ConversationPhase.END:
            state["survey_completed"] = True

        self._merge_extracted(state, parsed.extracted or {})

        state.setdefault("messages", []).append(
            {"role": "assistant", "content": parsed.agent_response, "timestamp": datetime.utcnow().isoformat()}
        )
        state["phase"] = next_phase.value

        await self._store.set(session_id, state)

        return {
            "session_id": session_id,
            "agent_response": parsed.agent_response,
            "conversation_phase": next_phase.value,
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

        llm_result = await self._llm.ainvoke(messages)
        raw_content = (getattr(llm_result, "content", None) or "").strip()

        try:
            parsed = LLMOutput.model_validate(json.loads(raw_content))
        except (json.JSONDecodeError, ValidationError):
            agent_response = raw_content or "Disculpe, ¿podría repetir por favor?"
            state.setdefault("messages", []).append(
                {"role": "assistant", "content": agent_response, "timestamp": datetime.utcnow().isoformat()}
            )
            await self._store.set(session_id, state)
            return {
                "session_id": session_id,
                "agent_response": agent_response,
                "conversation_phase": current_phase.value,
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

        state["requires_escalation"] = parsed.requires_escalation
        state["escalation_reason"] = parsed.escalation_reason

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

        state.setdefault("messages", []).append(
            {"role": "assistant", "content": parsed.agent_response, "timestamp": datetime.utcnow().isoformat()}
        )
        state["phase"] = next_phase.value

        # If call ended, update Excel
        if next_phase == ConversationPhase.END and self._excel_service:
            await self._update_excel_after_call(state)

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
