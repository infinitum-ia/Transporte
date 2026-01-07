# Guía de Administración de Llamadas

Esta guía explica cómo usar la funcionalidad de administración de llamadas entrantes (INBOUND) y salientes (OUTBOUND) en el sistema Transformas Medical Transport Agent.

## 📋 Tabla de Contenidos

1. [Descripción General](#descripción-general)
2. [Configuración](#configuración)
3. [Llamadas Entrantes (INBOUND)](#llamadas-entrantes-inbound)
4. [Llamadas Salientes (OUTBOUND)](#llamadas-salientes-outbound)
5. [Endpoints de Administración](#endpoints-de-administración)
6. [Ejemplos de Uso](#ejemplos-de-uso)
7. [Integración con Excel](#integración-con-excel)

---

## Descripción General

El sistema soporta dos tipos de llamadas:

### 🔵 Llamadas Entrantes (INBOUND)
- El paciente llama a la empresa
- El agente identifica al paciente y coordina el servicio
- Flujo conversacional desde `GREETING` hasta `END`

### 🟢 Llamadas Salientes (OUTBOUND)
- La empresa llama al paciente para confirmar servicios programados
- Los datos del paciente y servicio se cargan automáticamente desde Excel
- Flujo conversacional desde `OUTBOUND_GREETING` hasta `END`
- Se actualiza el estado de confirmación en Excel

---

## Configuración

### Variables de Entorno

Agregar en el archivo `.env`:

```bash
# Agent Mode (REQUIRED)
AGENT_MODE=llm

# OpenAI Configuration (REQUIRED)
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4-turbo

# Redis Configuration (REQUIRED for LLM mode)
REDIS_HOST=localhost
REDIS_PORT=6379

# Excel Configuration (REQUIRED for OUTBOUND calls)
EXCEL_PATH=/path/to/datos_llamadas_salientes.csv
EXCEL_BACKUP_FOLDER=/path/to/backups  # Optional, defaults to {EXCEL_PATH}/backups
```

### Estructura del Archivo Excel

El archivo CSV debe tener las siguientes columnas:

```csv
nombre_paciente,apellido_paciente,tipo_documento,numero_documento,eps,departamento,ciudad,telefono,nombre_familiar,parentesco,tipo_servicio,tipo_tratamiento,frecuencia,fecha_servicio,hora_servicio,destino_centro_salud,modalidad_transporte,zona_recogida,direccion_completa,observaciones_especiales,estado_confirmacion
```

**Columnas requeridas:**
- `nombre_paciente`: Nombre del paciente
- `apellido_paciente`: Apellido del paciente
- `tipo_documento`: CC, TI, CE, etc.
- `numero_documento`: Número de documento
- `eps`: Nombre de la EPS
- `telefono`: Teléfono de 10 dígitos
- `tipo_servicio`: Diálisis, Terapia, Cita con Especialista
- `fecha_servicio`: Fecha del servicio
- `hora_servicio`: Hora del servicio
- `destino_centro_salud`: Centro de salud destino
- `modalidad_transporte`: RUTA o DESEMBOLSO
- `direccion_completa`: Dirección de recogida
- `estado_confirmacion`: Pendiente, Confirmado, Reprogramar, Rechazado, No contesta, Zona sin cobertura

---

## Llamadas Entrantes (INBOUND)

### Crear Sesión INBOUND

**Endpoint Legacy:** `POST /api/v1/session`

```bash
curl -X POST http://localhost:8000/api/v1/session \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "María"
  }'
```

**Endpoint V2:** `POST /api/v1/session/v2`

```bash
curl -X POST http://localhost:8000/api/v1/session/v2 \
  -H "Content-Type: application/json" \
  -d '{
    "call_direction": "INBOUND",
    "agent_name": "María"
  }'
```

**Respuesta:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2024-01-15T10:30:00Z",
  "conversation_phase": "GREETING"
}
```

### Enviar Mensaje

**Endpoint Legacy:** `POST /api/v1/conversation/message`

```bash
curl -X POST http://localhost:8000/api/v1/conversation/message \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -d '{
    "message": "Buenos días"
  }'
```

**Endpoint V2:** `POST /api/v1/conversation/message/v2`

```bash
curl -X POST http://localhost:8000/api/v1/conversation/message/v2 \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -d '{
    "message": "Buenos días"
  }'
```

---

## Llamadas Salientes (OUTBOUND)

### Crear Sesión OUTBOUND

**Endpoint:** `POST /api/v1/calls/outbound`

```bash
curl -X POST http://localhost:8000/api/v1/calls/outbound \
  -H "Content-Type: application/json" \
  -d '{
    "patient_phone": "3001234567",
    "agent_name": "María"
  }'
```

**Respuesta:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "call_direction": "OUTBOUND",
  "patient_name": "Juan Pérez García",
  "service_type": "Diálisis",
  "appointment_date": "2024-01-20",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Nota:** Los datos del paciente se cargan automáticamente desde Excel usando el teléfono.

### Continuar Conversación OUTBOUND

Usar el mismo endpoint que INBOUND:

```bash
curl -X POST http://localhost:8000/api/v1/conversation/message/v2 \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -d '{
    "message": "Sí, confirmo el servicio"
  }'
```

**Respuesta:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "agent_response": "Perfecto, Juan. He confirmado su servicio de Diálisis...",
  "conversation_phase": "OUTBOUND_SERVICE_CONFIRMATION",
  "requires_escalation": false,
  "call_direction": "OUTBOUND",
  "metadata": {
    "confirmation_status": "Confirmado",
    "service_confirmed": true,
    "extracted": {
      "service_confirmed": true
    }
  }
}
```

---

## Endpoints de Administración

### 1. Obtener Llamadas Pendientes

**Endpoint:** `GET /api/v1/calls/outbound/pending`

```bash
curl -X GET http://localhost:8000/api/v1/calls/outbound/pending
```

**Respuesta:**
```json
{
  "total_pending": 2,
  "calls": [
    {
      "patient_name": "Juan Pérez García",
      "patient_phone": "3001234567",
      "service_type": "Diálisis",
      "appointment_date": "2024-01-20",
      "appointment_time": "08:00",
      "modality": "RUTA",
      "city": "Bogotá",
      "observations": "Paciente requiere silla de ruedas"
    },
    {
      "patient_name": "María López Sánchez",
      "patient_phone": "3009876543",
      "service_type": "Terapia",
      "appointment_date": "2024-01-21",
      "appointment_time": "10:00",
      "modality": "DESEMBOLSO",
      "city": "Medellín",
      "observations": null
    }
  ]
}
```

### 2. Obtener Estadísticas de Llamadas

**Endpoint:** `GET /api/v1/calls/statistics`

```bash
curl -X GET http://localhost:8000/api/v1/calls/statistics
```

**Respuesta:**
```json
{
  "total": 100,
  "pendiente": 25,
  "confirmado": 60,
  "reprogramar": 8,
  "rechazado": 5,
  "no_contesta": 2,
  "zona_sin_cobertura": 0,
  "by_service_type": {
    "Diálisis": 50,
    "Terapia": 30,
    "Cita con Especialista": 20
  },
  "by_modality": {
    "RUTA": 70,
    "DESEMBOLSO": 30
  }
}
```

### 3. Obtener Detalles de Sesión

**Endpoint:** `GET /api/v1/calls/{session_id}`

```bash
curl -X GET http://localhost:8000/api/v1/calls/550e8400-e29b-41d4-a716-446655440000
```

**Respuesta:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "call_direction": "OUTBOUND",
  "conversation_phase": "OUTBOUND_SERVICE_CONFIRMATION",
  "agent_name": "María",
  "patient_name": "Juan Pérez García",
  "patient_document": "CC-1234567890",
  "service_type": "Diálisis",
  "confirmation_status": "Confirmado",
  "service_confirmed": true,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:45:00Z"
}
```

### 4. Actualizar Estado de Confirmación

**Endpoint:** `PUT /api/v1/calls/{session_id}/status`

```bash
curl -X PUT http://localhost:8000/api/v1/calls/550e8400-e29b-41d4-a716-446655440000/status \
  -H "Content-Type: application/json" \
  -d '{
    "status": "Reprogramar",
    "observations": "Paciente solicita cambio de fecha"
  }'
