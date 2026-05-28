"""
CineIntelli - Visualización de estadísticas del catálogo.

Genera gráficos con Matplotlib y Seaborn a partir de los
análisis calculados por CatalogAnalytics.
"""

import os
from typing import Optional
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


class StatsVisualizer:
    """Crea y exporta gráficos estadísticos del catálogo."""

    def __init__(self, output_dir: str = "output"):
        """
        Inicializa el visualizador con el directorio de salida.

        Args:
            output_dir: Carpeta donde se guardarán las imágenes.
        """
        pass

    def plot_genre_distribution(self, genre_series: pd.Series, filename: str = "genre_distribution.png") -> str:
        """
        Genera un gráfico de barras con la distribución de géneros.

        Args:
            genre_series: Serie con la frecuencia de géneros.
            filename: Nombre del archivo de salida.

        Returns:
            Ruta del archivo generado.
        """
        pass

    def plot_rating_distribution(self, rating_series: pd.Series, filename: str = "rating_distribution.png") -> str:
        """
        Genera un histograma de la distribución de calificaciones.

        Args:
            rating_series: Serie con la frecuencia de calificaciones.
            filename: Nombre del archivo de salida.

        Returns:
            Ruta del archivo generado.
        """
        pass

    def plot_yearly_trend(self, yearly_df: pd.DataFrame, filename: str = "yearly_trend.png") -> str:
        """
        Genera un gráfico de líneas con la evolución anual.

        Args:
            yearly_df: DataFrame con estadísticas por año.
            filename: Nombre del archivo de salida.

        Returns:
            Ruta del archivo generado.
        """
        pass

    def plot_top_movies(self, top_df: pd.DataFrame, filename: str = "top_movies.png") -> str:
        """
        Genera un gráfico de barras horizontales con las películas top.

        Args:
            top_df: DataFrame con las películas mejor calificadas.
            filename: Nombre del archivo de salida.

        Returns:
            Ruta del archivo generado.
        """
        pass

    def generate_dashboard(self, analytics) -> str:
        """
        Genera una imagen combinada con múltiples gráficos.

        Args:
            analytics: Instancia de CatalogAnalytics.

        Returns:
            Ruta del archivo generado.
        """
        pass
