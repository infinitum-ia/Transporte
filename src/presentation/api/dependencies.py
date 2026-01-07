from __future__ import annotations

from fastapi import Request, HTTPException, status

from src.agent.base import ConversationalAgent
from src.agent.call_orchestrator import CallOrchestrator
from src.infrastructure.persistence.excel_service import ExcelOutboundService


def get_agent(request: Request) -> ConversationalAgent:
    """Get legacy conversational agent (for backward compatibility)"""
    return request.app.state.agent


def get_call_orchestrator(request: Request) -> CallOrchestrator:
    """
    Get call orchestrator from app state

    Raises:
        HTTPException: If orchestrator is not configured
    """
    orchestrator = getattr(request.app.state, "call_orchestrator", None)
    if orchestrator is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Call orchestrator not configured"
        )
    return orchestrator


def get_excel_service(request: Request) -> ExcelOutboundService:
    """
    Get Excel service from app state

    Raises:
        HTTPException: If Excel service is not configured
    """
    excel_service = getattr(request.app.state, "excel_service", None)
    if excel_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Excel service not configured. Ensure EXCEL_PATH is set in environment."
        )
    return excel_service

