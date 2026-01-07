"""
Unit tests for value objects (ServiceType, ServiceModality, IncidentType, ObservationTag, ConversationPhase)
"""
import pytest
from src.domain.value_objects.service_type import ServiceType
from src.domain.value_objects.service_modality import ServiceModality
from src.domain.value_objects.incident_type import IncidentType
from src.domain.value_objects.observation_tag import ObservationTag
from src.domain.value_objects.conversation_phase import ConversationPhase


class TestServiceType:
    """Test suite for ServiceType enum"""

    def test_service_type_values(self):
        """Test all service type values"""
        assert ServiceType.TERAPIA.value == "TERAPIA"
        assert ServiceType.DIALISIS.value == "DIALISIS"
        assert ServiceType.CONSULTA_ESPECIALIZADA.value == "CONSULTA_ESPECIALIZADA"

    def test_service_type_display_names(self):
        """Test display names"""
        assert ServiceType.TERAPIA.display_name == "Terapia"
        assert ServiceType.DIALISIS.display_name == "Diálisis"
        assert ServiceType.CONSULTA_ESPECIALIZADA.display_name == "Consulta Especializada"

    def test_service_type_high_priority(self):
        """Test high priority detection"""
        assert ServiceType.DIALISIS.is_high_priority is True
        assert ServiceType.TERAPIA.is_high_priority is False
        assert ServiceType.CONSULTA_ESPECIALIZADA.is_high_priority is False

    def test_service_type_from_string(self):
        """Test creating ServiceType from string"""
        assert ServiceType.from_string("terapia") == ServiceType.TERAPIA
        assert ServiceType.from_string("DIALISIS") == ServiceType.DIALISIS
        assert ServiceType.from_string("Consulta_Especializada") == ServiceType.CONSULTA_ESPECIALIZADA

    def test_service_type_from_string_invalid(self):
        """Test invalid string raises ValueError"""
        with pytest.raises(ValueError, match="Invalid service type"):
            ServiceType.from_string("INVALID")

    def test_service_type_str(self):
        """Test string representation"""
        assert str(ServiceType.TERAPIA) == "TERAPIA"


class TestServiceModality:
    """Test suite for ServiceModality enum"""

    def test_service_modality_values(self):
        """Test all modality values"""
        assert ServiceModality.RUTA_COMPARTIDA.value == "RUTA_COMPARTIDA"
        assert ServiceModality.DESEMBOLSO.value == "DESEMBOLSO"

    def test_service_modality_display_names(self):
        """Test display names"""
        assert ServiceModality.RUTA_COMPARTIDA.display_name == "Ruta Compartida"
        assert ServiceModality.DESEMBOLSO.display_name == "Desembolso"

    def test_service_modality_requires_documentation(self):
        """Test documentation requirement"""
        assert ServiceModality.DESEMBOLSO.requires_documentation is True
        assert ServiceModality.RUTA_COMPARTIDA.requires_documentation is False

    def test_service_modality_processing_time(self):
        """Test processing time"""
        assert ServiceModality.DESEMBOLSO.processing_time_hours == 24
        assert ServiceModality.RUTA_COMPARTIDA.processing_time_hours == 0

    def test_service_modality_from_string(self):
        """Test creating from string"""
        assert ServiceModality.from_string("ruta_compartida") == ServiceModality.RUTA_COMPARTIDA
        assert ServiceModality.from_string("DESEMBOLSO") == ServiceModality.DESEMBOLSO

    def test_service_modality_from_string_invalid(self):
        """Test invalid string raises ValueError"""
        with pytest.raises(ValueError, match="Invalid service modality"):
            ServiceModality.from_string("INVALID")


