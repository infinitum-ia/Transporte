"""
Service Repository Interface

Defines the contract for service persistence operations.
"""
from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import date
from ..entities.service import Service, ServiceStatus


class ServiceRepository(ABC):
    """
    Repository interface for Service aggregate

    Responsibilities:
        - CRUD operations for Service entities
        - Query services by patient, date, status
        - Support service lifecycle management
    """

    @abstractmethod
    async def find_by_id(self, service_id: str) -> Optional[Service]:
        """
        Find service by ID

        Args:
            service_id: Service identifier

        Returns:
            Service if found, None otherwise
        """
        pass

    @abstractmethod
    async def find_by_patient(self, patient_id: str) -> List[Service]:
        """
        Find all services for a patient

        Args:
            patient_id: Patient identifier

        Returns:
            List of services for patient
        """
        pass

    @abstractmethod
    async def find_by_patient_and_date(
        self,
        patient_id: str,
        appointment_date: date
    ) -> List[Service]:
        """
        Find services for patient on specific date

        Args:
            patient_id: Patient identifier
            appointment_date: Appointment date

        Returns:
            List of services for patient on date
        """
        pass

    @abstractmethod
    async def find_by_status(self, status: ServiceStatus) -> List[Service]:
        """
        Find all services with given status

        Args:
            status: Service status

        Returns:
            List of services with status
        """
        pass

    @abstractmethod
    async def find_by_date_range(
        self,
        start_date: date,
        end_date: date
    ) -> List[Service]:
        """
        Find services within date range

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            List of services in range
        """
        pass

    @abstractmethod
    async def save(self, service: Service) -> None:
        """
        Save (create or update) service

        Args:
            service: Service entity to save

        Business Rule:
            - Updates updated_at timestamp
        """
        pass

    @abstractmethod
    async def delete(self, service_id: str) -> None:
        """
        Delete service

        Args:
            service_id: Service identifier
        """
        pass

    @abstractmethod
    async def exists(self, service_id: str) -> bool:
        """
        Check if service exists

        Args:
            service_id: Service identifier

        Returns:
            True if service exists
        """
        pass

    @abstractmethod
    async def count_by_patient(self, patient_id: str) -> int:
        """
        Count services for patient

        Args:
            patient_id: Patient identifier

        Returns:
            Number of services for patient
        """
        pass
