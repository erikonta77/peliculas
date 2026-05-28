"""
CineIntelli - Utilidades compartidas del sistema.

Funciones auxiliares para logging, serialización JSON,
manejo de rutas y transformaciones comunes.
"""

import json
import logging
import os
from typing import Any, Dict


def setup_logging(level: int = logging.INFO, log_file: str = "cineintelli.log") -> logging.Logger:
    """
    Configura el logger con salida a consola y archivo.

    Args:
        level: Nivel de logging (default INFO).
        log_file: Nombre del archivo de logs.

    Returns:
        Instancia del logger configurado.
    """
    pass


def save_json(data: Dict[str, Any], filepath: str) -> None:
    """
    Guarda un diccionario como archivo JSON.

    Args:
        data: Diccionario a serializar.
        filepath: Ruta del archivo de salida.
    """
    pass


def load_json(filepath: str) -> Dict[str, Any]:
    """
    Carga un archivo JSON como diccionario.

    Args:
        filepath: Ruta del archivo JSON.

    Returns:
        Diccionario con los datos cargados.
    """
    pass


def ensure_dir(directory: str) -> str:
    """
    Crea un directorio si no existe.

    Args:
        directory: Ruta del directorio.

    Returns:
        Ruta del directorio asegurado.
    """
    pass
