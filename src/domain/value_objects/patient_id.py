"""
Patient ID Value Object

Represents the unique identifier for a patient composed of document type and number.
Following DDD principles, this is an immutable value object.
"""
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PatientId:
    """
    Value object representing a patient's unique identifier

    Attributes:
        document_type: Type of document (CC, TI, CE, PA)
        document_number: Document number as string

    Business Rules:
        - Document type must be one of: CC, TI, CE, PA
        - Document number must be non-empty
        - Two PatientIds are equal if both fields match
    """
    document_type: str
    document_number: str

    VALID_DOCUMENT_TYPES = {'CC', 'TI', 'CE', 'PA'}

    def __post_init__(self):
        """Validate patient ID upon creation"""
        if not self.document_type or self.document_type not in self.VALID_DOCUMENT_TYPES:
            raise ValueError(
                f"Invalid document type: {self.document_type}. "
                f"Must be one of {self.VALID_DOCUMENT_TYPES}"
            )

        if not self.document_number or not self.document_number.strip():
            raise ValueError("Document number cannot be empty")

        # Ensure document number contains only alphanumeric characters
        if not self.document_number.replace('-', '').isalnum():
            raise ValueError(
                f"Document number must be alphanumeric: {self.document_number}"
            )

    def to_string(self) -> str:
        """Convert to string representation"""
        return f"{self.document_type}:{self.document_number}"

    @classmethod
    def from_string(cls, id_string: str) -> 'PatientId':
        """
        Create PatientId from string representation

        Args:
            id_string: String in format "CC:1234567890"

        Returns:
            PatientId instance

        Raises:
            ValueError: If string format is invalid
        """
        parts = id_string.split(':', 1)
        if len(parts) != 2:
            raise ValueError(
                f"Invalid PatientId string format: {id_string}. "
                f"Expected format: 'TYPE:NUMBER'"
            )

        return cls(document_type=parts[0], document_number=parts[1])

    def __str__(self) -> str:
        return self.to_string()

    def __repr__(self) -> str:
        return f"PatientId('{self.to_string()}')"
