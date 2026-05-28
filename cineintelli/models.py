"""
CineIntelli - Modelos de dominio del sistema de recomendación.

Define las entidades principales: películas, perfiles de usuario
y el motor de recomendaciones basado en preferencias explícitas.
"""

from __future__ import annotations

import statistics
from typing import Any, Dict, List, Optional


class Pelicula:
    """Representa una película del catálogo con sus atributos descriptivos."""

    def __init__(
        self,
        id: int,
        titulo: str,
        generos: List[str],
        anio: int,
        puntuacion: float,
        popularidad: float,
        idioma: str,
        descripcion: str,
        votos: int,
    ) -> None:
        """
        Inicializa una instancia de Pelicula.

        Args:
            id: Identificador numérico único de la película.
            titulo: Título oficial de la película.
            generos: Lista de géneros asociados (ej. ["Drama", "Ciencia Ficción"]).
            anio: Año de estreno.
            puntuacion: Puntuación promedio (ej. 0.0 - 10.0).
            popularidad: Índice de popularidad del dataset (mayor es más popular).
            idioma: Código ISO del idioma original (ej. "en", "es").
            descripcion: Sinopsis o resumen de la trama.
            votos: Cantidad total de votos recibidos.
        """
        self._id = id
        self._titulo = titulo
        self._generos = list(generos)
        self._anio = anio
        self._puntuacion = float(puntuacion)
        self._popularidad = float(popularidad)
        self._idioma = idioma
        self._descripcion = descripcion
        self._votos = int(votos)

    @property
    def id(self) -> int:
        """Identificador único de la película."""
        return self._id

    @property
    def titulo(self) -> str:
        """Título de la película."""
        return self._titulo

    @property
    def generos(self) -> List[str]:
        """Lista de géneros de la película."""
        return self._generos

    @property
    def anio(self) -> int:
        """Año de estreno."""
        return self._anio

    @property
    def puntuacion(self) -> float:
        """Puntuación promedio."""
        return self._puntuacion

    @property
    def popularidad(self) -> float:
        """Índice de popularidad."""
        return self._popularidad

    @property
    def idioma(self) -> str:
        """Código ISO del idioma original."""
        return self._idioma

    @property
    def descripcion(self) -> str:
        """Sinopsis de la película."""
        return self._descripcion

    @property
    def votos(self) -> int:
        """Cantidad de votos recibidos."""
        return self._votos

    def __str__(self) -> str:
        """Retorna una representación legible de la película."""
        return f"{self._titulo} ({self._anio}) — {self._puntuacion:.1f}/10"

    def __repr__(self) -> str:
        """Retorna una representación técnica para depuración."""
        return (
            f"Pelicula(id={self._id}, titulo={self._titulo!r}, "
            f"anio={self._anio}, puntuacion={self._puntuacion}, "
            f"popularidad={self._popularidad:.2f})"
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Serializa la película a un diccionario.

        Returns:
            Diccionario con los atributos de la instancia.
        """
        return {
            "id": self._id,
            "titulo": self._titulo,
            "generos": self._generos,
            "anio": self._anio,
            "puntuacion": self._puntuacion,
            "popularidad": self._popularidad,
            "idioma": self._idioma,
            "descripcion": self._descripcion,
            "votos": self._votos,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Pelicula:
        """
        Deserializa una película desde un diccionario.

        Args:
            data: Diccionario con las claves esperadas.

        Returns:
            Nueva instancia de Pelicula.
        """
        return cls(
            id=int(data["id"]),
            titulo=str(data["titulo"]),
            generos=list(data.get("generos", [])),
            anio=int(data["anio"]),
            puntuacion=float(data["puntuacion"]),
            popularidad=float(data["popularidad"]),
            idioma=str(data["idioma"]),
            descripcion=str(data["descripcion"]),
            votos=int(data["votos"]),
        )

    def es_popular(self, umbral_popularidad: Optional[float] = None) -> bool:
        """
        Indica si la película es popular según el percentil 75 del catálogo.

        Args:
            umbral_popularidad: Valor de popularidad correspondiente al
                percentil 75 del catálogo. Si es None, retorna False.

        Returns:
            True si la popularidad de la película >= umbral, False en caso contrario.

        Note:
            El umbral se calcula en :meth:`Recomendador._evaluar_umbral_popularidad`.
            Ejemplo: ``pelicula.es_popular(recomendador._evaluar_umbral_popularidad())``
        """
        if umbral_popularidad is None:
            return False
        return self._popularidad >= umbral_popularidad


class Perfil:
    """Representa el perfil de preferencias de un usuario del sistema."""

    def __init__(
        self,
        nombre_usuario: str,
        generos_favoritos: Optional[List[str]] = None,
        anio_min: int = 1900,
        anio_max: int = 2100,
        puntuacion_minima: float = 0.0,
        idioma: str = "cualquiera",
        cantidad_recomendaciones: int = 10,
    ) -> None:
        """
        Inicializa un perfil de usuario con criterios de filtrado.

        Args:
            nombre_usuario: Nombre o alias del usuario.
            generos_favoritos: Géneros preferidos; None equivale a todos.
            anio_min: Año de estreno mínimo aceptable.
            anio_max: Año de estreno máximo aceptable.
            puntuacion_minima: Puntuación mínima requerida (0.0 - 10.0).
            idioma: Código ISO preferido o "cualquiera".
            cantidad_recomendaciones: Número de películas a recomendar por defecto.
        """
        self._nombre_usuario = nombre_usuario
        self._generos_favoritos = generos_favoritos if generos_favoritos is not None else []
        self._anio_min = anio_min
        self._anio_max = anio_max
        self._puntuacion_minima = puntuacion_minima
        self._idioma = idioma
        self._cantidad_recomendaciones = cantidad_recomendaciones
        self._historial: List[Dict[str, Any]] = []

    @property
    def nombre_usuario(self) -> str:
        """Nombre del usuario."""
        return self._nombre_usuario

    @property
    def generos_favoritos(self) -> List[str]:
        """Géneros preferidos del usuario."""
        return self._generos_favoritos

    @property
    def anio_min(self) -> int:
        """Año de estreno mínimo aceptable."""
        return self._anio_min

    @property
    def anio_max(self) -> int:
        """Año de estreno máximo aceptable."""
        return self._anio_max

    @property
    def puntuacion_minima(self) -> float:
        """Puntuación mínima requerida."""
        return self._puntuacion_minima

    @property
    def idioma(self) -> str:
        """Idioma preferido o 'cualquiera'."""
        return self._idioma

    @property
    def cantidad_recomendaciones(self) -> int:
        """Cantidad de recomendaciones solicitadas por defecto."""
        return self._cantidad_recomendaciones

    @property
    def historial(self) -> List[Dict[str, Any]]:
        """Lista de recomendaciones previamente aceptadas."""
        return self._historial

    def agregar_al_historial(self, pelicula: Pelicula, criterios: Dict[str, Any]) -> None:
        """
        Registra una película recomendada en el historial del usuario.

        Args:
            pelicula: Instancia de Pelicula recomendada.
            criterios: Diccionario con los criterios que coincidieron
                (ej. {"genero": "Drama", "puntuacion": 8.5}).
        """
        entrada = {
            "id": pelicula.id,
            "titulo": pelicula.titulo,
            "anio": pelicula.anio,
            "puntuacion": pelicula.puntuacion,
            "criterios": dict(criterios),
        }
        self._historial.append(entrada)

    def to_dict(self) -> Dict[str, Any]:
        """
        Serializa el perfil a un diccionario.

        Returns:
            Diccionario con los atributos del perfil.
        """
        return {
            "nombre_usuario": self._nombre_usuario,
            "generos_favoritos": self._generos_favoritos,
            "anio_min": self._anio_min,
            "anio_max": self._anio_max,
            "puntuacion_minima": self._puntuacion_minima,
            "idioma": self._idioma,
            "cantidad_recomendaciones": self._cantidad_recomendaciones,
            "historial": list(self._historial),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Perfil:
        """
        Deserializa un perfil desde un diccionario.

        Args:
            data: Diccionario con las claves esperadas.

        Returns:
            Nueva instancia de Perfil.
        """
        perfil = cls(
            nombre_usuario=str(data["nombre_usuario"]),
            generos_favoritos=list(data.get("generos_favoritos", [])),
            anio_min=int(data.get("anio_min", 1900)),
            anio_max=int(data.get("anio_max", 2100)),
            puntuacion_minima=float(data.get("puntuacion_minima", 0.0)),
            idioma=str(data.get("idioma", "cualquiera")),
            cantidad_recomendaciones=int(data.get("cantidad_recomendaciones", 10)),
        )
        perfil._historial = list(data.get("historial", []))
        return perfil

    def resumen(self) -> str:
        """
        Retorna un resumen textual con estadísticas del perfil.

        Returns:
            Cadena multilinea con información del perfil y su historial.
        """
        lineas = [
            f"Perfil: {self._nombre_usuario}",
            f"  Géneros favoritos: {', '.join(self._generos_favoritos) if self._generos_favoritos else 'Todos'}",
            f"  Rango de años: {self._anio_min} – {self._anio_max}",
            f"  Puntuación mínima: {self._puntuacion_minima}",
            f"  Idioma preferido: {self._idioma}",
            f"  Recomendaciones por lote: {self._cantidad_recomendaciones}",
            f"  Películas en historial: {len(self._historial)}",
        ]

        if self._historial:
            puntuaciones = [e["puntuacion"] for e in self._historial if isinstance(e.get("puntuacion"), (int, float))]
            if puntuaciones:
                promedio = statistics.mean(puntuaciones)
                lineas.append(f"  Puntuación media del historial: {promedio:.2f}")

        return "\n".join(lineas)


class Recomendador:
    """
    Motor de recomendaciones que filtra y ordena películas
    según un perfil de usuario y criterios de relevancia.
    """

    def __init__(self, catalogo: List[Pelicula], perfil: Perfil) -> None:
        """
        Inicializa el recomendador con un catálogo y un perfil.

        Args:
            catalogo: Lista completa de películas disponibles.
            perfil: Perfil de preferencias del usuario.
        """
        self._catalogo = list(catalogo)
        self._perfil = perfil
        self._umbral_popularidad: Optional[float] = None

    @property
    def catalogo(self) -> List[Pelicula]:
        """Catálogo completo de películas."""
        return self._catalogo

    @property
    def perfil(self) -> Perfil:
        """Perfil de usuario activo."""
        return self._perfil

    def _evaluar_umbral_popularidad(self) -> float:
        """
        Calcula el percentil 75 de popularidad del catálogo.

        Returns:
            Valor de popularidad correspondiente al percentil 75.
            Si el catálogo está vacío retorna 0.0.
        """
        if not self._catalogo:
            return 0.0
        if self._umbral_popularidad is None:
            popularidades = sorted(p.popularidad for p in self._catalogo)
            idx = int(len(popularidades) * 0.75)
            idx = min(idx, len(popularidades) - 1)
            self._umbral_popularidad = popularidades[idx]
        return self._umbral_popularidad

    def es_pelicula_popular(self, pelicula: Pelicula) -> bool:
        """
        Evalúa si una película es popular según el percentil 75 del catálogo.

        Args:
            pelicula: Película a evaluar.

        Returns:
            True si la popularidad de la película >= percentil 75, False en caso contrario.
        """
        umbral = self._evaluar_umbral_popularidad()
        return pelicula.es_popular(umbral_popularidad=umbral)

    def filtrar_por_criterios(self) -> List[Pelicula]:
        """
        Filtra el catálogo según los criterios del perfil.

        Returns:
            Lista de películas que cumplen los filtros de año,
            puntuación mínima, idioma y géneros favoritos.
        """
        resultado: List[Pelicula] = []
        generos_objetivo = set(self._perfil.generos_favoritos)
        cualquier_idioma = self._perfil.idioma.lower() == "cualquiera"

        for pelicula in self._catalogo:
            if not (self._perfil.anio_min <= pelicula.anio <= self._perfil.anio_max):
                continue
            if pelicula.puntuacion < self._perfil.puntuacion_minima:
                continue
            if not cualquier_idioma and pelicula.idioma.lower() != self._perfil.idioma.lower():
                continue
            if generos_objetivo and not generos_objetivo.intersection(pelicula.generos):
                continue
            resultado.append(pelicula)

        return resultado

    def calcular_puntuacion_relevancia(self, pelicula: Pelicula) -> float:
        """
        Calcula una puntuación de relevancia entre 0 y 1 para una película.

        La fórmula pondera:
        - Puntuación general (30 %)
        - Popularidad relativa al catálogo (30 %)
        - Coincidencia de géneros favoritos (25 %)
        - Proximidad al rango de años preferido (15 %)

        Args:
            pelicula: Película a evaluar.

        Returns:
            Valor entre 0.0 y 1.0 representando la relevancia.
        """
        if not self._catalogo:
            return 0.0

        max_puntuacion = max(p.puntuacion for p in self._catalogo) or 1.0
        max_popularidad = max(p.popularidad for p in self._catalogo) or 1.0

        norm_puntuacion = pelicula.puntuacion / max_puntuacion
        norm_popularidad = pelicula.popularidad / max_popularidad

        generos_objetivo = set(self._perfil.generos_favoritos)
        if generos_objetivo:
            coincidencias = generos_objetivo.intersection(pelicula.generos)
            total_generos = generos_objetivo.union(pelicula.generos)
            score_generos = len(coincidencias) / len(total_generos) if total_generos else 0.0
        else:
            score_generos = 1.0

        centro_anios = (self._perfil.anio_min + self._perfil.anio_max) / 2
        rango_anios = (self._perfil.anio_max - self._perfil.anio_min) or 1
        distancia = abs(pelicula.anio - centro_anios)
        score_anio = max(0.0, 1.0 - (distancia / rango_anios))

        relevancia = (
            0.30 * norm_puntuacion
            + 0.30 * norm_popularidad
            + 0.25 * score_generos
            + 0.15 * score_anio
        )
        return round(min(max(relevancia, 0.0), 1.0), 4)

    def recomendar(self, n: Optional[int] = None) -> List[Pelicula]:
        """
        Genera una lista ordenada de las n mejores películas para el perfil.

        Args:
            n: Cantidad de películas a retornar. Si es None, usa
                la cantidad configurada en el perfil.

        Returns:
            Lista de películas ordenadas por relevancia descendente.
        """
        cantidad = n if n is not None else self._perfil.cantidad_recomendaciones
        candidatas = self.filtrar_por_criterios()

        scored = [
            (pelicula, self.calcular_puntuacion_relevancia(pelicula))
            for pelicula in candidatas
        ]
        scored.sort(key=lambda x: x[1], reverse=True)

        return [pelicula for pelicula, _ in scored[:cantidad]]

    def peliculas_destacadas(self, genero: Optional[str] = None, n: int = 10) -> List[Pelicula]:
        """
        Retorna las películas más destacadas del catálogo, opcionalmente filtradas por género.

        El orden se define por una métrica combinada de puntuación y popularidad.

        Args:
            genero: Género por el cual filtrar; None incluye todos.
            n: Cantidad máxima de películas a retornar.

        Returns:
            Lista de películas destacadas ordenadas por métrica combinada.
        """
        max_popularidad = max((p.popularidad for p in self._catalogo), default=1.0) or 1.0
        max_puntuacion = max((p.puntuacion for p in self._catalogo), default=1.0) or 1.0

        seleccion = self._catalogo
        if genero:
            genero_normalizado = genero.lower()
            seleccion = [p for p in self._catalogo if any(g.lower() == genero_normalizado for g in p.generos)]

        scored = []
        for pelicula in seleccion:
            metrica = 0.6 * (pelicula.puntuacion / max_puntuacion) + 0.4 * (pelicula.popularidad / max_popularidad)
            scored.append((pelicula, metrica))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [pelicula for pelicula, _ in scored[:n]]
