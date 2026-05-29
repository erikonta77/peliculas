import urllib.request
import json
import sqlite3
import sys

BASE_URL = "http://127.0.0.1:8000/api/v1"
DB_PATH = "backend/cineintelli.db"

def verify():
    print("=== INICIANDO VALIDACIÓN DE CALIDAD DE PELÍCULAS ===")
    
    # 1. Obtener películas populares de la API
    try:
        req = urllib.request.Request(f"{BASE_URL}/movies/popular?limit=100", method="GET")
        with urllib.request.urlopen(req) as res:
            data = json.loads(res.read().decode("utf-8"))
            movies = data.get("results", [])
    except Exception as e:
        print(f"ERROR llamando al API: {e}")
        sys.exit(1)
        
    print(f"Obtenidas {len(movies)} películas populares de la API.")
    
    if not movies:
        print("ERROR: No se obtuvieron películas de la API!")
        sys.exit(1)
        
    # 2. Validar que ninguna película tenga rating > 9.2
    ratings = []
    corrupt_titles = []
    
    for m in movies:
        title = m.get("title")
        display_title = m.get("display_title")
        rating = m.get("rating")
        vote_count = m.get("vote_count", 0)
        
        if rating is not None:
            ratings.append(rating)
            if rating > 9.2:
                print(f"ERROR: Película '{title}' tiene rating irreal: {rating} (> 9.2)!")
                sys.exit(1)
                
        # Verificar caracteres corruptos (ej: acentos rotos, símbolos raros)
        if any(char in title or char in (display_title or "") for char in ["\ufffd", "Ã³", "Ã¡", "Ã©", "Ã", "Â"]):
            corrupt_titles.append(title)
            
    print("[OK] Ninguna película tiene rating mayor a 9.2.")
    
    # 3. Validar distribución de ratings (promedio entre 6.5 y 8.0)
    if ratings:
        avg_rating = sum(ratings) / len(ratings)
        print(f"Promedio de ratings en películas populares: {avg_rating:.2f}")
        if not (6.5 <= avg_rating <= 8.0):
            print(f"ERROR: Promedio de ratings fuera del rango realista (6.5 - 8.0): {avg_rating:.2f}!")
            sys.exit(1)
        print("[OK] Distribución de ratings realista (promedio entre 6.5 y 8.0).")
    else:
        print("ERROR: No se encontraron ratings en las películas!")
        sys.exit(1)
        
    # 4. Validar caracteres corruptos
    if corrupt_titles:
        print(f"ERROR: Se encontraron títulos con caracteres corruptos: {corrupt_titles}")
        sys.exit(1)
    print("[OK] No se detectaron caracteres corruptos en los títulos.")
    
    # 5. Validar títulos conocidos (ej: Inception, Matrix, Interstellar)
    # Busquemos Inception, Matrix o similares en toda la BD
    try:
        req_search = urllib.request.Request(f"{BASE_URL}/movies/?search=Inception", method="GET")
        with urllib.request.urlopen(req_search) as res:
            search_data = json.loads(res.read().decode("utf-8"))
            results = search_data.get("results", [])
            for m in results:
                if "Inception" in m.get("title") or "Inception" in m.get("original_title"):
                    print(f"[OK] Película Inception encontrada con formato correcto:")
                    print(f"     title: {m.get('title')}")
                    print(f"     display_title: {m.get('display_title')}")
                    print(f"     original_title: {m.get('original_title')}")
    except Exception as e:
        print(f"ERROR buscando Inception: {e}")
        
    # 6. Imprimir ejemplo de 10 películas con títulos y ratings corregidos
    print("\n=== EJEMPLO DE 10 PELÍCULAS DE LA API CON RATINGS Y TÍTULOS CORREGIDOS ===")
    sample_movies = movies[:10]
    for i, m in enumerate(sample_movies):
        print(f"{i+1:2d}. Título: {m.get('title')}")
        print(f"    Display: {m.get('display_title')}")
        print(f"    Original: {m.get('original_title')}")
        print(f"    Rating: {m.get('rating')} | Votos: {m.get('vote_count', 0)}")
        print("-" * 50)
        
    print("\n=== ¡TODAS LAS VERIFICACIONES DE CALIDAD PASARON CON ÉXITO! ===")

if __name__ == "__main__":
    verify()
