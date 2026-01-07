# 📞 Guía de Integración - API Llamadas Salientes

Guía rápida para integrar tu plataforma con el sistema de llamadas salientes de Transformas.

---

## 🎯 Endpoint Unificado (Recomendado)

### **POST** `/api/v1/calls/outbound/initiate`

**Función**: Inicia una llamada saliente completa en **un solo llamado**.

**Ventajas**:
- ✅ Un solo endpoint para todo
- ✅ Mensaje inicial generado automáticamente
- ✅ Perfecto para plataformas de marcación automática
- ✅ Menos complejidad en tu integración

---

## 📋 Request

### URL Base
```
http://tu-servidor:8081/api/v1/calls/outbound/initiate
```

### Headers
```http
Content-Type: application/json
```

### Body (JSON)
```json
{
    "patient_phone": "3001234567",
    "agent_name": "María"
}
```

**Parámetros**:
| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `patient_phone` | string | ✅ Sí | Teléfono del paciente (10 dígitos) |
| `agent_name` | string | ⚪ No | Nombre del agente (default: "María") |

---

## ✅ Response Exitosa (201 Created)

```json
{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "call_direction": "OUTBOUND",
    "conversation_phase": "OUTBOUND_GREETING",
    "agent_initial_message": "Buenos días, ¿hablo con Juan Pérez García? Le llamo de Transformas para confirmar su servicio de transporte médico programado para Diálisis el día 20 de enero a las 08:00 horas.",
    "patient_name": "Juan Pérez García",
    "service_type": "Diálisis",
    "appointment_date": "2024-01-20",
    "appointment_time": "08:00",
    "created_at": "2024-01-15T10:30:00Z"
}
```

**Campos de respuesta**:
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `session_id` | string | ID único de la sesión (úsalo para mensajes siguientes) |
| `call_direction` | string | Siempre "OUTBOUND" |
| `conversation_phase` | string | Fase actual ("OUTBOUND_GREETING") |
| `agent_initial_message` | string | **Mensaje que debe decir/reproducir el agente** |
| `patient_name` | string | Nombre completo del paciente |
| `service_type` | string | Tipo de servicio (Diálisis, Terapia, etc.) |
| `appointment_date` | string | Fecha de la cita |
| `appointment_time` | string | Hora de la cita |
| `created_at` | string | Timestamp de creación |

---

## ❌ Errores Posibles

### 404 - Paciente no encontrado
```json
{
    "detail": "No patient found with phone number: 3001234567"
}
```
**Solución**: Verificar que el teléfono existe en el archivo Excel.

### 503 - Servicio no disponible
```json
{
    "detail": "Excel service not configured. Cannot load patient data."
}
```
**Solución**: Verificar configuración de `EXCEL_PATH` en el servidor.

### 500 - Error interno
```json
{
    "detail": "Error initiating outbound call: <detalles>"
}
```
**Solución**: Revisar logs del servidor.

---

## 🔄 Flujo Completo de Integración

### **Paso 1: Iniciar llamada**

```bash
curl -X POST "http://tu-servidor:8081/api/v1/calls/outbound/initiate" \
     -H "Content-Type: application/json" \
     -d '{
       "patient_phone": "3001234567",
       "agent_name": "María"
     }'
```

**Obtienes**:
- ✅ `session_id` → Guardalo para los siguientes pasos
- ✅ `agent_initial_message` → Reproducir o mostrar al agente

---

### **Paso 2: Enviar respuesta del paciente**

Cuando el paciente responde (ej: "Sí, con él habla"):

```bash
curl -X POST "http://tu-servidor:8081/api/v1/conversation/message/v2" \
     -H "Content-Type: application/json" \
     -H "X-Session-ID: <session_id_del_paso_1>" \
     -d '{
       "message": "Sí, con él habla"
     }'
```

**Response**:
```json
{
    "agent_response": "Perfecto. Le llamo de Transformas, autorizada por Cosalud...",
    "conversation_phase": "OUTBOUND_LEGAL_NOTICE",
    "requires_escalation": false,
    "call_direction": "OUTBOUND",
    "metadata": {
        "confirmation_status": null,
        "service_confirmed": false
    }
}
```

---

### **Paso 3: Repetir hasta finalizar**

Continúa enviando mensajes hasta que:
- `conversation_phase` sea `"END"`, o
- `requires_escalation` sea `true`

---

## 🔐 Autenticación (Opcional)

Si el servidor tiene API Key configurada:

```bash
curl -X POST "http://tu-servidor:8081/api/v1/calls/outbound/initiate" \
     -H "Content-Type: application/json" \
     -H "X-API-Key: tu-api-key-aqui" \
     -d '{...}'
```

---

## 📊 Monitorear Estado de Llamada

### Obtener detalles de sesión

```bash
GET /api/v1/calls/{session_id}
```

**Response**:
```json
{
    "session_id": "550e8400...",
    "call_direction": "OUTBOUND",
    "conversation_phase": "OUTBOUND_SERVICE_CONFIRMATION",
    "agent_name": "María",
    "patient_name": "Juan Pérez García",
    "service_type": "Diálisis",
    "confirmation_status": "Confirmado",
    "service_confirmed": true,
    "created_at": "...",
    "updated_at": "..."
}
```

---

## 🔄 Ejemplos por Lenguaje

### JavaScript (fetch)

