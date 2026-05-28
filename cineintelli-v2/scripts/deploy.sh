#!/bin/bash
# =============================================================================
# CINEINTELLI - Deployment Script
# =============================================================================
# Script de despliegue completo para producción
# Autor: Arquitectura SaaS
# =============================================================================

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

ENVIRONMENT=${1:-production}

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              CINEINTELLI - Deployment Script                  ║"
echo "║                   Environment: $ENVIRONMENT                   ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Verificar archivos necesarios
echo -e "${YELLOW}Verificando configuración...${NC}"

if [ ! -f .env ]; then
    echo -e "${RED}Error: Archivo .env no encontrado${NC}"
    echo "Copia .env.example a .env y configura las variables"
    exit 1
fi

if [ ! -f docker-compose.yml ]; then
    echo -e "${RED}Error: docker-compose.yml no encontrado${NC}"
    exit 1
fi

# Verificar variables críticas
echo -e "${YELLOW}Verificando variables de entorno...${NC}"

if ! grep -q "SECRET_KEY=" .env || grep -q "SECRET_KEY=cambia_esto" .env; then
    echo -e "${RED}Error: SECRET_KEY no configurado correctamente${NC}"
    exit 1
fi

if ! grep -q "DB_PASSWORD=" .env || grep -q "DB_PASSWORD=tu_password" .env; then
    echo -e "${RED}Error: DB_PASSWORD no configurado correctamente${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Configuración válida${NC}"

# Pull de imágenes más recientes
echo -e "${YELLOW}Actualizando imágenes Docker...${NC}"
docker-compose pull

# Construir imágenes locales
echo -e "${YELLOW}Construyendo imágenes...${NC}"
docker-compose build --no-cache

# Iniciar servicios base primero
echo -e "${YELLOW}Iniciando servicios de infraestructura...${NC}"
docker-compose up -d postgres redis chromadb

echo -e "${YELLOW}Esperando a que PostgreSQL esté listo...${NC}"
sleep 10

# Verificar salud de PostgreSQL
until docker-compose exec -T postgres pg_isready -U cineintelli; do
    echo "Esperando PostgreSQL..."
    sleep 2
done
echo -e "${GREEN}✓ PostgreSQL listo${NC}"

# Iniciar backend y workers
echo -e "${YELLOW}Iniciando backend...${NC}"
docker-compose up -d backend

echo -e "${YELLOW}Esperando a que el backend esté listo...${NC}"
sleep 5

# Iniciar workers
echo -e "${YELLOW}Iniciando workers...${NC}"
docker-compose up -d worker scheduler

# Iniciar frontend
echo -e "${YELLOW}Iniciando frontend...${NC}"
docker-compose up -d frontend

# Iniciar nginx
echo -e "${YELLOW}Iniciando nginx...${NC}"
docker-compose up -d nginx

# Iniciar tunnel (opcional)
if grep -q "CLOUDFLARE_TUNNEL_TOKEN=" .env && ! grep -q "CLOUDFLARE_TUNNEL_TOKEN=tu_token" .env; then
    echo -e "${YELLOW}Iniciando Cloudflare Tunnel...${NC}"
    docker-compose up -d cloudflare-tunnel
    echo -e "${GREEN}✓ Cloudflare Tunnel iniciado${NC}"
fi

# Verificar estado
echo ""
echo -e "${BLUE}Verificando estado de servicios...${NC}"
docker-compose ps

echo ""
echo -e "${GREEN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              ✅ DESPLIEGUE COMPLETADO                        ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo "Servicios disponibles:"
echo "  • API: http://localhost/api"
echo "  • Health: http://localhost/health"
echo ""

# Mostrar URL del tunnel si existe
if docker-compose ps | grep -q "cloudflare-tunnel"; then
    echo -e "${YELLOW}Obteniendo URL del túnel...${NC}"
    sleep 5
    docker-compose logs --tail=20 cloudflare-tunnel | grep -E "(https://|your-url-is)" || true
fi

echo ""
echo "Comandos útiles:"
echo -e "  ${BLUE}Ver logs:${NC}           docker-compose logs -f"
echo -e "  ${BLUE}Ver logs API:${NC}       docker-compose logs -f backend"
echo -e "  ${BLUE}Escalar workers:${NC}    docker-compose up -d --scale worker=4"
echo -e "  ${BLUE}Detener:${NC}            docker-compose down"
echo -e "  ${BLUE}Detener todo:${NC}       docker-compose down -v"
echo ""
