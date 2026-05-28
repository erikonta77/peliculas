"""
CineIntelli - Modelos de dominio del sistema de recomendación.

Define las entidades principales: perfiles de usuario, catálogo de películas
y el motor de recomendaciones basado en similitud de contenido.
"""

from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class UserProfile:
    """Representa el perfil de preferencias de un usuario."""

    def __init__(self, user_id: str, name: str, preferred_genres: List[str] = None):
        """
        Inicializa un perfil de usuario.

        Args:
            user_id: Identificador único del usuario.
            name: Nombre del usuario.
            preferred_genres: Lista de géneros preferidos.
        """
        pass

    def add_rating(self, movie_id: int, rating: float) -> None:
        """
        Registra la calificación de una película.

        Args:
            movie_id: Identificador de la película.
            rating: Calificación otorgada (ej. 1.0 - 5.0).
        """
        pass

    def to_dict(self) -> Dict[str, Any]:
        """Serializa el perfil a un diccionario."""
        pass

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserProfile":
        """Deserializa un perfil desde un diccionario."""
        pass


class MovieCatalog:
    """Gestiona el catálogo de películas cargado desde datasets."""

    def __init__(self, movies_df: Optional[pd.DataFrame] = None):
        """
        Inicializa el catálogo.

        Args:
            movies_df: DataFrame con la información de las películas.
        """
        pass

    def get_movie_by_id(self, movie_id: int) -> Optional[pd.Series]:
        """
        Obtiene una película por su identificador.

        Args:
            movie_id: Identificador de la película.

        Returns:
            Serie con los datos de la película o None.
        """
        pass

    def search_by_title(self, title: str) -> pd.DataFrame:
        """
        Busca películas por título.

        Args:
            title: Subcadena del título a buscar.

        Returns:
            DataFrame con las coincidencias.
        """
        pass

    def get_genres(self) -> List[str]:
        """Devuelve la lista de géneros disponibles en el catálogo."""
        pass


class RecommendationEngine:
    """Motor de recomendaciones basado en similitud de contenido (TF-IDF + coseno)."""

    def __init__(self, catalog: MovieCatalog):
        """
        Inicializa el motor con un catálogo.

        Args:
            catalog: Instancia del catálogo de películas.
        """
        pass

    def build_tfidf_matrix(self, text_column: str = "overview") -> None:
        """
        Construye la matriz TF-IDF a partir de los textos del catálogo.

        Args:
            text_column: Nombre de la columna con el texto descriptivo.
        """
        pass

    def recommend_by_content(
        self, movie_id: int, top_n: int = 10
    ) -> pd.DataFrame:
        """
        Genera recomendaciones por similitud de contenido.

        Args:
            movie_id: Película semilla.
            top_n: Cantidad de recomendaciones a retornar.

        Returns:
            DataFrame con las películas recomendadas y su score.
        """
        pass

    def recommend_for_user(
        self, user: UserProfile, top_n: int = 10
    ) -> pd.DataFrame:
        """
        Genera recomendaciones personalizadas para un usuario.

        Args:
            user: Perfil del usuario.
            top_n: Cantidad de recomendaciones a retornar.

        Returns:
            DataFrame con las películas recomendadas.
        """
        pass
