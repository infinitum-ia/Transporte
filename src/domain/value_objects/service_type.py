"""
Service Type Value Object

Represents the type of medical transport service.
"""
from enum import Enum


class ServiceType(str, Enum):
    """
    Types of medical transport services offered by Transformas

    Business Rules:
        - TERAPIA: Physical therapy appointments
        - DIALISIS: Dialysis sessions (high priority)
        - CONSULTA_ESPECIALIZADA: Specialized medical consultations
    """
    TERAPIA = "TERAPIA"
    DIALISIS = "DIALISIS"
    CONSULTA_ESPECIALIZADA = "CONSULTA_ESPECIALIZADA"

    def __str__(self) -> str:
        return self.value

    @property
    def display_name(self) -> str:
        """Get human-readable display name"""
        display_names = {
            self.TERAPIA: "Terapia",
            self.DIALISIS: "Diálisis",
            self.CONSULTA_ESPECIALIZADA: "Consulta Especializada"
        }
        return display_names.get(self, self.value)

    @property
    def is_high_priority(self) -> bool:
        """Check if service type requires high priority handling"""
        return self == ServiceType.DIALISIS

    @classmethod
    def from_string(cls, value: str) -> 'ServiceType':
        """
        Create ServiceType from string

        Args:
            value: String representation (case-insensitive)

        Returns:
            ServiceType enum value

        Raises:
            ValueError: If value is not a valid service type
        """
        try:
            return cls[value.upper()]
        except KeyError:
            valid_types = ', '.join([t.value for t in cls])
            raise ValueError(
                f"Invalid service type: {value}. "
                f"Valid types: {valid_types}"
            )
