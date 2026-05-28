"""
Motor de recomendaciones - Clásico + Neural
"""

import random
from typing import List, Optional

import numpy as np
from scipy.spatial.distance import cosine
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.models.movie import Movie
from app.models.user import UserProfile


class MovieRecommender:
    """Motor de recomendaciones híbrido (clásico + embeddings)."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.model = None
        self.encoder = None

    async def get_recommendations(
        self,
        profile: UserProfile,
        count: int = 10,
        exclude_watched: bool = True
    ) -> List[Movie]:
        """
        Obtiene recomendaciones basadas en el perfil.
        Usa motor neuronal si está disponible, sino motor clásico.
        """
        if self.encoder:
            return await self._neural_recommendations(profile, count, exclude_watched)
        else:
            return await self._classical_recommendations(profile, count, exclude_watched)

    async def _classical_recommendations(
        self,
        profile: UserProfile,
        count: int,
        exclude_watched: bool
    ) -> List[Movie]:
        """Motor clásico basado en filtros y scoring."""
        query = select(Movie).where(
            Movie.is_active == True,
            Movie.year >= profile.year_min,
            Movie.year <= profile.year_max,
            Movie.rating >= profile.min_rating
        )

        # Filtrar por géneros favoritos
        if profile.favorite_genres:
            # Películas que tengan al menos un género favorito
            conditions = [Movie.genres.overlap([genre]) for genre in profile.favorite_genres]
            from sqlalchemy import or_
            query = query.where(or_(*conditions))

        # Filtrar idioma
        if profile.preferred_language and profile.preferred_language != "any":
            query = query.where(Movie.language == profile.preferred_language)

        # Excluir películas ya vistas
        if exclude_watched and profile.watch_history:
            watched_ids = [h.get("movie_id") for h in profile.watch_history if isinstance(h, dict)]
            if watched_ids:
                from sqlalchemy import not_
                query = query.where(not_(Movie.id.in_(watched_ids)))

        # Ordenar por puntuación y popularidad
        query = query.order_by(
            (Movie.rating * 0.6 + Movie.popularity * 0.4).desc()
        ).limit(count * 2)  # Obtener más para filtrar

        result = await self.db.execute(query)
        movies = result.scalars().all()

        # Scoring final y ordenamiento
        scored_movies = []
        for movie in movies:
            score = self._calculate_score(movie, profile)
            scored_movies.append((movie, score))

        # Ordenar por score y tomar top N
        scored_movies.sort(key=lambda x: x[1], reverse=True)
        return [m[0] for m in scored_movies[:count]]

    def _calculate_score(self, movie: Movie, profile: UserProfile) -> float:
        """Calcula score de relevancia para una película."""
        score = 0.0

        # Puntuación (30%)
        if movie.rating:
            score += (movie.rating / 10.0) * 0.30

        # Popularidad (30%)
        if movie.popularity:
            # Normalizar popularidad (asumiendo rango típico 0-100)
            score += min(movie.popularity / 100.0, 1.0) * 0.30

        # Géneros (25%)
        if profile.favorite_genres and movie.genres:
            overlap = set(movie.genres) & set(profile.favorite_genres)
            union = set(movie.genres) | set(profile.favorite_genres)
            if union:
                jaccard = len(overlap) / len(union)
                score += jaccard * 0.25

        # Proximidad temporal (15%)
        if movie.year and profile.year_min and profile.year_max:
            center = (profile.year_min + profile.year_max) / 2
            range_years = profile.year_max - profile.year_min
            if range_years > 0:
                distance = abs(movie.year - center) / (range_years / 2)
                score += (1 - min(distance, 1)) * 0.15

        return score

    async def _neural_recommendations(
        self,
        profile: UserProfile,
        count: int,
        exclude_watched: bool
    ) -> List[Movie]:
        """Motor neuronal usando embeddings del Autoencoder."""
        # TODO: Implementar usando embeddings
        logger.info("Usando motor neuronal para recomendaciones")
        return await self._classical_recommendations(profile, count, exclude_watched)

    async def get_similar_movies(self, movie_id: str, count: int = 10) -> List[Movie]:
        """Encuentra películas similares usando embeddings."""
        # Obtener película fuente
        result = await self.db.execute(
            select(Movie).where(Movie.id == movie_id)
        )
        source = result.scalar_one_or_none()

        if not source or not source.features_vector:
            # Fallback: películas del mismo género
            if source and source.genres:
                query = select(Movie).where(
                    Movie.id != movie_id,
                    Movie.genres.overlap(source.genres),
                    Movie.is_active == True
                ).order_by(Movie.rating.desc()).limit(count)
                result = await self.db.execute(query)
                return result.scalars().all()
            return []

        # Calcular similitud con todas las películas
        # TODO: Optimizar con ChromaDB
        query = select(Movie).where(
            Movie.id != movie_id,
            Movie.is_active == True,
            Movie.features_vector.isnot(None)
        )
        result = await self.db.execute(query)
        candidates = result.scalars().all()

        similarities = []
        source_vec = np.array(source.features_vector)

        for movie in candidates:
            if movie.features_vector:
                movie_vec = np.array(movie.features_vector)
                similarity = 1 - cosine(source_vec, movie_vec)
                similarities.append((movie, similarity))

        # Ordenar por similitud
        similarities.sort(key=lambda x: x[1], reverse=True)
        return [m[0] for m in similarities[:count]]

    async def get_roulette_recommendation(
        self,
        profile: Optional[UserProfile]
    ) -> Optional[Movie]:
        """Modo CineRoulette - película aleatoria fuera del perfil."""
        query = select(Movie).where(Movie.is_active == True)

        # Excluir géneros favoritos del perfil
        if profile and profile.favorite_genres:
            # Películas que NO tengan los géneros favoritos principales
            from sqlalchemy import not_, or_
            conditions = [Movie.genres.overlap([genre]) for genre in profile.favorite_genres]
            query = query.where(not_(or_(*conditions)))

        # Películas con buena puntuación pero menos populares
        query = query.where(
            Movie.rating >= 6.0,
            Movie.popularity < 50  # Menos populares
        )

        result = await self.db.execute(query)
        candidates = result.scalars().all()

        if candidates:
            return random.choice(candidates)

        # Si no hay resultados, devolver cualquier película aleatoria
        result = await self.db.execute(
            select(Movie).where(Movie.is_active == True).order_by(func.random()).limit(1)
        )
        return result.scalar_one_or_none()
