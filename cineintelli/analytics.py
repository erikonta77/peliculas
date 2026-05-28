"""
CineIntelli - Análisis estadístico, modelado neuronal y evaluación.

Calcula métricas descriptivas, entrena un Autoencoder para embeddings
neuronales, evalúa recomendaciones y mide compatibilidad entre perfiles.
"""

from __future__ import annotations

import os
import pickle
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, precision_score, recall_score
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler, MultiLabelBinarizer

from models import Pelicula, Perfil

# ---------------------------------------------------------------------------
# Suprimir verbosidad de TensorFlow
# ---------------------------------------------------------------------------
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")


# ---------------------------------------------------------------------------
# 1. Estadísticas descriptivas
# ---------------------------------------------------------------------------

def estadisticas_catalogo(catalogo: List[Pelicula]) -> Dict[str, Any]:
    """
    Calcula estadísticas descriptivas del catálogo.

    Args:
        catalogo: Lista de películas cargadas.

    Returns:
        Diccionario con métricas de puntuación, popularidad,
        distribuciones por género y década, y tops 10.
    """
    if not catalogo:
        return {}

    puntuaciones = np.array([p.puntuacion for p in catalogo])
    popularidades = np.array([p.popularidad for p in catalogo])

    # Distribución por género
    generos_counter: Dict[str, int] = {}
    for p in catalogo:
        for g in p.generos:
            generos_counter[g] = generos_counter.get(g, 0) + 1
    total_generos = sum(generos_counter.values())
    generos_pct = {g: round(c / total_generos * 100, 2) for g, c in generos_counter.items()}

    # Distribución por década
    decadas: Dict[int, int] = {}
    for p in catalogo:
        dec = (p.anio // 10) * 10
        decadas[dec] = decadas.get(dec, 0) + 1

    top_popular = sorted(catalogo, key=lambda p: p.popularidad, reverse=True)[:10]
    top_rated = sorted(catalogo, key=lambda p: p.puntuacion, reverse=True)[:10]

    return {
        "puntuacion": {
            "media": float(np.mean(puntuaciones)),
            "mediana": float(np.median(puntuaciones)),
            "std": float(np.std(puntuaciones)),
        },
        "popularidad": {
            "media": float(np.mean(popularidades)),
            "mediana": float(np.median(popularidades)),
            "std": float(np.std(popularidades)),
        },
        "distribucion_generos": {
            "conteo": generos_counter,
            "porcentaje": generos_pct,
        },
        "distribucion_decadas": decadas,
        "top_10_populares": [(p.titulo, round(p.popularidad, 2)) for p in top_popular],
        "top_10_calificadas": [(p.titulo, round(p.puntuacion, 2)) for p in top_rated],
    }


# ---------------------------------------------------------------------------
# 2. Tendencias temporales
# ---------------------------------------------------------------------------

def tendencias_temporales(catalogo: List[Pelicula]) -> Dict[str, Any]:
    """
    Analiza tendencias temporales del catálogo.

    Args:
        catalogo: Lista de películas.

    Returns:
        Diccionario con géneros en ascenso, año de mayor producción por género
        y correlación año vs puntuación media.
    """
    if not catalogo:
        return {}

    anio_max = max(p.anio for p in catalogo)
    ultimos_5 = [p for p in catalogo if p.anio >= anio_max - 5]
    decada_ant = [p for p in catalogo if anio_max - 15 <= p.anio < anio_max - 5]

    def _contar_generos(lista: List[Pelicula]) -> Dict[str, int]:
        c: Dict[str, int] = {}
        for p in lista:
            for g in p.generos:
                c[g] = c.get(g, 0) + 1
        return c

    gen_ultimos = _contar_generos(ultimos_5)
    gen_decada = _contar_generos(decada_ant)

    ascenso: Dict[str, Dict[str, Any]] = {}
    for g in set(gen_ultimos) | set(gen_decada):
        u = gen_ultimos.get(g, 0)
        d = gen_decada.get(g, 0)
        ascenso[g] = {
            "ultimos_5": u,
            "decada_anterior": d,
            "ratio": round(u / d, 2) if d > 0 else float("inf"),
        }

    # Año con mayor producción por género
    generos_años: Dict[str, Dict[int, int]] = {}
    for p in catalogo:
        for g in p.generos:
            if g not in generos_años:
                generos_años[g] = {}
            generos_años[g][p.anio] = generos_años[g].get(p.anio, 0) + 1

    anio_mayor_prod = {g: max(años, key=años.get) for g, años in generos_años.items()}

    # Correlación año vs puntuación media
    df = pd.DataFrame(
        [{"anio": p.anio, "puntuacion": p.puntuacion} for p in catalogo]
    )
    media_anual = df.groupby("anio")["puntuacion"].mean()
    corr = float(np.corrcoef(media_anual.index, media_anual.values)[0, 1])
    if np.isnan(corr):
        corr = 0.0

    return {
        "generos_ascenso": ascenso,
        "anio_mayor_produccion_por_genero": anio_mayor_prod,
        "correlacion_anio_puntuacion": corr,
    }


# ---------------------------------------------------------------------------
# 3. Modelo neuronal (Autoencoder)
# ---------------------------------------------------------------------------

def _vectorizar_catalogo(
    catalogo: List[Pelicula], preprocesadores: Dict[str, Any]
) -> np.ndarray:
    """
    Transforma una lista de películas en la matriz de características
    usando los preprocesadores entrenados.
    """
    generos = [p.generos for p in catalogo]
    puntuaciones = np.array([[p.puntuacion] for p in catalogo])
    popularidades = np.array([[p.popularidad] for p in catalogo])
    decadas = np.array([[(p.anio // 10) * 10] for p in catalogo])

    genres_mat = preprocesadores["mlb"].transform(generos)
    punt_mat = preprocesadores["scaler_punt"].transform(puntuaciones)
    pop_mat = preprocesadores["scaler_pop"].transform(popularidades)

    decada_map = preprocesadores["decada_map"]
    decadas_unique = preprocesadores["decadas_unique"]
    decada_onehot = np.zeros((len(catalogo), len(decadas_unique)))
    for i, d in enumerate(decadas):
        idx = decada_map.get(d[0])
        if idx is not None:
            decada_onehot[i, idx] = 1

    return np.hstack([genres_mat, punt_mat, pop_mat, decada_onehot])


def construir_modelo_recomendacion(
    catalogo: List[Pelicula],
) -> Tuple[Any, np.ndarray, Dict[str, Any], Optional[Any]]:
    """
    Entrena o carga un Autoencoder para generar embeddings de películas.

    La arquitectura comprime las características en un espacio latente
    de 16 dimensiones que captura patrones de género, puntuación,
    popularidad y década.

    Args:
        catalogo: Lista completa de películas.

    Returns:
        Tupla (modelo_encoder, matriz_original, preprocesadores, historial).
        El historial es el objeto History de Keras si se entrenó,
        o None si se cargó un modelo existente.
    """
    import tensorflow as tf
    from tensorflow.keras.layers import Dense, Input
    from tensorflow.keras.models import Model, load_model

    RUTA_MODELO = os.path.join("output", "modelo_recomendador.keras")
    RUTA_PREPROCESADORES = os.path.join("output", "preprocessors.pkl")
    os.makedirs("output", exist_ok=True)

    # ------------------------------------------------------------------
    # Preprocesamiento
    # ------------------------------------------------------------------
    generos = [p.generos for p in catalogo]
    puntuaciones = np.array([[p.puntuacion] for p in catalogo])
    popularidades = np.array([[p.popularidad] for p in catalogo])
    decadas = np.array([[(p.anio // 10) * 10] for p in catalogo])

    mlb = MultiLabelBinarizer()
    genres_mat = mlb.fit_transform(generos)

    scaler_punt = MinMaxScaler()
    punt_mat = scaler_punt.fit_transform(puntuaciones)

    scaler_pop = MinMaxScaler()
    pop_mat = scaler_pop.fit_transform(popularidades)

    decadas_unique = np.sort(np.unique(decadas))
    decada_map = {int(d): i for i, d in enumerate(decadas_unique)}
    decada_onehot = np.zeros((len(catalogo), len(decadas_unique)))
    for i, d in enumerate(decadas):
        decada_onehot[i, decada_map[int(d[0])]] = 1

    X = np.hstack([genres_mat, punt_mat, pop_mat, decada_onehot])

    preprocesadores = {
        "mlb": mlb,
        "scaler_punt": scaler_punt,
        "scaler_pop": scaler_pop,
        "decadas_unique": decadas_unique,
        "decada_map": decada_map,
    }

    # ------------------------------------------------------------------
    # Cargar o entrenar
    # ------------------------------------------------------------------
    if os.path.exists(RUTA_MODELO) and os.path.exists(RUTA_PREPROCESADORES):
        print("[analytics] Cargando modelo existente...")
        autoencoder = load_model(RUTA_MODELO)
        with open(RUTA_PREPROCESADORES, "rb") as f:
            preprocesadores = pickle.load(f)
        X = _vectorizar_catalogo(catalogo, preprocesadores)
        history = None
    else:
        print("[analytics] Entrenando Autoencoder...")
        n_features = X.shape[1]

        input_layer = Input(shape=(n_features,))
        encoded = Dense(64, activation="relu")(input_layer)
        encoded = Dense(32, activation="relu")(encoded)
        encoded = Dense(16, activation="relu", name="encoder_output")(encoded)

        decoded = Dense(32, activation="relu")(encoded)
        decoded = Dense(64, activation="relu")(decoded)
        decoded = Dense(n_features, activation="sigmoid")(decoded)

        autoencoder = Model(inputs=input_layer, outputs=decoded)
        autoencoder.compile(optimizer="adam", loss="mse")

        history = autoencoder.fit(
            X,
            X,
            epochs=50,
            batch_size=32,
            validation_split=0.1,
            verbose=0,
        )

        autoencoder.save(RUTA_MODELO)
        with open(RUTA_PREPROCESADORES, "wb") as f:
            pickle.dump(preprocesadores, f)
        print("[analytics] Modelo guardado.")

    encoder = Model(
        inputs=autoencoder.input,
        outputs=autoencoder.get_layer("encoder_output").output,
    )

    return encoder, X, preprocesadores, history


# ---------------------------------------------------------------------------
# 4. Similitud neuronal
# ---------------------------------------------------------------------------

def similitud_neuronal(
    encoder: Any, vector_perfil: np.ndarray, catalogo_vectorizado: np.ndarray
) -> List[float]:
    """
    Calcula la similitud coseno entre el embedding de un perfil y
    el catálogo completo usando el encoder entrenado.

    Args:
        encoder: Modelo encoder del Autoencoder.
        vector_perfil: Vector de características del perfil de usuario.
        catalogo_vectorizado: Matriz de características de todo el catálogo.

    Returns:
        Lista de scores de similitud (0-1) ordenada según el catálogo.
    """
    perfil_emb = encoder.predict(np.array([vector_perfil]), verbose=0)
    catalogo_emb = encoder.predict(catalogo_vectorizado, verbose=0)
    scores = cosine_similarity(perfil_emb, catalogo_emb)[0]
    return scores.tolist()


# ---------------------------------------------------------------------------
# 5. Evaluación de recomendaciones
# ---------------------------------------------------------------------------

def evaluar_recomendaciones(
    recomendadas: List[Pelicula], generos_esperados: List[str]
) -> Dict[str, Any]:
    """
    Evalúa la calidad de un conjunto de recomendaciones contra los
    géneros esperados del perfil de usuario.

    Args:
        recomendadas: Películas recomendadas por el motor.
        generos_esperados: Géneros favoritos del usuario.

    Returns:
        Diccionario con matriz de confusión, precisión, recall
        y métricas desglosadas por género.
    """
    if not recomendadas or not generos_esperados:
        return {
            "confusion_matrix": [],
            "precision_global": 0.0,
            "recall_global": 0.0,
            "por_genero": {},
        }

    y_true = [1 if set(p.generos) & set(generos_esperados) else 0 for p in recomendadas]
    y_pred = [1] * len(recomendadas)

    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    precision = float(precision_score(y_true, y_pred, zero_division=0))
    recall = float(recall_score(y_true, y_pred, zero_division=0))

    # Métricas por género esperado
    por_genero: Dict[str, Dict[str, float]] = {}
    for g in generos_esperados:
        apariciones = sum(1 for p in recomendadas if g in p.generos)
        por_genero[g] = {
            "apariciones": apariciones,
            "precision": round(apariciones / len(recomendadas), 2) if recomendadas else 0.0,
            "recall": 1.0 if apariciones > 0 else 0.0,
        }

    lineas = [
        "─" * 50,
        "  EVALUACIÓN DE RECOMENDACIONES",
        "─" * 50,
        f"  Películas evaluadas : {len(recomendadas)}",
        f"  Matriz confusión    : {cm.ravel().tolist()}",
        f"  Precisión global    : {precision:.2f}",
        f"  Recall global       : {recall:.2f}",
        "  Por género esperado:",
    ]
    for g, m in por_genero.items():
        lineas.append(
            f"    {g}: apariciones={m['apariciones']}, "
            f"precision={m['precision']:.2f}, recall={m['recall']:.2f}"
        )
    lineas.append("─" * 50)
    print("\n".join(lineas))

    return {
        "confusion_matrix": cm.tolist(),
        "precision_global": precision,
        "recall_global": recall,
        "por_genero": por_genero,
    }


# ---------------------------------------------------------------------------
# 6. Compatibilidad entre perfiles
# ---------------------------------------------------------------------------

def compatibilidad_perfiles(
    perfil1: Perfil, perfil2: Perfil, catalogo: List[Pelicula]
) -> Dict[str, Any]:
    """
    Calcula la compatibilidad entre dos perfiles de usuario.

    Args:
        perfil1: Primer perfil.
        perfil2: Segundo perfil.
        catalogo: Catálogo completo de películas.

    Returns:
        Diccionario con índice de compatibilidad, géneros comunes
        y películas sugeridas para ambos.
    """
    generos1 = set(perfil1.generos_favoritos)
    generos2 = set(perfil2.generos_favoritos)
    comunes = generos1 & generos2
    union = generos1 | generos2
    indice = len(comunes) / len(union) if union else 0.0

    anio_min = max(perfil1.anio_min, perfil2.anio_min)
    anio_max = min(perfil1.anio_max, perfil2.anio_max)
    punt_min = max(perfil1.puntuacion_minima, perfil2.puntuacion_minima)

    peliculas_ambos: List[Pelicula] = []
    for p in catalogo:
        if anio_min <= p.anio <= anio_max and p.puntuacion >= punt_min:
            if set(p.generos) & comunes:
                peliculas_ambos.append(p)

    return {
        "indice_compatibilidad": round(indice, 2),
        "generos_comunes": sorted(comunes),
        "peliculas_ambos": peliculas_ambos,
    }


# ---------------------------------------------------------------------------
# 7. Informe de tendencias
# ---------------------------------------------------------------------------

def generar_informe_tendencias(catalogo: List[Pelicula]) -> str:
    """
    Genera un texto legible con hallazgos relevantes del catálogo.

    Args:
        catalogo: Lista de películas.

    Returns:
        Cadena multilinea con el informe.
    """
    stats = estadisticas_catalogo(catalogo)
    tend = tendencias_temporales(catalogo)

    lineas = [
        "═" * 50,
        "  INFORME DE TENDENCIAS DEL CATÁLOGO",
        "═" * 50,
        f"  Total de películas  : {len(catalogo)}",
        f"  Puntuación media    : {stats['puntuacion']['media']:.2f} "
        f"(std: {stats['puntuacion']['std']:.2f})",
        f"  Popularidad media   : {stats['popularidad']['media']:.2f} "
        f"(std: {stats['popularidad']['std']:.2f})",
        "",
        "  Top géneros más frecuentes:",
    ]

    top_gen = sorted(
        stats["distribucion_generos"]["conteo"].items(),
        key=lambda x: x[1],
        reverse=True,
    )[:5]
    for g, c in top_gen:
        pct = stats["distribucion_generos"]["porcentaje"][g]
        lineas.append(f"    {g}: {c} películas ({pct:.1f}%)")

    lineas.append("")
    lineas.append("  Décadas más productivas:")
    top_dec = sorted(stats["distribucion_decadas"].items(), key=lambda x: x[1], reverse=True)[:5]
    for d, c in top_dec:
        lineas.append(f"    {d}s: {c} películas")

    if tend and "correlacion_anio_puntuacion" in tend:
        corr = tend["correlacion_anio_puntuacion"]
        lineas.append("")
        lineas.append(f"  Correlación año vs puntuación media: {corr:.3f}")

    lineas.append("═" * 50)
    return "\n".join(lineas)
