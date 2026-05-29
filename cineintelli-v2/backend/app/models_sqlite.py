"""
Modelos SQLite simplificados para despliegue rápido
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, JSON
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False)
    favorite_genres = Column(JSON, default=list)
    year_min = Column(Integer, default=1900)
    year_max = Column(Integer, default=2100)
    min_rating = Column(Float, default=0.0)
    preferred_language = Column(String(10), default="any")
    recommendations_count = Column(Integer, default=10)
    watch_history = Column(JSON, default=list)
    ratings_given = Column(JSON, default=dict)
    recommendations_accepted = Column(Integer, default=0)
    recommendations_rejected = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Movie(Base):
    __tablename__ = "movies"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tmdb_id = Column(Integer, nullable=True)
    imdb_id = Column(String(20), nullable=True)
    title = Column(String(500), nullable=False)
    original_title = Column(String(500), nullable=True)
    overview = Column(String(5000), nullable=True)
    tagline = Column(String(500), nullable=True)
    genres = Column(JSON, default=list)
    runtime = Column(Integer, nullable=True)
    language = Column(String(10), nullable=True)
    original_language = Column(String(10), nullable=True)
    release_date = Column(DateTime, nullable=True)
    year = Column(Integer, nullable=True)
    rating = Column(Float, nullable=True)
    vote_count = Column(Integer, default=0)
    popularity = Column(Float, default=0.0)
    poster_path = Column(String(500), nullable=True)
    backdrop_path = Column(String(500), nullable=True)
    trailer_url = Column(String(500), nullable=True)
    cast = Column(JSON, default=list)
    crew = Column(JSON, default=list)
    keywords = Column(JSON, default=list)
    external_ids = Column(JSON, default=dict)
    features_vector = Column(JSON, nullable=True)
    is_adult = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    source = Column(String(50), default="manual")
    enriched_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def poster_url(self):
        if self.poster_path:
            if self.poster_path.startswith("http"):
                return self.poster_path
            return f"https://image.tmdb.org/t/p/w500{self.poster_path}"
        return None

    def to_dict(self):
        return {
            "id": str(self.id),
            "title": self.title,
            "overview": self.overview,
            "genres": self.genres or [],
            "year": self.year,
            "rating": self.rating,
            "popularity": self.popularity,
            "poster_url": self.poster_url,
            "runtime": self.runtime,
            "language": self.language,
            "tagline": self.tagline,
        }


class MovieRating(Base):
    __tablename__ = "movie_ratings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False)
    movie_id = Column(String(36), nullable=False)
    rating = Column(Float, nullable=False)
    review = Column(String(5000), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
