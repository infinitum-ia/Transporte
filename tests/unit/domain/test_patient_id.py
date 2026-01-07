"""
Unit tests for PatientId value object
"""
import pytest
from src.domain.value_objects.patient_id import PatientId


class TestPatientId:
    """Test suite for PatientId value object"""

    def test_create_valid_patient_id(self):
        """Test creating valid PatientId"""
        patient_id = PatientId(document_type="CC", document_number="1234567890")

        assert patient_id.document_type == "CC"
        assert patient_id.document_number == "1234567890"

    def test_patient_id_all_valid_document_types(self):
        """Test all valid document types"""
        valid_types = ["CC", "TI", "CE", "PA"]

        for doc_type in valid_types:
            patient_id = PatientId(document_type=doc_type, document_number="123456")
            assert patient_id.document_type == doc_type

    def test_patient_id_invalid_document_type(self):
        """Test invalid document type raises ValueError"""
        with pytest.raises(ValueError, match="Invalid document type"):
            PatientId(document_type="INVALID", document_number="1234567890")

    def test_patient_id_empty_document_type(self):
        """Test empty document type raises ValueError"""
        with pytest.raises(ValueError, match="Invalid document type"):
            PatientId(document_type="", document_number="1234567890")

    def test_patient_id_empty_document_number(self):
        """Test empty document number raises ValueError"""
        with pytest.raises(ValueError, match="Document number cannot be empty"):
            PatientId(document_type="CC", document_number="")

    def test_patient_id_whitespace_document_number(self):
        """Test whitespace-only document number raises ValueError"""
        with pytest.raises(ValueError, match="Document number cannot be empty"):
            PatientId(document_type="CC", document_number="   ")

    def test_patient_id_non_alphanumeric_document_number(self):
        """Test non-alphanumeric characters (except hyphen) raise ValueError"""
        with pytest.raises(ValueError, match="must be alphanumeric"):
            PatientId(document_type="CC", document_number="123@456")

    def test_patient_id_with_hyphen(self):
        """Test document number with hyphen is valid"""
        patient_id = PatientId(document_type="CC", document_number="123-456")
        assert patient_id.document_number == "123-456"

    def test_patient_id_to_string(self):
        """Test conversion to string"""
        patient_id = PatientId(document_type="CC", document_number="1234567890")
        assert patient_id.to_string() == "CC:1234567890"

    def test_patient_id_from_string_valid(self):
        """Test creating PatientId from valid string"""
        id_string = "CC:1234567890"
        patient_id = PatientId.from_string(id_string)

        assert patient_id.document_type == "CC"
        assert patient_id.document_number == "1234567890"

    def test_patient_id_from_string_invalid_format(self):
        """Test from_string with invalid format raises ValueError"""
        with pytest.raises(ValueError, match="Invalid PatientId string format"):
            PatientId.from_string("CC1234567890")  # Missing colon

    def test_patient_id_from_string_missing_number(self):
        """Test from_string with missing number part"""
        with pytest.raises(ValueError, match="Invalid PatientId string format"):
            PatientId.from_string("CC:")

    def test_patient_id_str_method(self):
        """Test __str__ method"""
        patient_id = PatientId(document_type="CC", document_number="1234567890")
        assert str(patient_id) == "CC:1234567890"

    def test_patient_id_repr_method(self):
        """Test __repr__ method"""
        patient_id = PatientId(document_type="CC", document_number="1234567890")
        assert repr(patient_id) == "PatientId('CC:1234567890')"

    def test_patient_id_equality(self):
        """Test PatientId equality (frozen dataclass)"""
        id1 = PatientId(document_type="CC", document_number="1234567890")
        id2 = PatientId(document_type="CC", document_number="1234567890")
        id3 = PatientId(document_type="TI", document_number="1234567890")

        assert id1 == id2
        assert id1 != id3

    def test_patient_id_immutability(self):
        """Test PatientId is immutable (frozen)"""
        patient_id = PatientId(document_type="CC", document_number="1234567890")

        with pytest.raises(Exception):  # FrozenInstanceError
            patient_id.document_type = "TI"

    def test_patient_id_hashable(self):
        """Test PatientId is hashable (can be used in sets/dicts)"""
        id1 = PatientId(document_type="CC", document_number="1234567890")
        id2 = PatientId(document_type="CC", document_number="1234567890")

        # Should be able to use in set
        id_set = {id1, id2}
        assert len(id_set) == 1  # Both are equal, so set has 1 element
