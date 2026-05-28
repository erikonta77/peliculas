"""
CineIntelli - Visualización de estadísticas del catálogo.

Genera gráficos con Matplotlib y Seaborn a partir de las películas
cargadas y del historial de entrenamiento del modelo neuronal.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any, List, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from models import Pelicula

# Estilo por defecto
sns.set_theme(style="whitegrid")

_OUTPUT_DIR = "output"
_DPI = 150


def _ruta_salida(nombre_base: str) -> str:
    """Genera una ruta única en output/ usando timestamp."""
    os.makedirs(_OUTPUT_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(_OUTPUT_DIR, f"{nombre_base}_{ts}.png")


def _guardar_o_mostrar(fig: plt.Figure, ruta: str, guardar: bool) -> Optional[str]:
    """Guarda la figura en disco o la muestra en pantalla."""
    if guardar:
        fig.savefig(ruta, dpi=_DPI, bbox_inches="tight")
        plt.close(fig)
        return ruta
    plt.show()
    plt.close(fig)
    return None


# ---------------------------------------------------------------------------
# 1. Distribución de géneros
# ---------------------------------------------------------------------------

def grafico_distribucion_generos(
    catalogo: List[Pelicula],
    guardar: bool = True,
    figsize: tuple[int, int] = (10, 8),
) -> Optional[str]:
    """
    Barras horizontales con la frecuencia de cada género en el catálogo.

    Args:
        catalogo: Lista de películas.
        guardar: Si True, guarda PNG en output/.
        figsize: Dimensiones de la figura.

    Returns:
        Ruta del archivo guardado o None si se muestra en pantalla.
    """
    conteo: dict[str, int] = {}
    for p in catalogo:
        for g in p.generos:
            conteo[g] = conteo.get(g, 0) + 1

    df = (
        pd.DataFrame(list(conteo.items()), columns=["Género", "Cantidad"])
        .sort_values("Cantidad", ascending=False)
    )

    fig, ax = plt.subplots(figsize=figsize)
    sns.barplot(
        data=df,
        y="Género",
        x="Cantidad",
        hue="Género",
        palette="Blues_r",
        legend=False,
        orient="h",
        ax=ax,
    )
    ax.set_title("Distribución de Géneros en el Catálogo", fontsize=14, weight="bold")
    ax.set_xlabel("Número de Películas")
    ax.set_ylabel("Género")

    for i, v in enumerate(df["Cantidad"]):
        ax.text(v + max(df["Cantidad"]) * 0.01, i, str(v), va="center", fontsize=9)

    ruta = _ruta_salida("distribucion_generos")
    return _guardar_o_mostrar(fig, ruta, guardar)


# ---------------------------------------------------------------------------
# 2. Tendencia anual
# ---------------------------------------------------------------------------

def grafico_tendencia_anual(
    catalogo: List[Pelicula],
    guardar: bool = True,
    figsize: tuple[int, int] = (12, 6),
) -> Optional[str]:
    """
    Evolución de la puntuación media por año con desviación estándar
    y línea de tendencia lineal.

    Args:
        catalogo: Lista de películas.
        guardar: Si True, guarda PNG en output/.
        figsize: Dimensiones de la figura.

    Returns:
        Ruta del archivo guardado o None si se muestra en pantalla.
    """
    df = pd.DataFrame(
        [{"Año": p.anio, "Puntuación": p.puntuacion} for p in catalogo]
    )
    agrupado = df.groupby("Año")["Puntuación"].agg(["mean", "std", "count"]).reset_index()
    agrupado = agrupado[agrupado["count"] >= 3]  # evitar años con muy pocas muestras

    fig, ax = plt.subplots(figsize=figsize)
    sns.lineplot(
        data=agrupado,
        x="Año",
        y="mean",
        marker="o",
        ax=ax,
        label="Puntuación media",
    )
    ax.fill_between(
        agrupado["Año"],
        agrupado["mean"] - agrupado["std"],
        agrupado["mean"] + agrupado["std"],
        alpha=0.2,
    )

    # Línea de tendencia
    z = np.polyfit(agrupado["Año"], agrupado["mean"], 1)
    p = np.poly1d(z)
    ax.plot(
        agrupado["Año"],
        p(agrupado["Año"]),
        linestyle="--",
        color="crimson",
        label="Tendencia lineal",
    )

    ax.set_title("Evolución de la Puntuación Media por Año", fontsize=14, weight="bold")
    ax.set_xlabel("Año de Estreno")
    ax.set_ylabel("Puntuación Media")
    ax.legend()

    ruta = _ruta_salida("tendencia_anual")
    return _guardar_o_mostrar(fig, ruta, guardar)


# ---------------------------------------------------------------------------
# 3. Top géneros — calificación vs popularidad
# ---------------------------------------------------------------------------

def grafico_top_generos(
    catalogo: List[Pelicula],
    top_n: int = 10,
    guardar: bool = True,
    figsize: tuple[int, int] = (12, 8),
) -> Optional[str]:
    """
    Barras agrupadas con la película mejor calificada y la más popular
    para cada uno de los géneros principales.

    Args:
        catalogo: Lista de películas.
        top_n: Número de géneros a mostrar (ordenados por frecuencia).
        guardar: Si True, guarda PNG en output/.
        figsize: Dimensiones de la figura.

    Returns:
        Ruta del archivo guardado o None si se muestra en pantalla.
    """
    # Top géneros por frecuencia
    conteo: dict[str, int] = {}
    for p in catalogo:
        for g in p.generos:
            conteo[g] = conteo.get(g, 0) + 1
    top_generos = [g for g, _ in sorted(conteo.items(), key=lambda x: x[1], reverse=True)[:top_n]]

    filas = []
    for g in top_generos:
        pelis_con_genero = [p for p in catalogo if g in p.generos]
        if not pelis_con_genero:
            continue
        mejor = max(pelis_con_genero, key=lambda p: p.puntuacion)
        popular = max(pelis_con_genero, key=lambda p: p.popularidad)
        filas.append({"Género": g, "Métrica": "Puntuación", "Valor": mejor.puntuacion})
        filas.append({"Género": g, "Métrica": "Popularidad", "Valor": popular.popularidad})

    df = pd.DataFrame(filas)

    fig, ax = plt.subplots(figsize=figsize)
    sns.barplot(
        data=df,
        x="Género",
        y="Valor",
        hue="Métrica",
        palette="muted",
        ax=ax,
    )
    ax.set_title(
        f"Mejor Calificada vs Más Popular por Género (Top {top_n})",
        fontsize=14,
        weight="bold",
    )
    ax.set_xlabel("Género")
    ax.set_ylabel("Valor")
    ax.legend(title="Métrica")
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")

    ruta = _ruta_salida("top_generos")
    return _guardar_o_mostrar(fig, ruta, guardar)


# ---------------------------------------------------------------------------
# 4. Scatter popularidad vs puntuación
# ---------------------------------------------------------------------------

def grafico_scatter_popularidad(
    catalogo: List[Pelicula],
    guardar: bool = True,
    figsize: tuple[int, int] = (12, 8),
) -> Optional[str]:
    """
    Diagrama de dispersión de puntuación vs popularidad.
    El tamaño representa votos y el color el género principal.

    Args:
        catalogo: Lista de películas.
        guardar: Si True, guarda PNG en output/.
        figsize: Dimensiones de la figura.

    Returns:
        Ruta del archivo guardado o None si se muestra en pantalla.
    """
    df = pd.DataFrame(
        [
            {
                "Puntuación": p.puntuacion,
                "Popularidad": p.popularidad,
                "Votos": p.votos,
                "Género Principal": p.generos[0] if p.generos else "Desconocido",
            }
            for p in catalogo
        ]
    )

    fig, ax = plt.subplots(figsize=figsize)
    sns.scatterplot(
        data=df,
        x="Puntuación",
        y="Popularidad",
        size="Votos",
        hue="Género Principal",
        alpha=0.7,
        ax=ax,
        legend="brief",
    )
    sns.regplot(
        data=df,
        x="Puntuación",
        y="Popularidad",
        scatter=False,
        color="black",
        line_kws={"linestyle": "--", "linewidth": 1.5},
        ax=ax,
    )
    ax.set_title("Puntuación vs Popularidad", fontsize=14, weight="bold")
    ax.set_xlabel("Puntuación Media")
    ax.set_ylabel("Índice de Popularidad")
    plt.setp(ax.get_legend().get_texts(), fontsize="8")

    ruta = _ruta_salida("scatter_popularidad")
    return _guardar_o_mostrar(fig, ruta, guardar)


# ---------------------------------------------------------------------------
# 5. Pérdida de entrenamiento
# ---------------------------------------------------------------------------

def grafico_perdida_entrenamiento(
    historial_keras: Any,
    guardar: bool = True,
    figsize: tuple[int, int] = (10, 6),
) -> Optional[str]:
    """
    Curva de aprendizaje del Autoencoder mostrando loss y val_loss.

    Args:
        historial_keras: Objeto History devuelto por model.fit().
        guardar: Si True, guarda PNG en output/.
        figsize: Dimensiones de la figura.

    Returns:
        Ruta del archivo guardado o None si se muestra en pantalla.
    """
    if historial_keras is None or not hasattr(historial_keras, "history"):
        raise ValueError("Se requiere un objeto History válido de Keras.")

    hist = historial_keras.history
    epochs = list(range(1, len(hist["loss"]) + 1))
    df = pd.DataFrame({
        "Época": epochs,
        "Loss": hist["loss"],
        "Val_Loss": hist.get("val_loss", [np.nan] * len(epochs)),
    })

    fig, ax = plt.subplots(figsize=figsize)
    sns.lineplot(data=df, x="Época", y="Loss", label="Entrenamiento", color="steelblue", ax=ax)
    sns.lineplot(data=df, x="Época", y="Val_Loss", label="Validación", color="darkorange", ax=ax)

    # Marcar época de menor val_loss
    if "val_loss" in hist and hist["val_loss"]:
        mejor_epoca = int(np.argmin(hist["val_loss"])) + 1
        mejor_val = float(np.min(hist["val_loss"]))
        ax.axvline(mejor_epoca, color="green", linestyle=":", alpha=0.7)
        ax.annotate(
            f"Mejor val_loss\nÉpoca {mejor_epoca}\n{mejor_val:.4f}",
            xy=(mejor_epoca, mejor_val),
            xytext=(mejor_epoca + len(epochs) * 0.1, mejor_val * 1.1),
            arrowprops=dict(arrowstyle="->", color="green"),
            fontsize=9,
            color="green",
        )

    ax.set_title("Curva de Aprendizaje — Autoencoder CineIntelli", fontsize=14, weight="bold")
    ax.set_xlabel("Época")
    ax.set_ylabel("Pérdida (MSE)")
    ax.legend()

    ruta = _ruta_salida("perdida_entrenamiento")
    return _guardar_o_mostrar(fig, ruta, guardar)
