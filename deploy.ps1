# ==========================================
# Transformas - Production Deployment Script (PowerShell)
# ==========================================

$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting Transformas deployment..." -ForegroundColor Cyan

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "❌ Error: .env file not found" -ForegroundColor Red
    Write-Host "Please copy .env.production.example to .env and configure it" -ForegroundColor Yellow
    exit 1
}

# Check if datos_llamadas_salientes.csv exists
if (-not (Test-Path "datos_llamadas_salientes.csv")) {
    Write-Host "⚠️  Warning: datos_llamadas_salientes.csv not found" -ForegroundColor Yellow
    Write-Host "Creating from example..." -ForegroundColor Yellow
    if (Test-Path "datos_llamadas_salientes_ejemplo.csv") {
        Copy-Item "datos_llamadas_salientes_ejemplo.csv" "datos_llamadas_salientes.csv"
        Write-Host "✓ Created datos_llamadas_salientes.csv" -ForegroundColor Green
    } else {
        Write-Host "❌ Error: No example CSV file found" -ForegroundColor Red
        exit 1
    }
}

# Create necessary directories
Write-Host "📁 Creating directories..." -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path "excel_backups" | Out-Null
New-Item -ItemType Directory -Force -Path "logs" | Out-Null
Write-Host "✓ Directories created" -ForegroundColor Green

# Stop existing containers
Write-Host "🛑 Stopping existing containers..." -ForegroundColor Cyan
docker-compose -f docker-compose.prod.yml down

# Build images
Write-Host "🔨 Building Docker images..." -ForegroundColor Cyan
docker-compose -f docker-compose.prod.yml build --no-cache

# Start services
Write-Host "🚀 Starting services..." -ForegroundColor Cyan
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be healthy
Write-Host "⏳ Waiting for services to be healthy..." -ForegroundColor Cyan
Start-Sleep -Seconds 10

# Check health
Write-Host "🏥 Checking service health..." -ForegroundColor Cyan
$healthCheckSuccess = $false
for ($i = 1; $i -le 30; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8081/api/v1/health" -TimeoutSec 5 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Host "✓ Service is healthy!" -ForegroundColor Green
            $healthCheckSuccess = $true
            break
        }
    } catch {
        Write-Host "Attempt $i/30..." -ForegroundColor Yellow
        Start-Sleep -Seconds 2
    }
}

if (-not $healthCheckSuccess) {
    Write-Host "❌ Service health check failed" -ForegroundColor Red
    docker-compose -f docker-compose.prod.yml logs --tail=50
    exit 1
}

# Show logs
Write-Host ""
Write-Host "📋 Recent logs:" -ForegroundColor Cyan
docker-compose -f docker-compose.prod.yml logs --tail=20

Write-Host ""
Write-Host "✅ Deployment successful!" -ForegroundColor Green
Write-Host ""
Write-Host "Service is running on http://localhost:8081" -ForegroundColor Cyan
Write-Host "API Documentation: http://localhost:8081/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Yellow
Write-Host "  View logs:      docker-compose -f docker-compose.prod.yml logs -f"
Write-Host "  Stop services:  docker-compose -f docker-compose.prod.yml down"
Write-Host "  Restart:        docker-compose -f docker-compose.prod.yml restart"
Write-Host "  Shell access:   docker exec -it transformas_app_prod bash"
Write-Host ""
