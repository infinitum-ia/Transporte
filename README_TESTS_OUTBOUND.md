# Guía para Ejecutar Tests de Llamadas Salientes

Esta guía te ayudará a ejecutar los tests de llamadas salientes (OUTBOUND) paso a paso.

## 📋 Pre-requisitos

Antes de ejecutar los tests, asegúrate de tener:

1. ✅ Python 3.11+ instalado
2. ✅ Dependencias instaladas (`pip install -r requirements.txt`)
3. ✅ Redis corriendo
4. ✅ Archivo Excel/CSV con datos de pacientes
5. ✅ Variables de entorno configuradas

---

## 🚀 Paso 1: Configurar Archivo Excel

### Opción A: Usar el archivo de ejemplo

```bash
# Copia el archivo de ejemplo
cp datos_llamadas_salientes_ejemplo.csv datos_llamadas_salientes.csv
```

### Opción B: Usar tu propio archivo

Asegúrate de que tu archivo CSV tenga estas columnas:

```
nombre_paciente,apellido_paciente,tipo_documento,numero_documento,eps,departamento,ciudad,
telefono,nombre_familiar,parentesco,tipo_servicio,tipo_tratamiento,frecuencia,
fecha_servicio,hora_servicio,destino_centro_salud,modalidad_transporte,zona_recogida,
direccion_completa,observaciones_especiales,estado_confirmacion
```

**Importante:**
- El teléfono debe tener exactamente 10 dígitos
- El estado debe ser "Pendiente" para que aparezca en las llamadas pendientes

---

## 🔧 Paso 2: Configurar Variables de Entorno

Edita tu archivo `.env`:

```bash
# Agent Configuration
AGENT_MODE=llm
AGENT_NAME=María
COMPANY_NAME=Transformas
EPS_NAME=Cosalud

# OpenAI (REQUERIDO)
OPENAI_API_KEY=sk-tu-api-key-aqui
OPENAI_MODEL=gpt-4-turbo
OPENAI_TEMPERATURE=0.6
OPENAI_MAX_TOKENS=1500

# Redis (REQUERIDO)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# Excel (REQUERIDO para OUTBOUND)
EXCEL_PATH=C:\Users\Administrador\Documents\Transporte\datos_llamadas_salientes.csv
EXCEL_BACKUP_FOLDER=C:\Users\Administrador\Documents\Transporte\backups

# Session
SESSION_TTL_SECONDS=3600
```

**⚠️ IMPORTANTE:**
- Cambia `EXCEL_PATH` a la ruta absoluta de tu archivo
- Asegúrate de que `AGENT_MODE=llm` (no "mock")
- Necesitas una API key válida de OpenAI

---

## 🐳 Paso 3: Iniciar Redis

### Opción A: Con Docker

```bash
docker-compose up redis -d
```

### Opción B: Sin Docker (Windows)

1. Descarga Redis para Windows
2. Ejecuta `redis-server.exe`

### Verificar que Redis está corriendo:

```bash
redis-cli ping
# Debería responder: PONG
```

---

## 🖥️ Paso 4: Iniciar el Servidor API

En una terminal:

```bash
# Activar entorno virtual (si usas uno)
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Iniciar servidor
uvicorn src.presentation.api.main:app --reload --host 0.0.0.0 --port 8000
```

**Verificar que el servidor está corriendo:**

Abre tu navegador en: `http://localhost:8000/docs`

Deberías ver la documentación interactiva de la API.

---

## 🧪 Paso 5: Ejecutar los Tests

Ahora tienes dos opciones de tests:

### Opción A: Test Interactivo (Recomendado para primera vez)

```bash
python test_outbound_call.py
```

Este test te permite:
- ✅ Ver un menú con diferentes opciones
- ✅ Elegir el tipo de flujo a probar (confirmación, reprogramación, rechazo)
- ✅ Ver cada paso de la conversación con detalles
- ✅ Consultar llamadas pendientes y estadísticas

**Menú del test:**
```
1. Confirmación exitosa (flujo completo)
2. Reprogramación de cita
3. Rechazo de servicio
4. Solo consultar llamadas pendientes
5. Solo consultar estadísticas
0. Salir
```

### Opción B: Test Automatizado (Más rápido)

```bash
python test_outbound_call_simple.py
```

Este test:
- ✅ Se ejecuta automáticamente sin intervención
- ✅ Crea una sesión OUTBOUND
- ✅ Completa toda la conversación
- ✅ Verifica el estado final
- ✅ Muestra estadísticas

**Antes de ejecutar**, edita el archivo y cambia el teléfono:

```python
# En test_outbound_call_simple.py, línea 13:
PATIENT_PHONE = "3001234567"  # Cambiar por un teléfono de tu Excel
```

---

## 📊 Paso 6: Verificar Resultados

### 1. Ver Backups Creados

Los backups del Excel se guardan en:
```
backups/datos_llamadas_salientes_backup_YYYYMMDD_HHMMSS.csv
```

### 2. Ver Excel Actualizado

Abre tu archivo CSV y verifica:
- El `estado_confirmacion` debe haber cambiado de "Pendiente" a "Confirmado"
- Las `observaciones_especiales` deben tener una nueva entrada con timestamp

Ejemplo:
```
[2024-01-15 10:45:00] Llamada completada - Servicio confirmado
```

