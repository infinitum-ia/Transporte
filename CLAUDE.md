# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Transpormax Medical Transport Agent** - LLM-powered conversational agent for coordinating medical transport services. Built for Transpormax (transport company) authorized by EPS Cosalud (healthcare provider).

This system handles two call types:
- **Inbound**: Patients calling to request services or report issues
- **Outbound**: Automated confirmation calls for scheduled transport services

## Technology Stack

- **Python 3.11+** with FastAPI
- **LangChain/LangGraph** for LLM orchestration
- **OpenAI GPT-4-turbo** as the language model
- **Redis** for session persistence
- **Pydantic** for data validation
- **Clean Architecture** with Domain-Driven Design

## Quick Start Commands

```bash
# Setup environment
make setup                # Create virtual environment
source venv/bin/activate  # Unix/Mac
venv\Scripts\activate     # Windows
make install              # Install dependencies

# Run Redis (required for LLM agent mode)
docker-compose up redis -d

# Configure environment
cp .env.example .env
# Edit .env and set AGENT_MODE=llm and OPENAI_API_KEY=your-key

# Run application
make run
# Or: uvicorn src.presentation.api.main:app --reload --host 0.0.0.0 --port 8000

# API documentation: http://localhost:8000/docs
```

## Testing Commands

```bash
make test              # All tests with coverage report
make test-unit         # Unit tests only
make test-integration  # Integration tests only
make test-e2e          # End-to-end tests only
make test-bdd          # BDD tests only
make coverage          # Generate and open coverage report

# Linting and formatting
make lint              # Run flake8 and mypy
make format            # Format with black and isort
```

## Architecture Overview

The project follows **Clean Architecture** with clear separation of concerns:

```
Domain Layer (Pure business logic)
  └── Entities: Patient, Service, Incident, Observation, ConversationSession
  └── Value Objects: PatientId, ServiceType, ConversationPhase, ObservationTag
  └── Repositories: Abstract interfaces for data access
  └── Services: Domain services (PatientValidator, EligibilityChecker, EscalationRules)

Application Layer (Use cases)
  └── Use Cases: Orchestrate domain logic
  └── DTOs: Data transfer objects
  └── Ports: Interfaces for external systems

Infrastructure Layer (Technical implementations)
  └── Persistence: Redis session storage
  └── LLM: OpenAI integration via LangChain
  └── Config: Environment-based settings
  └── Logging: Structured logging setup

Agent Layer (LLM orchestration)
  └── LLMConversationalAgent: Main agent implementation
  └── MockAgent: Deterministic agent for testing
  └── Prompts: Phase-specific system prompts (inbound/outbound)
  └── Factory: Agent creation based on AGENT_MODE

Presentation Layer (API)
  └── FastAPI endpoints (session, conversation, health)
  └── Request/Response schemas
  └── Middleware and dependencies
```

### Conversation Phase Flow

The agent manages stateful conversations through **ConversationPhase** enum transitions:

**Inbound Flow** (patient calls in):
```
GREETING → IDENTIFICATION → LEGAL_NOTICE → SERVICE_COORDINATION
  → [INCIDENT_MANAGEMENT | ESCALATION] → CLOSING → SURVEY → END
```

**Outbound Flow** (system calls patient):
```
OUTBOUND_GREETING → OUTBOUND_LEGAL_NOTICE → OUTBOUND_SERVICE_CONFIRMATION
  → [OUTBOUND_SPECIAL_CASES] → OUTBOUND_CLOSING → END
```

Key architectural notes:
- Phase transitions are validated through `ConversationPhase.can_transition_to()`
- `INCIDENT_MANAGEMENT` and `ESCALATION` are optional phases
- `SERVICE_COORDINATION` can loop from `INCIDENT_MANAGEMENT`
- State persists in Redis with configurable TTL (default 3600s)

### Agent Modes

The system supports two operational modes (configured via `AGENT_MODE` in .env):

1. **`llm` mode** (production):
   - Uses OpenAI GPT-4-turbo via LangChain
   - Structured output extraction using Pydantic models
   - Context-aware responses based on conversation history
   - Temperature: 0.6 for natural but consistent responses

