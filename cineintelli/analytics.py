"""
CineIntelli - Análisis estadístico del catálogo de películas.

Calcula métricas descriptivas sobre géneros, calificaciones,
años de estreno y distribuciones generales del dataset.
"""

from typing import Dict, Any
import pandas as pd
import numpy as np


class CatalogAnalytics:
    """Proporciona análisis descriptivos sobre el catálogo."""

    def __init__(self, movies_df: pd.DataFrame, ratings_df: pd.DataFrame = None):
        """
        Inicializa el analizador con los DataFrames de referencia.

        Args:
            movies_df: DataFrame con la información de las películas.
            ratings_df: DataFrame con las calificaciones de los usuarios.
        """
        pass

    def top_rated_movies(self, min_votes: int = 100, top_n: int = 20) -> pd.DataFrame:
        """
        Obtiene las películas mejor calificadas filtrando por cantidad mínima de votos.

        Args:
            min_votes: Número mínimo de calificaciones requeridas.
            top_n: Cantidad de resultados a retornar.

        Returns:
            DataFrame con las películas top.
        """
        pass

    def genre_distribution(self) -> pd.Series:
        """
        Calcula la frecuencia de cada género en el catálogo.

        Returns:
            Serie con la cantidad de películas por género.
        """
        pass

    def yearly_stats(self) -> pd.DataFrame:
        """
        Agrupa métricas por año de estreno.

        Returns:
            DataFrame con estadísticas anuales.
        """
        pass

    def rating_distribution(self) -> pd.Series:
        """
        Calcula la distribución de calificaciones.

        Returns:
            Serie con la frecuencia de cada calificación.
        """
        pass

    def summary_report(self) -> Dict[str, Any]:
        """
        Genera un resumen general del catálogo en forma de diccionario.

        Returns:
            Diccionario con métricas clave.
        """
        pass
