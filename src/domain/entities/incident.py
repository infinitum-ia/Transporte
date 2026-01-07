"""
Incident Entity

Represents a complaint or issue reported by a user.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum
from ..value_objects.incident_type import IncidentType


class IncidentResolution(str, Enum):
    """Resolution status of an incident"""
    PENDING = "PENDING"  # Not yet addressed
    IN_PROGRESS = "IN_PROGRESS"  # Being worked on
    RESOLVED = "RESOLVED"  # Successfully resolved
    ESCALATED = "ESCALATED"  # Escalated to higher authority
    CLOSED = "CLOSED"  # Closed without resolution


@dataclass
class Incident:
    """
    Incident entity representing a user complaint or issue

    Business Rules from PRD (Section 6: Pain Points):
        - All complaints must be properly categorized
        - Severity determines handling priority
        - Some incidents require escalation to EPS
        - User fatigue from repeated complaints must be tracked

    Attributes:
        incident_id: Unique incident identifier
        session_id: ID of the conversation session
        patient_id: ID of the patient (optional if incident before identification)
        incident_type: Category of incident (IncidentType enum)
        description: Detailed description of the incident
        severity: Severity level (LOW, MEDIUM, HIGH)
        resolution_status: Current resolution status
        assigned_to: Person/team assigned to handle (optional)
        created_at: Incident creation timestamp
        updated_at: Last update timestamp
        resolved_at: Resolution timestamp (optional)
        resolution_notes: Notes about resolution (optional)
    """
    incident_id: str
    session_id: str
    incident_type: IncidentType
    description: str
    patient_id: Optional[str] = None
    severity: str = "MEDIUM"  # LOW, MEDIUM, HIGH
    resolution_status: IncidentResolution = IncidentResolution.PENDING
    assigned_to: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None

    def __post_init__(self):
        """Validate and initialize incident"""
        self._validate()
        # Set severity from incident type if not explicitly set
        if self.severity == "MEDIUM":
            object.__setattr__(self, 'severity', self.incident_type.severity_level)

    def _validate(self):
        """
        Validate incident entity

        Business Rules:
            - Description must not be empty
            - Severity must be LOW, MEDIUM, or HIGH
        """
        if not self.description or not self.description.strip():
            raise ValueError("Incident description cannot be empty")

        valid_severities = {"LOW", "MEDIUM", "HIGH"}
        if self.severity not in valid_severities:
            raise ValueError(
                f"Invalid severity: {self.severity}. "
                f"Must be one of {valid_severities}"
            )

    def requires_escalation(self) -> bool:
        """
        Check if incident requires escalation to EPS

        Business Rule from IncidentType:
            - Some types automatically require escalation
        """
        return self.incident_type.requires_escalation

    def is_high_severity(self) -> bool:
        """Check if incident is high severity"""
        return self.severity == "HIGH"

    def assign_to(self, assignee: str) -> None:
        """
        Assign incident to a person or team

        Args:
            assignee: Name of person/team to assign to
        """
        if not assignee or not assignee.strip():
            raise ValueError("Assignee cannot be empty")

        object.__setattr__(self, 'assigned_to', assignee.strip())
        object.__setattr__(self, 'resolution_status', IncidentResolution.IN_PROGRESS)
        object.__setattr__(self, 'updated_at', datetime.utcnow())

    def escalate(self, escalation_reason: Optional[str] = None) -> None:
        """
        Escalate incident to higher authority

        Args:
            escalation_reason: Optional reason for escalation

        Business Rule:
            - Updates status and timestamps
        """
        object.__setattr__(self, 'resolution_status', IncidentResolution.ESCALATED)
        object.__setattr__(self, 'updated_at', datetime.utcnow())

        if escalation_reason:
            notes = f"Escalated: {escalation_reason}"
            if self.resolution_notes:
                object.__setattr__(
                    self,
                    'resolution_notes',
                    f"{self.resolution_notes}\n{notes}"
                )
            else:
                object.__setattr__(self, 'resolution_notes', notes)

    def resolve(self, resolution_notes: str) -> None:
        """
        Mark incident as resolved

        Args:
            resolution_notes: Description of how incident was resolved

        Business Rule:
            - Must provide resolution notes
        """
        if not resolution_notes or not resolution_notes.strip():
            raise ValueError("Resolution notes are required")

        object.__setattr__(self, 'resolution_status', IncidentResolution.RESOLVED)
        object.__setattr__(self, 'resolved_at', datetime.utcnow())
        object.__setattr__(self, 'updated_at', datetime.utcnow())
        object.__setattr__(self, 'resolution_notes', resolution_notes.strip())

    def close(self, reason: Optional[str] = None) -> None:
        """
        Close incident without resolution

        Args:
            reason: Optional reason for closing

        Business Rule:
            - Can close without resolving (e.g., duplicate, invalid)
        """
        object.__setattr__(self, 'resolution_status', IncidentResolution.CLOSED)
        object.__setattr__(self, 'updated_at', datetime.utcnow())

        if reason:
            notes = f"Closed: {reason}"
            if self.resolution_notes:
                object.__setattr__(
                    self,
                    'resolution_notes',
                    f"{self.resolution_notes}\n{notes}"
                )
            else:
                object.__setattr__(self, 'resolution_notes', notes)

    def add_note(self, note: str) -> None:
        """
        Add note to incident

        Args:
            note: Note to add
        """
        if not note or not note.strip():
            return

        if self.resolution_notes:
            combined = f"{self.resolution_notes}\n{note}"
            object.__setattr__(self, 'resolution_notes', combined)
        else:
            object.__setattr__(self, 'resolution_notes', note.strip())

        object.__setattr__(self, 'updated_at', datetime.utcnow())

    def to_dict(self) -> dict:
        """Convert entity to dictionary"""
        return {
            "incident_id": self.incident_id,
            "session_id": self.session_id,
            "patient_id": self.patient_id,
            "incident_type": str(self.incident_type),
            "description": self.description,
            "severity": self.severity,
            "resolution_status": str(self.resolution_status),
            "assigned_to": self.assigned_to,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolution_notes": self.resolution_notes
        }

    def __str__(self) -> str:
        return (
            f"Incident({self.incident_id}, {self.incident_type}, "
            f"{self.severity}, {self.resolution_status})"
        )

    def __repr__(self) -> str:
        return (
            f"Incident(incident_id='{self.incident_id}', "
            f"incident_type={self.incident_type}, "
            f"severity='{self.severity}')"
        )
