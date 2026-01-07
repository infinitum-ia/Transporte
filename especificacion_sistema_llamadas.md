# Especificación del Sistema de Llamadas - Transporte de Pacientes

## 1. DESCRIPCIÓN GENERAL

El sistema debe manejar dos tipos de llamadas:
- **Llamadas Entrantes**: Usuarios/pacientes que llaman solicitando información o servicios
- **Llamadas Salientes**: Llamadas de confirmación de servicios programados

---

## 2. FLUJO DE LLAMADAS ENTRANTES

### 2.1 Etapa de Bienvenida
**Script obligatorio:**
> "Buenos días/tardes gracias por comunicarse con nosotros, mi nombre es [NOMBRE_AGENTE_IA]. ¿En qué le puedo servir/ayudar el día de hoy?"

### 2.2 Recolección de Datos
El sistema debe solicitar y capturar:
- Nombre y apellidos del paciente
- Tipo de documento (CC, TI, CE, etc.)
- Número de documento
- Departamento
- EPS (Entidad Promotora de Salud)

**Manejo de errores:**
Si no se entiende la información: "Disculpe, no entendí la información. ¿Me puede repetir, por favor?"

### 2.3 Etapa de Solución
- Ejecutar el procedimiento correspondiente
- Si no puede resolver al primer contacto: dar fecha de respuesta y cumplirla
- Usar lenguaje claro, evitar términos técnicos
- Hacer todas las preguntas necesarias para recopilar información completa
- Registrar toda la información con precisión

### 2.4 Asistencia Adicional
**Script obligatorio:**
> "¿Hay algo más en lo que pueda servirle el día de hoy? ¿Le puedo ayudar en algo más?"

### 2.5 Despedida
**Scripts obligatorios:**
1. Encuesta: "Lo invitamos a permanecer en línea para que califique nuestros servicios"
2. Cierre: "Gracias por su tiempo señor(a) [NOMBRE_USUARIO]. Recuerde que habló con [NOMBRE_AGENTE] de [EMPRESA]. Que tenga un excelente día"

---

## 3. FLUJO DE LLAMADAS SALIENTES

### 3.1 Objetivo
Confirmar servicios de transporte programados para pacientes.

### 3.2 Datos Previos Disponibles
El sistema debe cargar del archivo Excel (`datos_llamadas_salientes.csv`):

#### A) Información de Identidad Personal
- Nombre y apellidos completos del paciente
- Tipo y número de documento
- Nombre del familiar responsable (si aplica)
- Parentesco
- Teléfono de contacto

#### B) Datos del Servicio y Tratamiento
- Tipo de servicio: Terapia, Diálisis, Cita con Especialista
- Tipo de tratamiento específico
- Frecuencia: días de la semana
- Fechas programadas específicas
- Hora del servicio
- Centro de salud destino

#### C) Información Logística
- Ciudad y zona
- Modalidad de transporte: "Ruta" o "Desembolso"
- Dirección de recogida completa
- Observaciones especiales

#### D) Historial de Observaciones
- Necesidades especiales (ej: "requiere carro grande por silla de ruedas")
- Problemas previos
- Preferencias del paciente

### 3.3 Estructura de la Llamada Saliente

#### Paso 1: Identificación y Autorización
**Script:**
> "Habla con [NOMBRE_AGENTE] de Transformas, empresa de transporte autorizada por la EPS [NOMBRE_EPS]. ¿Me confirma, por favor, su nombre?"

#### Paso 2: Aviso de Grabación
> "Le indico que la llamada está siendo grabada y monitoreada"

#### Paso 3: Confirmación del Servicio
El script varía según el tipo de servicio:

**Para Terapias:**
> "El paciente tiene programado servicio de transporte para [TIPO_TRATAMIENTO] el/los día(s) [FECHAS] a las [HORA] hacia [CENTRO_SALUD]. ¿Confirma la asistencia?"

**Para Diálisis:**
> "Mi llamada es para coordinar los servicios de diálisis [FRECUENCIA] de [HORA_INICIO] a [HORA_FIN]. ¿Confirma los servicios?"