2. **`mock` mode** (testing):
   - Deterministic hardcoded responses
   - No LLM or Redis required
   - Useful for unit tests and development without API costs

### LLM Agent Architecture

The `LLMConversationalAgent` (src/agent/llm_agent.py) orchestrates:

1. **Session Management**: Creates/retrieves conversation state from Redis
2. **Prompt Construction**: Builds phase-specific system prompts with context
3. **LLM Invocation**: Calls OpenAI with structured output schema
4. **Response Extraction**: Parses LLM output into `LLMOutput` model
5. **State Updates**: Updates session state and persists to Redis

Key implementation details:
- Prompts are built dynamically based on current phase and extracted data
- Messages include full conversation history for context
- Structured output uses `LLMOutput(agent_response, next_phase, requires_escalation, extracted)`
- Extraction logic is phase-specific (see `src/agent/prompts/phase_prompts.py`)

### Excel-Driven Outbound Calls

Outbound calls load patient and service data from Excel/CSV files using `ExcelService`:
- File: `datos_llamadas_salientes.csv` (configurable path)
- Columns: patient identity, service type, schedule, logistics, special observations
- Agent personalizes script using pre-loaded data (e.g., "programado para [TIPO_TRATAMIENTO] el [FECHA]")

## Key Files and Their Purpose

### Domain Layer
- `src/domain/entities/conversation_session.py` - Core conversation state entity
- `src/domain/value_objects/conversation_phase.py` - Phase enum with transition logic
- `src/domain/value_objects/service_type.py` - Service types (Terapia, Diálisis, Cita)
- `src/domain/services/escalation_rules.py` - Business rules for EPS escalation

### Agent Layer
- `src/agent/llm_agent.py` - LLM agent implementation with OpenAI integration
- `src/agent/prompts/phase_prompts.py` - System prompts for inbound phases
- `src/agent/prompts/outbound_prompts.py` - System prompts for outbound calls
- `src/agent/agent_factory.py` - Factory for creating agent based on mode

### Infrastructure Layer
- `src/infrastructure/config/settings.py` - Environment-based configuration
- `src/infrastructure/persistence/redis/session_store.py` - Redis session persistence
- `src/infrastructure/persistence/excel_service.py` - Excel file loading for outbound calls

### Presentation Layer
- `src/presentation/api/main.py` - FastAPI app creation and lifecycle
- `src/presentation/api/v1/endpoints/conversation.py` - Message handling endpoint
- `src/presentation/api/v1/endpoints/session.py` - Session CRUD endpoints

## Important Development Notes

### Modifying Conversation Flows

When changing conversation phases or transitions:
1. Update `ConversationPhase` enum in `src/domain/value_objects/conversation_phase.py`
2. Update transition validation in `can_transition_to()` method
3. Add/modify corresponding prompts in `src/agent/prompts/`
4. Update tests in `tests/unit/domain/value_objects/test_conversation_phase.py`

### Adding New Data Extraction

To extract new fields from user messages:
1. Add field to session state schema (in `LLMConversationalAgent.init_session()`)
2. Update relevant phase prompt to instruct LLM to extract the field
3. Update `LLMOutput.extracted` dictionary structure
4. Add validation in domain services if needed

### Working with Prompts

Prompts are in `src/agent/prompts/`:
- `phase_prompts.py` - Inbound call prompts (phase-by-phase instructions)
- `outbound_prompts.py` - Outbound confirmation call scripts

Prompt construction pattern:
```python
def build_system_prompt(phase: ConversationPhase, state: dict) -> str:
    # Base instructions for phase
    prompt = f"You are {state['agent_name']} from {state['company_name']}..."

    # Add already-known context (avoid re-asking)
    if state['patient']['patient_full_name']:
        prompt += f"\nKnown: Patient name is {state['patient']['patient_full_name']}"

    # Phase-specific instructions
    if phase == ConversationPhase.IDENTIFICATION:
        prompt += "\n\nAsk for: full name, document type, document number"

    return prompt
```

### Redis Session Structure

