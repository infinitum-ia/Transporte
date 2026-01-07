# Guía de Uso - Interfaz Streamlit

## Descripción

Aplicación de chat interactiva para probar el agente conversacional de transporte médico de Transformas. Soporta tanto llamadas **ENTRANTES** (cliente llama) como **SALIENTES** (empresa confirma servicios).

## Requisitos Previos

1. **API en ejecución**
   - El servidor FastAPI debe estar corriendo en `http://localhost:8000`
   - Para iniciarlo: `uvicorn src.presentation.api.main:app --reload`

2. **Dependencias instaladas**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configuración**
   - Archivo `.env` configurado con `AGENT_MODE=llm` y `OPENAI_API_KEY`
   - Redis ejecutándose (para persistencia de sesiones)
   - Para llamadas salientes: archivo Excel con datos de pacientes

## Inicio Rápido

### Windows (Batch)
```bash
run_streamlit.bat
```

### Windows (PowerShell)
```powershell
.\run_streamlit.ps1
```

### Unix/Mac/Linux
```bash
chmod +x run_streamlit.sh
./run_streamlit.sh
```

### Manual
```bash
streamlit run app_streamlit.py
```

La aplicación se abrirá automáticamente en tu navegador en `http://localhost:8501`

## Uso de la Aplicación

### Panel Lateral (Configuración)

1. **Nombre del Agente**: Personaliza el nombre del agente (por defecto: María)

2. **Tipo de Llamada**:
   - 📞 **ENTRANTE**: Cliente llama solicitando servicio
   - 📱 **SALIENTE**: Confirmación de servicio programado

3. **Teléfono del Paciente** (solo para llamadas salientes):
   - Ingresa el número del paciente registrado en el sistema
   - Debe coincidir con los datos del archivo Excel

4. **Botón "Iniciar Nueva Conversación"**:
   - Crea una nueva sesión
   - Carga los datos del paciente (si es outbound)
   - Limpia el historial de chat

5. **Información de Sesión**:
   - Session ID
   - Tipo de llamada
   - Fase actual de conversación
   - Datos del paciente
   - Estado de confirmación (outbound)

### Área Principal (Chat)

1. **Historial de Conversación**:
   - Mensajes del usuario (azul, a la derecha)
   - Mensajes del agente (gris, a la izquierda)
   - Timestamps para cada mensaje

2. **Input de Mensaje**:
   - Escribe tu mensaje en el campo de texto
   - Click en "📤 Enviar" o presiona Enter

3. **Botones Rápidos** (solo llamadas entrantes):
   - "👋 Buenos días"
   - "🆔 Soy Juan Pérez"
   - "✅ Acepto grabación"

## Flujos de Conversación

### Llamada Entrante (INBOUND)

```
1. GREETING → Saludo inicial del agente
2. IDENTIFICATION → Identificación del paciente
3. LEGAL_NOTICE → Aviso de grabación
4. SERVICE_COORDINATION → Coordinación del servicio
5. [INCIDENT_MANAGEMENT] → Gestión de quejas (opcional)
6. [ESCALATION] → Derivación a EPS (opcional)
7. CLOSING → Cierre
8. SURVEY → Encuesta de satisfacción
9. END → Fin
```

**Ejemplo de conversación:**
```
Usuario: Buenos días
Agente: Buenos días, habla María de Transformas...

Usuario: Necesito transporte para diálisis
Agente: Con gusto le ayudo. ¿Podría indicarme su nombre completo?

Usuario: Juan Pérez, cédula 12345678
Agente: Gracias Sr. Pérez. Esta llamada será grabada...

Usuario: Sí, acepto
Agente: Perfecto. ¿Para qué fecha necesita el servicio?
...
```

### Llamada Saliente (OUTBOUND)

```
1. OUTBOUND_GREETING → Identificación y verificación
2. OUTBOUND_LEGAL_NOTICE → Aviso de grabación
3. OUTBOUND_SERVICE_CONFIRMATION → Confirmación del servicio
4. [OUTBOUND_SPECIAL_CASES] → Cambios/quejas (opcional)
5. OUTBOUND_CLOSING → Cierre
6. END → Fin
```

**Ejemplo de conversación:**
```
Agente: Buenos días, ¿hablo con el Sr. Juan Pérez?
Usuario: Sí, soy yo

Agente: Habla María de Transformas. Esta llamada será grabada...
Usuario: De acuerdo

Agente: Le llamo para confirmar su transporte de diálisis programado para el 20 de enero a las 8:00 AM...
Usuario: Sí, está correcto

Agente: Perfecto, su servicio está confirmado...
```

## Características Especiales