**Para Citas con Especialista:**
> "El paciente tiene una cita programada para el [FECHA] a las [HORA] en [CENTRO_SALUD]. ¿Confirma la asistencia?"

#### Paso 4: Especificación de Modalidad

**Si es RUTA (vehículo compartido):**
> "El servicio le queda coordinado por medio de ruta. Debe estar listo a las [HORA] y atento a la llamada del conductor"

**Si es DESEMBOLSO:**
> "El servicio le queda coordinado por medio de desembolso. Me confirma, por favor, su documento"
> [Esperar respuesta]
> "Se va a acercar a Efecty en el transcurso de 24 a 48 horas para que pueda realizar el retiro con el documento y el código de retiro"

#### Paso 5: Observaciones Especiales
Si existen observaciones en el campo `observaciones_especiales`, mencionarlas:
> "Tengo registrado que [OBSERVACION]. ¿Es correcto?"

#### Paso 6: Preguntas del Usuario
> "¿Tiene alguna pregunta o inquietud sobre el servicio?"

#### Paso 7: Cierre
> "Le confirmo que el servicio queda coordinado. Estaremos en contacto. ¿Le puedo ayudar en algo más?"

---

## 4. CASOS ESPECIALES Y MANEJO DE SITUACIONES

### 4.1 Cambio de Fechas (Caso Adaluz Valencia)
**Situación:** El usuario indica que las fechas han cambiado

**Respuesta del sistema:**
> "Entendido. Voy a dejar la observación para actualizar las fechas cuando nos envíen la nueva autorización y nos comunicaremos nuevamente"

**Acción:** Actualizar `estado_confirmacion` = "Reprogramar" y registrar nuevas fechas en observaciones

### 4.2 Quejas por Rotación de Conductores (Caso Joan)
**Situación:** El usuario expresa preferencia por un conductor específico

**Respuesta del sistema:**
> "Comprendo su inquietud. Los conductores se asignan de manera rotativa, pero enviaré su solicitud al área encargada para que evalúen su caso"

**Acción:** Registrar la queja en observaciones y marcar para seguimiento

### 4.3 Necesidades Especiales - Silla de Ruedas (Caso Álvaro Castro)
**Situación:** Paciente requiere vehículo grande por movilidad reducida

**Validación previa:** Verificar campo `observaciones_especiales` contiene "silla de ruedas" o "carro grande"

**Respuesta del sistema:**
> "Tengo registrado que el paciente requiere un vehículo grande por silla de ruedas. Esta observación está en el sistema y se validará con el coordinador antes de asignar el vehículo"

**Información adicional si el usuario insiste:**
> "Si continúa teniendo inconvenientes, puede acercarse a su EPS para solicitar un servicio expreso donde solo se traslade al paciente"

### 4.4 Zona Sin Cobertura (Caso Emilce)
**Situación:** Paciente vive fuera del área de cobertura

**Validación:** Verificar campo `observaciones_especiales` contiene "zona sin cobertura" o la ciudad no está en lista de cobertura

**Respuesta del sistema:**
> "El servicio de ruta opera únicamente interno [CIUDAD_BASE]. Para servicios desde [ZONA_PACIENTE] hasta [CIUDAD_BASE] debe acercarse a su EPS para que verifiquen la autorización de ese trayecto adicional"

**Acción:** Marcar `estado_confirmacion` = "Zona sin cobertura"

### 4.5 Paciente Fuera de la Ciudad (Caso Lilia Veleño)
**Situación:** Paciente temporalmente en otra ciudad

**Respuesta del sistema:**
> "Entendido. Los servicios de [FECHAS_AUSENCIA] quedarían como no prestados. ¿Tiene número de WhatsApp?"

[Esperar respuesta]

> "Cuando regrese a [CIUDAD], por favor envíeme un mensaje por WhatsApp para coordinar la reanudación del servicio"

**Acción:** Marcar `estado_confirmacion` = "Reprogramar" y registrar fecha de retorno

