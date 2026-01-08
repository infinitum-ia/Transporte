from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.agent.prompts.inbound_prompts import build_inbound_system_prompt
from src.domain.value_objects.conversation_phase import ConversationPhase
from src.infrastructure.config.settings import Settings
from src.infrastructure.persistence.redis.session_store import RedisSessionStore


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


class LLMConversationalAgent:
    def __init__(self, *, settings: Settings, store: RedisSessionStore, llm: Optional[Any] = None):
        self._settings = settings
        self._store = store

        # Configure LLM with structured output to ensure valid JSON responses
        base_llm = llm or ChatOpenAI(
            openai_api_key=settings.OPENAI_API_KEY,
            model_name=settings.OPENAI_MODEL,
            temperature=settings.OPENAI_TEMPERATURE,
            max_tokens=settings.OPENAI_MAX_TOKENS,
        )

        # Use structured output to guarantee JSON format
        self._llm = base_llm.with_structured_output(LLMOutput)

    def create_session(self, agent_name: Optional[str] = None) -> str:
        return str(uuid.uuid4())

    async def init_session(self, session_id: str, agent_name: Optional[str] = None) -> Dict[str, Any]:
        now = datetime.utcnow().isoformat()
        state: Dict[str, Any] = {
            "session_id": session_id,
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

    async def get_session_async(self, session_id: str) -> Optional[Dict[str, Any]]:
        return await self._store.get(session_id)

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        # Prefer get_session_async() in FastAPI handlers.
        return None

    def _guard_transition(self, current: ConversationPhase, proposed: ConversationPhase) -> ConversationPhase:
        return proposed if current.can_transition_to(proposed) else current

    def _merge_extracted(self, state: Dict[str, Any], extracted: Dict[str, Any]) -> None:
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

    async def process_message(self, session_id: str, user_message: str) -> Dict[str, Any]:
        state = await self._store.get(session_id)
        if not state:
            raise ValueError(f"Session not found: {session_id}")

        current_phase = ConversationPhase.from_string(state.get("phase", ConversationPhase.GREETING.value))
        agent_name = state.get("agent_name") or self._settings.AGENT_NAME
        company_name = state.get("company_name") or self._settings.COMPANY_NAME
        eps_name = state.get("eps_name") or self._settings.EPS_NAME

        state.setdefault("messages", []).append(
            {"role": "user", "content": user_message, "timestamp": datetime.utcnow().isoformat()}
        )

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
        except Exception:
            agent_response = "Disculpe, ¿podría repetir por favor?"
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
