"""
Users endpoints (SQLite sync version)
"""
from typing import Optional, List
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.auth_sqlite import get_current_active_user
from app.core.database_sqlite import get_db
from app.models_sqlite import User, UserProfile

router = APIRouter()

class ProfileUpdate(BaseModel):
    favorite_genres: Optional[List[str]] = None
    year_min: Optional[int] = None
    year_max: Optional[int] = None
    min_rating: Optional[float] = None
    preferred_language: Optional[str] = None
    recommendations_count: Optional[int] = None

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
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)

    if profile_data.favorite_genres is not None:
        profile.favorite_genres = profile_data.favorite_genres
    if profile_data.year_min is not None:
        profile.year_min = profile_data.year_min
    if profile_data.year_max is not None:
        profile.year_max = profile_data.year_max
    if profile_data.min_rating is not None:
        profile.min_rating = profile_data.min_rating
    if profile_data.preferred_language is not None:
        profile.preferred_language = profile_data.preferred_language
    if profile_data.recommendations_count is not None:
        profile.recommendations_count = profile_data.recommendations_count

    db.commit()
    return {"message": "Perfil actualizado", "profile": {
        "favorite_genres": profile.favorite_genres,
        "year_min": profile.year_min,
        "year_max": profile.year_max,
        "min_rating": profile.min_rating,
        "preferred_language": profile.preferred_language,
    }}
