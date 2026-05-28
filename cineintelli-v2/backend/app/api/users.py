"""
API endpoints para usuarios
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_active_user
from app.core.database import get_db
from app.core.logging import logger
from app.models.user import User, UserProfile

router = APIRouter()


@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Obtiene información del usuario actual."""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        "last_login": current_user.last_login.isoformat() if current_user.last_login else None
    }


@router.get("/me/profile")
async def get_user_profile(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Obtiene el perfil de preferencias del usuario."""
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        # Crear perfil por defecto
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
        await db.commit()
        await db.refresh(profile)

    return {
        "favorite_genres": profile.favorite_genres or [],
        "year_min": profile.year_min,
        "year_max": profile.year_max,
        "min_rating": profile.min_rating,
        "preferred_language": profile.preferred_language,
        "recommendations_count": profile.recommendations_count,
        "watch_history": profile.watch_history or [],
        "recommendations_accepted": profile.recommendations_accepted,
        "recommendations_rejected": profile.recommendations_rejected
    }


@router.put("/me/profile")
async def update_user_profile(
    favorite_genres: Optional[list] = None,
    year_min: Optional[int] = None,
    year_max: Optional[int] = None,
    min_rating: Optional[float] = None,
    preferred_language: Optional[str] = None,
    recommendations_count: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Actualiza el perfil de preferencias del usuario."""
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)

    # Actualizar campos
    if favorite_genres is not None:
        profile.favorite_genres = favorite_genres
    if year_min is not None:
        profile.year_min = year_min
    if year_max is not None:
        profile.year_max = year_max
    if min_rating is not None:
        profile.min_rating = min_rating
    if preferred_language is not None:
        profile.preferred_language = preferred_language
    if recommendations_count is not None:
        profile.recommendations_count = recommendations_count

    await db.commit()
    await db.refresh(profile)

    logger.info(f"Perfil actualizado para usuario {current_user.email}")

    return {
        "message": "Perfil actualizado correctamente",
        "profile": {
            "favorite_genres": profile.favorite_genres,
            "year_min": profile.year_min,
            "year_max": profile.year_max,
            "min_rating": profile.min_rating,
            "preferred_language": profile.preferred_language,
            "recommendations_count": profile.recommendations_count
        }
    }
