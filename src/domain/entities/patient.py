"""
Patient Entity

Aggregate root representing a patient in the medical transport system.
Contains business logic for patient validation and EPS verification.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from ..value_objects.patient_id import PatientId


@dataclass
class Patient:
    """
    Patient aggregate root

    Business Rules from PRD:
        - Patient must belong to EPS Cosalud
        - Patient identity must be validated with document
        - Can be represented by a responsible party (family member)
        - Contact information should be updated when available

    Attributes:
        id: Unique patient identifier (PatientId value object)
        full_name: Complete name of the patient
        document_type: Type of document (CC, TI, CE, PA)
        document_number: Document number
        eps: EPS name (must be COSALUD)
        is_responsible: True if patient calls directly, False if family member
        responsible_name: Name of responsible party if is_responsible=False
        phone: Contact phone number
        created_at: Timestamp of patient creation
        updated_at: Timestamp of last update
    """
    id: PatientId
    full_name: str
    document_type: str
    document_number: str
    eps: str
    is_responsible: bool
    responsible_name: Optional[str] = None
    phone: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    # EPS constant for validation
    VALID_EPS = "COSALUD"

    def __post_init__(self):
        """
        Validate patient data upon creation

        Raises:
            ValueError: If validation fails
        """
        self._validate()

    def _validate(self):
        """
        Validate patient entity

        Business Rules:
            - full_name must not be empty
            - EPS must be COSALUD (case-insensitive)
            - If not is_responsible, responsible_name is required
        """
        if not self.full_name or not self.full_name.strip():
            raise ValueError("Patient name cannot be empty")

        if not self.eps or self.eps.upper() != self.VALID_EPS:
            raise ValueError(
                f"Invalid EPS: {self.eps}. "
                f"Only {self.VALID_EPS} patients are served"
            )

        if not self.is_responsible and not self.responsible_name:
            raise ValueError(
                "Responsible party name is required when patient is not calling directly"
            )

        # Normalize EPS to uppercase
        object.__setattr__(self, 'eps', self.eps.upper())

    def validate_eps(self) -> bool:
        """
        Business rule: Validate that patient belongs to COSALUD EPS

        Returns:
            bool: True if EPS is COSALUD, False otherwise
        """
        return self.eps.upper() == self.VALID_EPS

    def update_contact_info(self, phone: str) -> None:
        """
        Update patient contact information

        Args:
            phone: New phone number

        Business Rule:
            - Updates timestamp when contact info changes
        """
        if phone and phone.strip():
            object.__setattr__(self, 'phone', phone.strip())
            object.__setattr__(self, 'updated_at', datetime.utcnow())

    def update_responsible_party(self, responsible_name: str) -> None:
        """
        Update responsible party information

        Args:
            responsible_name: Name of the responsible party

        Business Rule:
            - Only applicable when is_responsible is False
        """
        if not self.is_responsible:
            if not responsible_name or not responsible_name.strip():
                raise ValueError("Responsible party name cannot be empty")

            object.__setattr__(self, 'responsible_name', responsible_name.strip())
            object.__setattr__(self, 'updated_at', datetime.utcnow())
        else:
            raise ValueError("Cannot set responsible party when patient calls directly")

    def get_contact_name(self) -> str:
        """
        Get the name of the person to contact

        Returns:
            str: Patient name if calling directly, responsible party name otherwise
        """
        if self.is_responsible:
            return self.full_name
        return self.responsible_name or self.full_name

    def get_formal_treatment(self) -> str:
        """
        Get formal treatment name for addressing the contact person

        Business Rule from PRD (Section 15.2):
            - Use "Sr." or "Sra." followed by first name or lastname

        Returns:
            str: Formal treatment (e.g., "Sr. Pérez")
        """
        contact_name = self.get_contact_name()
        # Simple heuristic: use last part of name (usually lastname in Spanish)
        name_parts = contact_name.strip().split()
        if len(name_parts) > 1:
            lastname = name_parts[-1]
        else:
            lastname = name_parts[0]

        # Default to "Sr." (could be enhanced with gender detection)
        return f"Sr./Sra. {lastname}"

    def to_dict(self) -> dict:
        """
        Convert entity to dictionary representation

        Returns:
            dict: Entity as dictionary
        """
        return {
            "id": self.id.to_string(),
            "full_name": self.full_name,
            "document_type": self.document_type,
            "document_number": self.document_number,
            "eps": self.eps,
            "is_responsible": self.is_responsible,
            "responsible_name": self.responsible_name,
            "phone": self.phone,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def __str__(self) -> str:
        return f"Patient({self.full_name}, {self.id})"

    def __repr__(self) -> str:
        return (
            f"Patient(id={self.id!r}, full_name='{self.full_name}', "
            f"eps='{self.eps}', is_responsible={self.is_responsible})"
        )
