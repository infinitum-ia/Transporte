"""
Conversation Session Entity

Aggregate root representing a complete conversation session with a user.
Manages the conversation lifecycle and state transitions.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from ..value_objects.conversation_phase import ConversationPhase


@dataclass
class ConversationSession:
    """
    Conversation Session aggregate root

    Business Rules:
        - Session progresses through defined phases
        - Phase transitions must be valid
        - Session has maximum turn limit
        - Session expires after TTL
        - Tracks full conversation history

    Attributes:
        session_id: Unique session identifier
        conversation_phase: Current phase (ConversationPhase enum)
        patient_id: Patient ID (set after identification)
        turn_count: Number of conversation turns
        max_turns: Maximum allowed turns
        created_at: Session creation timestamp
        updated_at: Last update timestamp
        expired_at: Session expiration timestamp (optional)
        metadata: Additional session metadata
    """
    session_id: str
    conversation_phase: ConversationPhase = ConversationPhase.GREETING
    patient_id: Optional[str] = None
    turn_count: int = 0
    max_turns: int = 50
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    expired_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize session"""
        if self.max_turns <= 0:
            raise ValueError("max_turns must be positive")

    def is_active(self) -> bool:
        """
        Check if session is still active

        Returns:
            bool: True if session is active
        """
        # Check if expired
        if self.expired_at and datetime.utcnow() > self.expired_at:
            return False

        # Check if conversation ended
        if self.conversation_phase == ConversationPhase.END:
            return False

        # Check if max turns exceeded
        if self.turn_count >= self.max_turns:
            return False

        return True

    def is_expired(self) -> bool:
        """Check if session has expired"""
        if self.expired_at:
            return datetime.utcnow() > self.expired_at
        return False

    def is_ended(self) -> bool:
        """Check if conversation has ended"""
        return self.conversation_phase == ConversationPhase.END

    def has_exceeded_max_turns(self) -> bool:
        """Check if session has exceeded maximum turns"""
        return self.turn_count >= self.max_turns

    def increment_turn(self) -> None:
        """
        Increment turn counter

        Business Rule:
            - Cannot exceed max_turns
        """
        if self.turn_count >= self.max_turns:
            raise ValueError(
                f"Cannot increment turn: maximum turns ({self.max_turns}) reached"
            )

        object.__setattr__(self, 'turn_count', self.turn_count + 1)
        object.__setattr__(self, 'updated_at', datetime.utcnow())

    def transition_to_phase(self, next_phase: ConversationPhase) -> None:
        """
        Transition to next conversation phase

        Args:
            next_phase: The phase to transition to

        Raises:
            ValueError: If transition is invalid

        Business Rule:
            - Phase transitions must follow valid flow
        """
        if not self.conversation_phase.can_transition_to(next_phase):
            raise ValueError(
                f"Invalid phase transition from {self.conversation_phase} "
                f"to {next_phase}"
            )

        object.__setattr__(self, 'conversation_phase', next_phase)
        object.__setattr__(self, 'updated_at', datetime.utcnow())

    def set_patient(self, patient_id: str) -> None:
        """
        Set patient ID after identification

        Args:
            patient_id: Patient identifier

        Business Rule:
            - Patient ID can only be set once
            - Should be set during IDENTIFICATION phase
        """
        if self.patient_id:
            raise ValueError(
                f"Patient ID already set: {self.patient_id}. Cannot change."
            )

        if not patient_id or not patient_id.strip():
            raise ValueError("Patient ID cannot be empty")

        object.__setattr__(self, 'patient_id', patient_id.strip())
        object.__setattr__(self, 'updated_at', datetime.utcnow())

    def expire(self) -> None:
        """
        Mark session as expired

        Business Rule:
            - Sets expiration timestamp
            - Session becomes inactive
        """
        object.__setattr__(self, 'expired_at', datetime.utcnow())
        object.__setattr__(self, 'updated_at', datetime.utcnow())

    def end_conversation(self) -> None:
        """
        End the conversation

        Business Rule:
            - Transitions to END phase
            - Session becomes inactive
        """
        object.__setattr__(self, 'conversation_phase', ConversationPhase.END)
        object.__setattr__(self, 'updated_at', datetime.utcnow())

    def set_metadata(self, key: str, value: Any) -> None:
        """
        Set metadata value

        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value
        object.__setattr__(self, 'updated_at', datetime.utcnow())

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Get metadata value

        Args:
            key: Metadata key
            default: Default value if not found

        Returns:
            Metadata value or default
        """
        return self.metadata.get(key, default)

    def get_next_valid_phases(self) -> List[ConversationPhase]:
        """
        Get list of valid next phases from current phase

        Returns:
            List[ConversationPhase]: Valid next phases
        """
        return self.conversation_phase.get_next_phases()

    def can_accept_turn(self) -> bool:
        """
        Check if session can accept another turn

        Returns:
            bool: True if can accept turn
        """
        return (
            self.is_active() and
            not self.is_ended() and
            not self.has_exceeded_max_turns()
        )

    def get_duration_seconds(self) -> float:
        """
        Get session duration in seconds

        Returns:
            float: Duration in seconds
        """
        end_time = self.expired_at or self.updated_at or datetime.utcnow()
        return (end_time - self.created_at).total_seconds()

    def get_duration_minutes(self) -> float:
        """
        Get session duration in minutes

        Returns:
            float: Duration in minutes
        """
        return self.get_duration_seconds() / 60.0

    def to_dict(self) -> dict:
        """Convert entity to dictionary"""
        return {
            "session_id": self.session_id,
            "conversation_phase": str(self.conversation_phase),
            "patient_id": self.patient_id,
            "turn_count": self.turn_count,
            "max_turns": self.max_turns,
            "is_active": self.is_active(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "expired_at": self.expired_at.isoformat() if self.expired_at else None,
            "metadata": self.metadata
        }

    def __str__(self) -> str:
        return (
            f"ConversationSession({self.session_id}, "
            f"{self.conversation_phase}, turns={self.turn_count})"
        )

    def __repr__(self) -> str:
        return (
            f"ConversationSession(session_id='{self.session_id}', "
            f"phase={self.conversation_phase}, "
            f"patient_id='{self.patient_id}')"
        )
