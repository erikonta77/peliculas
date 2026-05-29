"""
Configuración de la aplicación usando Pydantic Settings
"""

from functools import lru_cache
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración global de la aplicación."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # =============================================================================
    # APLICACIÓN
    # =============================================================================
    APP_NAME: str = "CineIntelli"
    APP_VERSION: str = "2.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # =============================================================================
    # SEGURIDAD
    # =============================================================================
    SECRET_KEY: str = "cineintelli-secret-key-change-in-production-2024"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 días

    # =============================================================================
    # BASE DE DATOS
    # =============================================================================
    DATABASE_URL: str = "postgresql+asyncpg://cineintelli:password@localhost:5432/cineintelli"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # =============================================================================
    # REDIS / CACHE
    # =============================================================================
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_POOL_SIZE: int = 10
    CACHE_DEFAULT_TTL: int = 3600  # 1 hora

    # =============================================================================
    # CHROMADB (Vector DB)
    # =============================================================================
    CHROMADB_HOST: str = "localhost"
    CHROMADB_PORT: int = 8000
    CHROMADB_COLLECTION: str = "movies"

    # =============================================================================
    # APIS EXTERNAS
    # =============================================================================
    TMDB_API_KEY: Optional[str] = None
    OMDB_API_KEY: Optional[str] = None
    TMDB_BASE_URL: str = "https://api.themoviedb.org/3"
    TMDB_IMAGE_BASE_URL: str = "https://image.tmdb.org/t/p/w500"

    # =============================================================================
    # CORS
    # =============================================================================
    CORS_ORIGINS: List[str] = ["*"]

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


@lru_cache()
def get_settings() -> Settings:
    """Retorna instancia cacheada de configuración."""
    return Settings()


settings = get_settings()