```

**Estados válidos:**
- `Confirmado`
- `Reprogramar`
- `Rechazado`
- `No contesta`
- `Zona sin cobertura`

**Respuesta:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "Reprogramar",
  "updated_at": "2024-01-15T11:00:00Z",
  "success": true
}
```

**Nota:** Este endpoint actualiza automáticamente el archivo Excel.

---

## Ejemplos de Uso

### Ejemplo Completo: Llamada Saliente

```bash
# 1. Crear sesión OUTBOUND
SESSION_ID=$(curl -X POST http://localhost:8000/api/v1/calls/outbound \
  -H "Content-Type: application/json" \
  -d '{"patient_phone": "3001234567", "agent_name": "María"}' \
  | jq -r '.session_id')

echo "Session ID: $SESSION_ID"

# 2. Primer mensaje (saludo del agente)
curl -X POST http://localhost:8000/api/v1/conversation/message/v2 \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: $SESSION_ID" \
  -d '{"message": "Hola"}'

# 3. Responder al aviso legal
curl -X POST http://localhost:8000/api/v1/conversation/message/v2 \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: $SESSION_ID" \
  -d '{"message": "Sí, autorizo"}'

# 4. Confirmar servicio
curl -X POST http://localhost:8000/api/v1/conversation/message/v2 \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: $SESSION_ID" \
  -d '{"message": "Sí, confirmo el servicio"}'

# 5. Ver detalles de la sesión
curl -X GET http://localhost:8000/api/v1/calls/$SESSION_ID
```

