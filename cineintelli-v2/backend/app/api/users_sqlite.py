"""
Users endpoints (SQLite sync version)
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.auth_sqlite import get_current_active_user
from app.core.database_sqlite import get_db
from app.models_sqlite import User, UserProfile

router = APIRouter()

@router.get("/me")
def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "is_active": current_user.is_active,
    }

@router.get("/me/profile")
def get_user_profile(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
        db.commit()
    return {
        "favorite_genres": profile.favorite_genres or [],
        "year_min": profile.year_min,
        "year_max": profile.year_max,
        "min_rating": profile.min_rating,
        "preferred_language": profile.preferred_language,
        "recommendations_count": profile.recommendations_count,
    }

@router.put("/me/profile")
def update_user_profile(
    favorite_genres: list = None,
    year_min: int = None,
    year_max: int = None,
    min_rating: float = None,
    preferred_language: str = None,
    recommendations_count: int = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)

    if favorite_genres is not None:
        profile.favorite_genres = favorite_genres
    if year_min is not None:
        profile.year_min = year_min
    if year_max is not None:
        profile.year_max = year_max
    if min_rating is not None:
        profile.min_rating = min_rating
    if preferred_language is not None:
        profile.preferred_language = preferred_language
    if recommendations_count is not None:
        profile.recommendations_count = recommendations_count

    db.commit()
    return {"message": "Perfil actualizado", "profile": {
        "favorite_genres": profile.favorite_genres,
        "year_min": profile.year_min,
        "year_max": profile.year_max,
        "min_rating": profile.min_rating,
        "preferred_language": profile.preferred_language,
    }}
