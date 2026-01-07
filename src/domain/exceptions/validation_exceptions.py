"""
Validation Exceptions

Exceptions for validation errors in the domain layer.
"""
from typing import List, Dict, Any


class ValidationException(Exception):
    """Base exception for validation errors"""

    def __init__(self, message: str, field: str = None):
        self.field = field
        super().__init__(message)


class RequiredFieldException(ValidationException):
    """Raised when a required field is missing"""

    def __init__(self, field: str):
        super().__init__(f"Required field missing: {field}", field)


class InvalidFormatException(ValidationException):
    """Raised when field format is invalid"""

    def __init__(self, field: str, expected_format: str):
        self.expected_format = expected_format
        super().__init__(
            f"Invalid format for {field}. Expected: {expected_format}",
            field
        )


class InvalidDocumentException(ValidationException):
    """Raised when document validation fails"""

    def __init__(self, document_type: str, document_number: str, reason: str):
        self.document_type = document_type
        self.document_number = document_number
        self.reason = reason
        super().__init__(
            f"Invalid document {document_type}:{document_number} - {reason}",
            "document"
        )


class InvalidPhoneNumberException(ValidationException):
    """Raised when phone number is invalid"""

    def __init__(self, phone: str):
        super().__init__(f"Invalid phone number: {phone}", "phone")


class InvalidDateException(ValidationException):
    """Raised when date is invalid"""

    def __init__(self, field: str, date_value: str, reason: str):
        self.date_value = date_value
        self.reason = reason
        super().__init__(
            f"Invalid date for {field}: {date_value} - {reason}",
            field
        )


class DateInPastException(InvalidDateException):
    """Raised when date is in the past but should be future"""

    def __init__(self, field: str, date_value: str):
        super().__init__(
            field,
            date_value,
            "Date cannot be in the past"
        )


class InvalidAddressException(ValidationException):
    """Raised when address is invalid"""

    def __init__(self, address: str, reason: str):
        self.address = address
        self.reason = reason
        super().__init__(
            f"Invalid address: {address} - {reason}",
            "address"
        )


class MultipleValidationException(ValidationException):
    """Raised when multiple validation errors occur"""

    def __init__(self, errors: List[ValidationException]):
        self.errors = errors
        error_messages = [str(e) for e in errors]
        super().__init__(
            f"Multiple validation errors: {'; '.join(error_messages)}"
        )

    def get_errors_by_field(self) -> Dict[str, List[str]]:
        """
        Get errors grouped by field

        Returns:
            Dict mapping field names to error messages
        """
        errors_by_field: Dict[str, List[str]] = {}
        for error in self.errors:
            field = getattr(error, 'field', 'general')
            if field not in errors_by_field:
                errors_by_field[field] = []
            errors_by_field[field].append(str(error))
        return errors_by_field
