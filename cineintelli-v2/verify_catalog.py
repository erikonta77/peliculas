import urllib.request
import json
import sqlite3
import sys
import re

BASE_URL = "http://127.0.0.1:8000/api/v1"
DB_PATH = "backend/cineintelli.db"

def verify():
    print("=== INICIANDO VALIDACIÓN DE CATÁLOGO Y UX ===")
    
    # 1. Verificar número total de películas en base de datos > 1000
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM movies")
        count = cursor.fetchone()[0]
        conn.close()
        print(f"[OK] Total películas en la base de datos: {count} (> 1000)")
        if count <= 1000:
            print("ERROR: Menos de 1000 películas en BD!")
            sys.exit(1)
    except Exception as e:
        print(f"ERROR conectando a SQLite: {e}")
        sys.exit(1)

    # 2. Verificar que no hay duplicados en populares
    try:
        req = urllib.request.Request(f"{BASE_URL}/movies/popular?limit=50", method="GET")
        with urllib.request.urlopen(req) as res:
            data = json.loads(res.read().decode("utf-8"))
            results = data.get("results", [])
            print(f"Popular movies count returned: {len(results)}")
            
            seen = set()
            duplicates = []
            for m in results:
                key = m.get("tmdb_id") or f"{m.get('title')}_{m.get('year')}"
                if key in seen:
                    duplicates.append(m.get("title"))
                seen.add(key)
                
            if duplicates:
                print(f"ERROR: Encontrados duplicados en populares: {duplicates}")
                sys.exit(1)
            print("[OK] No hay duplicados en populares.")
    except Exception as e:
        print(f"ERROR en populares: {e}")
        sys.exit(1)

    # 3. Verificar que no hay duplicados en recomendaciones
    try:
        req = urllib.request.Request(f"{BASE_URL}/recommendations/personalized?count=24", method="GET")
        with urllib.request.urlopen(req) as res:
            results = json.loads(res.read().decode("utf-8"))
            print(f"Personalized recommendations count returned: {len(results)}")
            
            seen = set()
            duplicates = []
            for m in results:
                key = m.get("tmdb_id") or f"{m.get('title')}_{m.get('year')}"
                if key in seen:
                    duplicates.append(m.get("title"))
                seen.add(key)
                
            if duplicates:
                print(f"ERROR: Encontrados duplicados en recomendaciones: {duplicates}")
                sys.exit(1)
            print("[OK] No hay duplicados en recomendaciones.")
    except Exception as e:
        print(f"ERROR en recomendaciones: {e}")
        sys.exit(1)

    # 4. Verificar que el onboarding devuelve >= 40 películas únicas
    try:
        req = urllib.request.Request(f"{BASE_URL}/movies/onboarding?limit=60", method="GET")
        with urllib.request.urlopen(req) as res:
            data = json.loads(res.read().decode("utf-8"))
            results = data.get("results", [])
            print(f"Onboarding movies count returned: {len(results)}")
            
            seen = set()
            for m in results:
                key = m.get("tmdb_id") or f"{m.get('title')}_{m.get('year')}"
                seen.add(key)
                
            if len(seen) < 40:
                print(f"ERROR: Onboarding devolvió menos de 40 películas únicas! Únicas: {len(seen)}")
                sys.exit(1)
            print(f"[OK] Onboarding devolvió {len(seen)} películas únicas (>= 40).")
    except Exception as e:
        print(f"ERROR en onboarding: {e}")
        sys.exit(1)

    # 5. Verificar que no hay títulos con números basura al final
    try:
        # Consultar varios títulos de la BD
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT title FROM movies LIMIT 200")
        titles = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        # También chequear los del API
        req = urllib.request.Request(f"{BASE_URL}/movies/popular?limit=50", method="GET")
        with urllib.request.urlopen(req) as res:
            data = json.loads(res.read().decode("utf-8"))
            titles.extend([m.get("title") for m in data.get("results", [])])
            
        trash_titles = []
        for t in titles:
            if re.search(r"\s+\d+$", t):
                trash_titles.append(t)
                
        if trash_titles:
            print(f"ERROR: Encontrados títulos con números basura al final: {trash_titles[:10]}")
            sys.exit(1)
        print("[OK] No se encontraron títulos con números basura al final (todos normalizados).")
    except Exception as e:
        print(f"ERROR verificando títulos basura: {e}")
        sys.exit(1)

    print("\n=== ¡TODAS LAS VERIFICACIONES DEL CATÁLOGO PASARON CON ÉXITO! ===")

if __name__ == "__main__":
    verify()
