# 🎯 Endpoint Unificado - Guía Completa

## ✨ Ventaja Principal

**UN SOLO ENDPOINT para toda la conversación**. No necesitas manejar `session_id` manualmente.

---

## 🔗 Endpoint

**POST** `http://localhost:8081/api/v1/conversation/unified`

---

## 📋 Request

### Headers
```
Content-Type: application/json
```

### Body (JSON)
```json
{
    "patient_phone": "3001234567",
    "message": "Sí, con él habla",
    "is_outbound": true,
    "agent_name": "María"
}
```

### Parámetros

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `patient_phone` | string | ✅ Sí | Teléfono del paciente (10 dígitos) |
| `message` | string | ✅ Sí | Mensaje del usuario |
| `is_outbound` | boolean | ⚪ No | `true` = llamada saliente (default), `false` = llamada entrante |
| `agent_name` | string | ⚪ No | Nombre del agente (default: "María") |

---

## ✅ Response

```json
{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "agent_response": "Buenos días, ¿hablo con Juan Pérez García? Le llamo de Transformas...",
    "conversation_phase": "OUTBOUND_GREETING",
    "call_direction": "OUTBOUND",
    "requires_escalation": false,
    "session_created": true,
    "patient_name": "Juan Pérez García",
    "service_type": "Diálisis",
    "metadata": {}
}
```

### Campos de respuesta

| Campo | Descripción |
|-------|-------------|
| `session_id` | ID de la sesión (guárdalo para tracking) |
| `agent_response` | **Respuesta del agente** (lo que debe decir) |
| `conversation_phase` | Fase actual de la conversación |
| `call_direction` | `"OUTBOUND"` o `"INBOUND"` |
| `session_created` | `true` si se creó la sesión, `false` si continúa existente |
| `patient_name` | Nombre del paciente (si está disponible) |
| `service_type` | Tipo de servicio (si está disponible) |
| `requires_escalation` | Si requiere escalar a EPS |
| `metadata` | Información adicional |

---

## 🔄 Flujo Completo - Ejemplo

### **Mensaje 1: Iniciar llamada saliente**

```json
POST /api/v1/conversation/unified

{
    "patient_phone": "3001234567",
    "message": "START",
    "is_outbound": true
}
```

**Response:**
```json
{
    "session_id": "abc-123",
    "agent_response": "Buenos días, ¿hablo con Juan Pérez García? Le llamo de Transformas para confirmar su servicio de transporte médico programado para Diálisis el día 20 de enero a las 08:00 horas.",
    "conversation_phase": "OUTBOUND_GREETING",
    "call_direction": "OUTBOUND",
    "session_created": true,
    "patient_name": "Juan Pérez García",
    "service_type": "Diálisis"
}
```

---

### **Mensaje 2: Paciente responde**

```json
POST /api/v1/conversation/unified

{
    "patient_phone": "3001234567",
    "message": "Sí, con él habla",
    "is_outbound": true
}
```

**Response:**
```json
{
    "session_id": "abc-123",
    "agent_response": "Perfecto. Le llamo de Transformas, empresa autorizada por Cosalud. Esta llamada será grabada con fines de calidad y seguridad. ¿Está de acuerdo?",
    "conversation_phase": "OUTBOUND_LEGAL_NOTICE",
    "call_direction": "OUTBOUND",
    "session_created": false,
    "patient_name": "Juan Pérez García"
}
```

---

### **Mensaje 3: Paciente acepta**

```json
POST /api/v1/conversation/unified

{
    "patient_phone": "3001234567",
    "message": "Sí, acepto",
    "is_outbound": true
}
```

**Response:**
```json
{
    "session_id": "abc-123",
    "agent_response": "Muchas gracias. Le confirmo su servicio de Diálisis programado para el día 20 de enero a las 08:00 horas. El vehículo lo recogerá en su domicilio. ¿Confirma el servicio?",
    "conversation_phase": "OUTBOUND_SERVICE_CONFIRMATION",
    "call_direction": "OUTBOUND",
    "session_created": false
}
```

---

### **Mensaje 4: Paciente confirma**

```json
POST /api/v1/conversation/unified

{
    "patient_phone": "3001234567",
    "message": "Sí, confirmo",
    "is_outbound": true
}
```

**Response:**
```json
{
    "session_id": "abc-123",
    "agent_response": "Perfecto, su servicio está confirmado. Muchas gracias por su tiempo. Que tenga un buen día.",
    "conversation_phase": "OUTBOUND_CLOSING",
    "call_direction": "OUTBOUND",
    "session_created": false,
    "metadata": {
        "confirmation_status": "Confirmado",
        "service_confirmed": true
    }
}
```

---

### **Mensaje 5: Despedida**

```json
POST /api/v1/conversation/unified

{
    "patient_phone": "3001234567",
    "message": "Gracias",
    "is_outbound": true
}
```

