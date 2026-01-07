#!/bin/bash

# ==========================================
# Pre-deployment Check Script
# ==========================================

echo "🔍 Checking deployment readiness..."
echo ""

ERRORS=0
WARNINGS=0

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check Docker
echo "1. Checking Docker..."
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    echo -e "${GREEN}✓ Docker installed: $DOCKER_VERSION${NC}"
else
    echo -e "${RED}✗ Docker not found. Please install Docker.${NC}"
    ((ERRORS++))
fi

# Check Docker Compose
echo "2. Checking Docker Compose..."
if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version)
    echo -e "${GREEN}✓ Docker Compose installed: $COMPOSE_VERSION${NC}"
else
    echo -e "${RED}✗ Docker Compose not found. Please install Docker Compose.${NC}"
    ((ERRORS++))
fi

# Check .env file
echo "3. Checking .env file..."
if [ -f .env ]; then
    echo -e "${GREEN}✓ .env file exists${NC}"

    # Check critical variables
    if grep -q "OPENAI_API_KEY=sk-" .env; then
        echo -e "${GREEN}  ✓ OPENAI_API_KEY configured${NC}"
    else
        echo -e "${RED}  ✗ OPENAI_API_KEY not configured or invalid${NC}"
        ((ERRORS++))
    fi

    if grep -q "REDIS_HOST=redis" .env; then
        echo -e "${GREEN}  ✓ REDIS_HOST set to 'redis'${NC}"
    else
        echo -e "${YELLOW}  ⚠ REDIS_HOST should be 'redis' for Docker deployment${NC}"
        ((WARNINGS++))
    fi
else
    echo -e "${RED}✗ .env file not found${NC}"
    echo -e "${YELLOW}  Run: cp .env.production.example .env${NC}"
    ((ERRORS++))
fi

# Check Excel file
echo "4. Checking Excel/CSV file..."
if [ -f datos_llamadas_salientes.csv ]; then
    LINES=$(wc -l < datos_llamadas_salientes.csv)
    echo -e "${GREEN}✓ datos_llamadas_salientes.csv exists ($LINES lines)${NC}"
else
    echo -e "${YELLOW}⚠ datos_llamadas_salientes.csv not found${NC}"
    if [ -f datos_llamadas_salientes_ejemplo.csv ]; then
        echo -e "${YELLOW}  You can copy from: datos_llamadas_salientes_ejemplo.csv${NC}"
    fi
    ((WARNINGS++))
fi

# Check port availability
echo "5. Checking port 8081..."
if command -v lsof &> /dev/null; then
    if lsof -Pi :8081 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo -e "${YELLOW}⚠ Port 8081 is already in use${NC}"
        lsof -i :8081
        ((WARNINGS++))
    else
        echo -e "${GREEN}✓ Port 8081 is available${NC}"
    fi
else
    echo -e "${YELLOW}⚠ lsof not available, cannot check port${NC}"
fi

# Check required files
echo "6. Checking required files..."
REQUIRED_FILES=(
    "docker-compose.prod.yml"
    "Dockerfile"
    "requirements.txt"
    "src/presentation/api/main.py"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}  ✓ $file${NC}"
    else
        echo -e "${RED}  ✗ $file not found${NC}"
        ((ERRORS++))
    fi
done

# Check directories
echo "7. Checking/Creating directories..."
DIRS=("excel_backups" "logs")
for dir in "${DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo -e "${GREEN}  ✓ $dir exists${NC}"
    else
        mkdir -p "$dir"
        echo -e "${YELLOW}  ⚠ Created $dir${NC}"
    fi
done

# Summary
echo ""
echo "================================"
echo "📊 Summary:"
echo "================================"
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed! Ready to deploy.${NC}"
    echo ""
    echo "Run deployment with:"
    echo "  ./deploy.sh"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  $WARNINGS warning(s) found${NC}"
    echo -e "${YELLOW}You can proceed but review warnings above.${NC}"
    exit 0
else
    echo -e "${RED}❌ $ERRORS error(s) found${NC}"
    echo -e "${RED}Please fix errors before deploying.${NC}"
    exit 1
fi
