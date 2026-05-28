"""
CineIntelli v2.0 - FastAPI Application
API principal del sistema de recomendación de películas

Autor: Arquitectura SaaS
Versión: 2.0.0
"""

import asyncio
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from app.api import auth, health, movies, recommendations, users
from app.core.config import settings
from app.core.database import init_db
from app.core.logging import logger
from app.services.cache import CacheService
from app.services.model_loader import ModelLoader


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Contexto de vida de la aplicación.
    Inicializa recursos al iniciar y limpia al cerrar.
    """
    logger.info("🎬 Iniciando CineIntelli v2.0...")

    # Inicializar base de datos
    await init_db()
    logger.info("✅ Base de datos inicializada")

    # Cargar modelo de ML
    model_loader = ModelLoader()
    await model_loader.load_model()
    app.state.model_loader = model_loader
    logger.info("✅ Modelo de ML cargado")

    # Inicializar cache
    cache_service = CacheService()
    await cache_service.connect()
    app.state.cache = cache_service
    logger.info("✅ Servicio de cache conectado")

    logger.info("🚀 CineIntelli v2.0 listo!")

    yield

    # Cleanup
    logger.info("🛑 Cerrando CineIntelli...")
    await cache_service.disconnect()


# Crear aplicación FastAPI
app = FastAPI(
    title="CineIntelli API",
    description="Sistema inteligente de recomendación de películas",
    version="2.0.0",
    docs_url="/api/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/api/redoc" if settings.ENVIRONMENT != "production" else None,
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# =============================================================================
# MIDDLEWARES
# =============================================================================

# CORS - Permitir acceso desde cualquier origen en desarrollo
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Compresión GZip
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Middleware de logging y timing
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    start_time = time.time()

    # Log de la petición
    logger.info(
        f"📥 {request.method} {request.url.path}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "client": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        }
    )

    response = await call_next(request)

    # Log de la respuesta
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)

    logger.info(
        f"📤 {request.method} {request.url.path} - {response.status_code} ({process_time:.3f}s)",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration": process_time,
        }
    )

    return response


# Middleware de rate limiting simple (mejorar con Redis en producción)
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # En producción, implementar rate limiting con Redis
    # Por ahora, solo pasar la petición
    return await call_next(request)


# =============================================================================
# MANEJO DE EXCEPCIONES GLOBALES
# =============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        f"❌ Error no manejado: {str(exc)}",
        extra={"path": request.url.path, "exception": str(exc)},
        exc_info=True
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Error interno del servidor",
            "detail": str(exc) if settings.ENVIRONMENT != "production" else "Contacte al administrador"
        }
    )


# =============================================================================
# ROUTERS
# =============================================================================

# Health check (sin auth)
app.include_router(health.router, prefix="/health", tags=["Health"])

# API v1
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Autenticación"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Usuarios"])
app.include_router(movies.router, prefix="/api/v1/movies", tags=["Películas"])
app.include_router(recommendations.router, prefix="/api/v1/recommendations", tags=["Recomendaciones"])


# =============================================================================
# ENDPOINTS RAÍZ
# =============================================================================

@app.get("/")
async def root():
    """Endpoint raíz - información básica de la API."""
    return {
        "name": "CineIntelli API",
        "version": "2.0.0",
        "description": "Sistema inteligente de recomendación de películas",
        "docs": "/api/docs",
        "health": "/health",
        "status": "operational"
    }


@app.get("/api")
async def api_info():
    """Información de la API."""
    return {
        "version": "v1",
        "endpoints": {
            "auth": "/api/v1/auth",
            "users": "/api/v1/users",
            "movies": "/api/v1/movies",
            "recommendations": "/api/v1/recommendations"
        }
    }


# Punto de entrada para desarrollo
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
