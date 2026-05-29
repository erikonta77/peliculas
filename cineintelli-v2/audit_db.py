import sqlite3
import json
import collections

DB_PATH = "backend/cineintelli.db"

def audit():
    print("====================================================")
    print("    AUDITORÍA DE BASE DE DATOS SQLITE - CINEINTELLI")
    print("====================================================\n")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
    except Exception as e:
        print(f"Error conectando a la BD: {e}")
        return

    # 1. ESTADÍSTICAS GENERALES
    print("--- 1. ESTADÍSTICAS GENERALES ---")
    cursor.execute("SELECT COUNT(*) FROM movies")
    total_movies = cursor.fetchone()[0]
    print(f"Total de películas en BD: {total_movies}")
    
    cursor.execute("SELECT COUNT(*) FROM movies WHERE tmdb_id IS NOT NULL AND tmdb_id != 0")
    valid_tmdb = cursor.fetchone()[0]
    print(f"Películas con tmdb_id válido: {valid_tmdb}")
    
    cursor.execute("SELECT COUNT(*) FROM movies WHERE title IS NULL OR title = '' OR length(title) < 2")
    invalid_title = cursor.fetchone()[0]
    print(f"Películas con título vacío o sospechoso: {invalid_title}")
    
    cursor.execute("SELECT COUNT(*) FROM movies WHERE genres IS NULL OR genres = '[]' OR genres = ''")
    empty_genres = cursor.execute("SELECT COUNT(*) FROM movies WHERE genres IS NULL OR json_array_length(genres) = 0").fetchone()[0]
    print(f"Películas con géneros vacíos (JSON vacío): {empty_genres}")
    
    cursor.execute("SELECT COUNT(*) FROM movies WHERE rating IS NULL OR rating = 0")
    null_rating = cursor.fetchone()[0]
    print(f"Películas con rating NULL o 0.0: {null_rating}")
    
    cursor.execute("SELECT COUNT(*) FROM movies WHERE vote_count < 10")
    low_votes = cursor.fetchone()[0]
    print(f"Películas con vote_count < 10: {low_votes}")
    print()

    # 2. DETECTAR DUPLICADOS
    print("--- 2. DETECTAR DUPLICADOS ---")
    # A) Por tmdb_id
    cursor.execute("""
        SELECT tmdb_id, COUNT(*) 
        FROM movies 
        WHERE tmdb_id IS NOT NULL 
        GROUP BY tmdb_id 
        HAVING COUNT(*) > 1
    """)
    dup_tmdb_rows = cursor.fetchall()
    print(f"Número de tmdb_id duplicados: {len(dup_tmdb_rows)}")
    if dup_tmdb_rows:
        print("Ejemplos de duplicados por tmdb_id:")
        for tmdb_id, count in dup_tmdb_rows[:3]:
            cursor.execute("SELECT title, year FROM movies WHERE tmdb_id = ?", (tmdb_id,))
            titles = [f"{row[0]} ({row[1]})" for row in cursor.fetchall()]
            print(f"  - tmdb_id {tmdb_id}: {count} ocurrencias -> {', '.join(titles)}")
            
    # B) Por title + year
    cursor.execute("""
        SELECT title, year, COUNT(*) 
        FROM movies 
        GROUP BY title, year 
        HAVING COUNT(*) > 1
    """)
    dup_title_rows = cursor.fetchall()
    print(f"Número de combinaciones title + year duplicadas: {len(dup_title_rows)}")
    if dup_title_rows:
        print("Ejemplos de duplicados por title + year:")
        for title, year, count in dup_title_rows[:3]:
            print(f"  - '{title}' ({year}): {count} ocurrencias")
    print()

    # 3. CALIDAD DE DATOS
    print("--- 3. CALIDAD DE DATOS ---")
    
    # 10 películas RANDOM
    print("10 películas RANDOM:")
    cursor.execute("SELECT title, year, rating, vote_count, genres FROM movies ORDER BY random() LIMIT 10")
    for i, row in enumerate(cursor.fetchall()):
        print(f"  {i+1:2d}. '{row[0]}' ({row[1]}) | Rating: {row[2]} | Votos: {row[3]} | Géneros: {row[4]}")
    print()
    
    # 10 películas con rating más alto
    print("10 películas con RATING MÁS ALTO (en base de datos sin mapeo api):")
    cursor.execute("SELECT title, year, rating, vote_count FROM movies ORDER BY rating DESC, vote_count DESC LIMIT 10")
    for i, row in enumerate(cursor.fetchall()):
        print(f"  {i+1:2d}. '{row[0]}' ({row[1]}) | Rating: {row[2]} | Votos: {row[3]}")
    print()
    
    # 10 películas con rating más bajo
    print("10 películas con RATING MÁS BAJO:")
    cursor.execute("SELECT title, year, rating, vote_count FROM movies WHERE rating IS NOT NULL ORDER BY rating ASC LIMIT 10")
    for i, row in enumerate(cursor.fetchall()):
        print(f"  {i+1:2d}. '{row[0]}' ({row[1]}) | Rating: {row[2]} | Votos: {row[3]}")
    print()

    # 4. PROBLEMA DE VISIBILIDAD & FILTRADO
    print("--- 4. PROBLEMA DE VISIBILIDAD ---")
    cursor.execute("SELECT COUNT(*) FROM movies WHERE is_active = 1")
    active_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM movies WHERE is_active = 1 AND vote_count >= 50")
    vis_count = cursor.fetchone()[0]
    
    print(f"Películas activas totales: {active_count}")
    print(f"Películas que cumplen la condición 'vote_count >= 50': {vis_count}")
    print(f"Películas ocultas/filtradas debido a 'vote_count < 50': {active_count - vis_count}")
    
    # Simular /movies/popular
    cursor.execute("SELECT COUNT(*) FROM movies WHERE is_active = 1 AND vote_count >= 50")
    pop_sim = cursor.fetchone()[0]
    print(f"Resultado de simulación popular (/movies/popular): devolverá {min(pop_sim, 50)} películas de un pool total elegible de {pop_sim}.")
    print()

    # 5. DISTRIBUCIÓN DE DATOS
    print("--- 5. DISTRIBUCIÓN DE DATOS ---")
    
    # Histograma aproximado de ratings
    cursor.execute("SELECT rating FROM movies WHERE rating IS NOT NULL")
    ratings = [row[0] for row in cursor.fetchall()]
    buckets = collections.defaultdict(int)
    for r in ratings:
        bucket = int(r)
        buckets[bucket] += 1
    print("Histograma de ratings (Raw DB):")
    for bucket in sorted(buckets.keys()):
        count = buckets[bucket]
        bar = "*" * int(count / 100) if count >= 100 else "."
        print(f"  [{bucket}.0 - {bucket}.9]: {count:4d} {bar}")
    print()
        
    # Conteo por género
    cursor.execute("SELECT genres FROM movies WHERE genres IS NOT NULL")
    genres_counts = collections.defaultdict(int)
    for row in cursor.fetchall():
        try:
            gs = json.loads(row[0]) if isinstance(row[0], str) else row[0]
            if gs:
                for g in gs:
                    genres_counts[g] += 1
        except Exception:
            pass
    print("Conteo de películas por género:")
    for g, count in sorted(genres_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {g:18s}: {count}")
    print()
        
    # Conteo por año (décadas)
    cursor.execute("SELECT year FROM movies WHERE year IS NOT NULL")
    years = [row[0] for row in cursor.fetchall()]
    decades = collections.defaultdict(int)
    for y in years:
        decade = (y // 10) * 10
        decades[decade] += 1
    print("Conteo de películas por década:")
    for d in sorted(decades.keys()):
        print(f"  - {d}s: {decades[d]}")
    print()

    conn.close()

if __name__ == "__main__":
    audit()
