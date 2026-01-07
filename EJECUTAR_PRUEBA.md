# 🚀 Guía de Ejecución - Prueba End-to-End

## Prueba del Agente Conversacional de Transporte Médico

Esta guía te permitirá ejecutar y probar el agente conversacional con una conversación real.

---

## 📋 Requisitos Previos

1. **Python 3.11+** instalado
2. **Dependencias instaladas**

---

## 🔧 Paso 1: Instalar Dependencias

```bash
# Crear entorno virtual (si no existe)
python -m venv venv

# Activar entorno virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependencias
pip install fastapi uvicorn pydantic pydantic-settings requests
```

---

## 🚀 Paso 2: Iniciar el Servidor

Abre una **primera terminal** y ejecuta:

```bash
# Navegar al directorio del proyecto
cd C:\Users\Administrador\Documents\Transporte

# Activar entorno virtual
venv\Scripts\activate

# Iniciar servidor FastAPI
uvicorn src.presentation.api.main:app --reload --host 0.0.0.0 --port 8000
```

Deberías ver:

```
🚀 Transformas Medical Transport Agent v1.0.0 starting...
📍 Environment: development
🤖 Agent: María
🏥 Company: Transformas
📋 API Docs: http://0.0.0.0:8000/docs

INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**✅ ¡El servidor está corriendo!**

---

## 🧪 Paso 3: Ejecutar Prueba End-to-End

Abre una **segunda terminal** (deja la primera corriendo) y ejecuta:

```bash
# Navegar al directorio del proyecto
cd C:\Users\Administrador\Documents\Transporte

# Activar entorno virtual
venv\Scripts\activate

# Ejecutar script de prueba
python test_conversation_flow.py
```

---

## 📊 Qué Esperar

El script ejecutará **2 flujos de conversación**:

### **Flujo 1: Happy Path** ✅
Conversación exitosa de coordinación de servicio:
1. Saludo
2. Identificación del paciente
3. Validación de documento y EPS
4. Coordinación de servicio de terapia
5. Cierre
6. Encuesta de calidad

### **Flujo 2: Con Incidente** ⚠️
Conversación con reporte de queja:
1. Saludo
2. Identificación
3. Reporte de queja (conductor impuntual)
4. Gestión del incidente
5. Continuación con coordinación de servicio
6. Cierre y encuesta

---

## 🎯 Resultado Esperado

Verás una salida como esta:

```
🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀
TRANSFORMAS MEDICAL TRANSPORT AGENT - E2E TEST
🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀

🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯
TESTING: Happy Path - Successful Service Coordination
🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯

✅ Server healthy: Transformas Medical Transport Agent v1.0.0

🔄 Creating new session...
✅ Session created: 550e8400...
📅 Phase: GREETING

================================================================================

👤 USER: Hola, buenos días
🤖 AGENT: Buenos días, le habla María de Transformas, empresa autorizada por EPS Cosalud...

📊 Phase: IDENTIFICATION

...

✅ Happy path test completed successfully!
```

---

## 🌐 Explorar API Interactivamente

Mientras el servidor está corriendo, puedes:

### **1. Documentación Swagger**
Abre en tu navegador:
```
http://localhost:8000/docs
```

### **2. Documentación ReDoc**
```
http://localhost:8000/redoc
```

### **3. Health Check**
```bash
curl http://localhost:8000/api/v1/health
```

---

## 📝 Probar Manualmente con cURL

### Crear Sesión:
```bash
curl -X POST http://localhost:8000/api/v1/session \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "María"}'
```

**Respuesta:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2024-01-15T10:30:00Z",
  "conversation_phase": "GREETING"
}
```

### Enviar Mensaje:
```bash
curl -X POST http://localhost:8000/api/v1/conversation/message \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -d '{"message": "Hola, buenos días"}'
```

---

## 🔍 Debugging

### El servidor no inicia:
- Verifica que el puerto 8000 no esté en uso
- Revisa que las dependencias estén instaladas
- Asegúrate de estar en el directorio correcto

### El script de prueba falla:
- Asegúrate de que el servidor esté corriendo primero
- Verifica que uses el puerto correcto (8000)
- Revisa los logs del servidor para errores

### Ver logs en detalle:
```bash
# Iniciar servidor con logs de debug
uvicorn src.presentation.api.main:app --reload --log-level debug
```

---

## 🛑 Detener el Servidor

En la terminal del servidor, presiona:
```
Ctrl + C
```

---

## ✅ Verificación de Éxito

La prueba es exitosa si ves:

```
✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅
ALL TESTS COMPLETED SUCCESSFULLY!
✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅
```

---

## 📚 Próximos Pasos

Después de verificar que funciona:

1. **Revisar la implementación** en `src/agent/mock_agent.py`
2. **Explorar los endpoints** en `src/presentation/api/v1/endpoints/`
3. **Personalizar las respuestas** del agente
4. **Agregar más fases** conversacionales
5. **Integrar con LangGraph** para la versión de producción

---

## 🎓 Estructura de la Conversación

El agente maneja estas fases:

1. **GREETING** - Saludo inicial
2. **IDENTIFICATION** - Identificación del paciente
3. **LEGAL_NOTICE** - Aviso de grabación
4. **SERVICE_COORDINATION** - Coordinación del servicio
5. **INCIDENT_MANAGEMENT** - Gestión de quejas (opcional)
6. **ESCALATION** - Redirección a EPS (opcional)
7. **CLOSING** - Cierre cortés
8. **SURVEY** - Encuesta de calidad
9. **END** - Fin de conversación

---

## 💡 Tips

- El agente es un **mock simplificado** para demostración
- La versión final usará **LangGraph + OpenAI GPT-4**
- Actualmente **no requiere Redis** ni OpenAI API key
- Es **completamente funcional** para pruebas

---

## 🆘 Ayuda

Si tienes problemas, revisa:
1. Los logs del servidor
2. El archivo `test_conversation_flow.py`
3. La documentación en `/docs`
4. El código de los endpoints

---

¡Disfruta probando el agente! 🚀
