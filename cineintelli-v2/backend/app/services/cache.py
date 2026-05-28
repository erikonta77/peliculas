"""
Servicio de cache usando Redis
"""

import json
from typing import Any, Optional

import redis.asyncio as redis

from app.core.config import settings
from app.core.logging import logger


class CacheService:
    """Servicio de cache con Redis."""

    _instance = None
    _redis: Optional[redis.Redis] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def connect(self):
        """Conecta a Redis."""
        if self._redis is None:
            try:
                self._redis = await redis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True
                )
                await self._redis.ping()
                logger.info("✅ Conectado a Redis")
            except Exception as e:
                logger.error(f"❌ Error conectando a Redis: {e}")
                self._redis = None

    async def disconnect(self):
        """Desconecta de Redis."""
        if self._redis:
            await self._redis.close()
            self._redis = None
            logger.info("🔌 Desconectado de Redis")

    async def get(self, key: str) -> Optional[Any]:
        """Obtiene valor del cache."""
        if not self._redis:
            return None

        try:
            value = await self._redis.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.warning(f"Cache GET error: {e}")

        return None

    async def set(self, key: str, value: Any, ttl: int = None):
        """Guarda valor en cache."""
        if not self._redis:
            return

        try:
            serialized = json.dumps(value, default=str)
            ttl = ttl or settings.CACHE_DEFAULT_TTL
            await self._redis.setex(key, ttl, serialized)
        except Exception as e:
            logger.warning(f"Cache SET error: {e}")

    async def delete(self, key: str):
        """Elimina clave del cache."""
        if self._redis:
            await self._redis.delete(key)

    async def delete_pattern(self, pattern: str):
        """Elimina claves que coincidan con patrón."""
        if not self._redis:
            return

        try:
            keys = await self._redis.keys(pattern)
            if keys:
                await self._redis.delete(*keys)
        except Exception as e:
            logger.warning(f"Cache DELETE pattern error: {e}")

    async def increment(self, key: str, amount: int = 1) -> int:
        """Incrementa contador."""
        if not self._redis:
            return 0

        return await self._redis.incrby(key, amount)
