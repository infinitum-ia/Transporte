"""
Call Direction Value Object

Represents whether a call is inbound (customer calls us) or outbound (we call customer).
"""
from enum import Enum


class CallDirection(str, Enum):
    """
    Direction of the phone call

    INBOUND: Customer calls us (current flow)
    OUTBOUND: We call customer (confirmation calls)
    """
    INBOUND = "INBOUND"
    OUTBOUND = "OUTBOUND"

    def __str__(self) -> str:
        return self.value

    @property
    def display_name(self) -> str:
        """Get human-readable display name"""
        names = {
            self.INBOUND: "Llamada Entrante",
            self.OUTBOUND: "Llamada Saliente"
        }
        return names.get(self, self.value)

    @property
    def is_inbound(self) -> bool:
        """Check if this is an inbound call"""
        return self == CallDirection.INBOUND

    @property
    def is_outbound(self) -> bool:
        """Check if this is an outbound call"""
        return self == CallDirection.OUTBOUND

    @classmethod
    def from_string(cls, value: str) -> 'CallDirection':
        """
        Create CallDirection from string

        Args:
            value: String representation (case-insensitive)

        Returns:
            CallDirection enum value

        Raises:
            ValueError: If value is not valid
        """
        try:
            return cls[value.upper()]
        except KeyError:
            valid_values = ', '.join([d.value for d in cls])
            raise ValueError(
                f"Invalid call direction: {value}. "
                f"Valid values: {valid_values}"
            )