class TestIncidentType:
    """Test suite for IncidentType enum"""

    def test_incident_type_values(self):
        """Test key incident type values"""
        assert IncidentType.QUEJA_CONDUCTOR.value == "QUEJA_CONDUCTOR"
        assert IncidentType.IMPUNTUALIDAD.value == "IMPUNTUALIDAD"
        assert IncidentType.ZONA_NO_CUBIERTA.value == "ZONA_NO_CUBIERTA"

    def test_incident_type_display_names(self):
        """Test display names"""
        assert IncidentType.QUEJA_CONDUCTOR.display_name == "Queja del conductor"
        assert IncidentType.IMPUNTUALIDAD.display_name == "Impuntualidad"

    def test_incident_type_requires_escalation(self):
        """Test escalation requirement"""
        assert IncidentType.ZONA_NO_CUBIERTA.requires_escalation is True
        assert IncidentType.USUARIO_FUERA_CIUDAD.requires_escalation is True
        assert IncidentType.SERVICIO_NO_PRESTADO.requires_escalation is True
        assert IncidentType.QUEJA_CONDUCTOR.requires_escalation is False
        assert IncidentType.IMPUNTUALIDAD.requires_escalation is False

    def test_incident_type_severity_level(self):
        """Test severity levels"""
        assert IncidentType.SERVICIO_NO_PRESTADO.severity_level == "HIGH"
        assert IncidentType.ZONA_NO_CUBIERTA.severity_level == "HIGH"
        assert IncidentType.IMPUNTUALIDAD.severity_level == "MEDIUM"
        assert IncidentType.VEHICULO_INADECUADO.severity_level == "MEDIUM"
        assert IncidentType.QUEJA_CONDUCTOR.severity_level == "LOW"

    def test_incident_type_from_string_valid(self):
        """Test creating from valid string"""
        assert IncidentType.from_string("queja_conductor") == IncidentType.QUEJA_CONDUCTOR

    def test_incident_type_from_string_invalid_returns_otro(self):
        """Test invalid string returns OTRO"""
        assert IncidentType.from_string("invalid_type") == IncidentType.OTRO


class TestObservationTag:
    """Test suite for ObservationTag enum"""

    def test_observation_tag_values(self):
        """Test key observation tag values"""
        assert ObservationTag.NECESITA_CARRO_GRANDE.value == "NECESITA_CARRO_GRANDE"
        assert ObservationTag.ALTA_PRIORIDAD.value == "ALTA_PRIORIDAD"
        assert ObservationTag.SURVEY_SCORE.value == "SURVEY_SCORE"

    def test_observation_tag_display_names(self):
        """Test display names"""
        assert ObservationTag.NECESITA_CARRO_GRANDE.display_name == "Necesita carro grande"
        assert ObservationTag.ALTA_PRIORIDAD.display_name == "Alta prioridad"

    def test_observation_tag_categories(self):
        """Test tag categories"""
        assert ObservationTag.NECESITA_CARRO_GRANDE.category == "SERVICE_REQUIREMENT"
        assert ObservationTag.NECESITA_SILLA_RUEDAS.category == "SERVICE_REQUIREMENT"
        assert ObservationTag.QUEJA_CONDUCTOR.category == "COMPLAINT"
        assert ObservationTag.QUEJA_VEHICULO.category == "COMPLAINT"
        assert ObservationTag.ALTA_PRIORIDAD.category == "OPERATIONAL"
        assert ObservationTag.SURVEY_SCORE.category == "QUALITY"

    def test_observation_tag_requires_action(self):
        """Test action requirement"""
        assert ObservationTag.ALTA_PRIORIDAD.requires_action is True
        assert ObservationTag.REQUIERE_COORDINADOR.requires_action is True
        assert ObservationTag.FUERA_COBERTURA.requires_action is True
        assert ObservationTag.NECESITA_CARRO_GRANDE.requires_action is False
        assert ObservationTag.SURVEY_SCORE.requires_action is False

    def test_observation_tag_from_string(self):
        """Test creating from string"""
        assert ObservationTag.from_string("necesita_carro_grande") == ObservationTag.NECESITA_CARRO_GRANDE

    def test_observation_tag_from_string_invalid(self):
        """Test invalid string raises ValueError"""
        with pytest.raises(ValueError, match="Invalid observation tag"):
            ObservationTag.from_string("invalid_tag")