```javascript
async function iniciarLlamada(telefono) {
    const response = await fetch('http://tu-servidor:8081/api/v1/calls/outbound/initiate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            patient_phone: telefono,
            agent_name: 'María'
        })
    });

    if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
    }

    const data = await response.json();
    console.log('Session ID:', data.session_id);
    console.log('Mensaje inicial:', data.agent_initial_message);

    return data;
}

// Uso
iniciarLlamada('3001234567')
    .then(data => {
        // Reproducir data.agent_initial_message
        // Guardar data.session_id para siguientes mensajes
    })
    .catch(error => console.error('Error:', error));
```

### Python (requests)

```python
import requests

def iniciar_llamada(telefono):
    url = 'http://tu-servidor:8081/api/v1/calls/outbound/initiate'
    payload = {
        'patient_phone': telefono,
        'agent_name': 'María'
    }

    response = requests.post(url, json=payload)
    response.raise_for_status()

    data = response.json()
    print(f"Session ID: {data['session_id']}")
    print(f"Mensaje inicial: {data['agent_initial_message']}")

    return data

# Uso
try:
    resultado = iniciar_llamada('3001234567')
    # Reproducir resultado['agent_initial_message']
    # Guardar resultado['session_id']
except requests.exceptions.HTTPError as e:
    print(f"Error: {e}")
```

### PHP

```php
<?php

function iniciarLlamada($telefono) {
    $url = 'http://tu-servidor:8081/api/v1/calls/outbound/initiate';
    $data = [
        'patient_phone' => $telefono,
        'agent_name' => 'María'
    ];

    $options = [
        'http' => [
            'header'  => "Content-type: application/json\r\n",
            'method'  => 'POST',
            'content' => json_encode($data)
        ]
    ];

    $context  = stream_context_create($options);
    $result = file_get_contents($url, false, $context);

    if ($result === FALSE) {
        throw new Exception('Error al iniciar llamada');
    }

    return json_decode($result, true);
}

// Uso
try {
    $resultado = iniciarLlamada('3001234567');
    echo "Session ID: " . $resultado['session_id'] . "\n";
    echo "Mensaje: " . $resultado['agent_initial_message'] . "\n";
} catch (Exception $e) {
    echo "Error: " . $e->getMessage();
}
?>
```

### C# (.NET)

```csharp
using System;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

public class TransformasClient
{
    private readonly HttpClient _httpClient;
    private readonly string _baseUrl;

    public TransformasClient(string baseUrl)
    {
        _httpClient = new HttpClient();
        _baseUrl = baseUrl;
    }

    public async Task<LlamadaResponse> IniciarLlamada(string telefono)
    {
        var request = new
        {
            patient_phone = telefono,
            agent_name = "María"
        };

        var json = JsonSerializer.Serialize(request);
        var content = new StringContent(json, Encoding.UTF8, "application/json");

        var response = await _httpClient.PostAsync(
            $"{_baseUrl}/api/v1/calls/outbound/initiate",
            content
        );

        response.EnsureSuccessStatusCode();

        var responseBody = await response.Content.ReadAsStringAsync();
        return JsonSerializer.Deserialize<LlamadaResponse>(responseBody);
    }
}

public class LlamadaResponse
{
    public string session_id { get; set; }
    public string agent_initial_message { get; set; }
    public string patient_name { get; set; }
    // ... otros campos
}

// Uso
var client = new TransformasClient("http://tu-servidor:8081");
var resultado = await client.IniciarLlamada("3001234567");
Console.WriteLine($"Session ID: {resultado.session_id}");
Console.WriteLine($"Mensaje: {resultado.agent_initial_message}");
```

---

## 📝 Checklist de Integración

### Pre-requisitos
- [ ] Servidor Transformas desplegado y corriendo
- [ ] Puerto 8081 accesible desde tu plataforma
- [ ] Archivo Excel con datos de pacientes actualizado
- [ ] Teléfonos de prueba en el Excel

### Testing
- [ ] Probar endpoint `/health` para verificar conectividad
- [ ] Hacer llamada de prueba con teléfono real del Excel
- [ ] Verificar que recibes `session_id` y `agent_initial_message`
- [ ] Probar enviar un mensaje de continuación
- [ ] Verificar que funciona el ciclo completo hasta `END`

### Producción
- [ ] Implementar manejo de errores (404, 500, etc.)
- [ ] Guardar `session_id` para cada llamada
- [ ] Implementar logging de requests/responses
- [ ] Configurar timeouts apropiados (recomendado: 30s)
- [ ] Implementar retry logic para errores transitorios

---

## 🆘 Soporte

### Documentación completa
```
http://tu-servidor:8081/docs
```

### Logs del servidor
```bash
docker-compose -f docker-compose.prod.yml logs -f app
```

### Endpoints útiles
- **Health**: `GET /api/v1/health`
- **Pendientes**: `GET /api/v1/calls/outbound/pending`
- **Estadísticas**: `GET /api/v1/calls/statistics`

---

## ⚡ Mejores Prácticas

1. **Timeouts**: Configura timeouts de al menos 30 segundos (el LLM puede tardar)
2. **Reintentos**: Implementa reintentos con backoff exponencial
3. **Logs**: Guarda todos los `session_id` para debugging
4. **Validación**: Valida que el teléfono existe antes de llamar
5. **Cache**: Considera cachear información de pacientes localmente
6. **Monitoreo**: Implementa alertas para errores 5xx

---

¿Dudas? Revisa la documentación completa en `/docs` o los logs del servidor.
