# 📖 Guía de Uso del Sistema con Archivo Excel

## 🎯 Descripción General

El sistema trabaja **directamente con archivos Excel (CSV)** como fuente de datos. No requiere base de datos.

---

## 📁 Archivos del Sistema

### 1. **datos_llamadas_salientes.csv**
**Ubicación:** `C:\Users\Administrador\Documents\Transporte\datos_llamadas_salientes.csv`

**Función:** Archivo principal con la información de pacientes y servicios a confirmar.

**Formato:** CSV con 21 columnas

### 2. **procesador_llamadas_salientes.py**
**Ubicación:** `C:\Users\Administrador\Documents\Transporte\procesador_llamadas_salientes.py`

**Función:** Script que lee el archivo Excel y procesa las llamadas.

### 3. **especificacion_sistema_llamadas.md**
**Ubicación:** `C:\Users\Administrador\Documents\Transporte\especificacion_sistema_llamadas.md`

**Función:** Documentación técnica completa del sistema.

---

## 🚀 Cómo Funciona

### Flujo de Trabajo

```
1. ADMIN agrega pacientes al archivo Excel
   ↓
2. Sistema lee el archivo y filtra registros "Pendientes"
   ↓
3. Sistema valida datos (teléfono, fechas)
   ↓
4. Sistema realiza llamadas una por una
   ↓
5. Sistema actualiza estado en Excel después de cada llamada
   ↓
6. Sistema genera reporte final
```

---

## 📝 Agregar Nuevos Pacientes

### Opción A: Editar directamente el CSV

1. Abrir `datos_llamadas_salientes.csv` en Excel
2. Agregar nueva fila con todos los datos
3. **IMPORTANTE:** Dejar `estado_confirmacion` como `Pendiente`
4. Guardar el archivo

### Opción B: Copiar una fila existente

1. Copiar una fila similar (mismo tipo de servicio)
2. Modificar los datos del nuevo paciente
3. Cambiar `estado_confirmacion` a `Pendiente`
4. Guardar

### Campos Obligatorios

✅ **SIEMPRE completar:**
- nombre_paciente
- apellido_paciente
- telefono (10 dígitos)
- tipo_servicio
- fecha_servicio (formato: DD/MM/YYYY)
- hora_servicio (formato: HH:MM)
- destino_centro_salud
- modalidad_transporte (Ruta o Desembolso)
- estado_confirmacion (Pendiente para nuevos)

⚠️ **Opcionales:**
- nombre_familiar (solo si hay familiar responsable)
- parentesco
- observaciones_especiales

---

## ▶️ Ejecutar el Sistema

### Requisitos Previos

```bash
# Instalar Python (si no está instalado)
# Descargar desde: https://www.python.org/downloads/

# Instalar pandas
pip install pandas
```

### Ejecutar el Procesador

```bash
# Abrir terminal/cmd
cd C:\Users\Administrador\Documents\Transporte

# Ejecutar el script
python procesador_llamadas_salientes.py
```

### Qué hace el script:

1. ✅ Crea backup automático del archivo
2. ✅ Lee todos los registros
3. ✅ Filtra solo los "Pendientes"
4. ✅ Valida teléfonos y fechas
5. ✅ Genera script personalizado para cada llamada
6. ✅ Simula la llamada (muestra el script)
7. ✅ Actualiza el estado en el archivo
8. ✅ Genera reporte final

---

## 🔄 Estados de Confirmación

| Estado | Significado | Qué hacer |
|--------|-------------|-----------|
| **Pendiente** | Sin contactar | Sistema intentará llamar |
| **Confirmado** | Servicio aceptado | Coordinar vehículo |
| **Reprogramar** | Cambió fechas | Esperar nueva autorización EPS |
| **Rechazado** | Servicio cancelado | Notificar a EPS |
| **No contesta** | No respondió | Sistema reintentará (máx 3 veces) |
| **Zona sin cobertura** | Fuera de área | Redirigir a EPS |

---

## 📊 Ejemplo de Actualización Automática

### Antes de la llamada:
```csv
nombre_paciente,apellido_paciente,telefono,estado_confirmacion,observaciones_especiales
John Jairo,Mesa,3001234567,Pendiente,
```

