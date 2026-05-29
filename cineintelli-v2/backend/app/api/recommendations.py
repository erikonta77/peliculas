"""
API endpoints para recomendaciones de películas (versión unificada Postgres/SQLite)
"""
from datetime import datetime
import random
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings

# Importaciones dinámicas según la base de datos configurada
if "sqlite" in settings.DATABASE_URL.lower():
    from app.core.database_sqlite import get_db
    from app.models_sqlite import Movie, User, UserProfile
    from app.api.auth_sqlite import get_current_active_user
else:
    from app.core.database import get_db
    from app.models.movie import Movie
    from app.models.user import User, UserProfile
    from app.api.auth import get_current_active_user

router = APIRouter()


@router.get("/personalized")
async def get_personalized_recommendations(
    count: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """
    Obtiene recomendaciones personalizadas basadas en el perfil del usuario.
    Funciona tanto en modo PostgreSQL (async) como SQLite (sync).
    """
    # 1. Obtener/Crear Perfil
    if isinstance(db, AsyncSession):
        result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == current_user.id)
        )
        profile = result.scalar_one_or_none()
        if not profile:
            profile = UserProfile(user_id=current_user.id)
            db.add(profile)
            await db.commit()
            await db.refresh(profile)
    else:
        profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
        if not profile:
            profile = UserProfile(user_id=current_user.id)
            db.add(profile)
            db.commit()
            db.refresh(profile)

    # 2. Obtener Películas Activas
    if isinstance(db, AsyncSession):
        result = await db.execute(select(Movie).where(Movie.is_active == True))
        all_movies = result.scalars().all()
    else:
        all_movies = db.query(Movie).filter(Movie.is_active == True).all()

    # 3. Motor de Recomendación (Algoritmo Sync unificado)
    scored = []
    for m in all_movies:
        score = 0.0
        if m.rating:
            score += (m.rating / 10.0) * 0.4
        if m.popularity:
            score += min(m.popularity / 100.0, 1.0) * 0.3
        if m.genres and profile.favorite_genres:
            overlap = set(m.genres) & set(profile.favorite_genres)
            if overlap:
                score += len(overlap) / len(set(m.genres) | set(profile.favorite_genres)) * 0.3
        scored.append((m, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    recommendations = [m[0] for m in scored[:count]]

    return {
        "recommendations": [m.to_dict() for m in recommendations],
        "count": len(recommendations),
        "profile_used": {
            "genres": profile.favorite_genres or [],
            "year_range": [profile.year_min, profile.year_max],
            "min_rating": profile.min_rating
        }
    }


@router.post("/feedback")
async def submit_recommendation_feedback(
    movie_id: str,
    accepted: bool = True,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """
    Registra feedback del usuario sobre una recomendación.
    """
    if isinstance(db, AsyncSession):
        result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == current_user.id)
        )
        profile = result.scalar_one_or_none()
    else:
        profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()

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

    history = list(profile.watch_history)
    history.append({
        "movie_id": str(movie_id),
        "accepted": accepted,
        "timestamp": datetime.utcnow().isoformat()
    })
    profile.watch_history = history

    if isinstance(db, AsyncSession):
        await db.commit()
    else:
        db.commit()

    return {"message": "Feedback registrado correctamente"}


@router.get("/similar/{movie_id}")
async def get_similar_movies(
    movie_id: str,
    count: int = Query(10, ge=1, le=20),
    db = Depends(get_db)
):
    """
    Encuentra películas similares a una dada basándose en géneros comunes.
    """
    # Verificar que la película existe
    if isinstance(db, AsyncSession):
        try:
            uuid_id = UUID(str(movie_id))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid movie UUID")
        result = await db.execute(
            select(Movie).where(Movie.id == uuid_id, Movie.is_active == True)
        )
        movie = result.scalar_one_or_none()
    else:
        movie = db.query(Movie).filter(Movie.id == movie_id, Movie.is_active == True).first()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Película no encontrada"
        )

    if movie.genres:
        if isinstance(db, AsyncSession):
            result = await db.execute(
                select(Movie).where(Movie.id != movie.id, Movie.is_active == True)
            )
            similar = result.scalars().all()
        else:
            similar = db.query(Movie).filter(Movie.id != movie_id, Movie.is_active == True).all()

        # Puntuación por coincidencia de géneros
        scored = []
        for m in similar:
            if m.genres:
                overlap = set(m.genres) & set(movie.genres)
                score = len(overlap)
                scored.append((m, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return {
            "movie": movie.to_dict(),
            "similar_movies": [m[0].to_dict() for m in scored[:count]],
            "count": min(count, len(scored))
        }

    # Si no tiene géneros, devolver películas ordenadas por puntuación
    if isinstance(db, AsyncSession):
        result = await db.execute(
            select(Movie).where(Movie.id != movie.id, Movie.is_active == True)
            .order_by(Movie.rating.desc()).limit(count)
        )
        similar = result.scalars().all()
    else:
        similar = db.query(Movie).filter(Movie.id != movie_id, Movie.is_active == True).order_by(Movie.rating.desc()).limit(count).all()

    return {
        "movie": movie.to_dict(),
        "similar_movies": [m.to_dict() for m in similar],
        "count": len(similar)
    }


@router.get("/trending")
async def get_trending_recommendations(
    genre: Optional[str] = None,
    limit: int = Query(10, ge=1, le=50),
    db = Depends(get_db)
):
    """
    Películas trending basadas en popularidad reciente.
    """
    if isinstance(db, AsyncSession):
        query = select(Movie).where(
            Movie.is_active == True,
            Movie.popularity.isnot(None)
        )
        if genre:
            query = query.where(Movie.genres.contains([genre]))
        result = await db.execute(query.order_by(Movie.popularity.desc()).limit(limit))
        movies = result.scalars().all()
    else:
        query = db.query(Movie).filter(Movie.is_active == True, Movie.popularity.isnot(None))
        if genre:
            query = query.filter(Movie.genres.contains(f'"{genre}"'))
        movies = query.order_by(Movie.popularity.desc()).limit(limit).all()

    return {
        "trending": [m.to_dict() for m in movies],
        "genre_filter": genre
    }


@router.post("/roulette")
async def cine_roulette(
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db)
):
    """
    Modo CineRoulette - película aleatoria fuera del perfil habitual.
    """
    if isinstance(db, AsyncSession):
        result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == current_user.id)
        )
        profile = result.scalar_one_or_none()
    else:
        profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()

    if isinstance(db, AsyncSession):
        result = await db.execute(
            select(Movie).where(Movie.is_active == True, Movie.rating >= 6.0)
        )
        all_movies = result.scalars().all()
    else:
        all_movies = db.query(Movie).filter(Movie.is_active == True, Movie.rating >= 6.0).all()

    if profile and profile.favorite_genres:
        # Excluir géneros favoritos del perfil para dar una sorpresa real
        candidates = [m for m in all_movies if not (m.genres and any(g in profile.favorite_genres for g in m.genres))]
        if candidates:
            return {
                "roulette": random.choice(candidates).to_dict(),
                "message": "¡Sorpresa!"
            }

    if all_movies:
        return {
            "roulette": random.choice(all_movies).to_dict(),
            "message": "¡Sorpresa!"
        }
    return {
        "roulette": None,
        "message": "No hay películas disponibles"
    }
