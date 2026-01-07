"""
Session Repository Interface

Defines the contract for conversation session persistence operations.
"""
from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import datetime
from ..entities.conversation_session import ConversationSession
from ..value_objects.conversation_phase import ConversationPhase


class SessionRepository(ABC):
    """
    Repository interface for ConversationSession aggregate

    Responsibilities:
        - CRUD operations for ConversationSession entities
        - Query sessions by patient, phase, status
        - Support session lifecycle and expiration
    """

    @abstractmethod
    async def find_by_id(self, session_id: str) -> Optional[ConversationSession]:
        """
        Find session by ID

        Args:
            session_id: Session identifier

        Returns:
            ConversationSession if found, None otherwise
        """
        pass

    @abstractmethod
    async def find_by_patient(self, patient_id: str) -> List[ConversationSession]:
        """
        Find all sessions for a patient

        Args:
            patient_id: Patient identifier

        Returns:
            List of sessions for patient
        """
        pass

    @abstractmethod
    async def find_active_by_patient(
        self,
        patient_id: str
    ) -> Optional[ConversationSession]:
        """
        Find active session for patient

        Args:
            patient_id: Patient identifier

        Returns:
            Active session if exists, None otherwise

        Business Rule:
            - Typically only one active session per patient
        """
        pass

    @abstractmethod
    async def find_by_phase(
        self,
        phase: ConversationPhase
    ) -> List[ConversationSession]:
        """
        Find sessions in specific phase

        Args:
            phase: Conversation phase

        Returns:
            List of sessions in phase
        """
        pass

    @abstractmethod
    async def find_active_sessions(self) -> List[ConversationSession]:
        """
        Find all active sessions

        Returns:
            List of active sessions

        Business Rule:
            - Active = not expired, not ended, within turn limit
        """
        pass

    @abstractmethod
    async def find_expired_sessions(self) -> List[ConversationSession]:
        """
        Find all expired sessions

        Returns:
            List of expired sessions

        Business Rule:
            - Used for cleanup and maintenance
        """
        pass

    @abstractmethod
    async def save(self, session: ConversationSession) -> None:
        """
        Save (create or update) session

        Args:
            session: ConversationSession entity to save

        Business Rule:
            - Updates updated_at timestamp
        """
        pass

    @abstractmethod
    async def delete(self, session_id: str) -> None:
        """
        Delete session

        Args:
            session_id: Session identifier

        Note: Should archive before delete for audit purposes
        """
        pass

    @abstractmethod
    async def exists(self, session_id: str) -> bool:
        """
        Check if session exists

        Args:
            session_id: Session identifier

        Returns:
            True if session exists
        """
        pass

    @abstractmethod
    async def expire_old_sessions(self, before_datetime: datetime) -> int:
        """
        Expire sessions older than specified datetime

        Args:
            before_datetime: Sessions created before this will be expired

        Returns:
            Number of sessions expired

        Business Rule:
            - Maintenance operation for session cleanup
        """
        pass

    @abstractmethod
    async def count_active(self) -> int:
        """
        Count active sessions

        Returns:
            Number of active sessions

        Business Rule:
            - Used for capacity monitoring
        """
        pass

    @abstractmethod
    async def get_average_duration_minutes(self) -> float:
        """
        Get average session duration in minutes

        Returns:
            Average duration in minutes

        Business Rule:
            - Analytics metric for KPIs
        """
        pass
