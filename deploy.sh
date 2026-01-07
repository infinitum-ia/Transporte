#!/bin/bash

# ==========================================
# Transformas - Production Deployment Script
# ==========================================

set -e  # Exit on error

echo "🚀 Starting Transformas deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ Error: .env file not found${NC}"
    echo "Please copy .env.production.example to .env and configure it"
    exit 1
fi

# Check if datos_llamadas_salientes.csv exists
if [ ! -f datos_llamadas_salientes.csv ]; then
    echo -e "${YELLOW}⚠️  Warning: datos_llamadas_salientes.csv not found${NC}"
    echo "Creating from example..."
    if [ -f datos_llamadas_salientes_ejemplo.csv ]; then
        cp datos_llamadas_salientes_ejemplo.csv datos_llamadas_salientes.csv
        echo -e "${GREEN}✓ Created datos_llamadas_salientes.csv${NC}"
    else
        echo -e "${RED}❌ Error: No example CSV file found${NC}"
        exit 1
    fi
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p excel_backups
mkdir -p logs
echo -e "${GREEN}✓ Directories created${NC}"

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f docker-compose.prod.yml down

# Build images
echo "🔨 Building Docker images..."
docker-compose -f docker-compose.prod.yml build --no-cache

# Start services
echo "🚀 Starting services..."
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check health
echo "🏥 Checking service health..."
for i in {1..30}; do
    if curl -f http://localhost:8081/api/v1/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Service is healthy!${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}❌ Service health check failed${NC}"
        docker-compose -f docker-compose.prod.yml logs --tail=50
        exit 1
    fi
    echo "Attempt $i/30..."
    sleep 2
done

# Show logs
echo ""
echo "📋 Recent logs:"
docker-compose -f docker-compose.prod.yml logs --tail=20

echo ""
echo -e "${GREEN}✅ Deployment successful!${NC}"
echo ""
echo "Service is running on http://localhost:8081"
echo "API Documentation: http://localhost:8081/docs"
echo ""
echo "Useful commands:"
echo "  View logs:      docker-compose -f docker-compose.prod.yml logs -f"
echo "  Stop services:  docker-compose -f docker-compose.prod.yml down"
echo "  Restart:        docker-compose -f docker-compose.prod.yml restart"
echo "  Shell access:   docker exec -it transformas_app_prod bash"
echo ""