### 4.6 Transporte Intermunicipal (Caso Kelly García)
**Situación:** Servicio entre ciudades diferentes

**Información adicional a proporcionar:**
- Punto de encuentro específico
- Hora de salida del vehículo
- Confirmación clara de la información

**Script:**
> "El vehículo sale a las [HORA_SALIDA] desde [PUNTO_ENCUENTRO]. ¿Está clara la información?"

### 4.7 Problemas de Audio/Conexión (Caso Valeria)
**Situación:** Usuario indica que no escucha bien

**Respuesta del sistema:**
> "Disculpe, voy a hablar más claro. ¿Me escucha mejor ahora?"

**Acción:** Pausar 2 segundos, luego repetir la información importante lentamente

---

## 5. ESTRUCTURA DEL ARCHIVO EXCEL (FUENTE DE DATOS)

### 5.1 Ubicación
`C:\Users\Administrador\Documents\Transporte\datos_llamadas_salientes.csv`

**IMPORTANTE:** Este archivo es la fuente de datos principal del sistema. El sistema leerá directamente de aquí para obtener la información de los pacientes y servicios a confirmar.

### 5.2 Campos del Archivo

| Campo | Tipo | Descripción | Ejemplo |
|-------|------|-------------|---------|
| nombre_paciente | Texto | Nombre del paciente | John Jairo |
| apellido_paciente | Texto | Apellido del paciente | Mesa |
| tipo_documento | Texto | CC, TI, CE, etc. | CC |
| numero_documento | Numérico | Número de identificación | 1234567 |
| eps | Texto | Nombre de la EPS | Cosalud |
| departamento | Texto | Departamento de residencia | Magdalena |
| ciudad | Texto | Ciudad de residencia | Santa Marta |
| nombre_familiar | Texto | Nombre del familiar (opcional) | Carmen Gamero |
| parentesco | Texto | Relación con el paciente | Familiar/Madre/Esposa |
| telefono | Texto | Número de contacto | 3001234567 |
| tipo_servicio | Texto | Terapia/Diálisis/Cita Especialista | Terapia |
| tipo_tratamiento | Texto | Descripción del tratamiento | Fisioterapia |
| frecuencia | Texto | Días de la semana | Lunes-Miércoles-Viernes |
| fecha_servicio | Texto | Fechas separadas por coma | 07/01/2025,08/01/2025 |
| hora_servicio | Texto | Hora formato 24h | 07:20 |
| destino_centro_salud | Texto | Nombre del centro médico | Fundación Camel |
| modalidad_transporte | Texto | Ruta/Desembolso | Ruta |
| zona_recogida | Texto | Zona de la ciudad | Centro |
| direccion_completa | Texto | Dirección exacta | Calle 15 #10-20 |
| observaciones_especiales | Texto | Notas importantes | Prefiere conductor Juan Carlos |
| estado_confirmacion | Texto | Pendiente/Confirmado/Reprogramar | Pendiente |

### 5.3 Casos de Prueba Incluidos

El archivo contiene 10 casos de prueba que cubren:
1. ✅ Terapia por ruta - días múltiples
2. ✅ Terapia por desembolso - confirmación documento
3. ✅ Reprogramación de citas
4. ✅ Diálisis con queja de conductor
5. ✅ Cita especialista con necesidad de vehículo grande
6. ✅ Zona sin cobertura
7. ✅ Paciente fuera de la ciudad temporalmente
8. ✅ Transporte intermunicipal
9. ✅ Terapia ocupacional por desembolso
10. ✅ Diálisis estándar

---

## 6. LÓGICA DE PROCESAMIENTO

### 6.1 Para Llamadas Salientes (Lectura desde Excel)

