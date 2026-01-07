"""
Incident Type Value Object

Represents the category of incidents/complaints reported by users.
"""
from enum import Enum


class IncidentType(str, Enum):
    """
    Categories of incidents and complaints

    Business Rules from PRD (Section 6: Pain Points):
        - QUEJA_CONDUCTOR: Driver-related complaints
        - IMPUNTUALIDAD: Late arrival or no-show
        - CONDUCTOR_ROTACION: Excessive driver rotation
        - VEHICULO_INADECUADO: Inadequate vehicle
        - FALTA_ESPACIO_SILLA: No space for wheelchair
        - ZONA_NO_CUBIERTA: Area not covered by service
        - USUARIO_FUERA_CIUDAD: User outside city limits
        - SERVICIO_NO_PRESTADO: Service not provided
        - CITA_REPROGRAMADA: Appointment rescheduled not reflected
        - FALLA_COMUNICACION: Communication failure
        - OTRO: Other unclassified incidents
    """
    QUEJA_CONDUCTOR = "QUEJA_CONDUCTOR"
    IMPUNTUALIDAD = "IMPUNTUALIDAD"
    CONDUCTOR_ROTACION = "CONDUCTOR_ROTACION"
    VEHICULO_INADECUADO = "VEHICULO_INADECUADO"
    FALTA_ESPACIO_SILLA = "FALTA_ESPACIO_SILLA"
    ZONA_NO_CUBIERTA = "ZONA_NO_CUBIERTA"
    USUARIO_FUERA_CIUDAD = "USUARIO_FUERA_CIUDAD"
    SERVICIO_NO_PRESTADO = "SERVICIO_NO_PRESTADO"
    CITA_REPROGRAMADA = "CITA_REPROGRAMADA"
    FALLA_COMUNICACION = "FALLA_COMUNICACION"
    OTRO = "OTRO"

    def __str__(self) -> str:
        return self.value

    @property
    def display_name(self) -> str:
        """Get human-readable display name"""
        display_names = {
            self.QUEJA_CONDUCTOR: "Queja del conductor",
            self.IMPUNTUALIDAD: "Impuntualidad",
            self.CONDUCTOR_ROTACION: "Rotación excesiva de conductores",
            self.VEHICULO_INADECUADO: "Vehículo inadecuado",
            self.FALTA_ESPACIO_SILLA: "Falta espacio para silla de ruedas",
            self.ZONA_NO_CUBIERTA: "Zona no cubierta",
            self.USUARIO_FUERA_CIUDAD: "Usuario fuera de la ciudad",
            self.SERVICIO_NO_PRESTADO: "Servicio no prestado",
            self.CITA_REPROGRAMADA: "Cita reprogramada no reflejada",
            self.FALLA_COMUNICACION: "Falla de comunicación",
            self.OTRO: "Otro"
        }
        return display_names.get(self, self.value)

    @property
    def requires_escalation(self) -> bool:
        """Check if incident type requires escalation to EPS"""
        escalation_types = {
            self.ZONA_NO_CUBIERTA,
            self.USUARIO_FUERA_CIUDAD,
            self.SERVICIO_NO_PRESTADO
        }
        return self in escalation_types

    @property
    def severity_level(self) -> str:
        """Get severity level of incident (LOW, MEDIUM, HIGH)"""
        high_severity = {
            self.SERVICIO_NO_PRESTADO,
            self.ZONA_NO_CUBIERTA,
            self.USUARIO_FUERA_CIUDAD
        }
        medium_severity = {
            self.IMPUNTUALIDAD,
            self.VEHICULO_INADECUADO,
            self.FALTA_ESPACIO_SILLA,
            self.CITA_REPROGRAMADA
        }

        if self in high_severity:
            return "HIGH"
        elif self in medium_severity:
            return "MEDIUM"
        else:
            return "LOW"

    @classmethod
    def from_string(cls, value: str) -> 'IncidentType':
        """
        Create IncidentType from string

        Args:
            value: String representation (case-insensitive)

        Returns:
            IncidentType enum value

        Raises:
            ValueError: If value is not a valid incident type
        """
        try:
            return cls[value.upper()]
        except KeyError:
            # Return OTRO for unrecognized types
            return cls.OTRO