### Después de la llamada:
```csv
nombre_paciente,apellido_paciente,telefono,estado_confirmacion,observaciones_especiales
John Jairo,Mesa,3001234567,Confirmado,"[2025-01-06 10:30:15] Llamada realizada - Paciente confirmó asistencia. Sin novedades."
```

---

## 💾 Backups Automáticos

El sistema crea backups antes de modificar el archivo:

**Ubicación:** `C:\Users\Administrador\Documents\Transporte\backups\`

**Formato:** `datos_backup_YYYYMMDD_HHMMSS.csv`

**Ejemplo:** `datos_backup_20250106_103015.csv`

### Restaurar un Backup

Si algo sale mal:
1. Ir a la carpeta `backups`
2. Copiar el backup más reciente
3. Renombrar a `datos_llamadas_salientes.csv`
4. Reemplazar el archivo principal

---

## 🎨 Personalizar Scripts de Llamadas

El sistema genera scripts automáticamente según el tipo de servicio:

### Script para Diálisis
```
Mi llamada es para coordinar los servicios de diálisis Lunes-Miércoles-Viernes
a las 16:00 en Centro de Diálisis Renal.
¿Confirma los servicios?
```

### Script para Terapia
```
El paciente Valeria Ballerospina tiene programado servicio de transporte
para Fisioterapia el/los día(s) 07/01/2025 a las 08:00
hacia Centro de Rehabilitación.
¿Confirma la asistencia?
```

### Script para Cita Especialista
```
El paciente Kelly Joana García tiene una cita programada
para el 08/01/2025 a las 09:00 en Hospital Regional Sincelejo.
¿Confirma la asistencia?
```

---

## 🛠️ Configuración Avanzada

### Cambiar Tiempo de Espera Entre Llamadas

Editar en `procesador_llamadas_salientes.py` línea ~320:

```python
# Por defecto: 10 segundos
time.sleep(10)

# Para 5 segundos:
time.sleep(5)

# Para 30 segundos:
time.sleep(30)
```

### Cambiar Ubicación del Archivo

Editar en `procesador_llamadas_salientes.py` líneas 10-11:

```python
ARCHIVO_DATOS = "datos_llamadas_salientes.csv"
RUTA_COMPLETA = r"C:\TU\NUEVA\RUTA\datos_llamadas_salientes.csv"
```

---

## 📞 Integración con Telefonía Real

El script actual **simula** las llamadas. Para integrar con telefonía real:

### Opción 1: Twilio (Recomendado)

```python
from twilio.rest import Client

# Configurar credenciales
account_sid = "tu_account_sid"
auth_token = "tu_auth_token"
client = Client(account_sid, auth_token)

# En la función realizar_llamada()
call = client.calls.create(
    to=datos['telefono'],
    from_="+57TUNUMERO",
    url="http://tu-servidor.com/script-llamada.xml"
)
```

### Opción 2: Vonage (Nexmo)

```python
import vonage

client = vonage.Client(key="tu_api_key", secret="tu_api_secret")
voice = vonage.Voice(client)

