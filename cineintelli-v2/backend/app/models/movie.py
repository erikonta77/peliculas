"""
Modelos de películas y catálogo
"""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import ARRAY, Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Movie(Base):
    """Modelo de película en el catálogo."""
    __tablename__ = "movies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tmdb_id = Column(Integer, unique=True, nullable=True, index=True)
    imdb_id = Column(String(20), unique=True, nullable=True, index=True)

    # Información básica
    title = Column(String(500), nullable=False, index=True)
    original_title = Column(String(500), nullable=True)
    overview = Column(Text, nullable=True)
    tagline = Column(String(500), nullable=True)

    # Clasificación
    genres = Column(ARRAY(String), default=[])
    runtime = Column(Integer, nullable=True)  # minutos
    language = Column(String(10), nullable=True)
    original_language = Column(String(10), nullable=True)

    # Fechas
    release_date = Column(DateTime, nullable=True)
    year = Column(Integer, nullable=True, index=True)

    # Métricas
    rating = Column(Float, nullable=True, index=True)
    vote_count = Column(Integer, default=0)
    popularity = Column(Float, default=0.0)

    # Multimedia
    poster_path = Column(String(500), nullable=True)
    backdrop_path = Column(String(500), nullable=True)
    trailer_url = Column(String(500), nullable=True)

    # Enriquecimiento
    cast = Column(JSONB, default=list)  # Top actores
    crew = Column(JSONB, default=list)  # Directores, etc.
    keywords = Column(ARRAY(String), default=[])
    external_ids = Column(JSONB, default=dict)

    # ML / Embeddings
    embedding_id = Column(String(100), nullable=True)  # ID en ChromaDB
    features_vector = Column(ARRAY(Float), nullable=True)  # Vector de características

    # Flags
    is_adult = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    # Metadata
    source = Column(String(50), default="manual")  # tmdb, omdb, manual, etc.
    enriched_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    ratings = relationship("MovieRating", back_populates="movie")

    def __repr__(self):
        return f"<Movie {self.title} ({self.year})>"

    @property
    def poster_url(self) -> Optional[str]:
        """Retorna URL completa del poster."""
        if self.poster_path:
            if self.poster_path.startswith("http"):
                return self.poster_path
            return f"https://image.tmdb.org/t/p/w500{self.poster_path}"
        return None

    def to_dict(self) -> dict:
        """Convierte la película a diccionario."""
        return {
            "id": str(self.id),
            "tmdb_id": self.tmdb_id,
            "title": self.title,
            "overview": self.overview,
            "genres": self.genres,
            "year": self.year,
            "rating": self.rating,
            "popularity": self.popularity,
            "poster_url": self.poster_url,
            "runtime": self.runtime,
            "language": self.language,
        }


class MovieRating(Base):
    """Rating dado por un usuario a una película."""
    __tablename__ = "movie_ratings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    movie_id = Column(UUID(as_uuid=True), ForeignKey("movies.id"), nullable=False)

    rating = Column(Float, nullable=False)  # 0-10
    review = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    movie = relationship("Movie", back_populates="ratings")

    __table_args__ = (
        # Un usuario solo puede calificar una película una vez
        {"sqlite_autoincrement": True},
    )
