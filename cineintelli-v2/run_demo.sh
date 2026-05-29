#!/bin/bash
# =============================================================================
# CineIntelli V2 - Demo Execution Script
# =============================================================================

# Exit immediately if a command exits with a non-zero status
set -e

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🎬 Preparando demo de CineIntelli V2..."

# Paths to Python and Node/NPM
PYTHON_PATH="/c/Users/Estudiante/AppData/Local/Programs/Python/Python314/python.exe"
NODE_DIR="/c/Users/Estudiante/AppData/Local/Microsoft/WinGet/Packages/OpenJS.NodeJS.LTS_Microsoft.Winget.Source_8wekyb3d8bbwe/node-v24.16.0-win-x64"
NPM_PATH="$NODE_DIR/npm.cmd"

# Fallback to system path if not found
if [ ! -f "$PYTHON_PATH" ]; then
    PYTHON_PATH="python"
fi
if [ ! -d "$NODE_DIR" ]; then
    NPM_PATH="npm"
else
    # Add Node to PATH temporarily for the build process
    export PATH="$NODE_DIR:$PATH"
fi

# 1. Configurar Backend
echo "🐍 Configurando Backend (SQLite)..."
cd "$SCRIPT_DIR/backend"

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    "$PYTHON_PATH" -m venv .venv
fi

echo "Installing/Updating backend dependencies..."
./.venv/Scripts/pip install --upgrade pip
./.venv/Scripts/pip install fastapi uvicorn[standard] python-multipart "python-jose[cryptography]" "passlib[bcrypt]" sqlalchemy pydantic pydantic-settings email-validator httpx numpy pandas scikit-learn asyncpg structlog celery redis prometheus-client tenacity "bcrypt<4.0.0"

# 2. Configurar Frontend
echo "⚛️ Configurando Frontend (React)..."
cd "$SCRIPT_DIR/frontend"

echo "Installing frontend dependencies..."
"$NPM_PATH" install

echo "Building frontend..."
"$NPM_PATH" run build

# 3. Ejecutar Backend
echo "🚀 Iniciando servidor backend demo..."
cd "$SCRIPT_DIR/backend"
./.venv/Scripts/python -m app.main_sqlite
