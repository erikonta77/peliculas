"""
Health check endpoints
"""

from datetime import datetime

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import logger

router = APIRouter()


@router.get("/")
async def health_check():
    """Health check básico."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "cineintelli-api",
        "version": "2.0.0"
    }


@router.get("/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """Readiness check - verifica conexiones a servicios."""
    try:
        # Verificar conexión a BD
        from sqlalchemy import text
        await db.execute(text("SELECT 1"))

        return {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                "database": "ok",
            }
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {
            "status": "not_ready",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }


@router.get("/live")
async def liveness_check():
    """Liveness check - verifica que el proceso está vivo."""
    return {"status": "alive"}