**Response:**
```json
{
    "session_id": "abc-123",
    "agent_response": "Gracias a usted. Que tenga un excelente día.",
    "conversation_phase": "END",
    "call_direction": "OUTBOUND",
    "session_created": false
}
```

---

## 🎯 Ventajas del Endpoint Unificado

✅ **Un solo endpoint** - No necesitas múltiples endpoints
✅ **Sin manejo manual de session_id** - El teléfono identifica la conversación
✅ **Automático** - Crea sesión si no existe, continúa si existe
✅ **Compatible con ambos tipos** - Llamadas entrantes y salientes
✅ **Simplicidad** - Ideal para integraciones externas

---

## 📱 Ejemplo Postman

### Configuración del Request

1. **Método**: `POST`
2. **URL**: `http://localhost:8081/api/v1/conversation/unified`
3. **Headers**:
   - `Content-Type: application/json`
4. **Body** (raw, JSON):
   ```json
   {
       "patient_phone": "3001234567",
       "message": "START",
       "is_outbound": true,
       "agent_name": "María"
   }
   ```

### Para Mensajes Siguientes

**Cambia solo el campo `message`**:

```json
{
    "patient_phone": "3001234567",
    "message": "Sí, con él habla",
    "is_outbound": true
}
```

---

## 🔍 Cómo Funciona Internamente

1. **Primer mensaje** (`patient_phone` + `message`):
   - Sistema busca sesión activa con ese teléfono
   - Si NO existe: Crea nueva sesión (outbound o inbound según `is_outbound`)
   - Si SÍ existe: Continúa la conversación existente

2. **Mensajes siguientes** (mismo `patient_phone`):
   - Sistema encuentra la sesión existente
   - Continúa la conversación en la misma sesión
   - No crea sesión duplicada

3. **Identificación**:
   - El `patient_phone` es el identificador único
   - Una llamada = un teléfono = una sesión activa

---

## ⚠️ Notas Importantes

### 1. **Primer mensaje en llamadas salientes**

Para iniciar una llamada saliente, usa mensaje `"START"` o vacío:

```json
{
    "patient_phone": "3001234567",
    "message": "START",
    "is_outbound": true
}
```

Esto generará el saludo inicial automáticamente.

### 2. **Llamadas entrantes**

Para llamadas entrantes (paciente llama):

```json
{
    "patient_phone": "3001234567",
    "message": "Buenos días, necesito transporte para diálisis",
    "is_outbound": false
}
```

### 3. **Sesiones activas**

- Una sesión se mantiene activa durante `SESSION_TTL_SECONDS` (default: 3600 = 1 hora)
- Después expira automáticamente
- Un nuevo mensaje con el mismo teléfono creará nueva sesión

### 4. **Teléfono debe existir en Excel** (solo para outbound)

Para llamadas salientes (`is_outbound: true`), el teléfono **debe existir** en `datos_llamadas_salientes.csv`.

Si no existe, recibirás error 404:
```json
{
    "detail": "No patient found with phone: 3001234567"
}
```

---

## 🧪 Testing Rápido

### Test 1: Iniciar llamada

```bash
curl -X POST "http://localhost:8081/api/v1/conversation/unified" \
     -H "Content-Type: application/json" \
     -d '{
       "patient_phone": "3001234567",
       "message": "START",
       "is_outbound": true
     }'
```

### Test 2: Continuar conversación

```bash
curl -X POST "http://localhost:8081/api/v1/conversation/unified" \
     -H "Content-Type: application/json" \
     -d '{
       "patient_phone": "3001234567",
       "message": "Sí, con él habla",
       "is_outbound": true
     }'
```

---

## ❌ Errores Comunes

### Error 404 - Paciente no encontrado
```json
{
    "detail": "No patient found with phone: 3001234567"
}
```
**Solución**: Verifica que el teléfono existe en el CSV.

### Error 503 - Servicio no disponible
```json
{
    "detail": "Excel service not configured. Cannot create outbound session."
}
```
**Solución**: Verifica `EXCEL_PATH` en `.env` y reinicia el servidor.

### Error 503 - Orchestrator no configurado
```json
{
    "detail": "Call orchestrator not configured. Ensure AGENT_MODE=llm in environment."
}
```
**Solución**: Verifica `AGENT_MODE=llm` en `.env` y reinicia.

---

## 🎉 Resumen

**Antes** (3 pasos):
1. POST `/calls/outbound/initiate` → Obtener session_id
2. POST `/conversation/message/v2` + Header `X-Session-ID`
3. Repetir paso 2 para cada mensaje

**Ahora** (1 paso):
1. POST `/conversation/unified` → Todo en uno
   - Mismo endpoint para todos los mensajes
   - Mismo body, solo cambias `message`
   - No necesitas manejar session_id

---

¿Tienes dudas? Revisa `/docs` en tu servidor para documentación interactiva.