```
1. ABRIR archivo: datos_llamadas_salientes.csv
2. LEER todos los registros
3. FILTRAR registros donde estado_confirmacion = "Pendiente"
4. ORDENAR por fecha_servicio (más próxima primero)
5. Para cada registro:
   a. VALIDAR que tenga teléfono válido (10 dígitos)
   b. VALIDAR que fecha_servicio sea futura
   c. CARGAR todos los datos del paciente en memoria
   d. INICIAR llamada al teléfono
   e. SEGUIR flujo de llamada saliente (sección 3.3)
   f. MANEJAR casos especiales según corresponda (sección 4)
   g. ACTUALIZAR estado_confirmacion en el archivo según resultado:
      - "Confirmado" si acepta el servicio
      - "Reprogramar" si cambia fechas o está ausente
      - "Rechazado" si cancela el servicio
      - "Zona sin cobertura" si no hay servicio disponible
      - "No contesta" si no responde
   h. REGISTRAR observaciones de la llamada en campo observaciones_especiales
   i. GUARDAR cambios en el archivo Excel
   j. ESPERAR 10 segundos antes del siguiente registro
6. GENERAR reporte de llamadas realizadas
7. CERRAR archivo
```

### 6.2 Actualización del Archivo Excel

Después de cada llamada, el sistema debe:
1. Actualizar el campo `estado_confirmacion` con el nuevo estado
2. Agregar información a `observaciones_especiales` (sin borrar lo anterior)
3. Guardar el archivo inmediatamente
4. Mantener backup del archivo antes de modificar

**Formato de observaciones actualizadas:**
```
[FECHA_HORA] Llamada realizada - Estado: [ESTADO] - Notas: [COMENTARIOS]
```

### 6.3 Estados de Confirmación

| Estado | Descripción | Siguiente Acción |
|--------|-------------|------------------|
| Pendiente | Sin contactar | Realizar llamada |
| Confirmado | Servicio aceptado | Coordinar vehículo |
| Reprogramar | Cambio de fechas | Esperar nueva autorización |
| Rechazado | Servicio cancelado | Notificar a EPS |
| Zona sin cobertura | Fuera de área | Redirigir a EPS |
| No contesta | Sin respuesta | Reintentar en 2 horas (máx 3 intentos) |

---

## 7. VALIDACIONES Y REGLAS DE NEGOCIO

### 7.1 Validaciones Pre-Llamada
- ✅ Verificar que el teléfono tenga 10 dígitos
- ✅ Verificar que la fecha del servicio sea futura
- ✅ Verificar que exista modalidad de transporte definida
- ✅ Verificar que exista destino

### 7.2 Reglas de Horarios
- **Llamadas entre:** 8:00 AM - 6:00 PM
- **No llamar:** Domingos y festivos
- **Para servicios al día siguiente:** Llamar con mínimo 24h de anticipación

### 7.3 Reglas de Modalidad
- **RUTA:** Para servicios dentro de la ciudad, pacientes múltiples
- **DESEMBOLSO:** Para zonas de difícil acceso, requiere solicitar documento

### 7.4 Reglas de Observaciones Especiales
Si contiene:
- "silla de ruedas" o "carro grande" → Mencionar al confirmar y validar vehículo
- "conductor preferido" → Registrar pero informar que es rotativo
- "zona sin cobertura" → No confirmar, redirigir a EPS
- "temporalmente fuera" → Confirmar fecha de retorno

---

## 8. MÉTRICAS Y SEGUIMIENTO

### 8.1 KPIs del Sistema
- Tasa de confirmación exitosa (meta: >80%)
- Tiempo promedio por llamada (meta: 2-3 minutos)
- Tasa de reprogramación (tracking)
- Quejas registradas vs resueltas
- Servicios confirmados vs ejecutados

### 8.2 Registro de Llamadas
Cada llamada debe registrar:
- Fecha y hora de la llamada
- Duración
- Estado final
- Observaciones del usuario
- Problemas identificados
- Acciones de seguimiento requeridas

---

## 9. INTEGRACIÓN CON OTROS SISTEMAS

### 9.1 Sistema de Gestión de Vehículos
Enviar información de servicios confirmados:
- Fecha y hora
- Dirección de recogida
- Destino
- Observaciones especiales (silla de ruedas, etc.)
- Modalidad (ruta/individual)

