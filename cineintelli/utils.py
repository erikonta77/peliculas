"""
CineIntelli - Utilidades compartidas del sistema.

Funciones auxiliares para interfaz de consola, validación de entradas,
serialización de perfiles y operaciones comunes.
"""

from __future__ import annotations

import json
import os
import platform
from typing import Any, Dict, List, Optional

from models import Perfil


def limpiar_pantalla() -> None:
    """Limpia la pantalla de la terminal."""
    comando = "cls" if platform.system() == "Windows" else "clear"
    os.system(comando)


def imprimir_titulo(texto: str, ancho: int = 50) -> None:
    """
    Imprime un título decorado con bordes ASCII.

    Args:
        texto: Texto a centrar.
        ancho: Ancho total del recuadro.
    """
    texto_centrado = texto.center(ancho - 4)
    print("╔" + "═" * (ancho - 2) + "╗")
    print("║ " + texto_centrado + " ║")
    print("╚" + "═" * (ancho - 2) + "╝")


def imprimir_tabla(lista_dicts: List[Dict[str, Any]], columnas: List[str]) -> None:
    """
    Imprime una lista de diccionarios como tabla formateada.

    Args:
        lista_dicts: Filas de datos.
        columnas: Nombres de las columnas a mostrar.
    """
    if not lista_dicts:
        print("(Sin datos)")
        return

    anchos = {col: len(col) for col in columnas}
    for fila in lista_dicts:
        for col in columnas:
            val = str(fila.get(col, ""))
            anchos[col] = max(anchos[col], len(val))

    separador = "+-" + "-+-".join("-" * anchos[col] for col in columnas) + "-+"
    header = "| " + " | ".join(col.ljust(anchos[col]) for col in columnas) + " |"

    print(separador)
    print(header)
    print(separador)
    for fila in lista_dicts:
        linea = "| " + " | ".join(
            str(fila.get(col, "")).ljust(anchos[col]) for col in columnas
        ) + " |"
        print(linea)
    print(separador)


def validar_entrada(
    prompt: str,
    tipo: str = "str",
    minimo: Optional[float] = None,
    maximo: Optional[float] = None,
    opciones: List[str] = None,
    max_intentos: int = 3,
) -> Any:
    """
    Solicita y valida una entrada del usuario.

    Args:
        prompt: Texto a mostrar.
        tipo: 'str', 'int' o 'float'.
        minimo: Valor mínimo permitido (para numéricos).
        maximo: Valor máximo permitido (para numéricos).
        opciones: Lista de valores permitidos (para str).
        max_intentos: Reintentos antes de fallar.

    Returns:
        El valor validado.

    Raises:
        ValueError: Si se agotan los intentos sin entrada válida.
    """
    for intento in range(1, max_intentos + 1):
        try:
            valor_crudo = input(f"{prompt} ").strip()
            if not valor_crudo:
                raise ValueError("La entrada no puede estar vacía.")

            if tipo == "int":
                valor = int(valor_crudo)
            elif tipo == "float":
                valor = float(valor_crudo)
            else:
                valor = valor_crudo

            if tipo in ("int", "float"):
                if minimo is not None and valor < minimo:
                    raise ValueError(f"El valor debe ser mayor o igual a {minimo}.")
                if maximo is not None and valor > maximo:
                    raise ValueError(f"El valor debe ser menor o igual a {maximo}.")

            if opciones is not None:
                if str(valor).lower() not in [op.lower() for op in opciones]:
                    raise ValueError(f"Opciones válidas: {', '.join(opciones)}")

            return valor

        except ValueError as exc:
            print(f"  [Error] {exc} (intento {intento}/{max_intentos})")

    raise ValueError("Se agotaron los intentos de entrada válida.")


def cargar_perfil(nombre: str) -> Optional[Perfil]:
    """
    Carga un perfil de usuario desde profiles/{nombre}.json.

    Args:
        nombre: Nombre del usuario.

    Returns:
        Instancia de Perfil o None si no existe.
    """
    ruta = os.path.join("profiles", f"{nombre}.json")
    if not os.path.isfile(ruta):
        return None
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            datos = json.load(f)
        return Perfil.from_dict(datos)
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        print(f"[utils] Error al cargar perfil: {exc}")
        return None


def guardar_perfil(perfil: Perfil) -> str:
    """
    Guarda un perfil de usuario en profiles/{nombre}.json.

    Args:
        perfil: Instancia de Perfil a serializar.

    Returns:
        Ruta del archivo guardado.
    """
    os.makedirs("profiles", exist_ok=True)
    ruta = os.path.join("profiles", f"{perfil.nombre_usuario}.json")
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(perfil.to_dict(), f, ensure_ascii=False, indent=2)
    return ruta
