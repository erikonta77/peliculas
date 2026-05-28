"""
Modelos de usuario y perfil
"""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import ARRAY, Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    """Modelo de usuario."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Relación con perfil
    profile = relationship("UserProfile", back_populates="user", uselist=False)

    def __repr__(self):
        return f"<User {self.email}>"


class UserProfile(Base):
    """Perfil de preferencias del usuario para recomendaciones."""
    __tablename__ = "user_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)

    # Preferencias de recomendación
    favorite_genres = Column(ARRAY(String), default=[])
    year_min = Column(Integer, default=1900)
    year_max = Column(Integer, default=2100)
    min_rating = Column(Float, default=0.0)
    preferred_language = Column(String(10), default="any")
    recommendations_count = Column(Integer, default=10)

    # Historial y métricas
    watch_history = Column(JSONB, default=list)  # IDs de películas vistas
    ratings_given = Column(JSONB, default=dict)  # {movie_id: rating}
    recommendations_accepted = Column(Integer, default=0)
    recommendations_rejected = Column(Integer, default=0)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relación
    user = relationship("User", back_populates="profile")

    def to_recommendation_params(self) -> dict:
        """Convierte el perfil a parámetros para el motor de recomendaciones."""
        return {
            "genres": self.favorite_genres,
            "year_min": self.year_min,
            "year_max": self.year_max,
            "min_rating": self.min_rating,
            "language": self.preferred_language,
            "count": self.recommendations_count,
        }