class TestConversationPhase:
    """Test suite for ConversationPhase enum"""

    def test_conversation_phase_values(self):
        """Test all phase values"""
        assert ConversationPhase.GREETING.value == "GREETING"
        assert ConversationPhase.IDENTIFICATION.value == "IDENTIFICATION"
        assert ConversationPhase.END.value == "END"

    def test_conversation_phase_display_names(self):
        """Test display names"""
        assert ConversationPhase.GREETING.display_name == "Saludo"
        assert ConversationPhase.IDENTIFICATION.display_name == "Identificación"
        assert ConversationPhase.END.display_name == "Finalizado"

    def test_conversation_phase_sequence_order(self):
        """Test sequence order"""
        assert ConversationPhase.GREETING.sequence_order == 1
        assert ConversationPhase.IDENTIFICATION.sequence_order == 2
        assert ConversationPhase.LEGAL_NOTICE.sequence_order == 3
        assert ConversationPhase.END.sequence_order == 9

    def test_conversation_phase_is_terminal(self):
        """Test terminal phase detection"""
        assert ConversationPhase.END.is_terminal is True
        assert ConversationPhase.GREETING.is_terminal is False
        assert ConversationPhase.SURVEY.is_terminal is False

    def test_conversation_phase_is_optional(self):
        """Test optional phase detection"""
        assert ConversationPhase.INCIDENT_MANAGEMENT.is_optional is True
        assert ConversationPhase.ESCALATION.is_optional is True
        assert ConversationPhase.GREETING.is_optional is False
        assert ConversationPhase.CLOSING.is_optional is False

    def test_conversation_phase_requires_user_input(self):
        """Test user input requirement"""
        assert ConversationPhase.GREETING.requires_user_input is True
        assert ConversationPhase.IDENTIFICATION.requires_user_input is True
        assert ConversationPhase.END.requires_user_input is False

    def test_conversation_phase_valid_transitions(self):
        """Test valid phase transitions"""
        # Greeting -> Identification
        assert ConversationPhase.GREETING.can_transition_to(ConversationPhase.IDENTIFICATION) is True

        # Identification -> Legal Notice
        assert ConversationPhase.IDENTIFICATION.can_transition_to(ConversationPhase.LEGAL_NOTICE) is True

        # Service Coordination -> Closing
        assert ConversationPhase.SERVICE_COORDINATION.can_transition_to(ConversationPhase.CLOSING) is True

        # Service Coordination -> Incident Management
        assert ConversationPhase.SERVICE_COORDINATION.can_transition_to(ConversationPhase.INCIDENT_MANAGEMENT) is True

        # Incident Management -> Service Coordination (loop back)
        assert ConversationPhase.INCIDENT_MANAGEMENT.can_transition_to(ConversationPhase.SERVICE_COORDINATION) is True

    def test_conversation_phase_invalid_transitions(self):
        """Test invalid phase transitions"""
        # Cannot go backwards (except to SERVICE_COORDINATION)
        assert ConversationPhase.CLOSING.can_transition_to(ConversationPhase.GREETING) is False

        # Cannot skip required phases
        assert ConversationPhase.GREETING.can_transition_to(ConversationPhase.CLOSING) is False

        # Cannot leave END
        assert ConversationPhase.END.can_transition_to(ConversationPhase.GREETING) is False

    def test_conversation_phase_get_next_phases(self):
        """Test getting valid next phases"""
        next_from_greeting = ConversationPhase.GREETING.get_next_phases()
        assert ConversationPhase.IDENTIFICATION in next_from_greeting

        next_from_service_coord = ConversationPhase.SERVICE_COORDINATION.get_next_phases()
        assert ConversationPhase.INCIDENT_MANAGEMENT in next_from_service_coord
        assert ConversationPhase.ESCALATION in next_from_service_coord
        assert ConversationPhase.CLOSING in next_from_service_coord

        next_from_end = ConversationPhase.END.get_next_phases()
        assert len(next_from_end) == 0

    def test_conversation_phase_from_string(self):
        """Test creating from string"""
        assert ConversationPhase.from_string("greeting") == ConversationPhase.GREETING
        assert ConversationPhase.from_string("END") == ConversationPhase.END

    def test_conversation_phase_from_string_invalid(self):
        """Test invalid string raises ValueError"""
        with pytest.raises(ValueError, match="Invalid conversation phase"):
            ConversationPhase.from_string("invalid_phase")
