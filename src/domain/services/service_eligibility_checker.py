"""
Service Eligibility Checker Domain Service

Validates if a service is eligible for a patient based on business rules.
"""
from datetime import date, datetime, timedelta
from typing import Tuple, List
from ..entities.patient import Patient
from ..value_objects.service_type import ServiceType
from ..value_objects.service_modality import ServiceModality
from ..exceptions.domain_exceptions import ServiceNotEligibleException


class ServiceEligibilityChecker:
    """
    Domain service for checking service eligibility

    Business Rules from PRD:
        - Patient must belong to EPS Cosalud
        - Service must have valid EPS authorization
        - Appointment date cannot be in the past
        - Some service types have special requirements
        - Coverage area limitations exist
    """

    # Minimum advance notice for service (in days)
    MIN_ADVANCE_NOTICE_DAYS = 0  # Same day allowed

    # Maximum advance scheduling (in days)
    MAX_ADVANCE_DAYS = 90  # 3 months

    def check_patient_eligibility(self, patient: Patient) -> Tuple[bool, str]:
        """
        Check if patient is eligible for services

        Args:
            patient: Patient entity

        Returns:
            Tuple of (is_eligible, reason)

        Business Rule:
            - Patient must belong to EPS Cosalud
        """
        if not patient.validate_eps():
            return False, f"Patient EPS is {patient.eps}. Only COSALUD patients are eligible."

        return True, ""

    def check_patient_eligibility_strict(self, patient: Patient) -> None:
        """
        Check patient eligibility and raise exception if not eligible

        Args:
            patient: Patient entity

        Raises:
            ServiceNotEligibleException: If patient not eligible
        """
        is_eligible, reason = self.check_patient_eligibility(patient)
        if not is_eligible:
            raise ServiceNotEligibleException(reason)

    def check_appointment_date(
        self,
        appointment_date: date
    ) -> Tuple[bool, str]:
        """
        Validate appointment date

        Args:
            appointment_date: Requested appointment date

        Returns:
            Tuple of (is_valid, reason)

        Business Rules:
            - Cannot be in the past
            - Cannot exceed maximum advance scheduling
        """
        today = datetime.now().date()

        # Check not in past
        if appointment_date < today:
            return False, f"Appointment date cannot be in the past: {appointment_date}"

        # Check not too far in future
        max_date = today + timedelta(days=self.MAX_ADVANCE_DAYS)
        if appointment_date > max_date:
            return False, f"Cannot schedule more than {self.MAX_ADVANCE_DAYS} days in advance"

        return True, ""

    def check_appointment_date_strict(self, appointment_date: date) -> None:
        """
        Validate appointment date and raise exception if invalid

        Args:
            appointment_date: Appointment date

        Raises:
            ServiceNotEligibleException: If date invalid
        """
        is_valid, reason = self.check_appointment_date(appointment_date)
        if not is_valid:
            raise ServiceNotEligibleException(reason)

    def check_service_type_requirements(
        self,
        service_type: ServiceType,
        special_requirements: str = None
    ) -> Tuple[bool, str]:
        """
        Check service type specific requirements

        Args:
            service_type: Type of service
            special_requirements: Special requirements if any

        Returns:
            Tuple of (is_eligible, reason)

        Business Rules:
            - DIALISIS is high priority
            - Some service types may require special vehicles
        """
        # High priority services (DIALISIS) should be flagged
        if service_type.is_high_priority:
            # This is informational, not blocking
            pass

        # All service types are generally eligible
        return True, ""

    def check_modality_requirements(
        self,
        service_modality: ServiceModality
    ) -> Tuple[bool, str]:
        """
        Check service modality requirements

        Args:
            service_modality: Service modality

        Returns:
            Tuple of (is_eligible, reason)

        Business Rules from PRD:
            - DESEMBOLSO requires document and code
            - DESEMBOLSO has 24-48h processing time
        """
        if service_modality.requires_documentation:
            return True, f"Modality {service_modality} requires documentation and has {service_modality.processing_time_hours}h processing time"

        return True, ""

    def check_address_coverage(self, address: str) -> Tuple[bool, str]:
        """
        Check if address is within coverage area

        Args:
            address: Pickup or destination address

        Returns:
            Tuple of (is_covered, reason)

        Business Rules from PRD (Section 6.5):
            - Rural zones may not be covered
            - Cities outside operational area require EPS escalation

        Note: This is a simplified implementation.
        Production would integrate with geolocation service.
        """
        if not address or not address.strip():
            return False, "Address cannot be empty"

        address_lower = address.lower()

        # Keywords indicating out of coverage (example heuristics)
        rural_keywords = ['vereda', 'rural', 'corregimiento']
        for keyword in rural_keywords:
            if keyword in address_lower:
                return False, f"Rural area may not be covered: {address}"

        # Cities known to be outside coverage (example)
        out_of_coverage_cities = ['bogotá', 'cali', 'cartagena']
        for city in out_of_coverage_cities:
            if city in address_lower:
                return False, f"City not in coverage area: {city}"

        return True, ""

    def check_full_eligibility(
        self,
        patient: Patient,
        service_type: ServiceType,
        service_modality: ServiceModality,
        appointment_date: date,
        pickup_address: str,
        destination_address: str
    ) -> List[str]:
        """
        Check complete eligibility for service

        Args:
            patient: Patient requesting service
            service_type: Type of service
            service_modality: Service modality
            appointment_date: Appointment date
            pickup_address: Pickup address
            destination_address: Destination address

        Returns:
            List of warning/error messages (empty if fully eligible)

        Business Rule:
            - Comprehensive eligibility check
        """
        issues: List[str] = []

        # Check patient eligibility
        is_eligible, reason = self.check_patient_eligibility(patient)
        if not is_eligible:
            issues.append(f"Patient eligibility: {reason}")

        # Check appointment date
        is_valid, reason = self.check_appointment_date(appointment_date)
        if not is_valid:
            issues.append(f"Appointment date: {reason}")

        # Check pickup address coverage
        is_covered, reason = self.check_address_coverage(pickup_address)
        if not is_covered:
            issues.append(f"Pickup address: {reason}")

        # Check destination address coverage
        is_covered, reason = self.check_address_coverage(destination_address)
        if not is_covered:
            issues.append(f"Destination address: {reason}")

        # Check modality requirements
        is_eligible, reason = self.check_modality_requirements(service_modality)
        if reason:
            issues.append(f"Modality: {reason}")

        return issues

    def is_fully_eligible(
        self,
        patient: Patient,
        service_type: ServiceType,
        service_modality: ServiceModality,
        appointment_date: date,
        pickup_address: str,
        destination_address: str
    ) -> bool:
        """
        Check if service is fully eligible (no blocking issues)

        Args:
            patient: Patient entity
            service_type: Service type
            service_modality: Service modality
            appointment_date: Appointment date
            pickup_address: Pickup address
            destination_address: Destination address

        Returns:
            bool: True if fully eligible
        """
        issues = self.check_full_eligibility(
            patient,
            service_type,
            service_modality,
            appointment_date,
            pickup_address,
            destination_address
        )

        # Filter for actual blocking issues (vs warnings)
        blocking_keywords = ['cannot', 'not eligible', 'not in coverage', 'empty']
        blocking_issues = [
            issue for issue in issues
            if any(keyword in issue.lower() for keyword in blocking_keywords)
        ]

        return len(blocking_issues) == 0
