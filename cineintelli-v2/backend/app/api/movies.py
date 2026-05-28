"""
API endpoints para películas
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import logger
from app.models.movie import Movie
from app.services.tmdb import TMDBService

router = APIRouter()


@router.get("/", response_model=dict)
async def list_movies(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    genre: Optional[str] = None,
    year: Optional[int] = None,
    min_rating: Optional[float] = Query(None, ge=0, le=10),
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Lista películas con filtros opcionales.
    """
    query = select(Movie).where(Movie.is_active == True)

    # Aplicar filtros
    if genre:
        query = query.where(Movie.genres.contains([genre]))
    if year:
        query = query.where(Movie.year == year)
    if min_rating:
        query = query.where(Movie.rating >= min_rating)
    if search:
        query = query.where(Movie.title.ilike(f"%{search}%"))

    # Contar total
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    # Paginación
    query = query.offset(skip).limit(limit).order_by(Movie.popularity.desc())
    result = await db.execute(query)
    movies = result.scalars().all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "results": [m.to_dict() for m in movies]
    }


@router.get("/genres")
async def get_genres(db: AsyncSession = Depends(get_db)):
    """Retorna lista de géneros disponibles."""
    result = await db.execute(select(Movie.genres))
    all_genres = set()
    for row in result:
        if row[0]:
            all_genres.update(row[0])

    return {
        "genres": sorted(list(all_genres)),
        "count": len(all_genres)
    }


@router.get("/popular")
async def get_popular_movies(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Retorna películas más populares."""
    query = (
        select(Movie)
        .where(Movie.is_active == True)
        .order_by(Movie.popularity.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    movies = result.scalars().all()

    return {
        "results": [m.to_dict() for m in movies]
    }


@router.get("/top-rated")
async def get_top_rated(
    limit: int = Query(10, ge=1, le=50),
    min_votes: int = Query(100, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """Retorna películas mejor calificadas."""
    query = (
        select(Movie)
        .where(
            Movie.is_active == True,
            Movie.vote_count >= min_votes,
            Movie.rating.isnot(None)
        )
        .order_by(Movie.rating.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    movies = result.scalars().all()

    return {
        "results": [m.to_dict() for m in movies]
    }


@router.get("/{movie_id}")
async def get_movie(
    movie_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Obtiene detalle de una película."""
    result = await db.execute(
        select(Movie).where(Movie.id == movie_id, Movie.is_active == True)
    )
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Película no encontrada"
        )

    return movie.to_dict()


@router.post("/sync-tmdb")
async def sync_tmdb_movies(
    pages: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db)
):
    """
    Sincroniza películas populares desde TMDB.
    Requiere autenticación (implementar).
    """
    tmdb_service = TMDBService()

    try:
        movies_synced = await tmdb_service.sync_popular_movies(db, pages)
        return {
            "message": f"Sincronizadas {movies_synced} películas",
            "synced_count": movies_synced
        }
    except Exception as e:
        logger.error(f"Error syncing TMDB: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sincronizando: {str(e)}"
        )
