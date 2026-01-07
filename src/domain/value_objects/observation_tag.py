"""
Observation Tag Value Object

Represents structured tags for logging observations about services and users.
These tags enable analytics and proper service delivery.
"""
from enum import Enum


class ObservationTag(str, Enum):
    """
    Structured observation tags for service requirements and issues

    Business Rules from PRD (Section 7.1: Structured Logging):
        - NECESITA_CARRO_GRANDE: Requires large vehicle
        - NECESITA_SILLA_RUEDAS: Requires wheelchair accommodation
        - REQUIERE_ACOMPAÑANTE: Requires companion/caregiver
        - QUEJA_CONDUCTOR: Driver complaint
        - QUEJA_VEHICULO: Vehicle complaint
        - REPROGRAMACION_PENDIENTE: Rescheduling pending
        - FUERA_COBERTURA: Outside coverage area
        - ALTA_PRIORIDAD: High priority flag
        - REQUIERE_COORDINADOR: Requires coordinator intervention
        - FOLLOWUP_PROMISE: Follow-up promise made
        - SURVEY_SCORE: Quality survey score
    """
    NECESITA_CARRO_GRANDE = "NECESITA_CARRO_GRANDE"
    NECESITA_SILLA_RUEDAS = "NECESITA_SILLA_RUEDAS"
    REQUIERE_ACOMPAÑANTE = "REQUIERE_ACOMPAÑANTE"
    QUEJA_CONDUCTOR = "QUEJA_CONDUCTOR"
    QUEJA_VEHICULO = "QUEJA_VEHICULO"
    REPROGRAMACION_PENDIENTE = "REPROGRAMACION_PENDIENTE"
    FUERA_COBERTURA = "FUERA_COBERTURA"
    ALTA_PRIORIDAD = "ALTA_PRIORIDAD"
    REQUIERE_COORDINADOR = "REQUIERE_COORDINADOR"
    FOLLOWUP_PROMISE = "FOLLOWUP_PROMISE"
    SURVEY_SCORE = "SURVEY_SCORE"

    def __str__(self) -> str:
        return self.value

    @property
    def display_name(self) -> str:
        """Get human-readable display name"""
        display_names = {
            self.NECESITA_CARRO_GRANDE: "Necesita carro grande",
            self.NECESITA_SILLA_RUEDAS: "Necesita silla de ruedas",
            self.REQUIERE_ACOMPAÑANTE: "Requiere acompañante",
            self.QUEJA_CONDUCTOR: "Queja del conductor",
            self.QUEJA_VEHICULO: "Queja del vehículo",
            self.REPROGRAMACION_PENDIENTE: "Reprogramación pendiente",
            self.FUERA_COBERTURA: "Fuera de cobertura",
            self.ALTA_PRIORIDAD: "Alta prioridad",
            self.REQUIERE_COORDINADOR: "Requiere coordinador",
            self.FOLLOWUP_PROMISE: "Promesa de seguimiento",
            self.SURVEY_SCORE: "Puntuación de encuesta"
        }
        return display_names.get(self, self.value)

    @property
    def category(self) -> str:
        """Get category of observation tag"""
        service_requirements = {
            self.NECESITA_CARRO_GRANDE,
            self.NECESITA_SILLA_RUEDAS,
            self.REQUIERE_ACOMPAÑANTE
        }
        complaints = {
            self.QUEJA_CONDUCTOR,
            self.QUEJA_VEHICULO
        }
        operational = {
            self.REPROGRAMACION_PENDIENTE,
            self.FUERA_COBERTURA,
            self.ALTA_PRIORIDAD,
            self.REQUIERE_COORDINADOR,
            self.FOLLOWUP_PROMISE
        }
        quality = {
            self.SURVEY_SCORE
        }

        if self in service_requirements:
            return "SERVICE_REQUIREMENT"
        elif self in complaints:
            return "COMPLAINT"
        elif self in operational:
            return "OPERATIONAL"
        elif self in quality:
            return "QUALITY"
        else:
            return "OTHER"

    @property
    def requires_action(self) -> bool:
        """Check if tag requires immediate action"""
        action_required = {
            self.ALTA_PRIORIDAD,
            self.REQUIERE_COORDINADOR,
            self.FUERA_COBERTURA,
            self.REPROGRAMACION_PENDIENTE
        }
        return self in action_required

    @classmethod
    def from_string(cls, value: str) -> 'ObservationTag':
        """
        Create ObservationTag from string

        Args:
            value: String representation (case-insensitive)

        Returns:
            ObservationTag enum value

        Raises:
            ValueError: If value is not a valid observation tag
        """
        try:
            return cls[value.upper()]
        except KeyError:
            valid_tags = ', '.join([t.value for t in cls])
            raise ValueError(
                f"Invalid observation tag: {value}. "
                f"Valid tags: {valid_tags}"
            )
