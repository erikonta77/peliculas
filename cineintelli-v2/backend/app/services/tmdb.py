"""
Integración con The Movie Database (TMDB) API
"""

from typing import Dict, List, Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.logging import logger
from app.models.movie import Movie


class TMDBService:
    """Servicio de integración con TMDB API."""

    BASE_URL = "https://api.themoviedb.org/3"

    # Mapeo de géneros TMDB a nuestro catálogo canónico
    GENRE_MAP = {
        28: "Acción",
        12: "Aventura",
        16: "Animación",
        35: "Comedia",
        80: "Crimen",
        99: "Documental",
        18: "Drama",
        10751: "Familiar",
        14: "Fantasía",
        36: "Historia",
        27: "Terror",
        10402: "Música",
        9648: "Misterio",
        10749: "Romance",
        878: "Ciencia Ficción",
        10770: "TV",
        53: "Thriller",
        10752: "Guerra",
        37: "Western",
    }

    def __init__(self):
        self.api_key = settings.TMDB_API_KEY
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=30.0,
            headers={"Accept": "application/json"}
        )

    async def close(self):
        """Cierra el cliente HTTP."""
        await self.client.aclose()

    async def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Realiza petición a TMDB API."""
        params = params or {}
        params["api_key"] = self.api_key

        try:
            response = await self.client.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"TMDB HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"TMDB request error: {e}")
            raise

    async def get_popular_movies(self, page: int = 1) -> List[Dict]:
        """Obtiene películas populares."""
        data = await self._make_request("/movie/popular", {"page": page})
        return data.get("results", [])

    async def get_movie_details(self, tmdb_id: int) -> Dict:
        """Obtiene detalles completos de una película."""
        return await self._make_request(f"/movie/{tmdb_id}")

    async def search_movies(self, query: str, page: int = 1) -> List[Dict]:
        """Busca películas por título."""
        data = await self._make_request(
            "/search/movie",
            {"query": query, "page": page}
        )
        return data.get("results", [])

    async def get_genres(self) -> List[Dict]:
        """Obtiene lista de géneros."""
        data = await self._make_request("/genre/movie/list")
        return data.get("genres", [])

    def _convert_genres(self, tmdb_genres: List[int]) -> List[str]:
        """Convierte IDs de géneros TMDB a nombres en español."""
        return [
            self.GENRE_MAP.get(gid, "Otro")
            for gid in tmdb_genres
            if gid in self.GENRE_MAP
        ]

    async def sync_popular_movies(self, db: AsyncSession, pages: int = 5) -> int:
        """
        Sincroniza películas populares desde TMDB a nuestra base de datos.
        Retorna cantidad de películas sincronizadas.
        """
        if not self.api_key:
            logger.warning("TMDB API key no configurada")
            return 0

        synced_count = 0

        try:
            for page in range(1, pages + 1):
                logger.info(f"Sincronizando página {page} de TMDB...")
                movies = await self.get_popular_movies(page)

                for movie_data in movies:
                    # Verificar si ya existe
                    result = await db.execute(
                        select(Movie).where(Movie.tmdb_id == movie_data["id"])
                    )
                    existing = result.scalar_one_or_none()

                    # Extraer año
                    year = None
                    if movie_data.get("release_date"):
                        try:
                            year = int(movie_data["release_date"][:4])
                        except (ValueError, IndexError):
                            pass

                    genres = self._convert_genres(movie_data.get("genre_ids", []))

                    if existing:
                        # Actualizar
                        existing.popularity = movie_data.get("popularity", 0)
                        existing.rating = movie_data.get("vote_average", 0)
                        existing.vote_count = movie_data.get("vote_count", 0)
                    else:
                        # Crear nueva
                        new_movie = Movie(
                            tmdb_id=movie_data["id"],
                            title=movie_data["title"],
                            overview=movie_data.get("overview", ""),
                            poster_path=movie_data.get("poster_path"),
                            backdrop_path=movie_data.get("backdrop_path"),
                            release_date=year and f"{year}-01-01",  # Simplificado
                            year=year,
                            rating=movie_data.get("vote_average"),
                            vote_count=movie_data.get("vote_count", 0),
                            popularity=movie_data.get("popularity", 0),
                            genres=genres,
                            language=movie_data.get("original_language"),
                            original_language=movie_data.get("original_language"),
                            source="tmdb"
                        )
                        db.add(new_movie)
                        synced_count += 1

                await db.commit()
                logger.info(f"Página {page} sincronizada. Total: {synced_count}")

        except Exception as e:
            await db.rollback()
            logger.error(f"Error sincronizando TMDB: {e}")
            raise
        finally:
            await self.close()

        return synced_count
