# 🚀 Guía de Deployment - Transformas Medical Transport Agent

Esta guía explica cómo desplegar el sistema en un servidor de producción usando Docker.

## 📋 Pre-requisitos

### En el servidor:
- ✅ **Docker** instalado (versión 20.10 o superior)
- ✅ **Docker Compose** instalado (versión 2.0 o superior)
- ✅ **Puerto 8081** disponible
- ✅ Mínimo **2 GB RAM** y **2 CPU cores**
- ✅ Conexión a internet para descargar imágenes

### Archivos necesarios:
- ✅ Archivo Excel con datos de pacientes (`datos_llamadas_salientes.csv`)
- ✅ API Key de OpenAI válida
- ✅ Archivo `.env` configurado

---

## 🔧 Configuración Inicial

### 1. Clonar/Transferir el proyecto al servidor

```bash
# Ejemplo: transferir usando rsync
rsync -avz --exclude='*.pyc' --exclude='__pycache__' \
    /local/path/Transporte/ user@servidor:/opt/transformas/

# O clonar desde Git
cd /opt/transformas
git clone <tu-repositorio>
```

### 2. Configurar variables de entorno

```bash
cd /opt/transformas

# Copiar ejemplo de configuración
cp .env.production.example .env

# Editar con tu editor favorito
nano .env  # o vim .env
```

**Variables CRÍTICAS que DEBES modificar:**

```env
# OpenAI API Key (OBLIGATORIO)
OPENAI_API_KEY=sk-tu-api-key-aqui

# Redis (ya configurado para Docker)
REDIS_HOST=redis
REDIS_PORT=6379

# Paths (ya configurados para Docker)
EXCEL_PATH=/app/data/datos_llamadas_salientes.csv
EXCEL_BACKUP_FOLDER=/app/data/backups

# Configuración de la empresa
AGENT_NAME=María
COMPANY_NAME=Transformas
EPS_NAME=Cosalud
```

### 3. Preparar archivo Excel

```bash
# Asegúrate de que el archivo CSV existe
ls -la datos_llamadas_salientes.csv

# Si no existe, cópialo desde el ejemplo
cp datos_llamadas_salientes_ejemplo.csv datos_llamadas_salientes.csv
```

**Formato del CSV esperado:**
```csv
telefono,nombre_completo,tipo_documento,numero_documento,eps,tipo_servicio,fecha_servicio,hora_servicio,...
3001234567,Juan Pérez,CC,12345678,Cosalud,Diálisis,2024-01-20,08:00,...
```

---

## 🐳 Deployment con Docker

### Opción A: Script Automático (Recomendado)

#### Linux/Mac:
```bash
chmod +x deploy.sh
./deploy.sh
```

#### Windows (PowerShell):
```powershell
.\deploy.ps1
```

### Opción B: Manual

```bash
# 1. Crear directorios necesarios
mkdir -p excel_backups logs

# 2. Detener contenedores existentes (si los hay)
docker-compose -f docker-compose.prod.yml down

# 3. Construir imágenes
docker-compose -f docker-compose.prod.yml build --no-cache

# 4. Iniciar servicios
docker-compose -f docker-compose.prod.yml up -d

# 5. Verificar que estén corriendo
docker-compose -f docker-compose.prod.yml ps

# 6. Ver logs
docker-compose -f docker-compose.prod.yml logs -f
```

---

## ✅ Verificación del Deployment

### 1. Health Check

```bash
# Verificar que el servicio responde
curl http://localhost:8081/api/v1/health

# Respuesta esperada:
# {"status":"healthy","timestamp":"2024-01-15T10:30:00Z"}
```

### 2. Verificar contenedores

```bash
docker ps

# Deberías ver:
# - transformas_app_prod (corriendo)
# - transformas_redis_prod (corriendo)
```

### 3. Probar API Documentation

Abre en tu navegador:
```
http://servidor-ip:8081/docs
```

### 4. Probar endpoint de llamada saliente

```bash
# Usando curl
curl -X POST "http://localhost:8081/api/v1/calls/outbound/initiate" \
     -H "Content-Type: application/json" \
     -d '{"patient_phone":"3001234567","agent_name":"María"}'

# Deberías recibir:
{
  "session_id": "uuid-aqui",
  "agent_initial_message": "Buenos días...",
  "patient_name": "Juan Pérez",
  ...
}
```

---

## 📊 Monitoreo y Logs

### Ver logs en tiempo real

```bash
# Todos los servicios
docker-compose -f docker-compose.prod.yml logs -f

# Solo app
docker-compose -f docker-compose.prod.yml logs -f app

# Solo Redis
docker-compose -f docker-compose.prod.yml logs -f redis

# Últimas 100 líneas
docker-compose -f docker-compose.prod.yml logs --tail=100
```

### Logs en archivo

Los logs también se guardan en:
```
./logs/app.log
```

### Verificar uso de recursos

```bash
# Estadísticas de contenedores
docker stats

# Uso de Redis
docker exec -it transformas_redis_prod redis-cli INFO memory
```

---

## 🔄 Operaciones Comunes

### Reiniciar servicios

