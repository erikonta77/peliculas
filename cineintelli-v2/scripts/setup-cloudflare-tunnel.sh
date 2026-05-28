#!/bin/bash
# =============================================================================
# CINEINTELLI - Cloudflare Tunnel Setup Script
# =============================================================================
# Este script configura automáticamente un túnel de Cloudflare para CineIntelli
# Autor: Arquitectura SaaS
# =============================================================================

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║         CINEINTELLI - Cloudflare Tunnel Setup               ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Verificar dependencias
command -v docker >/dev/null 2>&1 || { echo -e "${RED}Error: Docker no está instalado${NC}"; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo -e "${RED}Error: Docker Compose no está instalado${NC}"; exit 1; }

# Verificar si cloudflared está instalado
if ! command -v cloudflared &> /dev/null; then
    echo -e "${YELLOW}cloudflared no está instalado. Instalando...${NC}"

    # Detectar arquitectura
    ARCH=$(uname -m)
    if [ "$ARCH" = "x86_64" ]; then
        CF_ARCH="amd64"
    elif [ "$ARCH" = "aarch64" ]; then
        CF_ARCH="arm64"
    else
        echo -e "${RED}Arquitectura no soportada: $ARCH${NC}"
        exit 1
    fi

    # Descargar e instalar
    curl -L --output cloudflared.deb "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-${CF_ARCH}.deb"
    sudo dpkg -i cloudflared.deb || sudo apt-get install -f -y
    rm cloudflared.deb

    echo -e "${GREEN}cloudflared instalado correctamente${NC}"
fi

# Login en Cloudflare
echo -e "${YELLOW}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Paso 1: Autenticación en Cloudflare"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${NC}"
echo "Se abrirá un navegador para autenticarte con tu cuenta de Cloudflare."
echo ""
read -p "Presiona ENTER para continuar..."
cloudflared tunnel login

# Crear tunnel
echo -e "${YELLOW}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Paso 2: Crear Túnel"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${NC}"
read -p "Nombre para el túnel [cineintelli]: " TUNNEL_NAME
TUNNEL_NAME=${TUNNEL_NAME:-cineintelli}

echo -e "${BLUE}Creando túnel '$TUNNEL_NAME'...${NC}"
TUNNEL_OUTPUT=$(cloudflared tunnel create "$TUNNEL_NAME" 2>&1)
echo "$TUNNEL_OUTPUT"

# Extraer UUID del tunnel
TUNNEL_ID=$(echo "$TUNNEL_OUTPUT" | grep -oP 'id [\w-]+' | head -1 | awk '{print $2}')
if [ -z "$TUNNEL_ID" ]; then
    # Intentar extraer de otra forma
    TUNNEL_ID=$(cloudflared tunnel list | grep "$TUNNEL_NAME" | awk '{print $1}' | head -1)
fi

echo -e "${GREEN}Túnel creado con ID: $TUNNEL_ID${NC}"

# Configurar DNS
echo -e "${YELLOW}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Paso 3: Configurar DNS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${NC}"
echo "Opciones de subdominio:"
echo "1. Usar subdominio gratuito de Cloudflare (*.trycloudflare.com)"
echo "2. Usar mi propio dominio en Cloudflare"
echo ""
read -p "Selecciona una opción [1-2]: " DNS_OPTION

if [ "$DNS_OPTION" = "2" ]; then
    read -p "Introduce tu dominio (ej: cineintelli.tudominio.com): " CUSTOM_DOMAIN
    echo -e "${BLUE}Configurando DNS para $CUSTOM_DOMAIN...${NC}"
    cloudflared tunnel route dns "$TUNNEL_ID" "$CUSTOM_DOMAIN"
    echo -e "${GREEN}DNS configurado: https://$CUSTOM_DOMAIN${NC}"
    echo "$CUSTOM_DOMAIN" > .tunnel_domain
else
    echo -e "${YELLOW}Se usará un subdominio temporal de trycloudflare.com${NC}"
    echo "trycloudflare" > .tunnel_domain
fi

# Obtener token
echo -e "${YELLOW}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Paso 4: Obtener Token de Autenticación"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${NC}"

TUNNEL_TOKEN=$(cloudflared tunnel token "$TUNNEL_ID" | tr -d '\n')
if [ -z "$TUNNEL_TOKEN" ]; then
    echo -e "${RED}Error: No se pudo obtener el token del túnel${NC}"
    exit 1
fi

# Guardar en archivo .env
echo -e "${BLUE}Guardando configuración...${NC}"
if [ -f .env ]; then
    # Actualizar token existente
    if grep -q "^CLOUDFLARE_TUNNEL_TOKEN=" .env; then
        sed -i "s|^CLOUDFLARE_TUNNEL_TOKEN=.*|CLOUDFLARE_TUNNEL_TOKEN=$TUNNEL_TOKEN|" .env
    else
        echo "" >> .env
        echo "# Cloudflare Tunnel" >> .env
        echo "CLOUDFLARE_TUNNEL_TOKEN=$TUNNEL_TOKEN" >> .env
    fi
else
    cp .env.example .env
    sed -i "s|^CLOUDFLARE_TUNNEL_TOKEN=.*|CLOUDFLARE_TUNNEL_TOKEN=$TUNNEL_TOKEN|" .env
fi

echo -e "${GREEN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              ✅ CONFIGURACIÓN COMPLETADA                      ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo -e "${GREEN}El token ha sido guardado en el archivo .env${NC}"
echo ""
echo "Para iniciar el túnel, ejecuta:"
echo -e "${BLUE}  docker-compose up -d cloudflare-tunnel${NC}"
echo ""
echo "O manualmente con:"
echo -e "${BLUE}  cloudflared tunnel run $TUNNEL_ID${NC}"
echo ""

if [ "$DNS_OPTION" = "2" ]; then
    echo -e "🌐 Tu aplicación estará disponible en: ${GREEN}https://$CUSTOM_DOMAIN${NC}"
else
    echo "🌐 Para obtener la URL temporal, ejecuta:"
    echo -e "${BLUE}  docker-compose logs -f cloudflare-tunnel${NC}"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