### Ejemplo: Flujo de Trabajo de Operador

```bash
# 1. Ver llamadas pendientes
curl -X GET http://localhost:8000/api/v1/calls/outbound/pending

# 2. Seleccionar un paciente y crear sesión
curl -X POST http://localhost:8000/api/v1/calls/outbound \
  -H "Content-Type: application/json" \
  -d '{"patient_phone": "3001234567"}'

# 3. Realizar la conversación...

# 4. Si el paciente no contesta, actualizar manualmente
curl -X PUT http://localhost:8000/api/v1/calls/$SESSION_ID/status \
  -H "Content-Type: application/json" \
  -d '{
    "status": "No contesta",
    "observations": "Intentado 3 veces sin respuesta"
  }'

# 5. Ver estadísticas actualizadas
curl -X GET http://localhost:8000/api/v1/calls/statistics
```

---

## Integración con Excel

### Actualización Automática

Cuando una llamada OUTBOUND termina (fase `END`), el sistema automáticamente:

1. Actualiza `estado_confirmacion` en Excel
2. Agrega observaciones con timestamp
3. Crea un backup antes de modificar

### Estructura de Observaciones

Las observaciones se agregan en formato:

```
[2024-01-15 10:45:00] Llamada completada - Servicio confirmado
```

Si hay múltiples observaciones, se separan con ` | `:

```
[2024-01-15 10:45:00] Llamada completada - Servicio confirmado | [2024-01-16 09:30:00] Fecha reprogramada: 2024-01-25
```

### Backups

Cada vez que se actualiza el Excel, se crea un backup automático:

```
backups/datos_llamadas_salientes_backup_20240115_104500.csv
```

---

## Consideraciones Importantes

### ⚠️ Requisitos

1. **AGENT_MODE=llm**: Los endpoints de administración requieren modo LLM
2. **Redis**: Debe estar corriendo para persistencia de sesiones
3. **Excel Path**: Debe estar configurado y el archivo debe existir
4. **Formato de Teléfono**: Debe ser exactamente 10 dígitos

### 🔒 Validaciones

- Los teléfonos deben tener exactamente 10 dígitos
- Los estados de confirmación deben ser uno de los valores válidos
- Las sesiones OUTBOUND requieren que el paciente exista en Excel
- Solo se pueden actualizar estados de sesiones OUTBOUND

### 📊 Monitoreo

Verificar logs de la aplicación para:
- Inicialización del Excel service
- Backups creados
- Errores de validación
- Actualizaciones de estado

```bash
# Ver logs en tiempo real
tail -f app.log

# Buscar errores de Excel
grep "Excel" app.log
```

---

## Troubleshooting

### Error: "Excel service not configured"

**Solución:** Verificar que `EXCEL_PATH` esté configurado en `.env`:

```bash
EXCEL_PATH=/ruta/completa/al/archivo.csv
```

### Error: "Call orchestrator not configured"

**Solución:** Verificar que `AGENT_MODE=llm` en `.env`:

```bash
AGENT_MODE=llm
```

### Error: "No patient found with phone"

**Solución:**
1. Verificar que el teléfono exista en el Excel
2. Verificar formato (10 dígitos sin espacios)
3. Revisar que el archivo Excel esté actualizado

### Backups no se crean

**Solución:** Verificar permisos de escritura en el directorio:

```bash
chmod 755 /path/to/backups
```

---

## Próximos Pasos

Para más información, consultar:

- [CLAUDE.md](./CLAUDE.md) - Arquitectura del proyecto
- [README.md](./README.md) - Guía general de setup
- Documentación de API: `http://localhost:8000/docs`
