"""
Logging Configuration

Provides structured logging for monitoring conversations and system events.
"""
import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path


# ANSI color codes for terminal
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

    # Text colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

    # Bright text colors
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'

    # Background colors
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'


class ConversationLogger:
    """Logger for conversation monitoring and debugging"""

    def __init__(self, name: str = "transformas", log_level: str = "INFO", use_colors: bool = True):
        """
        Initialize conversation logger

        Args:
            name: Logger name
            log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            use_colors: Enable colored output for better readability
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        self.use_colors = use_colors

        # Remove existing handlers to avoid duplicates
        self.logger.handlers = []

        # Console handler with readable conversation format
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))

        # Custom formatter for readable conversation logs
        formatter = ReadableConversationFormatter(use_colors=use_colors)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(console_handler)

    def log_session_created(
        self,
        session_id: str,
        call_direction: str,
        patient_phone: Optional[str] = None,
        patient_name: Optional[str] = None,
        agent_name: Optional[str] = None
    ):
        """Log session creation"""
        self.logger.info(
            "SESSION_CREATED",
            extra={
                "event_type": "session_created",
                "session_id": session_id,
                "call_direction": call_direction,
                "patient_phone": patient_phone,
                "patient_name": patient_name,
                "agent_name": agent_name,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    def log_phase_transition(
        self,
        session_id: str,
        from_phase: str,
        to_phase: str,
        call_direction: str
    ):
        """Log conversation phase transition"""
        self.logger.info(
            "PHASE_TRANSITION",
            extra={
                "event_type": "phase_transition",
                "session_id": session_id,
                "from_phase": from_phase,
                "to_phase": to_phase,
                "call_direction": call_direction,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    def log_message(
        self,
        session_id: str,
        role: str,
        content: str,
        current_phase: str,
        call_direction: str
    ):
        """Log conversation message"""
        self.logger.info(
            "MESSAGE",
            extra={
                "event_type": "message",
                "session_id": session_id,
                "role": role,
                "content": content[:200],  # Truncate long messages
                "content_length": len(content),
                "current_phase": current_phase,
                "call_direction": call_direction,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    def log_data_extraction(
        self,
        session_id: str,
        extracted_data: Dict[str, Any],
        current_phase: str
    ):
        """Log data extraction"""
        self.logger.info(
            "DATA_EXTRACTED",
            extra={
                "event_type": "data_extraction",
                "session_id": session_id,
                "extracted_fields": list(extracted_data.keys()),
                "extracted_data": extracted_data,
                "current_phase": current_phase,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    def log_escalation(
        self,
        session_id: str,
        reason: str,
        current_phase: str,
        call_direction: str
    ):
        """Log escalation event"""
        self.logger.warning(
            "ESCALATION_REQUIRED",
            extra={
                "event_type": "escalation",
                "session_id": session_id,
                "escalation_reason": reason,
                "current_phase": current_phase,
                "call_direction": call_direction,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    def log_llm_error(
        self,
        session_id: str,
        error_type: str,
        error_message: str,
        current_phase: str
    ):
        """Log LLM parsing or processing error"""
        self.logger.error(
            "LLM_ERROR",
            extra={
                "event_type": "llm_error",
                "session_id": session_id,
                "error_type": error_type,
                "error_message": error_message,
                "current_phase": current_phase,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    def log_call_completed(
        self,
        session_id: str,
        call_direction: str,
        final_phase: str,
        message_count: int,
        duration_seconds: Optional[float] = None,
        confirmation_status: Optional[str] = None
    ):
        """Log call completion"""
        self.logger.info(
            "CALL_COMPLETED",
            extra={
                "event_type": "call_completed",
                "session_id": session_id,
                "call_direction": call_direction,
                "final_phase": final_phase,
                "message_count": message_count,
                "duration_seconds": duration_seconds,
                "confirmation_status": confirmation_status,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    def log_unified_endpoint_request(
        self,
        patient_phone: str,
        is_outbound: bool,
        message_preview: str,
        session_found: bool
    ):
        """Log unified endpoint request"""
        self.logger.info(
            "UNIFIED_ENDPOINT_REQUEST",
            extra={
                "event_type": "unified_request",
                "patient_phone": patient_phone,
                "is_outbound": is_outbound,
                "message_preview": message_preview[:100],
                "session_found": session_found,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    def log_conversation_summary(
        self,
        session_id: str,
        call_direction: str,
        patient_name: Optional[str],
        service_type: Optional[str],
        phases_visited: list,
        total_messages: int,
        incidents: list,
        requires_escalation: bool
    ):
        """Log conversation summary for analytics"""
        self.logger.info(
            "CONVERSATION_SUMMARY",
            extra={
                "event_type": "conversation_summary",
                "session_id": session_id,
                "call_direction": call_direction,
                "patient_name": patient_name,
                "service_type": service_type,
                "phases_visited": phases_visited,
                "total_messages": total_messages,
                "incident_count": len(incidents),
                "incidents": incidents,
                "requires_escalation": requires_escalation,
                "timestamp": datetime.utcnow().isoformat()
            }
        )


class ReadableConversationFormatter(logging.Formatter):
    """Custom formatter for human-readable conversation logs"""

    def __init__(self, use_colors: bool = True):
        super().__init__()
        self.use_colors = use_colors

    def format(self, record: logging.LogRecord) -> str:
        """Format log record for readable conversation display"""
        timestamp = datetime.utcnow().strftime("%H:%M:%S")
        event_type = getattr(record, "event_type", None)

        # Handle different event types with custom formatting
        if event_type == "message":
            return self._format_message(record, timestamp)
        elif event_type == "phase_transition":
            return self._format_phase_transition(record, timestamp)
        elif event_type == "session_created":
            return self._format_session_created(record, timestamp)
        elif event_type == "escalation":
            return self._format_escalation(record, timestamp)
        elif event_type == "llm_error":
            return self._format_llm_error(record, timestamp)
        elif event_type == "data_extraction":
            return self._format_data_extraction(record, timestamp)
        elif event_type == "call_completed":
            return self._format_call_completed(record, timestamp)
        elif event_type == "unified_request":
            return self._format_unified_request(record, timestamp)
        else:
            # Default format for other messages
            return f"[{timestamp}] {record.levelname}: {record.getMessage()}"

    def _colorize(self, text: str, color: str) -> str:
        """Apply color to text if colors are enabled"""
        if self.use_colors:
            return f"{color}{text}{Colors.RESET}"
        return text

    def _format_message(self, record: logging.LogRecord, timestamp: str) -> str:
        """Format conversation messages with clear visual distinction"""
        role = getattr(record, "role", "unknown")
        content = getattr(record, "content", "")
        session_id = getattr(record, "session_id", "")[:8]
        phase = getattr(record, "current_phase", "")

        # Create separator
        separator = "─" * 80

        if role == "user":
            # User message in cyan
            header = self._colorize(f"👤 USUARIO", Colors.BRIGHT_CYAN + Colors.BOLD)
            return (
                f"\n{self._colorize(separator, Colors.BRIGHT_BLACK)}\n"
                f"{header} [{timestamp}] [Session: {session_id}] [Fase: {phase}]\n"
                f"{self._colorize(content, Colors.CYAN)}\n"
                f"{self._colorize(separator, Colors.BRIGHT_BLACK)}"
            )
        elif role == "assistant":
            # Agent message in green
            header = self._colorize(f"🤖 AGENTE", Colors.BRIGHT_GREEN + Colors.BOLD)
            return (
                f"\n{self._colorize(separator, Colors.BRIGHT_BLACK)}\n"
                f"{header} [{timestamp}] [Session: {session_id}] [Fase: {phase}]\n"
                f"{self._colorize(content, Colors.GREEN)}\n"
                f"{self._colorize(separator, Colors.BRIGHT_BLACK)}"
            )
        else:
            return f"[{timestamp}] {role}: {content}"

    def _format_phase_transition(self, record: logging.LogRecord, timestamp: str) -> str:
        """Format phase transition events"""
        from_phase = getattr(record, "from_phase", "")
        to_phase = getattr(record, "to_phase", "")
        session_id = getattr(record, "session_id", "")[:8]

        arrow = "→"
        message = f"🔄 TRANSICIÓN DE FASE: {from_phase} {arrow} {to_phase}"
        return (
            f"\n{self._colorize('═' * 80, Colors.BRIGHT_YELLOW)}\n"
            f"[{timestamp}] [Session: {session_id}] {self._colorize(message, Colors.YELLOW + Colors.BOLD)}\n"
            f"{self._colorize('═' * 80, Colors.BRIGHT_YELLOW)}\n"
        )

    def _format_session_created(self, record: logging.LogRecord, timestamp: str) -> str:
        """Format session creation events"""
        session_id = getattr(record, "session_id", "")[:8]
        call_direction = getattr(record, "call_direction", "")
        patient_name = getattr(record, "patient_name", None)
        patient_phone = getattr(record, "patient_phone", None)

        direction_emoji = "📱" if call_direction == "OUTBOUND" else "📞"
        message = f"{direction_emoji} NUEVA SESIÓN {call_direction}"

        details = f"Session ID: {session_id}"
        if patient_phone:
            details += f" | Teléfono: {patient_phone}"
        if patient_name:
            details += f" | Paciente: {patient_name}"

        return (
            f"\n{self._colorize('┌' + '─' * 78 + '┐', Colors.BRIGHT_BLUE)}\n"
            f"│ [{timestamp}] {self._colorize(message, Colors.BLUE + Colors.BOLD)}\n"
            f"│ {details}\n"
            f"{self._colorize('└' + '─' * 78 + '┘', Colors.BRIGHT_BLUE)}\n"
        )

    def _format_escalation(self, record: logging.LogRecord, timestamp: str) -> str:
        """Format escalation events"""
        session_id = getattr(record, "session_id", "")[:8]
        reason = getattr(record, "escalation_reason", "Unknown")

        return (
            f"\n{self._colorize('⚠' * 40, Colors.RED)}\n"
            f"[{timestamp}] [Session: {session_id}] "
            f"{self._colorize('⚠️ ESCALAMIENTO REQUERIDO', Colors.RED + Colors.BOLD)}\n"
            f"{self._colorize(f'Razón: {reason}', Colors.BRIGHT_RED)}\n"
            f"{self._colorize('⚠' * 40, Colors.RED)}\n"
        )

    def _format_llm_error(self, record: logging.LogRecord, timestamp: str) -> str:
        """Format LLM error events"""
        session_id = getattr(record, "session_id", "")[:8]
        error_type = getattr(record, "error_type", "Unknown")
        error_message = getattr(record, "error_message", "")

        return (
            f"\n{self._colorize('✗' * 40, Colors.BRIGHT_RED)}\n"
            f"[{timestamp}] [Session: {session_id}] "
            f"{self._colorize('❌ ERROR LLM', Colors.RED + Colors.BOLD)}\n"
            f"{self._colorize(f'Tipo: {error_type}', Colors.RED)}\n"
            f"{self._colorize(f'Mensaje: {error_message}', Colors.BRIGHT_RED)}\n"
            f"{self._colorize('✗' * 40, Colors.BRIGHT_RED)}\n"
        )

    def _format_data_extraction(self, record: logging.LogRecord, timestamp: str) -> str:
        """Format data extraction events"""
        session_id = getattr(record, "session_id", "")[:8]
        extracted_data = getattr(record, "extracted_data", {})

        data_str = ", ".join([f"{k}: {v}" for k, v in extracted_data.items() if v])

        return (
            f"[{timestamp}] [Session: {session_id}] "
            f"{self._colorize('📊 DATOS EXTRAÍDOS:', Colors.MAGENTA)} {data_str}"
        )

    def _format_call_completed(self, record: logging.LogRecord, timestamp: str) -> str:
        """Format call completion events"""
        session_id = getattr(record, "session_id", "")[:8]
        message_count = getattr(record, "message_count", 0)
        confirmation_status = getattr(record, "confirmation_status", None)

        details = f"Mensajes: {message_count}"
        if confirmation_status:
            details += f" | Estado: {confirmation_status}"

        return (
            f"\n{self._colorize('╔' + '═' * 78 + '╗', Colors.BRIGHT_GREEN)}\n"
            f"║ [{timestamp}] [Session: {session_id}] "
            f"{self._colorize('✅ LLAMADA COMPLETADA', Colors.GREEN + Colors.BOLD)}\n"
            f"║ {details}\n"
            f"{self._colorize('╚' + '═' * 78 + '╝', Colors.BRIGHT_GREEN)}\n"
        )

    def _format_unified_request(self, record: logging.LogRecord, timestamp: str) -> str:
        """Format unified endpoint request"""
        patient_phone = getattr(record, "patient_phone", "")
        is_outbound = getattr(record, "is_outbound", False)
        session_found = getattr(record, "session_found", False)
        message_preview = getattr(record, "message_preview", "")[:50]

        direction = "OUTBOUND" if is_outbound else "INBOUND"
        session_status = "EXISTENTE" if session_found else "NUEVA"

        return (
            f"[{timestamp}] {self._colorize('📡 REQUEST', Colors.BRIGHT_MAGENTA)} "
            f"| Tel: {patient_phone} | {direction} | Sesión: {session_status} | '{message_preview}...'"
        )


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logs (for file output)"""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        # Add extra fields if present
        if hasattr(record, "event_type"):
            log_data["event_type"] = record.event_type
        if hasattr(record, "session_id"):
            log_data["session_id"] = record.session_id
        if hasattr(record, "call_direction"):
            log_data["call_direction"] = record.call_direction
        if hasattr(record, "current_phase"):
            log_data["current_phase"] = record.current_phase
        if hasattr(record, "from_phase"):
            log_data["from_phase"] = record.from_phase
        if hasattr(record, "to_phase"):
            log_data["to_phase"] = record.to_phase
        if hasattr(record, "role"):
            log_data["role"] = record.role
        if hasattr(record, "content"):
            log_data["content"] = record.content
        if hasattr(record, "content_length"):
            log_data["content_length"] = record.content_length
        if hasattr(record, "extracted_fields"):
            log_data["extracted_fields"] = record.extracted_fields
        if hasattr(record, "extracted_data"):
            log_data["extracted_data"] = record.extracted_data
        if hasattr(record, "escalation_reason"):
            log_data["escalation_reason"] = record.escalation_reason
        if hasattr(record, "error_type"):
            log_data["error_type"] = record.error_type
        if hasattr(record, "error_message"):
            log_data["error_message"] = record.error_message
        if hasattr(record, "patient_phone"):
            log_data["patient_phone"] = record.patient_phone
        if hasattr(record, "patient_name"):
            log_data["patient_name"] = record.patient_name
        if hasattr(record, "agent_name"):
            log_data["agent_name"] = record.agent_name
        if hasattr(record, "service_type"):
            log_data["service_type"] = record.service_type
        if hasattr(record, "message_count"):
            log_data["message_count"] = record.message_count
        if hasattr(record, "final_phase"):
            log_data["final_phase"] = record.final_phase
        if hasattr(record, "confirmation_status"):
            log_data["confirmation_status"] = record.confirmation_status
        if hasattr(record, "is_outbound"):
            log_data["is_outbound"] = record.is_outbound
        if hasattr(record, "session_found"):
            log_data["session_found"] = record.session_found
        if hasattr(record, "message_preview"):
            log_data["message_preview"] = record.message_preview
        if hasattr(record, "phases_visited"):
            log_data["phases_visited"] = record.phases_visited
        if hasattr(record, "total_messages"):
            log_data["total_messages"] = record.total_messages
        if hasattr(record, "incident_count"):
            log_data["incident_count"] = record.incident_count
        if hasattr(record, "incidents"):
            log_data["incidents"] = record.incidents
        if hasattr(record, "requires_escalation"):
            log_data["requires_escalation"] = record.requires_escalation
        if hasattr(record, "duration_seconds"):
            log_data["duration_seconds"] = record.duration_seconds

        return json.dumps(log_data, ensure_ascii=False)


# Global logger instance
_logger_instance = None


def get_logger(log_level: str = "INFO", use_colors: bool = True) -> ConversationLogger:
    """
    Get or create global logger instance

    Args:
        log_level: Log level (DEBUG, INFO, WARNING, ERROR)
        use_colors: Enable colored output (default: True)

    Returns:
        ConversationLogger instance
    """
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = ConversationLogger(log_level=log_level, use_colors=use_colors)
    return _logger_instance
