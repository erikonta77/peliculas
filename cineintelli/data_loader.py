"""
CineIntelli - Carga y preprocesamiento de datasets.

Lee archivos CSV o JSON de MovieLens y/o TMDB, los limpia,
normaliza géneros y expone una lista de objetos Pelicula listos
para el motor de recomendaciones.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Dict, List

import pandas as pd
import numpy as np

from models import Pelicula


# ---------------------------------------------------------------------------
# Constantes de normalización
# ---------------------------------------------------------------------------

MAPEO_COLUMNAS: Dict[str, str] = {
    "title": "titulo",
    "titulo": "titulo",
    "movie_title": "titulo",
    "genres": "generos",
    "generos": "generos",
    "movie_genre": "generos",
    "release_date": "anio",
    "anio": "anio",
    "movie_release_date": "anio",
    "vote_average": "puntuacion",
    "puntuacion": "puntuacion",
    "movie_vote": "puntuacion",
    "popularity": "popularidad",
    "popularidad": "popularidad",
    "movie_popularity": "popularidad",
    "original_language": "idioma",
    "idioma": "idioma",
    "movie_language": "idioma",
    "overview": "descripcion",
    "descripcion": "descripcion",
    "movie_overview": "descripcion",
    "vote_count": "votos",
    "votos": "votos",
    "movie_vote_count": "votos",
    "id": "id",
    "movie_id": "id",
}

MAPEO_GENEROS: Dict[str, str] = {
    "action": "Acción",
    "adventure": "Aventura",
    "animation": "Animación",
    "comedy": "Comedia",
    "crime": "Crimen",
    "documentary": "Documental",
    "drama": "Drama",
    "fantasy": "Fantasía",
    "horror": "Terror",
    "history": "Historia",
    "music": "Música",
    "mystery": "Misterio",
    "romance": "Romance",
    "science fiction": "Ciencia Ficción",
    "sci-fi": "Ciencia Ficción",
    "scifi": "Ciencia Ficción",
    "sci fi": "Ciencia Ficción",
    "thriller": "Thriller",
    "western": "Western",
    "family": "Familiar",
    "biography": "Biográfico",
    "sport": "Deportes",
    "sports": "Deportes",
    "war": "Guerra",
    "tv movie": "Telefilme",
    "foreign": "Extranjero",
}

GENEROS_CANONICOS: set[str] = {
    "Acción", "Aventura", "Animación", "Comedia", "Crimen", "Documental",
    "Drama", "Fantasía", "Terror", "Historia", "Música", "Misterio",
    "Romance", "Ciencia Ficción", "Thriller", "Western", "Familiar",
    "Biográfico", "Deportes", "Guerra",
}

URL_DATASET_EJEMPLO = (
    "https://raw.githubusercontent.com/YBI-Foundation/Dataset/main/"
    "Movies%20Recommendation.csv"
)


# ---------------------------------------------------------------------------
# Funciones auxiliares privadas
# ---------------------------------------------------------------------------

def _normalizar_nombre_columna(nombre: str) -> str:
    """Mapea un nombre de columna crudo al nombre canónico del sistema."""
    return MAPEO_COLUMNAS.get(str(nombre).strip().lower(), nombre)


def _extraer_generos(valor: Any) -> List[str]:
    """
    Extrae una lista de géneros a partir de diversos formatos de entrada.

    Soporta:
    - Pipe-separated string (MovieLens): "Action|Adventure"
    - JSON string con lista de objetos (TMDB): '[{"name": "Action"}, ...]'
    - Espacios como separadores con reconocimiento de substrings
    - Lista de strings
    - String simple
    """
    if pd.isna(valor):
        return []

    if isinstance(valor, str):
        valor = valor.strip()
        if not valor:
            return []
        if valor.startswith("["):
            try:
                parsed = json.loads(valor)
                if isinstance(parsed, list):
                    nombres = []
                    for item in parsed:
                        if isinstance(item, dict):
                            nombres.append(str(item.get("name", "")))
                        elif isinstance(item, str):
                            nombres.append(item)
                    return nombres
            except json.JSONDecodeError:
                pass
        if "|" in valor:
            return valor.split("|")

        # Fallback: reconocer géneros conocidos como substrings
        # Se ordenan por longitud descendente para priorizar matches largos
        # (ej. "science fiction" antes que "fiction")
        texto = valor.lower()
        encontrados: List[str] = []
        for ingles in sorted(MAPEO_GENEROS.keys(), key=len, reverse=True):
            if ingles in texto:
                encontrados.append(MAPEO_GENEROS[ingles])
                texto = texto.replace(ingles, " ")
        return encontrados

    if isinstance(valor, list):
        return [str(v) for v in valor]

    return []


def _normalizar_genero(genero: str) -> str:
    """Traduce un género crudo al catálogo canónico en español."""
    clave = str(genero).strip().lower()
    return MAPEO_GENEROS.get(clave, genero.strip())


def _filtrar_generos_canonicos(generos: List[str]) -> List[str]:
    """
    Normaliza géneros al catálogo canónico.

    Si algún género coincide con el catálogo canónico se conservan solo esos;
    de lo contrario se retornan los géneros normalizados originales para
    no perder la película por falta de mapeo exacto.
    """
    normalizados = [_normalizar_genero(g) for g in generos]
    canonicos = [g for g in normalizados if g in GENEROS_CANONICOS]
    return canonicos if canonicos else normalizados


def _limpiar_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Limpia el DataFrame crudo y retorna el DataFrame limpio junto con estadísticas.
    """
    stats: Dict[str, Any] = {
        "filas_originales": len(df),
        "columnas_originales": list(df.columns),
    }

    # Normalizar nombres de columnas
    df = df.rename(columns=lambda c: _normalizar_nombre_columna(c)).copy()
    print(f"[data_loader] Columnas detectadas: {list(df.columns)}")

    # Asegurar columnas requeridas
    requeridas = {"id", "titulo", "generos", "anio", "puntuacion",
                  "popularidad", "idioma", "descripcion", "votos"}
    faltantes = requeridas - set(df.columns)
    if faltantes:
        raise ValueError(f"Faltan columnas requeridas: {sorted(faltantes)}")

    # Normalizar tipos y extraer año
    df["id"] = pd.to_numeric(df["id"], errors="coerce").fillna(-1).astype(int)
    df["titulo"] = df["titulo"].astype(str)
    df["generos"] = df["generos"].apply(_extraer_generos)

    if pd.api.types.is_string_dtype(df["anio"]):
        df["anio"] = pd.to_datetime(df["anio"], errors="coerce", dayfirst=True).dt.year
    df["anio"] = pd.to_numeric(df["anio"], errors="coerce")

    for col_num in ("puntuacion", "popularidad", "votos"):
        df[col_num] = pd.to_numeric(df[col_num], errors="coerce")

    df["idioma"] = df["idioma"].astype(str)
    df["descripcion"] = df["descripcion"].astype(str)

    # Limpiar nulos
    nulos_antes = int(df.isnull().sum().sum())
    mediana_puntuacion = df["puntuacion"].median()
    mediana_popularidad = df["popularidad"].median()
    mediana_votos = df["votos"].median()
    mediana_anio = df["anio"].median()

    df["puntuacion"] = df["puntuacion"].fillna(mediana_puntuacion if pd.notna(mediana_puntuacion) else 0.0)
    df["popularidad"] = df["popularidad"].fillna(mediana_popularidad if pd.notna(mediana_popularidad) else 0.0)
    df["votos"] = df["votos"].fillna(int(mediana_votos) if pd.notna(mediana_votos) else 0)
    df["anio"] = df["anio"].fillna(int(mediana_anio) if pd.notna(mediana_anio) else 0).astype(int)
    df["idioma"] = df["idioma"].replace("nan", "Desconocido").fillna("Desconocido")
    df["descripcion"] = df["descripcion"].replace("nan", "Desconocido").fillna("Desconocido")
    df["titulo"] = df["titulo"].replace("nan", "Desconocido").fillna("Desconocido")

    nulos_despues = int(df.isnull().sum().sum())

    # Normalizar géneros al catálogo canónico
    df["generos"] = df["generos"].apply(lambda g: _filtrar_generos_canonicos(g) if isinstance(g, list) else [])

    # Eliminar duplicados por título + año
    duplicados_antes = len(df)
    df = df.drop_duplicates(subset=["titulo", "anio"], keep="first")
    duplicados_eliminados = duplicados_antes - len(df)

    stats.update({
        "filas_finales": len(df),
        "nulos_antes": nulos_antes,
        "nulos_despues": nulos_despues,
        "duplicados_eliminados": duplicados_eliminados,
        "mediana_puntuacion": float(mediana_puntuacion) if pd.notna(mediana_puntuacion) else 0.0,
        "mediana_popularidad": float(mediana_popularidad) if pd.notna(mediana_popularidad) else 0.0,
        "mediana_votos": int(mediana_votos) if pd.notna(mediana_votos) else 0,
    })

    return df, stats


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def cargar_dataset(ruta: str) -> List[Pelicula]:
    """
    Carga un dataset de películas desde CSV o JSON y retorna objetos Pelicula limpios.

    Detecta automáticamente el formato por extensión, normaliza columnas
    de MovieLens/TMDB, limpia nulos, elimina duplicados y traduce géneros
    al catálogo canónico en español.

    Args:
        ruta: Ruta local al archivo (CSV o JSON).

    Returns:
        Lista de instancias Pelicula listas para usar.

    Raises:
        FileNotFoundError: Si el archivo no existe.
        ValueError: Si faltan columnas requeridas o el formato es inválido.
        RuntimeError: Para errores inesperados durante la carga.
    """
    print(f"[data_loader] Iniciando carga: {ruta}")

    if not os.path.isfile(ruta):
        raise FileNotFoundError(f"El archivo no existe: {ruta}")

    extension = os.path.splitext(ruta)[1].lower()

    try:
        if extension == ".csv":
            df = pd.read_csv(ruta)
        elif extension == ".json":
            df = pd.read_json(ruta)
        else:
            raise ValueError(f"Formato no soportado: '{extension}'. Use CSV o JSON.")

        print(f"[data_loader] Leídas {len(df)} filas desde {extension}")

        df, stats = _limpiar_dataframe(df)
        informe = generar_informe_calidad(stats)
        print(informe)

        peliculas: List[Pelicula] = []
        for _, fila in df.iterrows():
            pelicula = Pelicula(
                id=int(fila["id"]),
                titulo=str(fila["titulo"]),
                generos=list(fila["generos"]),
                anio=int(fila["anio"]),
                puntuacion=float(fila["puntuacion"]),
                popularidad=float(fila["popularidad"]),
                idioma=str(fila["idioma"]),
                descripcion=str(fila["descripcion"]),
                votos=int(fila["votos"]),
            )
            peliculas.append(pelicula)

        print(f"[data_loader] Carga finalizada: {len(peliculas)} películas válidas.")
        return peliculas

    except ValueError:
        raise
    except Exception as exc:
        raise RuntimeError(f"Error inesperado al cargar '{ruta}': {exc}") from exc