### Detección de Incidencias
El sistema detecta automáticamente:
- Quejas sobre conductores
- Problemas de puntualidad
- Solicitudes de conductor específico
- Cambios de fecha
- Necesidades especiales

### Actualización Excel (Outbound)
Al finalizar una llamada saliente, el sistema actualiza automáticamente:
- Estado de confirmación
- Observaciones
- Cambios solicitados
- Incidencias reportadas

### Escalamiento Automático
Solicitudes fuera del alcance se escalan a la EPS:
- Cambios médicos
- Problemas de cobertura
- Solicitudes no autorizadas

## Información de Sesión

La aplicación muestra en tiempo real:
- **Session ID**: Identificador único de la conversación
- **Call Direction**: INBOUND o OUTBOUND
- **Conversation Phase**: Fase actual del flujo
- **Patient Name**: Nombre del paciente
- **Service Type**: Tipo de servicio (Diálisis, Terapia, Cita)
- **Confirmation Status**: Estado de confirmación (outbound)

## API Endpoints Utilizados

La aplicación interactúa con los siguientes endpoints:

1. **POST /api/v1/session/create**
   - Crea nueva sesión con parámetro booleano `is_outbound`

2. **POST /api/v1/conversation/message/v2**
   - Envía mensajes del usuario
   - Header: `X-Session-ID`

3. **GET /api/v1/calls/{session_id}**
   - Obtiene detalles completos de la sesión

## Solución de Problemas

### La aplicación no inicia
```bash
# Verificar que streamlit está instalado
pip install streamlit

# Ejecutar directamente
streamlit run app_streamlit.py
```

### Error: "Call orchestrator not configured"
- Asegúrate de que `AGENT_MODE=llm` en `.env`
- Reinicia el servidor FastAPI

### Error: "No patient found with phone"
- Verifica que el teléfono existe en el archivo Excel
- Asegúrate de que `EXCEL_PATH` está configurado en `.env`
- El formato debe ser 10 dígitos sin espacios ni guiones

### Error: "Session not found"
- La sesión puede haber expirado (TTL por defecto: 1 hora)
- Inicia una nueva conversación

### API no responde
```bash
# Verificar que el API está corriendo
curl http://localhost:8000/health

# Iniciar el API si no está corriendo
uvicorn src.presentation.api.main:app --reload
```

## Variables de Entorno Requeridas

```bash
# API Configuration
AGENT_MODE=llm                          # Modo del agente (llm/mock)
OPENAI_API_KEY=sk-...                   # API key de OpenAI

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Agent Configuration
AGENT_NAME=María
COMPANY_NAME=Transformas
EPS_NAME=Cosalud

# Excel (para llamadas salientes)
EXCEL_PATH=./datos_llamadas_salientes.csv
```

## Personalización

### Modificar URL del API
Edita `app_streamlit.py`:
```python
API_BASE_URL = "http://localhost:8000/api/v1"
```

### Cambiar Puerto de Streamlit
```bash
streamlit run app_streamlit.py --server.port 8502
```

### Modificar Estilos
Edita la sección de CSS en `app_streamlit.py`:
```python
st.markdown("""
<style>
    .main-header {
        /* Tus estilos aquí */
    }
</style>
""", unsafe_allow_html=True)
```

## Características Avanzadas

### Botones de Ejemplo
Los botones rápidos facilitan el testing al proporcionar mensajes predefinidos para casos comunes.

### Auto-actualización
La interfaz se actualiza automáticamente después de cada mensaje para reflejar cambios en la fase de conversación.

### Historial Persistente
El historial de chat se mantiene en la sesión de Streamlit mientras esté activa.

### Timestamps
Cada mensaje incluye la hora exacta de envío para facilitar el análisis.

## Limitaciones Conocidas

1. **Una sesión a la vez**: La interfaz maneja una conversación por pestaña del navegador
2. **Sin historial entre recargas**: El historial de chat se pierde al recargar la página (pero la sesión del backend persiste)
3. **Sin soporte para multimedia**: Solo mensajes de texto
4. **Dependencia del API**: Requiere que el servidor FastAPI esté ejecutándose

## Soporte

Para problemas o preguntas:
1. Revisa los logs de Streamlit en la terminal
2. Verifica los logs del API en `api.log`
3. Consulta la documentación interactiva del API en `http://localhost:8000/docs`

## Próximas Mejoras

- [ ] Soporte para múltiples sesiones
- [ ] Historial persistente entre recargas
- [ ] Export de conversaciones a PDF
- [ ] Métricas y estadísticas en tiempo real
- [ ] Soporte para adjuntar documentos
- [ ] Notificaciones visuales mejoradas
