"""
CineIntelli v2.0 - FastAPI Application (SQLite quick-deploy edition)
Backend simplificado que corre sin Docker, sin PostgreSQL, sin Redis.
Ideal para despliegue rápido con TryCloudflare.
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import health_sqlite as health
from app.api import auth_sqlite as auth
from app.api import users_sqlite as users
from app.api import movies_sqlite as movies
from app.api import recommendations_sqlite as recommendations
from app.core.database_sqlite import init_db

app = FastAPI(
    title="CineIntelli API",
    description="Sistema inteligente de recomendación de películas",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# API routes
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Autenticación"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Usuarios"])
app.include_router(movies.router, prefix="/api/v1/movies", tags=["Películas"])
app.include_router(recommendations.router, prefix="/api/v1/recommendations", tags=["Recomendaciones"])

# Static frontend
static_path = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
if os.path.exists(static_path):
    app.mount("/", StaticFiles(directory=static_path, html=True), name="static")
else:
    @app.get("/")
    def root():
        return {
            "name": "CineIntelli API",
            "version": "2.0.0",
            "status": "operational",
            "docs": "/api/docs",
            "health": "/health"
        }

# Init DB on startup
init_db()
