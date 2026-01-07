"""
Incident Repository Interface

Defines the contract for incident persistence operations.
"""
from abc import ABC, abstractmethod
from typing import Optional, List
from ..entities.incident import Incident, IncidentResolution
from ..value_objects.incident_type import IncidentType


class IncidentRepository(ABC):
    """
    Repository interface for Incident aggregate

    Responsibilities:
        - CRUD operations for Incident entities
        - Query incidents by session, patient, type
        - Support incident tracking and analytics
    """

    @abstractmethod
    async def find_by_id(self, incident_id: str) -> Optional[Incident]:
        """
        Find incident by ID

        Args:
            incident_id: Incident identifier

        Returns:
            Incident if found, None otherwise
        """
        pass

    @abstractmethod
    async def find_by_session(self, session_id: str) -> List[Incident]:
        """
        Find all incidents for a session

        Args:
            session_id: Session identifier

        Returns:
            List of incidents in session
        """
        pass

    @abstractmethod
    async def find_by_patient(self, patient_id: str) -> List[Incident]:
        """
        Find all incidents for a patient

        Args:
            patient_id: Patient identifier

        Returns:
            List of incidents for patient

        Business Rule:
            - Supports tracking user fatigue (repeated complaints)
        """
        pass

    @abstractmethod
    async def find_by_type(self, incident_type: IncidentType) -> List[Incident]:
        """
        Find incidents by type

        Args:
            incident_type: Incident type

        Returns:
            List of incidents of given type
        """
        pass

    @abstractmethod
    async def find_by_resolution_status(
        self,
        status: IncidentResolution
    ) -> List[Incident]:
        """
        Find incidents by resolution status

        Args:
            status: Resolution status

        Returns:
            List of incidents with status
        """
        pass

    @abstractmethod
    async def find_by_severity(self, severity: str) -> List[Incident]:
        """
        Find incidents by severity level

        Args:
            severity: Severity level (LOW, MEDIUM, HIGH)

        Returns:
            List of incidents with severity
        """
        pass

    @abstractmethod
    async def find_requiring_escalation(self) -> List[Incident]:
        """
        Find incidents requiring escalation

        Returns:
            List of incidents that require escalation to EPS

        Business Rule:
            - Based on incident type escalation rules
        """
        pass

    @abstractmethod
    async def save(self, incident: Incident) -> None:
        """
        Save (create or update) incident

        Args:
            incident: Incident entity to save
        """
        pass

    @abstractmethod
    async def delete(self, incident_id: str) -> None:
        """
        Delete incident

        Args:
            incident_id: Incident identifier
        """
        pass

    @abstractmethod
    async def count_by_patient(self, patient_id: str) -> int:
        """
        Count incidents for patient

        Args:
            patient_id: Patient identifier

        Returns:
            Number of incidents for patient

        Business Rule:
            - Used to detect user fatigue
        """
        pass

    @abstractmethod
    async def count_by_type(self, incident_type: IncidentType) -> int:
        """
        Count incidents by type

        Args:
            incident_type: Incident type

        Returns:
            Number of incidents of type

        Business Rule:
            - Supports analytics and trend detection
        """
        pass
