# 🤖 Guía de Uso: Agente LLM Conversacional

## ✅ Mejoras Implementadas

### 🎯 **Problemas Resueltos:**
1. ✅ **Activado modo LLM** - Ya no usa respuestas hardcodeadas
2. ✅ **Prompts mejorados** - Conversación natural y flexible
3. ✅ **Temperatura ajustada** - Respuestas más naturales (0.6)
4. ✅ **Extracción inteligente** - Captura múltiples datos en un mensaje
5. ✅ **Contexto conversacional** - Adapta respuestas según lo que ya sabe

### 🚀 **Características del Agente LLM:**
- **Conversacional**: Responde como una persona real, no como robot
- **Inteligente**: Extrae múltiples datos en un solo mensaje
- **Contextual**: Recuerda lo que el usuario ya dijo
- **Empático**: Maneja quejas con comprensión
- **Flexible**: No sigue un guión rígido

---

## 📋 Requisitos Previos

1. **Docker Desktop** instalado y corriendo
2. **Python 3.11+** con dependencias instaladas
3. **OpenAI API Key** configurada en `.env`
4. **Redis** corriendo (vía Docker)

---

## 🔧 Paso 1: Verificar Configuración

Abre el archivo `.env` y verifica que tenga:

```bash
# IMPORTANTE: Debe estar en modo "llm"
AGENT_MODE=llm

# OpenAI configurado
OPENAI_API_KEY=sk-proj-tu-key-aqui
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.6
OPENAI_MAX_TOKENS=1500

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
```

---

## 🚀 Paso 2: Iniciar Redis

**Opción A - Usando Docker Compose (Recomendado):**

```bash
# Iniciar solo Redis
docker-compose up redis -d

# Verificar que esté corriendo
docker ps
```

Deberías ver:
```
CONTAINER ID   IMAGE           STATUS         PORTS
xxxxx          redis:7-alpine  Up 10 seconds  0.0.0.0:6379->6379/tcp
```

**Opción B - Comando directo:**

```bash
docker run -d --name transformas_redis -p 6379:6379 redis:7-alpine
```

---

## 🎮 Paso 3: Iniciar el Servidor FastAPI

Abre una terminal y ejecuta:

```bash
# Activar entorno virtual
venv\Scripts\activate

# Iniciar servidor
uvicorn src.presentation.api.main:app --reload --host 0.0.0.0 --port 8000
```

**Verás un mensaje confirmando que está en modo LLM:**
```
🚀 Transformas Medical Transport Agent v1.0.0 starting...
📍 Environment: development
🤖 Agent: María
🏥 Company: Transformas
📋 API Docs: http://0.0.0.0:8000/docs
INFO:     Application startup complete.
```

---

## 🧪 Paso 4: Probar el Agente Conversacional

### **Prueba Manual con Swagger UI:**

1. Abre http://localhost:8000/docs
2. Crea una sesión en **POST /api/v1/session**
3. Copia el `session_id` que te devuelve
4. Usa **POST /api/v1/conversation/message**
   - Headers: `X-Session-ID: <tu-session-id>`
   - Body: `{"message": "tu mensaje aquí"}`

### **Prueba con cURL:**

```bash
# 1. Crear sesión
curl -X POST http://localhost:8000/api/v1/session \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "María"}'

# Respuesta (guarda el session_id):
# {"session_id":"550e8400-e29b-41d4-a716-446655440000", ...}

# 2. Enviar mensaje
curl -X POST http://localhost:8000/api/v1/conversation/message \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -d '{"message": "Hola buenos días"}'
```

---

## 🎯 Ejemplos de Conversaciones Mejoradas

### **Ejemplo 1: Usuario da múltiples datos juntos**

❌ **ANTES (Mock Agent - Robótico):**
```
Usuario: "Hola, soy Juan Pérez, CC 123456789, necesito transporte para terapia"
Agente: "¿Podría confirmar su tipo de documento y número de cédula?"
         [Ignora que YA lo dio]
```

✅ **AHORA (LLM Agent - Natural):**
```
Usuario: "Hola, soy Juan Pérez, CC 123456789, necesito transporte para terapia"
Agente: "Buenos días Sr. Pérez, con mucho gusto le ayudo a coordinar su
         transporte para terapia. ¿Me confirma su EPS y si habla directamente
         el paciente o un familiar?"
         [Reconoce todos los datos: nombre, documento, servicio]
```

### **Ejemplo 2: Conversación con queja**

❌ **ANTES:**
```
Usuario: "El conductor llegó tarde ayer"
Agente: "Comprendo su situación. Voy a registrar su observación."
         [Respuesta genérica y fría]
```

✅ **AHORA:**
```
Usuario: "El conductor llegó tarde ayer"
Agente: "Lamento mucho que haya tenido esa experiencia, Sr. Pérez. Entiendo
         lo frustrante que puede ser esperar por el transporte. Permítame
         tomar nota de los detalles para escalar su caso. ¿Recuerda
         aproximadamente cuánto tiempo se retrasó?"
         [Empática, pide detalles específicos]
```

### **Ejemplo 3: Usuario da información parcial**

❌ **ANTES:**
```
Usuario: "Necesito ir a mi cita"
Agente: "¿Me puede indicar si es para terapia, diálisis o consulta?"
         [Mecánico, no pregunta más]
```

