"""
Movies endpoints (SQLite sync version)
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database_sqlite import get_db
from app.models_sqlite import Movie

router = APIRouter()

@router.get("/")
def list_movies(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    genre: Optional[str] = None,
    year: Optional[int] = None,
    min_rating: Optional[float] = Query(None, ge=0, le=10),
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Movie).filter(Movie.is_active == True)
    if genre:
        query = query.filter(Movie.genres.contains(f'"{genre}"'))
    if year:
        query = query.filter(Movie.year == year)
    if min_rating:
        query = query.filter(Movie.rating >= min_rating)
    if search:
        query = query.filter(Movie.title.ilike(f"%{search}%"))

    total = query.count()
    movies = query.order_by(Movie.popularity.desc()).offset(skip).limit(limit).all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "results": [m.to_dict() for m in movies]
    }

@router.get("/genres")
def get_genres(db: Session = Depends(get_db)):
    movies = db.query(Movie).all()
    all_genres = set()
    for m in movies:
        if m.genres:
            all_genres.update(m.genres)
    return {"genres": sorted(list(all_genres)), "count": len(all_genres)}

@router.get("/popular")
def get_popular_movies(limit: int = Query(10, ge=1, le=50), db: Session = Depends(get_db)):
    movies = db.query(Movie).filter(Movie.is_active == True).order_by(Movie.popularity.desc()).limit(limit).all()
    return {"results": [m.to_dict() for m in movies]}

@router.get("/top-rated")
def get_top_rated(limit: int = Query(10, ge=1, le=50), db: Session = Depends(get_db)):
    movies = db.query(Movie).filter(
        Movie.is_active == True,
        Movie.rating.isnot(None)
    ).order_by(Movie.rating.desc()).limit(limit).all()
    return {"results": [m.to_dict() for m in movies]}

@router.post("/seed-demo")
def seed_demo_movies(db: Session = Depends(get_db)):
    """Carga películas de demo si la base está vacía."""
    count = db.query(Movie).count()
    if count > 0:
        return {"message": f"Ya existen {count} películas en la base de datos"}

    demo_movies = [
        {"title": "Inception", "year": 2010, "rating": 8.8, "popularity": 95.5, "genres": ["Ciencia Ficción", "Acción", "Thriller"], "overview": "Un ladrón que roba secretos corporativos a través del uso de la tecnología de sueños compartidos.", "language": "en"},
        {"title": "The Dark Knight", "year": 2008, "rating": 9.0, "popularity": 98.2, "genres": ["Acción", "Crimen", "Drama"], "overview": "Batman enfrenta al Joker, un criminal caótico.", "language": "en"},
        {"title": "Interstellar", "year": 2014, "rating": 8.7, "popularity": 92.1, "genres": ["Ciencia Ficción", "Drama", "Aventura"], "overview": "Un equipo de exploradores viaja a través de un agujero de gusano en el espacio.", "language": "en"},
        {"title": "Parasite", "year": 2019, "rating": 8.5, "popularity": 88.4, "genres": ["Thriller", "Drama", "Comedia"], "overview": "Una familia pobre se infiltra en la vida de una familia rica.", "language": "ko"},
        {"title": "The Matrix", "year": 1999, "rating": 8.7, "popularity": 90.3, "genres": ["Ciencia Ficción", "Acción"], "overview": "Un hacker descubre la verdadera naturaleza de su realidad.", "language": "en"},
        {"title": "Pulp Fiction", "year": 1994, "rating": 8.9, "popularity": 87.6, "genres": ["Crimen", "Drama"], "overview": "Las vidas de dos matones, un boxeador y otros personajes se entrelazan.", "language": "en"},
        {"title": "The Shawshank Redemption", "year": 1994, "rating": 9.3, "popularity": 91.2, "genres": ["Drama"], "overview": "Dos hombres encarcelados forjan una amistad a lo largo de años.", "language": "en"},
        {"title": "Spider-Man: Across the Spider-Verse", "year": 2023, "rating": 8.7, "popularity": 96.1, "genres": ["Animación", "Acción", "Aventura"], "overview": "Miles Morales viaja a través del multiverso.", "language": "en"},
        {"title": "Dune: Part Two", "year": 2024, "rating": 8.5, "popularity": 94.7, "genres": ["Ciencia Ficción", "Aventura", "Drama"], "overview": "Paul Atreides busca venganza contra los conspiradores que destruyeron a su familia.", "language": "en"},
        {"title": "Oppenheimer", "year": 2023, "rating": 8.4, "popularity": 93.8, "genres": ["Drama", "Historia", "Biográfico"], "overview": "La historia de J. Robert Oppenheimer y la creación de la bomba atómica.", "language": "en"},
        {"title": "Everything Everywhere All at Once", "year": 2022, "rating": 7.8, "popularity": 85.3, "genres": ["Aventura", "Comedia", "Ciencia Ficción"], "overview": "Una inmigrante china es arrastrada a una aventura salvaje.", "language": "en"},
        {"title": "The Godfather", "year": 1972, "rating": 9.2, "popularity": 86.5, "genres": ["Crimen", "Drama"], "overview": "El patriarca de una dinastía del crimen organiza la transferencia de poder.", "language": "en"},
    ]

    for m_data in demo_movies:
        movie = Movie(**m_data, is_active=True, source="demo")
        db.add(movie)
    db.commit()

    return {"message": f"Cargadas {len(demo_movies)} películas de demo"}


@router.get("/{movie_id}")
def get_movie(movie_id: str, db: Session = Depends(get_db)):
    movie = db.query(Movie).filter(Movie.id == movie_id, Movie.is_active == True).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Película no encontrada")
    return movie.to_dict()
