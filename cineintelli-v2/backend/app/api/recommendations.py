"""
API endpoints para recomendaciones de películas
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_active_user
from app.core.config import settings
from app.core.database import get_db
from app.core.logging import logger
from app.models_sqlite import Movie
from app.models_sqlite import User, UserProfile
from app.services.cache import CacheService
from app.services.recommender import MovieRecommender

router = APIRouter()


@router.get("/personalized")
async def get_personalized_recommendations(
    request: Request,
    count: int = Query(10, ge=1, le=50),
    include_watched: bool = Query(False),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene recomendaciones personalizadas basadas en el perfil del usuario.
    Usa cache para mejorar rendimiento.
    """
    cache_key = f"recs:{current_user.id}:{count}:{include_watched}"

    # Intentar obtener del cache
    cache = CacheService()
    cached = await cache.get(cache_key)
    if cached:
        logger.info(f"Cache HIT para recomendaciones de {current_user.email}")
        return cached

    # Cargar perfil
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        # Crear perfil por defecto
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
        await db.commit()

    # Obtener recomendaciones
    recommender = MovieRecommender(db)

    # Cargar modelo si existe
    model_loader = request.app.state.model_loader
    if model_loader.model:
        recommender.model = model_loader.model

    recommendations = await recommender.get_recommendations(
        profile=profile,
        count=count,
        exclude_watched=not include_watched
    )

    response = {
        "recommendations": [r.to_dict() for r in recommendations],
        "count": len(recommendations),
        "profile_used": {
            "genres": profile.favorite_genres,
            "year_range": [profile.year_min, profile.year_max],
            "min_rating": profile.min_rating
        }
    }

    # Guardar en cache (5 minutos)
    await cache.set(cache_key, response, ttl=300)

    return response


@router.post("/feedback")
async def submit_recommendation_feedback(
    movie_id: UUID,
    accepted: bool = True,
    rating: Optional[float] = Query(None, ge=0, le=10),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Registra feedback del usuario sobre una recomendación.
    Ayuda a mejorar futuras recomendaciones.
    """
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil no encontrado"
        )

    # Actualizar contadores
    if accepted:
        profile.recommendations_accepted += 1
    else:
        profile.recommendations_rejected += 1

    # Agregar a historial
    if not profile.watch_history:
        profile.watch_history = []

    profile.watch_history.append({
        "movie_id": str(movie_id),
        "accepted": accepted,
        "rating": rating,
        "timestamp": datetime.utcnow().isoformat()
    })

    await db.commit()

    # Invalidar cache de recomendaciones
    cache = CacheService()
    await cache.delete_pattern(f"recs:{current_user.id}:*")

    return {"message": "Feedback registrado correctamente"}


@router.get("/similar/{movie_id}")
async def get_similar_movies(
    movie_id: UUID,
    count: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db)
):
    """
    Encuentra películas similares a una dada.
    Usa embeddings del autoencoder.
    """
    # Verificar que la película existe
    result = await db.execute(
        select(Movie).where(Movie.id == movie_id, Movie.is_active == True)
    )
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Película no encontrada"
        )

    # Obtener similares
    recommender = MovieRecommender(db)
    similar = await recommender.get_similar_movies(movie_id, count)

    return {
        "movie": movie.to_dict(),
        "similar_movies": [m.to_dict() for m in similar],
        "count": len(similar)
    }


@router.get("/trending")
async def get_trending_recommendations(
    genre: Optional[str] = None,
    days: int = Query(7, ge=1, le=30),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """
    Películas trending basadas en popularidad reciente.
    """
    query = select(Movie).where(
        Movie.is_active == True,
        Movie.popularity.isnot(None)
    )

    if genre:
        query = query.where(Movie.genres.contains([genre]))

    query = query.order_by(Movie.popularity.desc()).limit(limit)

    result = await db.execute(query)
    movies = result.scalars().all()

    return {
        "trending": [m.to_dict() for m in movies],
        "genre_filter": genre,
        "period_days": days
    }


@router.post("/roulette")
async def cine_roulette(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Modo CineRoulette - película aleatoria fuera del perfil habitual.
    """
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()

    recommender = MovieRecommender(db)
    roulette_movie = await recommender.get_roulette_recommendation(profile)

    return {
        "roulette": roulette_movie.to_dict() if roulette_movie else None,
        "message": "¡Sorpresa cinematográfica!"
    }


# Import necesario
from datetime import datetime