✅ **AHORA:**
```
Usuario: "Necesito ir a mi cita"
Agente: "Claro, con gusto le ayudo. ¿Qué tipo de cita tiene programada:
         terapia, diálisis o consulta especializada? Y si me puede compartir
         la fecha y hora sería perfecto."
         [Natural, hace múltiples preguntas útiles]
```

---

## 🔍 Verificar que está usando LLM (no Mock)

### **Señales de que está usando el Agente LLM:**
✅ Respuestas varían según el contexto
✅ Extrae múltiples datos en un mensaje
✅ Lenguaje natural y conversacional
✅ Se adapta al tono del usuario
✅ Maneja casos no previstos con inteligencia

### **Señales de que sigue en Mock:**
❌ Respuestas idénticas cada vez
❌ Ignora datos que el usuario ya dio
❌ Respuestas muy genéricas tipo "template"
❌ Pregunta lo mismo aunque ya lo dijiste

---

## 🛠️ Troubleshooting

### **Error: "Session store not configured"**
- **Causa**: Redis no está corriendo o AGENT_MODE no está en "llm"
- **Solución**:
  1. Verifica `.env` tiene `AGENT_MODE=llm`
  2. Inicia Redis: `docker-compose up redis -d`
  3. Reinicia el servidor FastAPI

### **Error: "OpenAI API key invalid"**
- **Causa**: API key incorrecta o expirada
- **Solución**: Verifica tu API key en https://platform.openai.com/api-keys

### **Error: Connection refused (Redis)**
- **Causa**: Redis no está corriendo en puerto 6379
- **Solución**:
  ```bash
  docker ps  # Verifica si está corriendo
  docker-compose up redis -d  # Inicia Redis
  ```

### **Respuestas siguen siendo robóticas**
- **Verifica**: El log del servidor debe mostrar que cargó el modo LLM
- **Solución**: Reinicia el servidor después de cambiar `.env`

---

## 📊 Monitoreo y Logs

### **Ver logs en tiempo real:**
```bash
# Logs de Redis
docker logs -f transformas_redis

# Logs del servidor
# (verás las llamadas a OpenAI en consola)
```

### **Verificar sesiones en Redis:**
```bash
# Entrar a Redis CLI
docker exec -it transformas_redis redis-cli

# Ver todas las sesiones
KEYS transport:session:*

# Ver contenido de una sesión
GET transport:session:550e8400-e29b-41d4-a716-446655440000
```

---

## 🎓 Tips para Mejores Conversaciones

### **Como Usuario de Prueba:**
✅ Varía tus mensajes (no uses siempre los mismos)
✅ Da múltiples datos en un mensaje ("Soy Juan, CC 123, de Cosalud")
✅ Simula usuarios reales (algunos dan toda la info, otros no)
✅ Prueba quejas y casos edge

### **Ajustes de Temperatura:**
- **0.3-0.4**: Más conservador, respuestas predecibles
- **0.6-0.7**: Balance (actual) - Natural pero controlado
- **0.8-1.0**: Muy creativo, puede divagar

---

## 🚀 Próximos Pasos

1. **Probar con usuarios reales** - Observa cómo interactúan
2. **Ajustar prompts** según necesidades específicas
3. **Agregar validaciones** de negocio si es necesario
4. **Monitorear costos** de OpenAI API
5. **Implementar caché** para reducir llamadas repetitivas

---

## 📞 Ejemplo Completo de Conversación

```
🟢 GREETING
Usuario: "Hola"
Agente: "Buenos días, le habla María de Transformas. ¿Hablo con el paciente
         o con algún familiar?"

🔵 IDENTIFICATION
Usuario: "Soy yo, Juan Pérez, CC 987654321 de Cosalud"
Agente: "Perfecto Sr. Pérez, muchas gracias. Le informo que esta llamada
         está siendo grabada con fines de calidad. ¿Está de acuerdo?"

📢 LEGAL_NOTICE
Usuario: "Sí, claro"
Agente: "Gracias. Cuénteme, ¿en qué puedo ayudarle hoy?"

🏥 SERVICE_COORDINATION
Usuario: "Necesito transporte para mi cita de terapia el viernes a las 3pm"
Agente: "Claro, vamos a coordinar su transporte para terapia el viernes a las
         3pm. ¿Me puede confirmar la dirección desde donde lo recogeríamos?"

Usuario: "Calle 123 #45-67, barrio Suba"
Agente: "Perfecto, Calle 123 #45-67 en Suba. ¿Y cuál es la dirección exacta
         de la clínica o centro médico donde tiene su cita?"

Usuario: "Clínica San Rafael, Calle 100 con Carrera 15"
Agente: "Excelente, todo listo. Tengo registrado: terapia el viernes a las 3pm,
         recogida en Calle 123 #45-67 Suba, destino Clínica San Rafael.
         ¿Hay algo más en lo que pueda ayudarle?"

✅ CLOSING
Usuario: "No, eso es todo, gracias"
Agente: "Antes de despedirnos, lo invito a calificar nuestro servicio del 1
         al 5. ¿Cómo calificaría su experiencia hoy?"

⭐ SURVEY
Usuario: "5"
Agente: "Muchas gracias por su calificación. Que tenga un excelente día!"
```

---

¡Disfruta del agente conversacional mejorado! 🎉