```bash
docker-compose -f docker-compose.prod.yml restart
```

### Actualizar código (sin reconstruir)

```bash
# Si solo cambias código Python
docker-compose -f docker-compose.prod.yml restart app
```

### Actualizar con rebuild completo

```bash
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
```

### Backup del archivo Excel

```bash
# Los backups automáticos están en:
ls -la excel_backups/

# Hacer backup manual
cp datos_llamadas_salientes.csv excel_backups/manual_$(date +%Y%m%d_%H%M%S).csv
```

### Acceder al contenedor

```bash
# Shell interactivo
docker exec -it transformas_app_prod bash

# Ver estructura de directorios
docker exec transformas_app_prod ls -la /app/

# Ver archivo Excel montado
docker exec transformas_app_prod cat /app/data/datos_llamadas_salientes.csv | head
```

---

## 🛑 Detener servicios

### Detener sin eliminar

```bash
docker-compose -f docker-compose.prod.yml stop
```

### Detener y eliminar contenedores

```bash
docker-compose -f docker-compose.prod.yml down
```

### Detener y eliminar TODO (incluye volúmenes)

```bash
docker-compose -f docker-compose.prod.yml down -v
```

---

## 🔒 Seguridad

### Recomendaciones de producción:

1. **Firewall**: Restringir acceso al puerto 8081
   ```bash
   # Ejemplo con ufw (Ubuntu)
   sudo ufw allow from IP_PERMITIDA to any port 8081
   ```

2. **HTTPS**: Usar un reverse proxy (Nginx/Caddy)
   ```nginx
   server {
       listen 443 ssl;
       server_name api.transformas.com;

       location / {
           proxy_pass http://localhost:8081;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

3. **API Key**: Configurar en `.env`
   ```env
   API_KEY=tu-api-key-super-segura
   ```

4. **Límites de Redis**:
   - Ya configurado en `docker-compose.prod.yml`
   - Máximo 256MB de memoria
   - Política LRU para liberar memoria

---

## 🐛 Troubleshooting

### Problema: Contenedor no inicia

```bash
# Ver logs de error
docker-compose -f docker-compose.prod.yml logs app

# Verificar configuración
docker-compose -f docker-compose.prod.yml config
```

### Problema: No encuentra archivo Excel

```bash
# Verificar que el archivo existe
ls -la datos_llamadas_salientes.csv

# Verificar que está montado en el contenedor
docker exec transformas_app_prod ls -la /app/data/
```

### Problema: Error de OpenAI API Key

```bash
# Verificar que la variable está configurada
docker exec transformas_app_prod env | grep OPENAI_API_KEY

# Si no aparece, revisar .env y reiniciar
docker-compose -f docker-compose.prod.yml restart
```

### Problema: Puerto 8081 ya en uso

```bash
# Verificar qué está usando el puerto
sudo lsof -i :8081
# o
sudo netstat -tulpn | grep 8081

# Cambiar puerto en docker-compose.prod.yml
# Editar línea: "8081:8000" -> "OTRO_PUERTO:8000"
```

### Problema: Redis sin conexión

```bash
# Verificar que Redis está corriendo
docker exec transformas_redis_prod redis-cli ping
# Debe responder: PONG

# Verificar logs de Redis
docker-compose -f docker-compose.prod.yml logs redis
```

---

## 📈 Escalabilidad

### Aumentar workers de la aplicación

Editar `docker-compose.prod.yml`:
```yaml
command: uvicorn src.presentation.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Fórmula recomendada: `workers = (2 x CPU cores) + 1`

### Límites de recursos

Ya configurado en `docker-compose.prod.yml`:
```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 1G
    reservations:
      cpus: '0.5'
      memory: 512M
```

Ajustar según capacidad del servidor.

---

## 📞 Endpoints Principales

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/v1/health` | GET | Health check |
| `/api/v1/calls/outbound/initiate` | POST | Iniciar llamada saliente (UNIFICADO) |
| `/api/v1/conversation/message/v2` | POST | Enviar mensaje en conversación |
| `/api/v1/calls/{session_id}` | GET | Obtener detalles de sesión |
| `/api/v1/calls/outbound/pending` | GET | Lista de llamadas pendientes |
| `/docs` | GET | Documentación Swagger |

---

## 🎯 Puerto Configurado

El sistema está configurado para usar el **puerto 8081** en el servidor:

```yaml
# En docker-compose.prod.yml
ports:
  - "8081:8000"  # Externo:Interno
```

- **Puerto externo (servidor)**: 8081
- **Puerto interno (contenedor)**: 8000

Para cambiar el puerto externo, edita solo la primera parte: `"NUEVO_PUERTO:8000"`

---

## 📝 Notas Finales

- ✅ Sistema configurado para **alta disponibilidad**
- ✅ Logs rotativos configurados (max 50MB x 5 archivos)
- ✅ Healthchecks automáticos cada 30 segundos
- ✅ Restart policy: `unless-stopped`
- ✅ Backups automáticos del Excel
- ✅ Usuario no-root para seguridad

**¿Problemas?** Revisa los logs primero:
```bash
docker-compose -f docker-compose.prod.yml logs --tail=100
```
