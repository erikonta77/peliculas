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
    query = db.query(Movie).filter(Movie.is_active == True, Movie.vote_count >= 50)
    if genre:
        query = query.filter(Movie.genres.contains(f'"{genre}"'))
    if year:
        query = query.filter(Movie.year == year)
    if min_rating:
        query = query.filter(Movie.rating >= min_rating)
    if search:
        query = query.filter(Movie.title.ilike(f"%{search}%"))

    total = query.count()
    raw_movies = query.order_by(Movie.vote_count.desc(), Movie.rating.desc()).offset(skip).limit(limit * 2).all()
    seen = set()
    unique_movies = []
    for m in raw_movies:
        key = m.tmdb_id or f"{m.title}_{m.year}"
        if key not in seen:
            seen.add(key)
            unique_movies.append(m)
    movies = unique_movies[:limit]

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
def get_popular_movies(limit: int = Query(50, ge=1, le=100), db: Session = Depends(get_db)):
    raw_movies = db.query(Movie).filter(
        Movie.is_active == True,
        Movie.vote_count >= 50
    ).order_by(Movie.vote_count.desc(), Movie.rating.desc()).limit(max(limit * 2, 100)).all()
    seen = set()
    unique_movies = []
    for m in raw_movies:
        key = m.tmdb_id or f"{m.title}_{m.year}"
        if key not in seen:
            seen.add(key)
            unique_movies.append(m)
    movies = unique_movies[:limit]
    return {"results": [m.to_dict() for m in movies]}

@router.get("/top-rated")
def get_top_rated(limit: int = Query(10, ge=1, le=50), db: Session = Depends(get_db)):
    movies = db.query(Movie).filter(
        Movie.is_active == True,
        Movie.rating.isnot(None),
        Movie.vote_count >= 50
    ).order_by(Movie.vote_count.desc(), Movie.rating.desc()).limit(limit).all()
    return {"results": [m.to_dict() for m in movies]}

