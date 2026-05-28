# 🎬 CineIntelli 2.0 - SaaS Edition

> **Sistema inteligente de recomendación de películas**
> 
> Acceso público • IA Avanzada • Auto-enriquecimiento de datos

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![Docker](https://img.shields.io/badge/docker-ready-green)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688)
![React](https://img.shields.io/badge/React-18+-61DAFB)

---

## 🚀 Acceso Rápido

| Servicio | URL |
|----------|-----|
| **Aplicación Web** | `https://tu-tunel.trycloudflare.com` |
| **API Documentation** | `/api/docs` |
| **Health Check** | `/health` |

---

## 📋 Índice

1. [Arquitectura](#-arquitectura)
2. [Stack Tecnológico](#-stack-tecnológico)
3. [Instalación Rápida](#-instalación-rápida)
4. [Configuración Cloudflare Tunnel](#-configuración-cloudflare-tunnel)
5. [Despliegue](#-despliegue)
6. [Uso](#-uso)
7. [API Reference](#-api-reference)
8. [Monitoreo](#-monitoreo)
9. [Escalabilidad](#-escalabilidad)
10. [Roadmap](#-roadmap)

---

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                        USUARIO FINAL                            │
│                    (Navegador/Móvil)                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CLOUDFLARE EDGE                              │
│              (SSL + WAF + CDN + DDoS Protection)               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   CLOUDFLARE TUNNEL                             │
│              (cloudflared - Túnel seguro)                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DOCKER COMPOSE STACK                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   NGINX     │  │  FastAPI    │  │   React     │             │
│  │  (Proxy)    │──│  (Backend)  │  │  (Frontend) │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│         │                │                                       │
│  ┌──────┴────────────────┴──────┐  ┌─────────────┐             │
│  │     PostgreSQL 15            │  │   Redis 7   │             │
│  │  (Usuarios, Películas)       │  │  (Cache)    │             │
│  └──────────────────────────────┘  └─────────────┘             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  ChromaDB   │  │   Celery    │  │  Celery     │             │
│  │ (Vector DB) │  │  (Workers)  │  │  (Beat)     │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Stack Tecnológico

| Capa | Tecnología | Propósito |
|------|------------|-----------|
| **Frontend** | React 18 + Vite + TailwindCSS | SPA moderna y rápida |
| **Backend** | FastAPI + Python 3.11 | API REST async de alto rendimiento |
| **ML/AI** | TensorFlow + ChromaDB | Embeddings y búsqueda semántica |
| **Database** | PostgreSQL 15 | Datos persistentes ACID |
| **Cache** | Redis 7 | Sessions, rate limiting, cache |
| **Queue** | Celery + Redis | Tareas en background |
| **Vector DB** | ChromaDB | RAG y búsqueda por similitud |
| **Proxy** | Nginx | Load balancing, static files |
| **Tunnel** | Cloudflare Tunnel | HTTPS gratis, sin abrir puertos |
| **Container** | Docker + Compose | Portabilidad y escalabilidad |

---

## ⚡ Instalación Rápida

### Requisitos

- Docker 24.0+
- Docker Compose 2.20+
- Cuenta Cloudflare (gratuita)
- 4GB RAM mínimo
- 20GB espacio en disco

### Paso 1: Clonar y Configurar

```bash
# Clonar repositorio
git clone https://github.com/erikonta77/peliculas.git
cd peliculas/cineintelli-v2

# Copiar configuración
cp .env.example .env

# Editar variables de entorno
nano .env
```

### Variables Obligatorias (.env)

```bash
# Seguridad (generar con: openssl rand -hex 32)
SECRET_KEY=tu_clave_secreta_aqui_64_caracteres

# Base de datos
DB_PASSWORD=password_seguro_complejo_123!

# API TMDB (obtener en https://www.themoviedb.org/settings/api)
TMDB_API_KEY=tu_api_key_de_tmdb
```

---

## 🔒 Configuración Cloudflare Tunnel

### Opción A: Script Automático (Recomendado)

```bash
./scripts/setup-cloudflare-tunnel.sh
```

Este script:
1. Instala `cloudflared` si no está presente
2. Autentica con tu cuenta Cloudflare
3. Crea un túnel persistente
4. Configura DNS automáticamente
5. Guarda el token en `.env`

### Opción B: Manual

```bash
# 1. Login
cloudflared tunnel login

# 2. Crear túnel
cloudflared tunnel create cineintelli

# 3. Obtener token
cloudflared tunnel token <UUID>

# 4. Guardar token en .env
# CLOUDFLARE_TUNNEL_TOKEN=tu_token_aqui
```

### Dominio Personalizado (Opcional)

```bash
# Si tienes un dominio en Cloudflare
cloudflared tunnel route dns <UUID> cineintelli.tudominio.com
```

---

## 🚀 Despliegue

### Despliegue Completo

```bash
./scripts/deploy.sh production
```

### Comandos Manuales

```bash
# Construir e iniciar
docker-compose up -d --build

# Ver estado
docker-compose ps

# Ver logs
docker-compose logs -f

# Ver logs específicos
docker-compose logs -f backend
docker-compose logs -f cloudflare-tunnel

# Escalar workers
docker-compose up -d --scale worker=4

# Detener
docker-compose down

# Detener y eliminar datos
docker-compose down -v
```

---

## 📖 Uso

### Acceder a la Aplicación

Una vez desplegado:

1. **Web**: Abre el URL proporcionado por Cloudflare
2. **API Docs**: `https://tu-url.com/api/docs`
3. **Health**: `https://tu-url.com/health`

### Crear Usuario

```bash
# Registrar usuario
curl -X POST "https://tu-url.com/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "usuario@ejemplo.com",
    "password": "password123",
    "full_name": "Usuario Ejemplo"
  }'
```

### Configurar Perfil

```bash
# Actualizar preferencias
curl -X PUT "https://tu-url.com/api/v1/users/me/profile" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "favorite_genres": ["Ciencia Ficción", "Acción"],
    "year_min": 2010,
    "year_max": 2024,
    "min_rating": 7.0
  }'
```

### Obtener Recomendaciones

```bash
# Recomendaciones personalizadas
curl "https://tu-url.com/api/v1/recommendations/personalized?count=10" \
  -H "Authorization: Bearer <token>"
```

### Sincronizar Películas (TMDB)

```bash
# Sincronizar catálogo desde TMDB
curl -X POST "https://tu-url.com/api/v1/movies/sync-tmdb?pages=5" \
  -H "Authorization: Bearer <token>"
```

---

## 📚 API Reference

### Endpoints Principales

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/auth/login` | Login con JWT |
| POST | `/api/v1/auth/register` | Registro de usuario |
| GET | `/api/v1/auth/me` | Usuario actual |
| GET | `/api/v1/movies` | Listar películas |
| GET | `/api/v1/movies/{id}` | Detalle de película |
| GET | `/api/v1/movies/popular` | Populares |
| GET | `/api/v1/movies/top-rated` | Mejor calificadas |
| GET | `/api/v1/recommendations/personalized` | Recomendaciones IA |
| GET | `/api/v1/recommendations/similar/{id}` | Similares |
| POST | `/api/v1/recommendations/roulette` | CineRoulette |
| GET | `/api/v1/users/me/profile` | Obtener perfil |
| PUT | `/api/v1/users/me/profile` | Actualizar perfil |

### Ejemplo de Respuesta

```json
{
  "recommendations": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Inception",
      "year": 2010,
      "rating": 8.8,
      "genres": ["Ciencia Ficción", "Acción", "Thriller"],
      "poster_url": "https://image.tmdb.org/t/p/w500/..."
    }
  ],
  "count": 10
}
```

---

## 📊 Monitoreo

### Health Checks

```bash
# Health general
curl http://localhost/health

# Readiness (incluye BD)
curl http://localhost/health/ready

# Liveness
curl http://localhost/health/live
```

### Logs

```bash
# Logs en tiempo real
docker-compose logs -f --tail=100

# Logs de errores
docker-compose logs -f backend 2>&1 | grep ERROR

# Métricas de Celery
docker-compose exec worker celery -A app.core.celery inspect stats
```

### Comandos Útiles

```bash
# Backup de base de datos
docker-compose exec postgres pg_dump -U cineintelli cineintelli > backup.sql

# Restore
cat backup.sql | docker-compose exec -T postgres psql -U cineintelli

# Shell de PostgreSQL
docker-compose exec postgres psql -U cineintelli

# Shell de Redis
docker-compose exec redis redis-cli
```

---

## 📈 Escalabilidad

### Vertical (Más Recursos)

```yaml
# docker-compose.override.yml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 4G
  
  postgres:
    command:
      - "postgres"
      - "-c"
      - "shared_buffers=1GB"
      - "-c"
      - "effective_cache_size=3GB"
```

### Horizontal (Más Instancias)

```bash
# Escalar workers
docker-compose up -d --scale worker=8

# Con Docker Swarm
docker stack deploy -c docker-compose.yml cineintelli
```

### Optimizaciones

```bash
# Habilitar compresión Nginx
# (ya configurado en nginx.conf)

# Cache de Redis para recomendaciones
# (implementado automáticamente)

# Connection pooling de PostgreSQL
# (ya configurado en database.py)
```

---

## 🗺️ Roadmap

### Fase 1: MVP ✅
- [x] Dockerización completa
- [x] FastAPI backend
- [x] React frontend
- [x] Cloudflare Tunnel
- [x] PostgreSQL + Redis
- [x] Autenticación JWT

### Fase 2: Inteligencia 🔄
- [ ] Integración TMDB API completa
- [ ] ChromaDB para RAG
- [ ] Celery workers para scraping
- [ ] Auto-actualización de películas
- [ ] Embeddings mejorados

### Fase 3: Escalabilidad 📊
- [ ] Kubernetes manifests
- [ ] Prometheus + Grafana
- [ ] CI/CD con GitHub Actions
- [ ] Tests E2E
- [ ] Rate limiting avanzado

### Fase 4: Producto 🚀
- [ ] OAuth (Google/GitHub)
- [ ] Panel de administración
- [ ] Analytics de usuarios
- [ ] Notificaciones push
- [ ] Mobile app (PWA)

---

## 🔐 Seguridad

### Implementado

- ✅ HTTPS automático (Cloudflare)
- ✅ Autenticación JWT
- ✅ Rate limiting
- ✅ WAF (Cloudflare)
- ✅ Headers de seguridad
- ✅ SQL Injection protection (SQLAlchemy)
- ✅ XSS protection

### Recomendaciones

```bash
# Actualizar imágenes regularmente
docker-compose pull
docker-compose up -d

# Rotar SECRET_KEY periódicamente
# Monitorear logs con fail2ban
```

---

## 🆘 Troubleshooting

### Problema: No se puede conectar a PostgreSQL

```bash
# Verificar estado
docker-compose logs postgres

# Resetear volumen (⚠️ PIERDE DATOS)
docker-compose down -v
docker-compose up -d postgres
```

### Problema: Token de Cloudflare inválido

```bash
# Regenerar token
cloudflared tunnel token <UUID>
# Actualizar en .env y reiniciar
docker-compose up -d cloudflare-tunnel
```

### Problema: Error 502 Bad Gateway

```bash
# Verificar backend
docker-compose logs backend

# Reiniciar nginx
docker-compose restart nginx
```

---

## 🤝 Contribuir

```bash
# Fork y clone
git clone https://github.com/tu-usuario/cineintelli.git

# Crear branch
git checkout -b feature/nueva-funcionalidad

# Commit
git commit -m "feat: nueva funcionalidad"

# Push
git push origin feature/nueva-funcionalidad
```

---

## 📄 Licencia

MIT License - Ver [LICENSE](LICENSE)

---

## 🙏 Créditos

- **Autor Original**: Claude Opus 4.7
- **Arquitectura SaaS**: Claude Opus 4.7
- **Dataset**: TMDB API
- **Hosting**: Cloudflare

---

## 📞 Soporte

- Issues: [GitHub Issues](https://github.com/erikonta77/peliculas/issues)
- Documentación: `/api/docs` (desplegado)
- Health: `/health`

---

<p align="center">
  <strong>🎬 CineIntelli 2.0 - Descubre tu próxima película favorita</strong>
</p>
