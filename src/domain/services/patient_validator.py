"""
Patient Validator Domain Service

Contains complex validation logic for patients that doesn't belong to the Patient entity.
"""
import re
from typing import List, Tuple
from ..exceptions.validation_exceptions import (
    ValidationException,
    InvalidDocumentException,
    InvalidPhoneNumberException,
    MultipleValidationException
)


class PatientValidator:
    """
    Domain service for patient validation

    Responsibilities:
        - Validate document types and formats
        - Validate phone numbers
        - Complex business rule validation
    """

    # Valid document types
    VALID_DOCUMENT_TYPES = {'CC', 'TI', 'CE', 'PA'}

    # Document number patterns by type
    DOCUMENT_PATTERNS = {
        'CC': r'^\d{7,10}$',  # Cédula: 7-10 digits
        'TI': r'^\d{10,11}$',  # Tarjeta de identidad: 10-11 digits
        'CE': r'^\d{6,10}$',   # Cédula extranjería: 6-10 digits
        'PA': r'^[A-Z]{2}\d{6,9}$'  # Passport: 2 letters + 6-9 digits
    }

    # Colombian phone pattern (mobile and landline)
    PHONE_PATTERN = r'^(\+?57)?[0-9]{7,10}$'

    def validate_document(
        self,
        document_type: str,
        document_number: str
    ) -> Tuple[bool, str]:
        """
        Validate document type and number

        Args:
            document_type: Type of document
            document_number: Document number

        Returns:
            Tuple of (is_valid, error_message)

        Business Rules:
            - Document type must be valid
            - Document number must match format for type
        """
        # Validate document type
        if not document_type or document_type.upper() not in self.VALID_DOCUMENT_TYPES:
            return False, f"Invalid document type: {document_type}. Valid types: {self.VALID_DOCUMENT_TYPES}"

        document_type = document_type.upper()

        # Validate document number
        if not document_number or not document_number.strip():
            return False, "Document number cannot be empty"

        document_number = document_number.strip().upper()

        # Check pattern
        pattern = self.DOCUMENT_PATTERNS.get(document_type)
        if pattern and not re.match(pattern, document_number):
            return False, f"Invalid format for {document_type}: {document_number}"

        return True, ""

    def validate_document_strict(
        self,
        document_type: str,
        document_number: str
    ) -> None:
        """
        Validate document and raise exception if invalid

        Args:
            document_type: Type of document
            document_number: Document number

        Raises:
            InvalidDocumentException: If validation fails
        """
        is_valid, error_message = self.validate_document(document_type, document_number)
        if not is_valid:
            raise InvalidDocumentException(document_type, document_number, error_message)

    def validate_phone(self, phone: str) -> Tuple[bool, str]:
        """
        Validate Colombian phone number

        Args:
            phone: Phone number to validate

        Returns:
            Tuple of (is_valid, error_message)

        Business Rules:
            - Must match Colombian phone format
            - Can include country code (+57)
            - 7-10 digits
        """
        if not phone or not phone.strip():
            return False, "Phone number cannot be empty"

        phone = phone.strip()

        if not re.match(self.PHONE_PATTERN, phone):
            return False, f"Invalid phone number format: {phone}"

        return True, ""

    def validate_phone_strict(self, phone: str) -> None:
        """
        Validate phone and raise exception if invalid

        Args:
            phone: Phone number

        Raises:
            InvalidPhoneNumberException: If validation fails
        """
        is_valid, error_message = self.validate_phone(phone)
        if not is_valid:
            raise InvalidPhoneNumberException(phone)

    def normalize_phone(self, phone: str) -> str:
        """
        Normalize phone number to standard format

        Args:
            phone: Phone number

        Returns:
            Normalized phone number (without country code, just digits)

        Business Rule:
            - Remove country code prefix
            - Remove non-digit characters
        """
        if not phone:
            return ""

        # Remove country code
        phone = phone.replace('+57', '').replace('+', '')

        # Remove non-digits
        phone = re.sub(r'\D', '', phone)

        return phone

    def validate_name(self, name: str) -> Tuple[bool, str]:
        """
        Validate person name

        Args:
            name: Full name

        Returns:
            Tuple of (is_valid, error_message)

        Business Rules:
            - Cannot be empty
            - Must have at least 2 characters
            - Should contain only letters, spaces, and common accents
        """
        if not name or not name.strip():
            return False, "Name cannot be empty"

        name = name.strip()

        if len(name) < 2:
            return False, "Name must be at least 2 characters"

        # Allow letters, spaces, accents, hyphens, apostrophes
        if not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s\-'\.]+$", name):
            return False, f"Name contains invalid characters: {name}"

        return True, ""

    def validate_patient_data(
        self,
        full_name: str,
        document_type: str,
        document_number: str,
        phone: str = None
    ) -> None:
        """
        Validate complete patient data

        Args:
            full_name: Patient full name
            document_type: Document type
            document_number: Document number
            phone: Optional phone number

        Raises:
            MultipleValidationException: If multiple validations fail

        Business Rule:
            - Aggregate validation for all patient fields
        """
        errors: List[ValidationException] = []

        # Validate name
        is_valid, error = self.validate_name(full_name)
        if not is_valid:
            errors.append(ValidationException(error, "full_name"))

        # Validate document
        is_valid, error = self.validate_document(document_type, document_number)
        if not is_valid:
            errors.append(InvalidDocumentException(document_type, document_number, error))

        # Validate phone if provided
        if phone:
            is_valid, error = self.validate_phone(phone)
            if not is_valid:
                errors.append(InvalidPhoneNumberException(phone))

        if errors:
            raise MultipleValidationException(errors)