@router.post("/seed-demo")
def seed_demo_movies(db: Session = Depends(get_db)):
    """Carga películas de demo si la base está vacía o tiene pocas películas."""
    import random
    count = db.query(Movie).count()
    if count >= 1000:
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

    # Evitar duplicados por título
    existing_titles = set(m.title for m in db.query(Movie).all())
    for m in demo_movies:
        existing_titles.add(m["title"])

    # Generar variaciones de títulos de alta calidad hasta llegar a 1050
    adj_es = ["Secreto", "Último", "Misterioso", "Perdido", "Eterno", "Oscuro", "Silencioso", "Brillante", "Salvaje", "Invisible", "Vengador", "Legendario", "Destino", "Origen", "Imperio", "Renacimiento", "Poder", "Espejo", "Camino", "Viaje"]
    noun_es = ["del Tiempo", "en el Espacio", "de la Noche", "del Destino", "bajo la Lluvia", "de Cristal", "del Guerrero", "del Viento", "en la Niebla", "de Arena", "del Laberinto", "del Silencio", "del Fuego", "de las Sombras", "de la Razón", "de las Estrellas", "del Infinito", "en el Abismo", "del Trono", "del Templo"]
    
    genres_pool = [
        ["Ciencia Ficción", "Acción"],
        ["Drama"],
        ["Comedia", "Romance"],
        ["Terror", "Misterio"],
        ["Thriller", "Crimen", "Acción"],
        ["Aventura", "Fantasía"],
        ["Animación", "Familiar"],
        ["Historia", "Drama"],
        ["Biográfico", "Drama"],
        ["Música", "Drama"],
        ["Documental"],
        ["Western"]
    ]
    
    overviews = [
        "Un grupo de valientes exploradores se adentra en un misterio ancestral que podría cambiar el destino de la humanidad.",
        "Una historia conmovedora sobre la superación, la amistad y los lazos familiares que trascienden el tiempo.",
        "Una divertida comedia de enredos donde los malentendidos amorosos desatan situaciones desternillantes.",
        "En un pueblo apartado, extraños sucesos y desapariciones apuntan a una antigua maldición oculta en el bosque.",
        "Un thriller tenso y trepidante donde un detective retirado debe resolver un último caso lleno de giros inesperados.",
        "Una aventura épica en un reino de fantasía donde un joven héroe busca recuperar un objeto sagrado.",
        "Una enternecedora película animada que nos enseña el valor de la lealtad y el coraje frente a la adversidad.",
        "Basada en hechos reales, narra los conflictos y pasiones que definieron una época crucial de la historia.",
        "Un viaje biográfico íntimo que explora los momentos clave y los sacrificios de una figura legendaria.",
        "La música y el drama se entrelazan en la emocionante trayectoria de un artista que busca su propia voz.",
        "Una investigación profunda y reveladora que expone los secretos mejor guardados de nuestro planeta.",
        "Un implacable sheriff cabalga por el desierto persiguiendo a una banda de forajidos en busca de justicia."
    ]
    
    taglines = [
        "El destino está en juego.",
        "Una historia que nunca olvidarás.",
        "Risas aseguradas de principio a fin.",
        "No entres al bosque después del anochecer.",
        "Cada pista tiene un precio.",
        "La aventura de tu vida comienza hoy.",
        "Descubre la magia en tu interior.",
        "La historia la escriben los sobrevivientes.",
        "Detrás de la leyenda hay un hombre.",
        "La melodía del alma.",
        "La verdad que nadie quiere ver.",
        "Solo un hombre puede hacer justicia."
    ]

    random.seed(42)
    counter = 1
    while len(demo_movies) < 1050:
        a = random.choice(adj_es)
        n = random.choice(noun_es)
        title = f"El {a} {n} {counter}"
        counter += 1
        if title in existing_titles:
            continue
        existing_titles.add(title)
        
        idx = random.randint(0, len(genres_pool) - 1)
        genres = genres_pool[idx]
        overview = overviews[idx]
        tagline = taglines[idx]
        
        year = random.randint(1980, 2025)
        rating = round(random.uniform(5.5, 9.5), 1)
        popularity = round(random.uniform(10.0, 95.0), 1)
        runtime = random.randint(80, 180)
        language = random.choice(["es", "en", "fr", "de"])
        
        demo_movies.append({
            "title": title,
            "year": year,
            "rating": rating,
            "popularity": popularity,
            "genres": genres,
            "overview": overview,
            "language": language,
            "runtime": runtime,
            "tagline": tagline
        })

    for m_data in demo_movies:
        movie = Movie(**m_data, is_active=True, source="demo")
        db.add(movie)
    db.commit()

    return {"message": f"Se completó la base de datos. Total películas cargadas: {db.query(Movie).count()}"}


@router.get("/onboarding")
def get_onboarding_movies(limit: int = Query(60, ge=10, le=100), db: Session = Depends(get_db)):
    popular = db.query(Movie).filter(
        Movie.is_active == True,
        Movie.vote_count >= 50
    ).order_by(Movie.vote_count.desc(), Movie.rating.desc()).limit(150).all()
    
    genres = ["Ciencia Ficción", "Acción", "Drama", "Comedia", "Thriller", "Aventura"]
    genre_movies = []
    for g in genres:
        m_list = db.query(Movie).filter(
            Movie.is_active == True,
            Movie.vote_count >= 50,
            Movie.genres.contains(f'"{g}"')
        ).order_by(Movie.vote_count.desc(), Movie.rating.desc()).limit(30).all()
        genre_movies.extend(m_list)
        
    decade_movies = []
    for start_year in [1980, 1990, 2000, 2010, 2020]:
        m_list = db.query(Movie).filter(
            Movie.is_active == True,
            Movie.vote_count >= 50,
            Movie.year >= start_year,
            Movie.year < start_year + 10
        ).order_by(Movie.vote_count.desc(), Movie.rating.desc()).limit(30).all()
        decade_movies.extend(m_list)
        
    all_candidates = popular + genre_movies + decade_movies
    
    seen = set()
    unique_candidates = []
    for m in all_candidates:
        key = m.tmdb_id or f"{m.title}_{m.year}"
        if key not in seen:
            seen.add(key)
            unique_candidates.append(m)
            
    import random
    random.shuffle(unique_candidates)
    selected = unique_candidates[:limit]
    
    return {"results": [m.to_dict() for m in selected]}


