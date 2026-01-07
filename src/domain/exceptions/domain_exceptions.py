"""
Domain Exceptions

Business logic exceptions for the domain layer.
"""


class DomainException(Exception):
    """Base exception for all domain-related errors"""
    pass


class EntityNotFoundException(DomainException):
    """Raised when an entity is not found"""

    def __init__(self, entity_type: str, entity_id: str):
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(f"{entity_type} not found: {entity_id}")


class PatientNotFoundException(EntityNotFoundException):
    """Raised when a patient is not found"""

    def __init__(self, patient_id: str):
        super().__init__("Patient", patient_id)


class ServiceNotFoundException(EntityNotFoundException):
    """Raised when a service is not found"""

    def __init__(self, service_id: str):
        super().__init__("Service", service_id)


class IncidentNotFoundException(EntityNotFoundException):
    """Raised when an incident is not found"""

    def __init__(self, incident_id: str):
        super().__init__("Incident", incident_id)


class SessionNotFoundException(EntityNotFoundException):
    """Raised when a session is not found"""

    def __init__(self, session_id: str):
        super().__init__("Session", session_id)


class EntityAlreadyExistsException(DomainException):
    """Raised when attempting to create an entity that already exists"""

    def __init__(self, entity_type: str, entity_id: str):
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(f"{entity_type} already exists: {entity_id}")


class InvalidEPSException(DomainException):
    """Raised when patient EPS is not COSALUD"""

    def __init__(self, eps: str):
        self.eps = eps
        super().__init__(
            f"Invalid EPS: {eps}. Only COSALUD patients are served by Transformas."
        )


class InvalidTransitionException(DomainException):
    """Raised when attempting an invalid state transition"""

    def __init__(self, from_state: str, to_state: str):
        self.from_state = from_state
        self.to_state = to_state
        super().__init__(
            f"Invalid transition from {from_state} to {to_state}"
        )


class SessionExpiredException(DomainException):
    """Raised when attempting to use an expired session"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        super().__init__(f"Session has expired: {session_id}")


class SessionInactiveException(DomainException):
    """Raised when attempting to use an inactive session"""

    def __init__(self, session_id: str, reason: str):
        self.session_id = session_id
        self.reason = reason
        super().__init__(f"Session is inactive: {session_id}. Reason: {reason}")


class MaxTurnsExceededException(DomainException):
    """Raised when session exceeds maximum allowed turns"""

    def __init__(self, session_id: str, max_turns: int):
        self.session_id = session_id
        self.max_turns = max_turns
        super().__init__(
            f"Session {session_id} has exceeded maximum turns ({max_turns})"
        )


class InvalidOperationException(DomainException):
    """Raised when attempting an invalid operation"""

    def __init__(self, operation: str, reason: str):
        self.operation = operation
        self.reason = reason
        super().__init__(f"Invalid operation '{operation}': {reason}")


class BusinessRuleViolationException(DomainException):
    """Raised when a business rule is violated"""

    def __init__(self, rule: str, details: str):
        self.rule = rule
        self.details = details
        super().__init__(f"Business rule violated - {rule}: {details}")


class ServiceNotEligibleException(BusinessRuleViolationException):
    """Raised when service is not eligible for patient"""

    def __init__(self, reason: str):
        super().__init__(
            "Service Eligibility",
            f"Service not eligible: {reason}"
        )


class EscalationRequiredException(DomainException):
    """Raised when a request requires escalation to EPS"""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(
            f"Request requires escalation to EPS Cosalud: {reason}"
        )


class OutOfCoverageAreaException(EscalationRequiredException):
    """Raised when requested area is outside coverage"""

    def __init__(self, address: str):
        self.address = address
        super().__init__(f"Address outside coverage area: {address}")
