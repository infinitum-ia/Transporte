"""
Escalation Rules Domain Service

Determines when and why requests should be escalated to EPS Cosalud.
"""
from typing import Tuple, List
from ..value_objects.incident_type import IncidentType
from ..value_objects.service_type import ServiceType
from ..exceptions.domain_exceptions import EscalationRequiredException


class EscalationRules:
    """
    Domain service for escalation logic

    Business Rules from PRD (Section 7.3: Redireccionamiento a EPS):
        - Service express requests (not available)
        - Out of coverage zones
        - Missing EPS authorization
        - Patient outside city
        - Certain incident types require escalation
    """

    def __init__(self):
        # Incident types that automatically require escalation
        self.auto_escalation_incident_types = {
            IncidentType.ZONA_NO_CUBIERTA,
            IncidentType.USUARIO_FUERA_CIUDAD,
            IncidentType.SERVICIO_NO_PRESTADO
        }

        # Keywords in user messages that indicate escalation need
        self.escalation_keywords = [
            'servicio expreso',
            'servicio express',
            'urgente ya',
            'inmediato',
            'fuera de la ciudad',
            'zona rural',
            'no autorizado',
            'sin autorización',
            'zona no cubierta'
        ]

    def should_escalate_for_incident(
        self,
        incident_type: IncidentType
    ) -> Tuple[bool, str]:
        """
        Check if incident type requires escalation

        Args:
            incident_type: Type of incident

        Returns:
            Tuple of (should_escalate, reason)

        Business Rule:
            - Certain incident types require EPS intervention
        """
        if incident_type in self.auto_escalation_incident_types:
            return True, f"Incident type {incident_type.display_name} requires EPS escalation"

        return False, ""

    def should_escalate_for_coverage(
        self,
        address: str
    ) -> Tuple[bool, str]:
        """
        Check if address is out of coverage and requires escalation

        Args:
            address: Address to check

        Returns:
            Tuple of (should_escalate, reason)

        Business Rules:
            - Rural areas may require escalation
            - Out of city requires escalation
        """
        if not address or not address.strip():
            return False, ""

        address_lower = address.lower()

        # Rural area indicators
        rural_keywords = ['vereda', 'rural', 'corregimiento', 'campo']
        for keyword in rural_keywords:
            if keyword in address_lower:
                return True, f"Rural area outside coverage: {address}"

        # Cities outside operational area
        out_of_coverage_cities = ['bogotá', 'cali', 'cartagena', 'barranquilla']
        for city in out_of_coverage_cities:
            if city in address_lower:
                return True, f"City outside operational area: {city}"

        return False, ""

    def should_escalate_for_service_type(
        self,
        service_type: ServiceType,
        is_express_requested: bool = False
    ) -> Tuple[bool, str]:
        """
        Check if service type requires escalation

        Args:
            service_type: Type of service requested
            is_express_requested: Whether express/urgent service was requested

        Returns:
            Tuple of (should_escalate, reason)

        Business Rules from PRD:
            - Express service requests require EPS contact
            - All services require EPS authorization
        """
        if is_express_requested:
            return True, "Express/urgent service is not available. Contact EPS Cosalud for alternatives."

        return False, ""

    def should_escalate_from_message(
        self,
        user_message: str
    ) -> Tuple[bool, str]:
        """
        Detect if user message indicates escalation need

        Args:
            user_message: User's message

        Returns:
            Tuple of (should_escalate, reason)

        Business Rule:
            - Certain keywords indicate requests beyond operational scope
        """
        if not user_message or not user_message.strip():
            return False, ""

        message_lower = user_message.lower()

        for keyword in self.escalation_keywords:
            if keyword in message_lower:
                return True, f"Request contains '{keyword}' which requires EPS coordination"

        return False, ""

    def should_escalate_for_authorization(
        self,
        has_authorization: bool
    ) -> Tuple[bool, str]:
        """
        Check if lack of authorization requires escalation

        Args:
            has_authorization: Whether service has EPS authorization

        Returns:
            Tuple of (should_escalate, reason)

        Business Rule from PRD (Section 8):
            - No service can be coordinated without EPS authorization
        """
        if not has_authorization:
            return True, "Service requires EPS Cosalud authorization. Contact EPS to obtain authorization."

        return False, ""

    def check_escalation_needed(
        self,
        incident_type: IncidentType = None,
        pickup_address: str = None,
        destination_address: str = None,
        service_type: ServiceType = None,
        is_express_requested: bool = False,
        has_authorization: bool = True,
        user_message: str = None
    ) -> Tuple[bool, List[str]]:
        """
        Comprehensive escalation check

        Args:
            incident_type: Optional incident type
            pickup_address: Optional pickup address
            destination_address: Optional destination address
            service_type: Optional service type
            is_express_requested: Whether express service requested
            has_authorization: Whether service has authorization
            user_message: Optional user message to analyze

        Returns:
            Tuple of (should_escalate, list_of_reasons)

        Business Rule:
            - Aggregates all escalation rules
        """
        reasons: List[str] = []

        # Check incident type
        if incident_type:
            should_escalate, reason = self.should_escalate_for_incident(incident_type)
            if should_escalate:
                reasons.append(reason)

        # Check pickup address coverage
        if pickup_address:
            should_escalate, reason = self.should_escalate_for_coverage(pickup_address)
            if should_escalate:
                reasons.append(reason)

        # Check destination address coverage
        if destination_address:
            should_escalate, reason = self.should_escalate_for_coverage(destination_address)
            if should_escalate:
                reasons.append(reason)

        # Check service type
        if service_type:
            should_escalate, reason = self.should_escalate_for_service_type(
                service_type,
                is_express_requested
            )
            if should_escalate:
                reasons.append(reason)

        # Check authorization
        should_escalate, reason = self.should_escalate_for_authorization(has_authorization)
        if should_escalate:
            reasons.append(reason)

        # Check user message
        if user_message:
            should_escalate, reason = self.should_escalate_from_message(user_message)
            if should_escalate:
                reasons.append(reason)

        return len(reasons) > 0, reasons

    def get_escalation_instructions(self, reasons: List[str]) -> str:
        """
        Get instructions for user on how to escalate to EPS

        Args:
            reasons: List of escalation reasons

        Returns:
            str: Instructions for contacting EPS

        Business Rule:
            - Provide clear guidance for EPS contact
        """
        base_message = (
            "Su solicitud requiere coordinación directa con EPS Cosalud. "
            "Por favor contacte a su EPS a través de: "
            "Línea de atención: 018000-123456 o "
            "su portal web: www.cosalud.com.co"
        )

        if reasons:
            reason_text = "\n\nMotivo(s):\n- " + "\n- ".join(reasons)
            return base_message + reason_text

        return base_message

    def raise_if_escalation_required(
        self,
        incident_type: IncidentType = None,
        pickup_address: str = None,
        destination_address: str = None,
        service_type: ServiceType = None,
        is_express_requested: bool = False,
        has_authorization: bool = True,
        user_message: str = None
    ) -> None:
        """
        Check escalation and raise exception if needed

        Args:
            (same as check_escalation_needed)

        Raises:
            EscalationRequiredException: If escalation is required

        Business Rule:
            - Blocks operation if escalation needed
        """
        should_escalate, reasons = self.check_escalation_needed(
            incident_type,
            pickup_address,
            destination_address,
            service_type,
            is_express_requested,
            has_authorization,
            user_message
        )

        if should_escalate:
            reason_text = "; ".join(reasons)
            raise EscalationRequiredException(reason_text)