### 3. Ver Logs del Servidor

En la terminal donde corre el servidor, deberías ver:
```
📊 Excel service initialized: /ruta/al/archivo.csv
INFO: 127.0.0.1:xxxxx - "POST /api/v1/calls/outbound HTTP/1.1" 201 Created
INFO: 127.0.0.1:xxxxx - "POST /api/v1/conversation/message/v2 HTTP/1.1" 200 OK
```

---

## 🐛 Troubleshooting

### Error: "Excel service not configured"

**Problema:** El servidor no encuentra el archivo Excel.

**Solución:**
```bash
# 1. Verifica que EXCEL_PATH esté en .env
echo $EXCEL_PATH  # Linux/Mac
echo %EXCEL_PATH%  # Windows

# 2. Verifica que el archivo existe
ls -la datos_llamadas_salientes.csv  # Linux/Mac
dir datos_llamadas_salientes.csv     # Windows

# 3. Reinicia el servidor después de cambiar .env
```

### Error: "No patient found with phone: 3001234567"

**Problema:** El teléfono no existe en el Excel o tiene formato incorrecto.

**Solución:**
1. Abre el archivo CSV
2. Verifica que el teléfono existe
3. Verifica que tiene exactamente 10 dígitos (sin espacios, guiones, o paréntesis)
4. Cambia el teléfono en el test por uno que sí exista

### Error: "Call orchestrator not configured"

**Problema:** El servidor está en modo `mock` en lugar de `llm`.

**Solución:**
```bash
# 1. Edita .env
AGENT_MODE=llm  # NO "mock"

# 2. Reinicia el servidor
# Ctrl+C en la terminal del servidor
# Luego: uvicorn src.presentation.api.main:app --reload
```

### Error: "Connection refused" o "Cannot connect to API"

**Problema:** El servidor no está corriendo.

**Solución:**
```bash
# Inicia el servidor en otra terminal
uvicorn src.presentation.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Error: OpenAI API error

**Problema:** API key inválida o sin créditos.

**Solución:**
1. Verifica tu API key en https://platform.openai.com/api-keys
2. Verifica que tengas créditos disponibles
3. Actualiza `OPENAI_API_KEY` en `.env`

---

## 📝 Ejemplos de Salida Esperada

### Test Exitoso

```
================================================================================
  3. CREANDO SESIÓN OUTBOUND
================================================================================

Teléfono del paciente: 3001234567
Agente: María
✅ Sesión creada exitosamente

Session ID: 550e8400-e29b-41d4-a716-446655440000
Paciente: Juan Pérez García
Servicio: Diálisis
Fecha cita: 2024-01-20

================================================================================
  4. SALUDO INICIAL DEL PACIENTE
================================================================================

Usuario: Hola

María (Agente): ¡Buenos días! ¿Hablo con Juan Pérez García o con algún familiar?...

📍 Fase: OUTBOUND_GREETING
📞 Tipo de llamada: OUTBOUND

================================================================================
  5. ACEPTACIÓN AVISO LEGAL
================================================================================

Usuario: Sí, autorizo la grabación

María (Agente): Perfecto, muchas gracias. Le llamo de Transformas...

📍 Fase: OUTBOUND_LEGAL_NOTICE

================================================================================
✅ TEST COMPLETADO EXITOSAMENTE
================================================================================
La llamada fue confirmada y el Excel debería estar actualizado
Session ID: 550e8400-e29b-41d4-a716-446655440000
```

---

## 🎯 Flujos de Conversación Disponibles

### 1. Confirmación Exitosa
```
Usuario: Hola
Usuario: Sí, autorizo
Usuario: Sí, confirmo el servicio
Usuario: Gracias, adiós
→ Resultado: estado_confirmacion = "Confirmado"
```

### 2. Reprogramación
```
Usuario: Hola
Usuario: Sí, autorizo
Usuario: No puedo ese día, necesito cambiar la fecha
Usuario: Prefiero el martes
Usuario: Gracias, adiós
→ Resultado: estado_confirmacion = "Reprogramar"
```

### 3. Rechazo
```
Usuario: Hola
Usuario: Sí, autorizo
Usuario: No, ya no necesito el servicio
Usuario: Gracias, adiós
→ Resultado: estado_confirmacion = "Rechazado"
```

---

## 📚 Recursos Adicionales

- **Documentación API:** http://localhost:8000/docs
- **Guía de Administración:** [GUIA_ADMINISTRACION_LLAMADAS.md](./GUIA_ADMINISTRACION_LLAMADAS.md)
- **Arquitectura del Proyecto:** [CLAUDE.md](./CLAUDE.md)

---

## ✅ Checklist Pre-Ejecución

Antes de ejecutar los tests, verifica:

- [ ] Redis está corriendo (`redis-cli ping`)
- [ ] `.env` tiene `AGENT_MODE=llm`
- [ ] `.env` tiene `OPENAI_API_KEY` válida
- [ ] `.env` tiene `EXCEL_PATH` configurado
- [ ] El archivo Excel existe y tiene datos
- [ ] El servidor API está corriendo (`http://localhost:8000/docs`)
- [ ] Has cambiado `PATIENT_PHONE` en el test por un teléfono real de tu Excel

---

¡Listo! Ahora puedes ejecutar los tests. 🚀
