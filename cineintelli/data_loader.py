"""
CineIntelli - Carga y preprocesamiento de datasets.

Lee archivos CSV de MovieLens y/o TMDB, los limpia y expone
DataFrames listos para el análisis y el motor de recomendaciones.
"""

import os
from typing import Optional, Tuple
import pandas as pd
import numpy as np


class DataLoader:
    """Gestiona la carga y limpieza de datasets de películas."""

    def __init__(self, data_dir: str = "data"):
        """
        Inicializa el cargador con la ruta base de datos.

        Args:
            data_dir: Directorio donde residen los datasets.
        """
        pass

    def load_movielens(self, movies_file: str = "movies.csv", ratings_file: str = "ratings.csv") -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Carga los archivos principales de MovieLens.

        Args:
            movies_file: Nombre del CSV de películas.
            ratings_file: Nombre del CSV de calificaciones.

        Returns:
            Tupla (movies_df, ratings_df).
        """
        pass

    def load_tmdb(self, tmdb_file: str = "tmdb_movies.csv") -> pd.DataFrame:
        """
        Carga el dataset enriquecido de TMDB.

        Args:
            tmdb_file: Nombre del CSV de TMDB.

        Returns:
            DataFrame con la información de TMDB.
        """
        pass

    def merge_datasets(self, movielens_df: pd.DataFrame, tmdb_df: pd.DataFrame) -> pd.DataFrame:
        """
        Fusiona los datasets de MovieLens y TMDB por título o ID.

        Args:
            movielens_df: DataFrame de MovieLens.
            tmdb_df: DataFrame de TMDB.

        Returns:
            DataFrame combinado.
        """
        pass

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aplica limpieza básica: elimina duplicados, normaliza textos, etc.

        Args:
            df: DataFrame a limpiar.

        Returns:
            DataFrame limpio.
        """
        pass
