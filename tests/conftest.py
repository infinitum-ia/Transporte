"""
Pytest configuration and fixtures for all tests
"""
import pytest
import asyncio
from typing import Generator, AsyncGenerator
from unittest.mock import Mock, AsyncMock
import redis.asyncio as redis
from faker import Faker

# Initialize Faker for generating test data
fake = Faker('es_ES')


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def fake_data():
    """Provide Faker instance for generating test data"""
    return fake


@pytest.fixture
async def redis_client() -> AsyncGenerator[redis.Redis, None]:
    """
    Provide Redis client for integration tests

    Note: Requires Redis to be running (use docker-compose up -d)
    """
    client = redis.Redis(
        host='localhost',
        port=6379,
        db=1,  # Use different DB for tests
        decode_responses=True
    )

    yield client

    # Cleanup: flush test database
    await client.flushdb()
    await client.close()


@pytest.fixture
def mock_redis_client():
    """Provide mocked Redis client for unit tests"""
    mock_client = AsyncMock(spec=redis.Redis)
    mock_client.get = AsyncMock(return_value=None)
    mock_client.set = AsyncMock(return_value=True)
    mock_client.delete = AsyncMock(return_value=1)
    mock_client.exists = AsyncMock(return_value=0)
    return mock_client


@pytest.fixture
def mock_llm():
    """Provide mocked LLM for testing agent nodes"""
    mock = AsyncMock()
    mock.ainvoke = AsyncMock(return_value=Mock(
        content="Mocked LLM response",
        additional_kwargs={}
    ))
    return mock


@pytest.fixture
def sample_patient_data(fake_data):
    """Generate sample patient data for testing"""
    return {
        "full_name": fake_data.name(),
        "document_type": "CC",
        "document_number": fake_data.random_number(digits=10, fix_len=True),
        "eps": "COSALUD",
        "is_responsible": True,
        "responsible_name": None,
        "phone": fake_data.phone_number()
    }


@pytest.fixture
def sample_service_data(fake_data):
    """Generate sample service data for testing"""
    return {
        "service_type": "TERAPIA",
        "service_modality": "RUTA_COMPARTIDA",
        "appointment_date": fake_data.date_between(start_date='today', end_date='+30d').isoformat(),
        "appointment_time": "09:00",
        "pickup_address": fake_data.address(),
        "destination_address": fake_data.address()
    }


@pytest.fixture
def sample_incident_data():
    """Generate sample incident data for testing"""
    return {
        "incident_type": "QUEJA_CONDUCTOR",
        "description": "El conductor llegó 30 minutos tarde",
        "severity": "MEDIUM"
    }


@pytest.fixture
def sample_session_state():
    """Generate sample conversation session state"""
    return {
        "session_id": "test-session-123",
        "conversation_phase": "GREETING",
        "patient_id": None,
        "patient_name": None,
        "document_type": None,
        "document_number": None,
        "eps": None,
        "is_responsible": True,
        "responsible_name": None,
        "service_id": None,
        "service_type": None,
        "service_modality": None,
        "appointment_date": None,
        "appointment_time": None,
        "pickup_address": None,
        "destination_address": None,
        "incidents": [],
        "observations": [],
        "messages": [],
        "current_user_message": "",
        "current_agent_response": "",
        "requires_escalation": False,
        "escalation_reason": None,
        "legal_notice_acknowledged": False,
        "survey_completed": False,
        "created_at": "2024-01-15T10:00:00Z",
        "updated_at": "2024-01-15T10:00:00Z"
    }


# Markers for different test types
def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
