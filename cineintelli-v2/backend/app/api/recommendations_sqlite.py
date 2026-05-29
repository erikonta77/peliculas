"""
Recommendations endpoints (SQLite sync version)
"""
from typing import Optional
import random

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.auth_sqlite import get_current_active_user
from app.core.database_sqlite import get_db
from app.models_sqlite import Movie
from app.models_sqlite import User, UserProfile

router = APIRouter()

@router.get("/personalized")
def get_personalized_recommendations(
    count: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
        db.commit()

    query = db.query(Movie).filter(Movie.is_active == True)

    if profile.favorite_genres:
        # Simple genre matching
        all_movies = query.all()
        scored = []
        for m in all_movies:
            score = 0
            if m.rating:
                score += (m.rating / 10) * 0.4
            if m.popularity:
                score += min(m.popularity / 100, 1) * 0.3
            if m.genres and profile.favorite_genres:
                overlap = set(m.genres) & set(profile.favorite_genres)
                if overlap:
                    score += len(overlap) / len(set(m.genres) | set(profile.favorite_genres)) * 0.3
            scored.append((m, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        recommendations = [m[0] for m in scored[:count]]
    else:
        recommendations = query.order_by(Movie.popularity.desc()).limit(count).all()

    return {
        "recommendations": [m.to_dict() for m in recommendations],
        "count": len(recommendations),
        "profile_used": {
            "genres": profile.favorite_genres,
            "year_range": [profile.year_min, profile.year_max],
            "min_rating": profile.min_rating
        }
    }

@router.post("/feedback")
def submit_recommendation_feedback(
    movie_id: str,
    accepted: bool = True,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")

    if accepted:
        profile.recommendations_accepted += 1
    else:
        profile.recommendations_rejected += 1

    if not profile.watch_history:
        profile.watch_history = []
    profile.watch_history.append({"movie_id": movie_id, "accepted": accepted})
    db.commit()
    return {"message": "Feedback registrado"}

@router.get("/similar/{movie_id}")
def get_similar_movies(movie_id: str, count: int = Query(10, ge=1, le=20), db: Session = Depends(get_db)):
    movie = db.query(Movie).filter(Movie.id == movie_id, Movie.is_active == True).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Película no encontrada")

    if movie.genres:
        similar = db.query(Movie).filter(
            Movie.id != movie_id,
            Movie.is_active == True
        ).all()
        # Score by genre overlap
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

    similar = db.query(Movie).filter(Movie.id != movie_id, Movie.is_active == True).order_by(Movie.rating.desc()).limit(count).all()
    return {"movie": movie.to_dict(), "similar_movies": [m.to_dict() for m in similar], "count": len(similar)}

@router.get("/trending")
def get_trending_recommendations(
    genre: Optional[str] = None,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    query = db.query(Movie).filter(Movie.is_active == True, Movie.popularity.isnot(None))
    if genre:
        query = query.filter(Movie.genres.contains(f'"{genre}"'))
    movies = query.order_by(Movie.popularity.desc()).limit(limit).all()
    return {"trending": [m.to_dict() for m in movies], "genre_filter": genre}

@router.post("/roulette")
def cine_roulette(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()

    query = db.query(Movie).filter(Movie.is_active == True, Movie.rating >= 6.0)
    if profile and profile.favorite_genres:
        # Exclude favorite genres for surprise
        all_movies = query.all()
        candidates = [m for m in all_movies if not (m.genres and any(g in profile.favorite_genres for g in m.genres))]
        if candidates:
            return {"roulette": random.choice(candidates).to_dict(), "message": "¡Sorpresa!"}

    candidates = query.all()
    if candidates:
        return {"roulette": random.choice(candidates).to_dict(), "message": "¡Sorpresa!"}
    return {"roulette": None, "message": "No hay películas disponibles"}

from fastapi import HTTPException