def generar_informe_calidad(stats: Dict[str, Any]) -> str:
    """
    Genera un informe legible con las estadísticas del proceso de limpieza.

    Args:
        stats: Diccionario con métricas producidas por `_limpiar_dataframe`.

    Returns:
        Cadena multilinea con el resumen de calidad.
    """
    lineas = [
        "─" * 50,
        "  INFORME DE CALIDAD DEL DATASET",
        "─" * 50,
        f"  Filas originales      : {stats.get('filas_originales', 'N/A')}",
        f"  Filas finales         : {stats.get('filas_finales', 'N/A')}",
        f"  Duplicados eliminados : {stats.get('duplicados_eliminados', 'N/A')}",
        f"  Nulos antes           : {stats.get('nulos_antes', 'N/A')}",
        f"  Nulos después         : {stats.get('nulos_despues', 'N/A')}",
        f"  Mediana puntuación    : {stats.get('mediana_puntuacion', 'N/A'):.2f}",
        f"  Mediana popularidad   : {stats.get('mediana_popularidad', 'N/A'):.2f}",
        f"  Mediana votos         : {stats.get('mediana_votos', 'N/A')}",
        "─" * 50,
    ]
    return "\n".join(lineas)


def descargar_dataset_ejemplo() -> str:
    """
    Descarga un CSV de muestra de TMDB y lo guarda en ``data/tmdb_movies.csv``.

    Returns:
        Ruta absoluta del archivo descargado.

    Raises:
        RuntimeError: Si la descarga falla por problemas de red o URL.
    """
    ruta_destino = os.path.join("data", "tmdb_movies.csv")
    os.makedirs(os.path.dirname(ruta_destino), exist_ok=True)

    print(f"[data_loader] Descargando dataset de ejemplo desde:\n  {URL_DATASET_EJEMPLO}")

    try:
        urllib.request.urlretrieve(URL_DATASET_EJEMPLO, ruta_destino)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Error HTTP al descargar el dataset: {exc.code} {exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Error de red al descargar el dataset: {exc.reason}") from exc
    except Exception as exc:
        raise RuntimeError(f"Error inesperado durante la descarga: {exc}") from exc

    print(f"[data_loader] Dataset guardado en: {os.path.abspath(ruta_destino)}")
    return os.path.abspath(ruta_destino)
