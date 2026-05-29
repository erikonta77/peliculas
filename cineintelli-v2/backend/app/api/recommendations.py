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


def normalize_genre(g: str) -> str:
    if not g:
        return ""
    g = g.lower()
    replacements = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'ñ': 'n',
        '\ufffd': 'o',
    }
    for k, v in replacements.items():
        g = g.replace(k, v)
    g = g.replace("ficcin", "ficcion")
    g = g.replace("accin", "accion")
    return "".join(c for c in g if c.isalnum())


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

    # 3. Motor de Recomendación
    if isinstance(db, AsyncSession):
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
    else:
        # SQLite - Nueva exploración inteligente y experiencia personalizada
        # A. Evitar repetición de contenido (excluir visto o rechazado)
        watched_movie_ids = set()
        rejected_movie_ids = set()
        if profile.watch_history:
            for entry in profile.watch_history:
                if isinstance(entry, dict):
                    m_id = entry.get("movie_id")
                    if m_id:
                        if entry.get("accepted", True):
                            watched_movie_ids.add(str(m_id))
                        else:
                            rejected_movie_ids.add(str(m_id))
                elif isinstance(entry, str):
                    watched_movie_ids.add(entry)

        eligible_movies = []
        for m in all_movies:
            m_id_str = str(m.id)
            if m_id_str in watched_movie_ids or m_id_str in rejected_movie_ids:
                continue
            eligible_movies.append(m)

        # Determinar popularidad media (percentiles 15 a 75)
        pops = sorted([x.popularity for x in all_movies if x.popularity is not None])
        if len(pops) >= 5:
            low_idx = int(len(pops) * 0.15)
            high_idx = int(len(pops) * 0.75)
            low_val = pops[low_idx]
            high_val = pops[high_idx]
        else:
            low_val = -1.0
            high_val = 9999.0

        favorite_genres = profile.favorite_genres or []

        scored_movies = []
        for m in eligible_movies:
            score = 0.0
            
            # 1. Géneros: 35%
            overlap_genres = []
            has_favorite_genre = False
            if m.genres and favorite_genres:
                movie_genres_norm = {normalize_genre(g) for g in m.genres}
                fav_genres_norm = {normalize_genre(g) for g in favorite_genres}
                overlap = movie_genres_norm & fav_genres_norm
                if overlap:
                    for fg in favorite_genres:
                        if normalize_genre(fg) in overlap:
                            overlap_genres.append(fg)
                    union_len = len(movie_genres_norm | fav_genres_norm)
                    if union_len > 0:
                        score += (len(overlap) / union_len) * 0.35
                has_favorite_genre = bool(overlap)
            
            # 2. Rating: 25%
            if m.rating is not None:
                score += (m.rating / 10.0) * 0.25

            # 3. Popularidad: 20%
            if m.popularity is not None:
                score += min(m.popularity / 100.0, 1.0) * 0.20

            # 4. Exploración bonus: +20% (0.20) si no es género favorito
            if favorite_genres and not has_favorite_genre:
                score += 0.20

            scored_movies.append({
                "movie": m,
                "score": score,
                "has_favorite_genre": has_favorite_genre,
                "overlap_genres": overlap_genres
            })

        # Clasificar en afines vs exploración
        lista_exploracion = []
        lista_afines = []

        for item in scored_movies:
            m = item["movie"]
            has_fav = item["has_favorite_genre"]
            
            is_exp = False
            if favorite_genres:
                if not has_fav:
                    if m.rating is not None and m.rating > 6.5:
                        if low_val <= (m.popularity or 0.0) <= high_val:
                            is_exp = True

            item["is_exploration"] = is_exp
            if is_exp:
                lista_exploracion.append(item)
            else:
                lista_afines.append(item)

        # Ordenar por puntuación descendente
        lista_exploracion.sort(key=lambda x: x["score"], reverse=True)
        lista_afines.sort(key=lambda x: x["score"], reverse=True)

        # Mezclar: 70% afinidad, 30% exploración
        target_afines = int(count * 0.7)
        target_exploration = count - target_afines

        selected_afines = lista_afines[:target_afines]
        selected_exp = lista_exploracion[:target_exploration]

        # Completar si alguna lista se queda corta
        if len(selected_afines) < target_afines:
            extra_slots = target_afines - len(selected_afines)
            selected_exp += lista_exploracion[target_exploration : target_exploration + extra_slots]

        if len(selected_exp) < target_exploration:
            extra_slots = target_exploration - len(selected_exp)
            selected_afines += lista_afines[target_afines : target_afines + extra_slots]

        # Ajustar longitud final al count
        selected_afines = selected_afines[:target_afines + max(0, target_exploration - len(selected_exp))]
        selected_exp = selected_exp[:target_exploration + max(0, target_afines - len(selected_afines))]

        # Intercalado (A, A, E, A, A, E...) para mejor UX
        final_items = []
        i_af = 0
        i_ex = 0
        while i_af < len(selected_afines) or i_ex < len(selected_exp):
            for _ in range(2):
                if i_af < len(selected_afines):
                    final_items.append(selected_afines[i_af])
                    i_af += 1
            if i_ex < len(selected_exp):
                final_items.append(selected_exp[i_ex])
                i_ex += 1

        # Formatear respuesta con explicabilidad
        results = []
        for item in final_items:
            m = item["movie"]
            is_exp = item["is_exploration"]
            overlap = item["overlap_genres"]

            if is_exp:
                reason = "Recomendación para descubrir algo diferente"
            else:
                if overlap:
                    genres_str = " y ".join(overlap[:2]) if len(overlap) > 1 else overlap[0]
                    reason = f"Porque te gusta {genres_str} y esta película tiene alta puntuación"
                else:
                    reason = "Recomendada por su popularidad y valoración general"

            m_dict = m.to_dict()
            m_dict["reason"] = reason
            m_dict["type"] = "exploration" if is_exp else "affinity"
            results.append(m_dict)

        return results[:count]


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
    else:
        # SQLite - CineRoulette mejorado (Rating >= 6.5, excluir vistos/rechazados, excluir favoritos)
        watched_movie_ids = set()
        rejected_movie_ids = set()
        if profile and profile.watch_history:
            for entry in profile.watch_history:
                if isinstance(entry, dict):
                    m_id = entry.get("movie_id")
                    if m_id:
                        if entry.get("accepted", True):
                            watched_movie_ids.add(str(m_id))
                        else:
                            rejected_movie_ids.add(str(m_id))
                elif isinstance(entry, str):
                    watched_movie_ids.add(entry)

        all_movies = db.query(Movie).filter(Movie.is_active == True, Movie.rating >= 6.5).all()

        favorite_genres = profile.favorite_genres if profile else []

        candidates = []
        for m in all_movies:
            m_id_str = str(m.id)
            if m_id_str in watched_movie_ids or m_id_str in rejected_movie_ids:
                continue

            # Excluir favoritos
            if favorite_genres and m.genres:
                movie_genres_norm = {normalize_genre(g) for g in m.genres}
                fav_genres_norm = {normalize_genre(g) for g in favorite_genres}
                if movie_genres_norm & fav_genres_norm:
                    continue
            candidates.append(m)

        # Fallback si no quedan películas sin sus géneros favoritos: incluir todas las no vistas
        if not candidates:
            candidates = [
                m for m in all_movies
                if str(m.id) not in watched_movie_ids and str(m.id) not in rejected_movie_ids
            ]

        if candidates:
            return {
                "roulette": random.choice(candidates).to_dict(),
                "message": "¡Sorpresa!"
            }

    return {
        "roulette": None,
        "message": "No hay películas disponibles"
    }
