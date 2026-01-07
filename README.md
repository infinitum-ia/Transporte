# Agente Conversacional de Transporte Médico
## Transformas / EPS Cosalud - MVP

Agente conversacional basado en LLM para automatizar y asistir la coordinación de servicios de transporte médico prestados por **Transformas**, empresa autorizada por la **EPS Cosalud**.

---

## Características Principales

- **Automatización del flujo conversacional**: Desde saludo hasta encuesta de calidad
- **Gestión de incidencias**: Registro estructurado de quejas y novedades
- **Validación inteligente**: Verificación de pacientes y elegibilidad de servicios
- **Escalamiento controlado**: Redirección a EPS cuando sea necesario
- **Observaciones estructuradas**: Tags normalizados para análisis
- **Cumplimiento normativo**: Avisos legales y grabación de llamadas

---

## Stack Técnico

- **Python 3.11+**
- **FastAPI** - Framework web moderno y de alto rendimiento
- **LangChain/LangGraph** - Orquestación conversacional con LLM
- **OpenAI GPT-4-turbo** - Modelo de lenguaje
- **Redis** - Persistencia y gestión de sesiones
- **Pydantic** - Validación de datos
- **Pytest** - Testing comprehensivo

---

## Arquitectura

El proyecto sigue **Clean Architecture** con **Domain-Driven Design**:

```
┌─────────────────────────────────┐
│   PRESENTATION (FastAPI)        │
└─────────────┬───────────────────┘
              │
┌─────────────▼───────────────────┐
│   AGENT (LangGraph)             │
└─────────────┬───────────────────┘
              │
┌─────────────▼───────────────────┐
│   APPLICATION (Use Cases)       │
└─────────────┬───────────────────┘
              │
┌─────────────▼───────────────────┐
│   DOMAIN (Business Logic)       │
└─────────────┬───────────────────┘
              │
┌─────────────▼───────────────────┐
│   INFRASTRUCTURE (Redis/OpenAI) │
└─────────────────────────────────┘
```

---

## Instalación y Setup

### Requisitos Previos

- Python 3.11 o superior
- Docker y Docker Compose (para Redis)
- Git
- Make (opcional, para comandos simplificados)

### 1. Clonar el Repositorio

```bash
git clone <repository-url>
cd Transporte
```

### 2. Crear Entorno Virtual e Instalar Dependencias

**Opción A: Usando Make (recomendado)**

```bash
make setup
# Activar el entorno virtual
# Windows:
venv\Scripts\activate
# Unix/macOS:
source venv/bin/activate

make install
```

**Opción B: Manual**

```bash
python -m venv venv

# Activar entorno virtual
# Windows:
venv\Scripts\activate
# Unix/macOS:
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configurar Variables de Entorno

```bash
# Copiar el template
cp .env.example .env

# Editar .env y agregar tu OpenAI API key
# OPENAI_API_KEY=sk-your-actual-key-here
```

### 4. Iniciar Redis con Docker

```bash
make docker-up
# O manualmente:
docker-compose up -d
```

### 5. Ejecutar la Aplicación

```bash
make run
# O manualmente:
uvicorn src.presentation.api.main:app --reload --host 0.0.0.0 --port 8000
```

La API estará disponible en: **http://localhost:8000**

Documentación interactiva: **http://localhost:8000/docs**

---

## Uso Rápido

### Crear una Sesión de Conversación

```bash
curl -X POST http://localhost:8000/api/v1/session \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "María"}'
```

Respuesta:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2024-01-15T10:30:00Z",
  "conversation_phase": "GREETING"
}
```

### Enviar un Mensaje

```bash
curl -X POST http://localhost:8000/api/v1/conversation/message \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -d '{"message": "Hola, buenos días"}'
```

Respuesta:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "agent_response": "Buenos días, le habla María de Transformas, empresa autorizada por EPS Cosalud. ¿Tengo el gusto de hablar con el paciente?",
  "conversation_phase": "IDENTIFICATION",
  "requires_escalation": false
}
```

---

## Testing

### Ejecutar Todos los Tests

```bash
make test
```

### Tests por Tipo

```bash
# Unit tests
make test-unit

# Integration tests
make test-integration

# End-to-end tests
make test-e2e