### 9.2 Sistema de la EPS
Reportar:
- Servicios no prestados
- Zonas sin cobertura
- Solicitudes de servicio expreso
- Cambios de autorización

### 9.3 Sistema de Notificaciones
- WhatsApp: Para confirmaciones y recordatorios
- SMS: Para información de conductor asignado
- Email: Resumen del servicio coordinado

---

## 10. EJEMPLO DE FLUJO COMPLETO

### Llamada Saliente - Caso John Jairo Mesa

**Sistema carga datos:**
```
Paciente: John Jairo Mesa
Familiar: Carmen Gamero
Teléfono: 3001234567
Servicio: Terapia - Fisioterapia
Fechas: 07/01/2025, 08/01/2025
Hora: 07:20
Destino: Fundación Camel
Modalidad: Ruta
```

**Flujo de conversación:**

1. 📞 Sistema marca a 3001234567

2. 🤖 **Sistema:** "Habla con [Nombre_IA] de Transformas, empresa de transporte autorizada por la EPS Cosalud. ¿Me confirma, por favor, su nombre?"

3. 👤 **Usuario:** "Carmen Gamero"

4. 🤖 **Sistema:** "Le indico que la llamada está siendo grabada y monitoreada. El paciente John Jairo Mesa tiene programado servicio de transporte para fisioterapia los días 7 y 8 de enero a las 7:20 AM hacia Fundación Camel. ¿Confirma la asistencia?"

5. 👤 **Usuario:** "Sí, confirmado"

6. 🤖 **Sistema:** "Perfecto. Le confirmo que el servicio queda coordinado por medio de ruta los dos días. Debe estar listo a las 7:20 y atento a la llamada del conductor. ¿Tiene alguna pregunta?"

7. 👤 **Usuario:** "¿Ese transporte sirve para citas con especialistas?"

8. 🤖 **Sistema:** "El servicio cubre solamente las terapias autorizadas por la EPS. Si el paciente tiene citas con especialistas, debe solicitarlo directamente en Cosalud para que nos envíen la autorización correspondiente. ¿Algo más en que pueda ayudarle?"

9. 👤 **Usuario:** "No, gracias"

10. 🤖 **Sistema:** "Gracias por su tiempo. El servicio queda confirmado para los días 7 y 8 de enero. Que tenga un excelente día"

11. ✅ Sistema actualiza registro:
```
estado_confirmacion: "Confirmado"
observaciones_adicionales: "Preguntó por citas con especialistas - se le informó del proceso"
fecha_confirmacion: 2025-01-05 10:30:00
```

---

## 11. NOTAS TÉCNICAS

### 11.1 Tecnologías Sugeridas
- **Motor de voz:** Text-to-Speech de calidad natural
- **Reconocimiento de voz:** Speech-to-Text con modelo en español
- **Base de datos:** Para almacenar registros y actualizaciones
- **API de telefonía:** Twilio, Vonage o similar

### 11.2 Consideraciones de UX
- Pausas naturales entre frases (0.5-1 segundo)
- Velocidad de habla: Normal, no acelerada
- Tono: Profesional pero amable
- Pronunciación clara de números y fechas

### 11.3 Manejo de Errores
- Si no reconoce la respuesta: pedir repetición (máximo 2 veces)
- Si el usuario no responde: esperar 5 segundos y repetir pregunta
- Si la llamada se corta: registrar como "No completada" e intentar nuevamente

---

## RESUMEN EJECUTIVO

Este sistema automatiza las llamadas de confirmación de transporte para pacientes, siguiendo protocolos establecidos y manejando casos especiales de manera inteligente. El archivo Excel de prueba contiene 10 casos reales que permiten validar todos los flujos y situaciones documentadas.

**Próximos pasos:**
1. ✅ Archivo de datos de prueba creado
2. ⏳ Implementar motor de llamadas
3. ⏳ Integrar reconocimiento y síntesis de voz
4. ⏳ Desarrollar lógica de casos especiales
5. ⏳ Conectar con sistemas externos (vehículos, EPS)
6. ⏳ Pruebas con casos reales del archivo Excel