Sessions are stored as JSON in Redis with key pattern `session:{session_id}`:
```json
{
  "session_id": "uuid",
  "phase": "SERVICE_COORDINATION",
  "agent_name": "María",
  "patient": {
    "patient_full_name": "Juan Pérez",
    "document_type": "CC",
    "document_number": "12345678",
    ...
  },
  "service": {
    "service_type": "Diálisis",
    "appointment_date": "2024-01-20",
    ...
  },
  "messages": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ],
  "created_at": "2024-01-15T10:00:00",
  "updated_at": "2024-01-15T10:05:00"
}
```

### Testing Strategy

- **Unit tests** (`tests/unit/`): Test domain logic and value objects in isolation
- **Integration tests** (`tests/integration/`): Test Redis and LLM integrations
- **E2E tests** (`tests/e2e/`): Full conversation flows through API
- **BDD tests** (`tests/bdd/`): Business scenarios in Gherkin format

Coverage requirements:
- Domain layer: >95%
- Overall: >80%

### Common Patterns

**Creating a conversation:**
```python
# POST /api/v1/session
response = await client.post("/api/v1/session", json={"agent_name": "María"})
session_id = response.json()["session_id"]
```

**Sending a message:**
```python
# POST /api/v1/conversation/message
response = await client.post(
    "/api/v1/conversation/message",
    headers={"X-Session-ID": session_id},
    json={"message": "Buenos días"}
)
```

**Retrieving session state:**
```python
# GET /api/v1/session/{session_id}
response = await client.get(f"/api/v1/session/{session_id}")
state = response.json()
```

## Environment Variables Reference

Key variables in `.env`:

```bash
# Agent Mode (CRITICAL)
AGENT_MODE=llm              # "llm" for production, "mock" for testing

# OpenAI (required if AGENT_MODE=llm)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo    # or gpt-4o-mini for cost savings
OPENAI_TEMPERATURE=0.6      # 0.3-0.7 recommended
OPENAI_MAX_TOKENS=1500

# Redis (required if AGENT_MODE=llm)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=              # Optional

# Agent Configuration
AGENT_NAME=María
COMPANY_NAME=Transformas
EPS_NAME=Cosalud

# Session
SESSION_TTL_SECONDS=3600     # 1 hour default
```

## Troubleshooting

**"Agent not responding naturally"**
- Check `AGENT_MODE=llm` in .env (not "mock")
- Verify `OPENAI_TEMPERATURE` is 0.5-0.7 (too low = robotic)
- Inspect prompts in `src/agent/prompts/` for clarity

**"Redis connection errors"**
- Ensure Docker is running: `docker ps`
- Start Redis: `docker-compose up redis -d`
- Check `REDIS_HOST` and `REDIS_PORT` in .env

**"Session state not persisting"**
- Verify `AGENT_MODE=llm` (mock mode doesn't use Redis)
- Check Redis is healthy: `docker-compose logs redis`
- Increase `SESSION_TTL_SECONDS` if sessions expire too quickly

**"Tests failing"**
- Ensure Redis is running for integration tests
- Use `pytest -v -m unit` to run only unit tests (no Redis needed)
- Check `.env` file exists with valid `OPENAI_API_KEY` for E2E tests

## Business Rules Summary

Key constraints from specification document:

1. **Mandatory scripts**: GREETING, LEGAL_NOTICE (recording consent), CLOSING, SURVEY
2. **Data validation**: Patient identity must be verified before service coordination
3. **Escalation triggers**: Out-of-scope requests redirect to EPS (see `escalation_rules.py`)
4. **Observation tags**: Must use normalized tags for analytics (defined in `observation_tag.py`)
5. **Service types**: Terapia, Diálisis, Cita con Especialista (see `service_type.py`)
6. **Transport modalities**: "Ruta" (shared vehicle) or "Desembolso" (reimbursement)

## Related Documentation

- `README.md` - Setup and usage guide
- `especificacion_sistema_llamadas.md` - Full business specification with scripts
- `GUIA_AGENTE_LLM.md` - Step-by-step guide for running LLM agent
- `EJECUTAR_PRUEBA.md` - Testing guide
- `GUIA_USO_SISTEMA_EXCEL.md` - Excel integration guide for outbound calls