@router.post("/sync-tmdb")
def sync_tmdb_movies(pages: int = Query(5, ge=1, le=20), db: Session = Depends(get_db)):
    from app.core.config import settings
    import urllib.request
    import json
    import random
    import re
    
    api_key = settings.TMDB_API_KEY
    total_synced = 0
    
    if api_key:
        GENRE_MAP = {
            28: "Acción", 12: "Aventura", 16: "Animación", 35: "Comedia", 80: "Crimen",
            99: "Documental", 18: "Drama", 10751: "Familiar", 14: "Fantasía",
            36: "Historia", 27: "Terror", 10402: "Música", 9648: "Misterio",
            10749: "Romance", 878: "Ciencia Ficción", 10770: "TV", 53: "Thriller",
            10752: "Guerra", 37: "Western"
        }
        try:
            for page in range(1, pages + 1):
                url = f"https://api.themoviedb.org/3/movie/popular?api_key={api_key}&page={page}"
                req = urllib.request.Request(url, headers={"Accept": "application/json"})
                with urllib.request.urlopen(req) as res:
                    data = json.loads(res.read().decode("utf-8"))
                    results = data.get("results", [])
                    for m_data in results:
                        existing = db.query(Movie).filter(Movie.tmdb_id == m_data["id"]).first()
                        
                        year = None
                        release_date_obj = None
                        rd_str = m_data.get("release_date")
                        if rd_str:
                            try:
                                year = int(rd_str[:4])
                                from datetime import datetime
                                release_date_obj = datetime.strptime(rd_str, "%Y-%m-%d")
                            except (ValueError, IndexError):
                                pass
                                
                        genres = [GENRE_MAP.get(gid, "Otro") for gid in m_data.get("genre_ids", []) if gid in GENRE_MAP]
                        
                        raw_title = m_data.get("title", "")
                        clean_title = re.sub(r"\s+\d+$", "", raw_title).strip()
                        
                        if existing:
                            existing.popularity = m_data.get("popularity", 0.0)
                            existing.rating = m_data.get("vote_average", 0.0)
                            existing.vote_count = m_data.get("vote_count", 0)
                        else:
                            new_movie = Movie(
                                tmdb_id=m_data["id"],
                                title=clean_title,
                                overview=m_data.get("overview", ""),
                                poster_path=m_data.get("poster_path"),
                                backdrop_path=m_data.get("backdrop_path"),
                                release_date=release_date_obj,
                                year=year,
                                rating=m_data.get("vote_average"),
                                vote_count=m_data.get("vote_count", 0),
                                popularity=m_data.get("popularity", 0.0),
                                genres=genres,
                                language=m_data.get("original_language"),
                                original_language=m_data.get("original_language"),
                                source="tmdb"
                            )
                            db.add(new_movie)
                            total_synced += 1
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"[sync-tmdb] Error syncing movies from TMDB: {e}")
            api_key = None
            
    if not api_key:
        print("[sync-tmdb] No active/working TMDB API key. Skipping mock generation.")
        
    final_count = db.query(Movie).count()
    print(f"Total movies in DB: {final_count}")
    return {"message": f"Sincronización completada. Sincronizadas: {total_synced} películas. Total en BD: {final_count}", "synced_count": total_synced}


@router.get("/{movie_id}")
def get_movie(movie_id: str, db: Session = Depends(get_db)):
    movie = db.query(Movie).filter(Movie.id == movie_id, Movie.is_active == True).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Película no encontrada")
    return movie.to_dict()