# BDD tests
make test-bdd
```

### Generar Reporte de Coverage

```bash
make coverage
```

---

## Comandos Disponibles

```bash
make help              # Ver todos los comandos disponibles
make setup             # Crear entorno virtual
make install           # Instalar dependencias
make test              # Ejecutar tests con coverage
make run               # Ejecutar aplicación
make docker-up         # Iniciar Docker containers
make docker-down       # Detener Docker containers
make docker-logs       # Ver logs de Docker
make lint              # Ejecutar linting
make format            # Formatear código
make coverage          # Generar y ver reporte de coverage
make clean             # Limpiar archivos generados
```

---

## Estructura del Proyecto

```
Transporte/
├── src/
│   ├── domain/              # Lógica de negocio
│   ├── application/         # Casos de uso
│   ├── infrastructure/      # Implementaciones técnicas
│   ├── agent/               # LangGraph y orquestación
│   ├── presentation/        # API FastAPI
│   └── shared/              # Utilidades compartidas
├── tests/
│   ├── unit/                # Tests unitarios
│   ├── integration/         # Tests de integración
│   ├── e2e/                 # Tests end-to-end
│   └── bdd/                 # Tests BDD
├── docs/                    # Documentación
├── docker-compose.yml       # Configuración Docker
├── requirements.txt         # Dependencias Python
├── pytest.ini               # Configuración de tests
├── Makefile                 # Comandos útiles
└── README.md                # Este archivo
```

---

## Flujo Conversacional

El agente maneja el siguiente flujo:

```
GREETING → IDENTIFICATION → LEGAL_NOTICE →
SERVICE_COORDINATION → [INCIDENT_MGMT | ESCALATION] →
CLOSING → SURVEY → END
```

### Fases:

1. **GREETING**: Saludo y presentación del agente
2. **IDENTIFICATION**: Validación de identidad del paciente
3. **LEGAL_NOTICE**: Aviso de grabación
4. **SERVICE_COORDINATION**: Coordinación de fechas, horarios, tipo de servicio
5. **INCIDENT_MANAGEMENT**: Gestión de quejas y novedades
6. **ESCALATION**: Redirección a EPS cuando sea necesario
7. **CLOSING**: Cierre cortés
8. **SURVEY**: Encuesta de calidad

---

## Configuración

Todas las configuraciones se manejan mediante variables de entorno (ver `.env.example`):

- **OPENAI_API_KEY**: Tu API key de OpenAI (requerido)
- **REDIS_HOST**: Host de Redis (default: localhost)
- **AGENT_MODE**: `llm` (OpenAI) o `mock` (simulado)
- **AGENT_NAME**: Nombre del agente (default: María)
- **LOG_LEVEL**: Nivel de logging (default: INFO)

---

## API Endpoints

### Health Check
- **GET** `/api/v1/health` - Verificar estado del servicio

### Session Management
- **POST** `/api/v1/session` - Crear nueva sesión
- **GET** `/api/v1/session/{session_id}` - Obtener estado de sesión
- **DELETE** `/api/v1/session/{session_id}` - Eliminar sesión

### Conversation
- **POST** `/api/v1/conversation/message` - Enviar mensaje

Ver documentación completa en: http://localhost:8000/docs

---

## Desarrollo

### Linting y Formateo

```bash
# Verificar código
make lint

# Formatear código
make format
```

### Agregar Nuevas Dependencias

```bash
pip install <package>
pip freeze > requirements.txt
```

---

## Troubleshooting

### Redis no se conecta

Verificar que Docker esté corriendo:
```bash
docker ps
```

Si Redis no está activo:
```bash
make docker-up
```

### Tests fallan

Asegurarse de que Redis esté corriendo y que las variables de entorno estén configuradas:
```bash
make docker-up
cp .env.example .env
# Editar .env con tu API key
```

### Problemas con dependencias

Reinstalar desde cero:
```bash
rm -rf venv
make setup
# Activar venv
make install
```

---

## Contribución

### Workflow

1. Crear branch para feature/fix
2. Desarrollar y escribir tests
3. Ejecutar `make format` y `make lint`
4. Ejecutar `make test` (coverage >80%)
5. Commit y push
6. Crear Pull Request

### Estándares de Código

- **Cobertura**: >80% en general, >95% en domain layer
- **Linting**: Pasar flake8 y mypy
- **Formateo**: Black con line-length=127
- **Tests**: Obligatorios para nuevas features

---

## Licencia

[Especificar licencia]

---

## Contacto y Soporte

- **Equipo**: [Información de contacto]
- **Issues**: [URL del repositorio de issues]
- **Documentación**: Ver carpeta `docs/`

---

## Roadmap Post-MVP

- [ ] Integración con WhatsApp Business API
- [ ] Sistema de voz (text-to-speech)
- [ ] Integración con API de EPS Cosalud
- [ ] Dashboard de analytics
- [ ] Multi-idioma
- [ ] Handoff a agente humano
