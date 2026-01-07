"""
Service Modality Value Object

Represents the modality of transport service delivery.
"""
from enum import Enum


class ServiceModality(str, Enum):
    """
    Transport service delivery modalities

    Business Rules:
        - RUTA_COMPARTIDA: Shared route with other patients (most common)
        - DESEMBOLSO: Patient pays upfront and gets reimbursed (requires document + code, 24-48h processing)
    """
    RUTA_COMPARTIDA = "RUTA_COMPARTIDA"
    DESEMBOLSO = "DESEMBOLSO"

    def __str__(self) -> str:
        return self.value

    @property
    def display_name(self) -> str:
        """Get human-readable display name"""
        display_names = {
            self.RUTA_COMPARTIDA: "Ruta Compartida",
            self.DESEMBOLSO: "Desembolso"
        }
        return display_names.get(self, self.value)

    @property
    def requires_documentation(self) -> bool:
        """Check if modality requires special documentation"""
        return self == ServiceModality.DESEMBOLSO

    @property
    def processing_time_hours(self) -> int:
        """Get typical processing time in hours"""
        if self == ServiceModality.DESEMBOLSO:
            return 24  # 24-48 hours for reimbursement
        return 0  # Immediate for shared route

    @classmethod
    def from_string(cls, value: str) -> 'ServiceModality':
        """
        Create ServiceModality from string

        Args:
            value: String representation (case-insensitive)

        Returns:
            ServiceModality enum value

        Raises:
            ValueError: If value is not a valid modality
        """
        try:
            return cls[value.upper()]
        except KeyError:
            valid_modalities = ', '.join([m.value for m in cls])
            raise ValueError(
                f"Invalid service modality: {value}. "
                f"Valid modalities: {valid_modalities}"
            )
