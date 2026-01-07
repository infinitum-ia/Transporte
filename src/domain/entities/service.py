"""
Service Entity

Represents a medical transport service request.
"""
from dataclasses import dataclass, field
from datetime import datetime, date, time
from typing import Optional
from enum import Enum
from ..value_objects.service_type import ServiceType
from ..value_objects.service_modality import ServiceModality


class ServiceStatus(str, Enum):
    """Status of a service"""
    PENDING = "PENDING"  # Awaiting confirmation
    CONFIRMED = "CONFIRMED"  # Confirmed and scheduled
    IN_PROGRESS = "IN_PROGRESS"  # Currently being provided
    COMPLETED = "COMPLETED"  # Successfully completed
    CANCELLED = "CANCELLED"  # Cancelled
    NO_SHOW = "NO_SHOW"  # Patient did not show up


@dataclass
class Service:
    """
    Service entity representing a transport service request

    Business Rules from PRD (Section 5.3):
        - Must have confirmed appointment date and time
        - Service type determines priority (DIALISIS is high priority)
        - Modality affects processing time (DESEMBOLSO requires 24-48h)
        - Must have valid pickup and destination addresses
        - Special requirements should be noted

    Attributes:
        service_id: Unique service identifier
        patient_id: ID of the patient (PatientId as string)
        service_type: Type of service (ServiceType enum)
        service_modality: Delivery modality (ServiceModality enum)
        appointment_date: Date of the appointment
        appointment_time: Time of the appointment
        pickup_address: Address where patient will be picked up
        destination_address: Medical facility address
        special_requirements: Optional special needs (wheelchair, large vehicle, etc.)
        status: Current status of the service
        created_at: Service creation timestamp
        updated_at: Last update timestamp
        notes: Additional notes about the service
    """
    service_id: str
    patient_id: str
    service_type: ServiceType
    service_modality: ServiceModality
    appointment_date: date
    appointment_time: time
    pickup_address: str
    destination_address: str
    special_requirements: Optional[str] = None
    status: ServiceStatus = ServiceStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    notes: Optional[str] = None

    def __post_init__(self):
        """Validate service upon creation"""
        self._validate()

    def _validate(self):
        """
        Validate service entity

        Business Rules:
            - Appointment date must be in the future or today
            - Addresses must not be empty
            - Service type and modality must be valid enums
        """
        if not self.pickup_address or not self.pickup_address.strip():
            raise ValueError("Pickup address cannot be empty")

        if not self.destination_address or not self.destination_address.strip():
            raise ValueError("Destination address cannot be empty")

        # Validate appointment date is not in the past
        today = datetime.now().date()
        if self.appointment_date < today:
            raise ValueError(
                f"Appointment date cannot be in the past: {self.appointment_date}"
            )

    def is_high_priority(self) -> bool:
        """
        Check if service is high priority

        Business Rule:
            - DIALISIS services are high priority
        """
        return self.service_type.is_high_priority

    def confirm(self) -> None:
        """
        Confirm the service

        Business Rule:
            - Can only confirm from PENDING status
        """
        if self.status != ServiceStatus.PENDING:
            raise ValueError(
                f"Cannot confirm service in {self.status} status. "
                f"Must be PENDING."
            )

        object.__setattr__(self, 'status', ServiceStatus.CONFIRMED)
        object.__setattr__(self, 'updated_at', datetime.utcnow())

    def start(self) -> None:
        """
        Mark service as in progress

        Business Rule:
            - Can only start from CONFIRMED status
        """
        if self.status != ServiceStatus.CONFIRMED:
            raise ValueError(
                f"Cannot start service in {self.status} status. "
                f"Must be CONFIRMED."
            )

        object.__setattr__(self, 'status', ServiceStatus.IN_PROGRESS)
        object.__setattr__(self, 'updated_at', datetime.utcnow())

    def complete(self) -> None:
        """
        Mark service as completed

        Business Rule:
            - Can only complete from IN_PROGRESS status
        """
        if self.status != ServiceStatus.IN_PROGRESS:
            raise ValueError(
                f"Cannot complete service in {self.status} status. "
                f"Must be IN_PROGRESS."
            )

        object.__setattr__(self, 'status', ServiceStatus.COMPLETED)
        object.__setattr__(self, 'updated_at', datetime.utcnow())

    def cancel(self, reason: Optional[str] = None) -> None:
        """
        Cancel the service

        Args:
            reason: Optional reason for cancellation

        Business Rule:
            - Cannot cancel already completed services
        """
        if self.status == ServiceStatus.COMPLETED:
            raise ValueError("Cannot cancel a completed service")

        object.__setattr__(self, 'status', ServiceStatus.CANCELLED)
        object.__setattr__(self, 'updated_at', datetime.utcnow())

        if reason:
            current_notes = self.notes or ""
            object.__setattr__(
                self,
                'notes',
                f"{current_notes}\nCancellation reason: {reason}".strip()
            )

    def mark_no_show(self) -> None:
        """
        Mark patient as no-show

        Business Rule from PRD (Section 7.4):
            - Mark services as not provided when patient doesn't show
        """
        if self.status not in [ServiceStatus.PENDING, ServiceStatus.CONFIRMED]:
            raise ValueError(
                f"Cannot mark no-show for service in {self.status} status"
            )

        object.__setattr__(self, 'status', ServiceStatus.NO_SHOW)
        object.__setattr__(self, 'updated_at', datetime.utcnow())

    def add_special_requirement(self, requirement: str) -> None:
        """
        Add special requirement to service

        Args:
            requirement: Special requirement description

        Business Rule:
            - All special needs must be documented
        """
        if not requirement or not requirement.strip():
            return

        if self.special_requirements:
            combined = f"{self.special_requirements}; {requirement}"
            object.__setattr__(self, 'special_requirements', combined)
        else:
            object.__setattr__(self, 'special_requirements', requirement.strip())

        object.__setattr__(self, 'updated_at', datetime.utcnow())

    def add_note(self, note: str) -> None:
        """
        Add note to service

        Args:
            note: Note to add
        """
        if not note or not note.strip():
            return

        if self.notes:
            combined = f"{self.notes}\n{note}"
            object.__setattr__(self, 'notes', combined)
        else:
            object.__setattr__(self, 'notes', note.strip())

        object.__setattr__(self, 'updated_at', datetime.utcnow())

    def requires_documentation(self) -> bool:
        """
        Check if service modality requires special documentation

        Business Rule:
            - DESEMBOLSO modality requires document and code
        """
        return self.service_modality.requires_documentation

    def get_processing_time_hours(self) -> int:
        """
        Get processing time based on modality

        Business Rule:
            - DESEMBOLSO: 24-48 hours
            - RUTA_COMPARTIDA: Immediate
        """
        return self.service_modality.processing_time_hours

    def to_dict(self) -> dict:
        """Convert entity to dictionary"""
        return {
            "service_id": self.service_id,
            "patient_id": self.patient_id,
            "service_type": str(self.service_type),
            "service_modality": str(self.service_modality),
            "appointment_date": self.appointment_date.isoformat(),
            "appointment_time": self.appointment_time.isoformat(),
            "pickup_address": self.pickup_address,
            "destination_address": self.destination_address,
            "special_requirements": self.special_requirements,
            "status": str(self.status),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "notes": self.notes
        }

    def __str__(self) -> str:
        return (
            f"Service({self.service_id}, {self.service_type}, "
            f"{self.appointment_date}, {self.status})"
        )

    def __repr__(self) -> str:
        return (
            f"Service(service_id='{self.service_id}', "
            f"patient_id='{self.patient_id}', "
            f"service_type={self.service_type}, "
            f"status={self.status})"
        )