response = voice.create_call({
    'to': [{'type': 'phone', 'number': datos['telefono']}],
    'from': {'type': 'phone', 'number': '57TUNUMERO'},
    'answer_url': ['http://tu-servidor.com/answer']
})
```

---

## 🧪 Probar el Sistema

### Paso 1: Verificar el archivo de prueba

```bash
# Ver primeros 5 registros
python -c "import pandas as pd; df = pd.read_csv('datos_llamadas_salientes.csv'); print(df.head())"
```

### Paso 2: Ejecutar con modo de prueba

El script ya está configurado para simular llamadas y mostrar los scripts generados.

### Paso 3: Revisar resultados

1. Abrir `datos_llamadas_salientes.csv`
2. Verificar que los estados se actualizaron
3. Ver las observaciones agregadas
4. Revisar el reporte en consola

---

## ❓ Preguntas Frecuentes

### ¿Puedo usar Excel en vez de CSV?

Sí, pero debes guardarlo como CSV UTF-8:
1. Archivo → Guardar como
2. Tipo: CSV UTF-8 (delimitado por comas)

### ¿Qué pasa si cierro el programa a mitad de proceso?

- ✅ Los cambios ya guardados se conservan
- ✅ Puedes volver a ejecutar, solo procesará los "Pendientes"
- ✅ Existe backup del estado anterior

### ¿Cómo agregar 100 pacientes rápido?

1. Exporta desde tu sistema actual a CSV
2. Asegúrate que tenga las 21 columnas requeridas
3. Importa/copia los datos al archivo principal
4. Verifica que todos tengan `estado_confirmacion = Pendiente`

### ¿Puedo ejecutar llamadas a horas específicas?

Sí, puedes usar Windows Task Scheduler o cron (Linux):

**Windows:**
```bash
# Crear tarea programada para ejecutar a las 9 AM diariamente
schtasks /create /tn "LlamadasSalientes" /tr "python C:\Users\Administrador\Documents\Transporte\procesador_llamadas_salientes.py" /sc daily /st 09:00
```

---

## 📈 Reportes y Estadísticas

El sistema genera un reporte al finalizar cada ejecución:

```
================================================================================
📊 REPORTE FINAL
================================================================================
Total procesados: 10
✅ Confirmados: 7
⚠️  Otros estados: 3
Tasa de éxito: 70.0%
================================================================================
```

### Generar Reporte Detallado

```python
import pandas as pd

df = pd.read_csv('datos_llamadas_salientes.csv')

# Resumen por estado
print(df['estado_confirmacion'].value_counts())

# Resumen por tipo de servicio
print(df.groupby('tipo_servicio')['estado_confirmacion'].value_counts())

# Servicios próximos (7 días)
from datetime import datetime, timedelta
df['fecha_servicio_dt'] = pd.to_datetime(df['fecha_servicio'].str.split(',').str[0], format='%d/%m/%Y')
proximos = df[df['fecha_servicio_dt'] <= datetime.now() + timedelta(days=7)]
print(f"Servicios en los próximos 7 días: {len(proximos)}")
```

---

## 🔐 Seguridad y Privacidad

### Datos Sensibles

El archivo contiene información personal (LOPD/GDPR):
- ✅ No compartir el archivo
- ✅ Encriptar backups
- ✅ Restringir acceso a carpeta
- ✅ Eliminar backups antiguos (>30 días)

### Recomendaciones

```bash
# Cambiar permisos de carpeta (solo admin)
icacls "C:\Users\Administrador\Documents\Transporte" /grant Administrador:F /inheritance:r

# Encriptar carpeta de backups
cipher /e C:\Users\Administrador\Documents\Transporte\backups
```

---

## 🆘 Solución de Problemas

### Error: "File not found"
```
❌ Solución: Verificar que la ruta del archivo sea correcta
RUTA_COMPLETA = r"C:\Users\Administrador\Documents\Transporte\datos_llamadas_salientes.csv"
```

### Error: "Encoding issue"
```
❌ Solución: Guardar el CSV con encoding UTF-8
# En el código:
pd.read_csv(archivo, encoding='utf-8')
```

### Error: "Permission denied"
```
❌ Solución: Cerrar Excel antes de ejecutar el script
El archivo no puede estar abierto en otro programa
```

### No procesa ningún registro
```
❌ Solución: Verificar que haya registros con estado_confirmacion = "Pendiente"
```

---

## 📞 Soporte

Si necesitas ayuda:
1. Revisa `especificacion_sistema_llamadas.md` (documentación completa)
2. Revisa los ejemplos en el archivo CSV de prueba
3. Verifica los logs en consola

---

## 🎯 Próximos Pasos

1. ✅ Archivo de prueba creado con 10 casos
2. ✅ Script procesador funcionando (simulación)
3. ⏳ Integrar con API de telefonía real (Twilio/Vonage)
4. ⏳ Agregar reconocimiento de voz para respuestas automáticas
5. ⏳ Crear dashboard web para ver estadísticas
6. ⏳ Migrar a base de datos (opcional, si crece el volumen)

---

**Versión:** 1.0
**Última actualización:** 2025-01-06
**Autor:** Sistema Transporte Pacientes
