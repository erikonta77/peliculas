# =============================================================================
# CINEINTELLI FRONTEND - React + Vite
# =============================================================================
FROM node:20-alpine AS builder

WORKDIR /app

# Copiar package.json e instalar dependencias
COPY package*.json ./
RUN npm ci

# Copiar código fuente
COPY . .

# Build de producción
ARG VITE_API_URL=/api
ENV VITE_API_URL=${VITE_API_URL}
RUN npm run build

# =============================================================================
# Production Stage - Solo archivos estáticos
# =============================================================================
FROM alpine:latest

WORKDIR /app

# Copiar build
COPY --from=builder /app/dist ./dist

# Volume para compartir con Nginx
VOLUME /app/dist

CMD ["sh", "-c", "cp -r /app/dist/* /dist/ 2>/dev/null || true; echo 'Build copied'"]
