"""
Patient Repository Interface

Defines the contract for patient persistence operations.
Following Repository pattern from DDD.
"""
from abc import ABC, abstractmethod
from typing import Optional, List
from ..entities.patient import Patient
from ..value_objects.patient_id import PatientId


class PatientRepository(ABC):
    """
    Repository interface for Patient aggregate

    Responsibilities:
        - CRUD operations for Patient entities
        - Query patients by various criteria
        - Maintain aggregate consistency
    """

    @abstractmethod
    async def find_by_id(self, patient_id: PatientId) -> Optional[Patient]:
        """
        Find patient by ID

        Args:
            patient_id: Patient identifier

        Returns:
            Patient if found, None otherwise
        """
        pass

    @abstractmethod
    async def find_by_document(
        self,
        document_type: str,
        document_number: str
    ) -> Optional[Patient]:
        """
        Find patient by document

        Args:
            document_type: Type of document (CC, TI, etc.)
            document_number: Document number

        Returns:
            Patient if found, None otherwise
        """
        pass

    @abstractmethod
    async def save(self, patient: Patient) -> None:
        """
        Save (create or update) patient

        Args:
            patient: Patient entity to save

        Business Rule:
            - Updates updated_at timestamp
        """
        pass

    @abstractmethod
    async def delete(self, patient_id: PatientId) -> None:
        """
        Delete patient

        Args:
            patient_id: Patient identifier

        Note: Soft delete is recommended for audit purposes
        """
        pass

    @abstractmethod
    async def exists(self, patient_id: PatientId) -> bool:
        """
        Check if patient exists

        Args:
            patient_id: Patient identifier

        Returns:
            True if patient exists, False otherwise
        """
        pass

    @abstractmethod
    async def find_by_phone(self, phone: str) -> List[Patient]:
        """
        Find patients by phone number

        Args:
            phone: Phone number

        Returns:
            List of patients with matching phone
        """
        pass

    @abstractmethod
    async def count(self) -> int:
        """
        Get total count of patients

        Returns:
            Number of patients in repository
        """
        pass
