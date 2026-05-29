"""
Health check endpoints (SQLite sync version)
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def health_check():
    return {"status": "healthy", "service": "cineintelli-api", "version": "2.0.0"}

@router.get("/ready")
def readiness_check():
    return {"status": "ready"}

@router.get("/live")
def liveness_check():
    return {"status": "alive"}
