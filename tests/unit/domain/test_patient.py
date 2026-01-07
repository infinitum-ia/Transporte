"""
Unit tests for Patient entity
"""
import pytest
from datetime import datetime
from src.domain.entities.patient import Patient
from src.domain.value_objects.patient_id import PatientId


class TestPatient:
    """Test suite for Patient entity"""

    @pytest.fixture
    def valid_patient_id(self):
        """Fixture for valid patient ID"""
        return PatientId(document_type="CC", document_number="1234567890")

    @pytest.fixture
    def valid_patient_data(self, valid_patient_id):
        """Fixture for valid patient data"""
        return {
            "id": valid_patient_id,
            "full_name": "Juan Pérez",
            "document_type": "CC",
            "document_number": "1234567890",
            "eps": "COSALUD",
            "is_responsible": True
        }

    def test_create_valid_patient(self, valid_patient_data):
        """Test creating valid patient"""
        patient = Patient(**valid_patient_data)

        assert patient.full_name == "Juan Pérez"
        assert patient.eps == "COSALUD"
        assert patient.is_responsible is True
        assert patient.responsible_name is None
        assert isinstance(patient.created_at, datetime)
        assert isinstance(patient.updated_at, datetime)

    def test_patient_eps_normalized_to_uppercase(self, valid_patient_id):
        """Test EPS is normalized to uppercase"""
        patient = Patient(
            id=valid_patient_id,
            full_name="Juan Pérez",
            document_type="CC",
            document_number="1234567890",
            eps="cosalud",  # lowercase
            is_responsible=True
        )

        assert patient.eps == "COSALUD"

    def test_patient_invalid_eps(self, valid_patient_id):
        """Test invalid EPS raises ValueError"""
        with pytest.raises(ValueError, match="Invalid EPS"):
            Patient(
                id=valid_patient_id,
                full_name="Juan Pérez",
                document_type="CC",
                document_number="1234567890",
                eps="SURA",
                is_responsible=True
            )

    def test_patient_empty_name(self, valid_patient_id):
        """Test empty name raises ValueError"""
        with pytest.raises(ValueError, match="name cannot be empty"):
            Patient(
                id=valid_patient_id,
                full_name="",
                document_type="CC",
                document_number="1234567890",
                eps="COSALUD",
                is_responsible=True
            )

    def test_patient_not_responsible_requires_name(self, valid_patient_id):
        """Test when patient is not responsible, responsible_name is required"""
        with pytest.raises(ValueError, match="Responsible party name is required"):
            Patient(
                id=valid_patient_id,
                full_name="Juan Pérez",
                document_type="CC",
                document_number="1234567890",
                eps="COSALUD",
                is_responsible=False,
                responsible_name=None
            )

    def test_patient_with_responsible_party(self, valid_patient_id):
        """Test patient with responsible party"""
        patient = Patient(
            id=valid_patient_id,
            full_name="Juan Pérez",
            document_type="CC",
            document_number="1234567890",
            eps="COSALUD",
            is_responsible=False,
            responsible_name="María Pérez"
        )

        assert patient.is_responsible is False
        assert patient.responsible_name == "María Pérez"

    def test_validate_eps_method(self, valid_patient_data):
        """Test validate_eps method"""
        patient = Patient(**valid_patient_data)
        assert patient.validate_eps() is True

        # Create patient with invalid EPS for testing
        # (bypassing validation for test)
        invalid_patient_data = valid_patient_data.copy()
        invalid_patient_data["eps"] = "SURA"

        with pytest.raises(ValueError):
            Patient(**invalid_patient_data)

    def test_update_contact_info(self, valid_patient_data):
        """Test updating contact information"""
        patient = Patient(**valid_patient_data)
        original_updated_at = patient.updated_at

        patient.update_contact_info("3001234567")

        assert patient.phone == "3001234567"
        assert patient.updated_at > original_updated_at

    def test_update_contact_info_with_empty_phone(self, valid_patient_data):
        """Test updating with empty phone does nothing"""
        patient = Patient(**valid_patient_data)
        patient.update_contact_info("")

        assert patient.phone is None

    def test_update_responsible_party(self, valid_patient_id):
        """Test updating responsible party name"""
        patient = Patient(
            id=valid_patient_id,
            full_name="Juan Pérez",
            document_type="CC",
            document_number="1234567890",
            eps="COSALUD",
            is_responsible=False,
            responsible_name="María Pérez"
        )

        patient.update_responsible_party("Pedro Pérez")
        assert patient.responsible_name == "Pedro Pérez"

    def test_update_responsible_party_when_is_responsible(self, valid_patient_data):
        """Test cannot update responsible party when patient calls directly"""
        patient = Patient(**valid_patient_data)

        with pytest.raises(ValueError, match="Cannot set responsible party"):
            patient.update_responsible_party("María Pérez")

    def test_update_responsible_party_empty_name(self, valid_patient_id):
        """Test updating responsible party with empty name raises error"""
        patient = Patient(
            id=valid_patient_id,
            full_name="Juan Pérez",
            document_type="CC",
            document_number="1234567890",
            eps="COSALUD",
            is_responsible=False,
            responsible_name="María Pérez"
        )

        with pytest.raises(ValueError, match="cannot be empty"):
            patient.update_responsible_party("")

    def test_get_contact_name_when_responsible(self, valid_patient_data):
        """Test get_contact_name when patient is responsible"""
        patient = Patient(**valid_patient_data)
        assert patient.get_contact_name() == "Juan Pérez"

    def test_get_contact_name_when_not_responsible(self, valid_patient_id):
        """Test get_contact_name when family member is responsible"""
        patient = Patient(
            id=valid_patient_id,
            full_name="Juan Pérez",
            document_type="CC",
            document_number="1234567890",
            eps="COSALUD",
            is_responsible=False,
            responsible_name="María Pérez"
        )

        assert patient.get_contact_name() == "María Pérez"

    def test_get_formal_treatment(self, valid_patient_data):
        """Test getting formal treatment name"""
        patient = Patient(**valid_patient_data)
        formal_name = patient.get_formal_treatment()

        # Should contain "Sr./Sra." and last name
        assert "Sr./Sra." in formal_name
        assert "Pérez" in formal_name

    def test_get_formal_treatment_single_name(self, valid_patient_id):
        """Test formal treatment with single name"""
        patient = Patient(
            id=valid_patient_id,
            full_name="Juan",
            document_type="CC",
            document_number="1234567890",
            eps="COSALUD",
            is_responsible=True
        )

        formal_name = patient.get_formal_treatment()
        assert "Sr./Sra. Juan" in formal_name

    def test_patient_to_dict(self, valid_patient_data):
        """Test converting patient to dictionary"""
        patient = Patient(**valid_patient_data)
        patient_dict = patient.to_dict()

        assert patient_dict["id"] == "CC:1234567890"
        assert patient_dict["full_name"] == "Juan Pérez"
        assert patient_dict["eps"] == "COSALUD"
        assert patient_dict["is_responsible"] is True
        assert "created_at" in patient_dict
        assert "updated_at" in patient_dict

    def test_patient_str_representation(self, valid_patient_data):
        """Test string representation"""
        patient = Patient(**valid_patient_data)
        str_repr = str(patient)

        assert "Juan Pérez" in str_repr
        assert "CC:1234567890" in str_repr

    def test_patient_repr_representation(self, valid_patient_data):
        """Test repr representation"""
        patient = Patient(**valid_patient_data)
        repr_str = repr(patient)

        assert "Patient" in repr_str
        assert "Juan Pérez" in repr_str
        assert "COSALUD" in repr_str
