"""
CineIntelli - Punto de entrada principal del sistema de recomendación de películas.

Coordina la carga de datos, el análisis, la generación de recomendaciones
y la visualización de estadísticas del catálogo.
"""

from data_loader import DataLoader
from models import UserProfile, MovieCatalog, RecommendationEngine
from analytics import CatalogAnalytics
from visualizer import StatsVisualizer
from utils import setup_logging, save_json, load_json


def main():
    """Orquesta el flujo completo del sistema de recomendación."""
    pass


if __name__ == "__main__":
    main()
