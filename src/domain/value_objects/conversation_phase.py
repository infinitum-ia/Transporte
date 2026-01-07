"""
Conversation Phase Value Object

Represents the current phase of the conversation flow.
"""
from enum import Enum
from typing import List, Optional


class ConversationPhase(str, Enum):
    """
    Phases of the conversation flow

    Business Rules from PRD (Section 5: Core Flow):

    INBOUND CALLS (Customer calls us):
        1. GREETING: Initial greeting and agent identification
        2. IDENTIFICATION: Patient identity validation
        3. LEGAL_NOTICE: Recording notice and consent
        4. SERVICE_COORDINATION: Service scheduling and logistics
        5. INCIDENT_MANAGEMENT: Handling complaints and issues
        6. ESCALATION: Redirecting to EPS for out-of-scope requests
        7. CLOSING: Closing statements and final questions
        8. SURVEY: Quality survey
        9. END: Conversation completed

    OUTBOUND CALLS (We call customer for service confirmation):
        1. OUTBOUND_GREETING: Agent identifies, verifies contact
        2. OUTBOUND_LEGAL_NOTICE: Recording notice
        3. OUTBOUND_SERVICE_CONFIRMATION: Confirm scheduled service
        4. OUTBOUND_SPECIAL_CASES: Handle date changes, complaints, special needs
        5. OUTBOUND_CLOSING: Final questions and farewell
        6. END: Call completed
    """
    # INBOUND PHASES (existing)
    GREETING = "GREETING"
    IDENTIFICATION = "IDENTIFICATION"
    LEGAL_NOTICE = "LEGAL_NOTICE"
    SERVICE_COORDINATION = "SERVICE_COORDINATION"
    INCIDENT_MANAGEMENT = "INCIDENT_MANAGEMENT"
    ESCALATION = "ESCALATION"
    CLOSING = "CLOSING"
    SURVEY = "SURVEY"
    END = "END"

    # OUTBOUND PHASES (new)
    OUTBOUND_GREETING = "OUTBOUND_GREETING"
    OUTBOUND_LEGAL_NOTICE = "OUTBOUND_LEGAL_NOTICE"
    OUTBOUND_SERVICE_CONFIRMATION = "OUTBOUND_SERVICE_CONFIRMATION"
    OUTBOUND_SPECIAL_CASES = "OUTBOUND_SPECIAL_CASES"
    OUTBOUND_CLOSING = "OUTBOUND_CLOSING"

    def __str__(self) -> str:
        return self.value

    @property
    def display_name(self) -> str:
        """Get human-readable display name"""
        display_names = {
            # Inbound phases
            self.GREETING: "Saludo",
            self.IDENTIFICATION: "Identificación",
            self.LEGAL_NOTICE: "Aviso Legal",
            self.SERVICE_COORDINATION: "Coordinación de Servicio",
            self.INCIDENT_MANAGEMENT: "Gestión de Incidencias",
            self.ESCALATION: "Escalamiento a EPS",
            self.CLOSING: "Cierre",
            self.SURVEY: "Encuesta",
            self.END: "Finalizado",
            # Outbound phases
            self.OUTBOUND_GREETING: "Saludo e Identificación (Saliente)",
            self.OUTBOUND_LEGAL_NOTICE: "Aviso Legal (Saliente)",
            self.OUTBOUND_SERVICE_CONFIRMATION: "Confirmación de Servicio",
            self.OUTBOUND_SPECIAL_CASES: "Casos Especiales",
            self.OUTBOUND_CLOSING: "Cierre (Saliente)"
        }
        return display_names.get(self, self.value)

    @property
    def sequence_order(self) -> int:
        """Get the typical order in conversation flow"""
        order = {
            self.GREETING: 1,
            self.IDENTIFICATION: 2,
            self.LEGAL_NOTICE: 3,
            self.SERVICE_COORDINATION: 4,
            self.INCIDENT_MANAGEMENT: 5,
            self.ESCALATION: 6,
            self.CLOSING: 7,
            self.SURVEY: 8,
            self.END: 9
        }
        return order.get(self, 0)

    @property
    def is_terminal(self) -> bool:
        """Check if this is a terminal phase (conversation cannot continue)"""
        return self == ConversationPhase.END

    @property
    def is_optional(self) -> bool:
        """Check if this phase can be skipped in the flow"""
        optional_phases = {
            self.INCIDENT_MANAGEMENT,
            self.ESCALATION
        }
        return self in optional_phases

    @property
    def requires_user_input(self) -> bool:
        """Check if this phase requires user input"""
        # END doesn't require input
        return self != ConversationPhase.END

    def can_transition_to(self, next_phase: 'ConversationPhase') -> bool:
        """
        Check if transition to next_phase is valid

        Args:
            next_phase: The phase to transition to

        Returns:
            bool: True if transition is valid

        Business Rules:
            - Generally follows sequence order
            - Can loop back to SERVICE_COORDINATION from INCIDENT_MANAGEMENT
            - Can skip optional phases
            - Cannot return to earlier phases (except SERVICE_COORDINATION)
            - Cannot leave END phase
        """
        if self == ConversationPhase.END:
            return False  # Cannot leave END

        # Allow transition to same phase (loop)
        if self == next_phase:
            return True

        # Allow specific valid transitions
        valid_transitions = {
            # Inbound flow
            self.GREETING: [self.IDENTIFICATION],
            self.IDENTIFICATION: [self.LEGAL_NOTICE, self.ESCALATION],
            self.LEGAL_NOTICE: [self.SERVICE_COORDINATION],
            self.SERVICE_COORDINATION: [
                self.INCIDENT_MANAGEMENT,
                self.ESCALATION,
                self.CLOSING
            ],
            self.INCIDENT_MANAGEMENT: [
                self.SERVICE_COORDINATION,  # Loop back
                self.ESCALATION,
                self.CLOSING
            ],
            self.ESCALATION: [self.CLOSING],
            self.CLOSING: [self.SURVEY],
            self.SURVEY: [self.END],

            # Outbound flow
            self.OUTBOUND_GREETING: [self.OUTBOUND_LEGAL_NOTICE],
            # Allow jumping to special cases if user raises an issue early (complaints, date change, etc.)
            self.OUTBOUND_LEGAL_NOTICE: [self.OUTBOUND_SERVICE_CONFIRMATION, self.OUTBOUND_SPECIAL_CASES],
            self.OUTBOUND_SERVICE_CONFIRMATION: [
                self.OUTBOUND_SPECIAL_CASES,  # If user has questions/issues
                self.OUTBOUND_CLOSING  # Direct to closing if all confirmed
            ],
            self.OUTBOUND_SPECIAL_CASES: [
                self.OUTBOUND_SERVICE_CONFIRMATION,  # Loop back to confirm changes
                self.OUTBOUND_CLOSING
            ],
            self.OUTBOUND_CLOSING: [self.END]  # Outbound calls skip survey
        }

        return next_phase in valid_transitions.get(self, [])

    def get_next_phases(self) -> List['ConversationPhase']:
        """Get list of valid next phases from current phase"""
        transitions = {
            # Inbound flow
            self.GREETING: [self.IDENTIFICATION],
            self.IDENTIFICATION: [self.LEGAL_NOTICE, self.ESCALATION],
            self.LEGAL_NOTICE: [self.SERVICE_COORDINATION],
            self.SERVICE_COORDINATION: [
                self.INCIDENT_MANAGEMENT,
                self.ESCALATION,
                self.CLOSING
            ],
            self.INCIDENT_MANAGEMENT: [
                self.SERVICE_COORDINATION,
                self.ESCALATION,
                self.CLOSING
            ],
            self.ESCALATION: [self.CLOSING],
            self.CLOSING: [self.SURVEY],
            self.SURVEY: [self.END],
            self.END: [],

            # Outbound flow
            self.OUTBOUND_GREETING: [self.OUTBOUND_LEGAL_NOTICE],
            self.OUTBOUND_LEGAL_NOTICE: [self.OUTBOUND_SERVICE_CONFIRMATION, self.OUTBOUND_SPECIAL_CASES],
            self.OUTBOUND_SERVICE_CONFIRMATION: [
                self.OUTBOUND_SPECIAL_CASES,
                self.OUTBOUND_CLOSING
            ],
            self.OUTBOUND_SPECIAL_CASES: [
                self.OUTBOUND_SERVICE_CONFIRMATION,
                self.OUTBOUND_CLOSING
            ],
            self.OUTBOUND_CLOSING: [self.END]
        }
        return transitions.get(self, [])

    @classmethod
    def from_string(cls, value: str) -> 'ConversationPhase':
        """
        Create ConversationPhase from string

        Args:
            value: String representation (case-insensitive)

        Returns:
            ConversationPhase enum value

        Raises:
            ValueError: If value is not a valid phase
        """
        try:
            return cls[value.upper()]
        except KeyError:
            valid_phases = ', '.join([p.value for p in cls])
            raise ValueError(
                f"Invalid conversation phase: {value}. "
                f"Valid phases: {valid_phases}"
            )
