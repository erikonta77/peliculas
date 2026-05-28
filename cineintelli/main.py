"""
CineIntelli - Punto de entrada principal del sistema de recomendación.

Orquesta la carga de datos, el perfil de usuario, el modelo neuronal
y el menú interactivo de consola.
"""

from __future__ import annotations

import os
import random
import sys
import traceback
from typing import Any, Dict, List, Optional

import numpy as np

from data_loader import cargar_dataset, descargar_dataset_ejemplo
from models import Pelicula, Perfil, Recomendador
from utils import (
    cargar_perfil,
    guardar_perfil,
    imprimir_titulo,
    imprimir_tabla,
    limpiar_pantalla,
    validar_entrada,
)

# Analytics y visualizaciones que no dependen de TensorFlow
from analytics import (
    compatibilidad_perfiles,
    evaluar_recomendaciones,
    estadisticas_catalogo,
    generar_informe_tendencias,
    tendencias_temporales,
)
from visualizer import (
    grafico_distribucion_generos,
    grafico_perdida_entrenamiento,
    grafico_scatter_popularidad,
    grafico_tendencia_anual,
    grafico_top_generos,
)

# ---------------------------------------------------------------------------
# Degradación graceful si TensorFlow no está instalado
# ---------------------------------------------------------------------------
try:
    from analytics import construir_modelo_recomendacion, similitud_neuronal

    TENSORFLOW_DISPONIBLE = True
except ImportError:
    TENSORFLOW_DISPONIBLE = False

BANNER = r"""
   _______  ____  __  ___         __    _ ___
  / ____/ |/ / / / / / (_)_______/ /_  (_)__ \
 / /   |   / / / / / / / / ___/ __ / / __/ /
/ /___ /   / /_/ / /_/ / (__  ) / / / / / __/
\____//_/|_\____/\____/_/____/_/ /_/_(_)____/
        Sistema Inteligente de Recomendación
"""


class CineIntelliApp:
    """Aplicación principal que encapsula estado y flujo de CineIntelli."""

    def __init__(self) -> None:
        self.catalogo: List[Pelicula] = []
        self.perfil: Optional[Perfil] = None
        self.encoder: Optional[Any] = None
        self.matriz_catalogo: Optional[np.ndarray] = None
        self.preprocesadores: Optional[Dict[str, Any]] = None
        self.historial_entrenamiento: Optional[Any] = None
        self.ultimas_recomendaciones: List[Pelicula] = []
        self.tensorflow_disponible = TENSORFLOW_DISPONIBLE

    # ------------------------------------------------------------------
    # Inicio
    # ------------------------------------------------------------------

    def iniciar(self) -> None:
        """Orquesta el arranque completo de la aplicación."""
        limpiar_pantalla()
        print(BANNER)
        self._cargar_perfil_usuario()
        self._cargar_datos()
        self._configurar_modelo()
        self._mostrar_dashboard()
        self._menu_principal()

    def _cargar_perfil_usuario(self) -> None:
        """Solicita nombre y carga o crea un perfil."""
        nombre = input("¿Cuál es tu nombre de usuario? ").strip()
        if not nombre:
            nombre = "invitado"
        perfil_cargado = cargar_perfil(nombre)
        if perfil_cargado:
            print(f"[main] Perfil '{nombre}' cargado exitosamente.")
            self.perfil = perfil_cargado
        else:
            print(f"[main] Creando nuevo perfil para '{nombre}'.")
            self.perfil = Perfil(nombre_usuario=nombre)
            guardar_perfil(self.perfil)

    def _cargar_datos(self) -> None:
        """Carga el dataset de películas, descargándolo si es necesario."""
        print("[main] Buscando dataset local...")
        ruta_dataset = os.path.join("data", "tmdb_movies.csv")
        if not os.path.isfile(ruta_dataset):
            print("[main] Dataset no encontrado. Descargando ejemplo...")
            descargar_dataset_ejemplo()
        print("[main] Cargando películas en memoria...")
        self.catalogo = cargar_dataset(ruta_dataset)
        print(f"[main] {len(self.catalogo)} películas listas para recomendar.")

    def _configurar_modelo(self) -> None:
        """Entrena o carga el modelo neuronal según disponibilidad."""
        if self.tensorflow_disponible:
            print("[main] Configurando modelo neuronal (Autoencoder)...")
            (
                self.encoder,
                self.matriz_catalogo,
                self.preprocesadores,
                self.historial_entrenamiento,
            ) = construir_modelo_recomendacion(self.catalogo)
            print("[main] Modelo listo.")
        else:
            print(
                "[AVISO] TensorFlow no está instalado. "
                "Se usará el recomendador clásico basado en reglas."
            )

    def _mostrar_dashboard(self) -> None:
        """Muestra resumen rápido al usuario tras el arranque."""
        print()
        imprimir_titulo(f"Dashboard — {self.perfil.nombre_usuario}", ancho=60)
        print(f"  Películas en catálogo : {len(self.catalogo)}")
        generos_unicos: set[str] = set()
        for p in self.catalogo:
            generos_unicos.update(p.generos)
        print(f"  Géneros disponibles   : {len(generos_unicos)}")
        print(f"  Recomendaciones config: {self.perfil.cantidad_recomendaciones}")

        recomendadas = self._obtener_recomendaciones(3)
        print("  Top 3 sugerencias para ti:")
        for i, p in enumerate(recomendadas, 1):
            print(f"    {i}. {p}")
        print()

    # ------------------------------------------------------------------
    # Motor de recomendaciones
    # ------------------------------------------------------------------

    def _obtener_recomendaciones(
        self, n: Optional[int] = None
    ) -> List[Pelicula]:
        """
        Genera recomendaciones usando el autoencoder si está disponible,
        o el recomendador clásico en caso contrario.
        """
        cantidad = n if n is not None else self.perfil.cantidad_recomendaciones

        if (
            self.tensorflow_disponible
            and self.encoder is not None
            and self.preprocesadores is not None
        ):
            proc = self.preprocesadores
            generos_vec = proc["mlb"].transform(
                [self.perfil.generos_favoritos]
            )[0]

            punt_val = proc["scaler_punt"].transform(
                [[self.perfil.puntuacion_minima]]
            )[0, 0]
            mediana_pop = float(
                np.median([p.popularidad for p in self.catalogo])
            )
            pop_val = proc["scaler_pop"].transform([[mediana_pop]])[0, 0]

            decada_rep = (self.perfil.anio_min + self.perfil.anio_max) // 2
            decada_rep = (decada_rep // 10) * 10
            decada_onehot = np.zeros(len(proc["decadas_unique"]))
            idx = proc["decada_map"].get(decada_rep, 0)
            decada_onehot[idx] = 1

            vector_perfil = np.concatenate(
                [generos_vec, [punt_val], [pop_val], decada_onehot]
            )
            scores = similitud_neuronal(
                self.encoder, vector_perfil, self.matriz_catalogo
            )
            indices = np.argsort(scores)[::-1]
            return [self.catalogo[i] for i in indices[:cantidad]]

        recomendador = Recomendador(self.catalogo, self.perfil)
        return recomendador.recomendar(cantidad)

    # ------------------------------------------------------------------
    # Menú principal
    # ------------------------------------------------------------------

    def _menu_principal(self) -> None:
        """Bucle principal de navegación por consola."""
        while True:
            imprimir_titulo("MENÚ PRINCIPAL", ancho=60)
            print("  [1] Obtener recomendaciones")
            print("  [2] Explorar catálogo")
            print("  [3] Visualizar estadísticas")
            print("  [4] Modo CineRoulette")
            print("  [5] Comparar películas")
            print("  [6] Compatibilidad de perfiles")
            print("  [7] Evaluar recomendaciones")
            print("  [8] Mi perfil")
            print("  [9] Salir")
            print()

            try:
                opcion = validar_entrada(
                    "Selecciona una opción:",
                    tipo="int",
                    minimo=1,
                    maximo=9,
                )
            except ValueError:
                print("[Error] Opción inválida.\n")
                continue

            try:
                if opcion == 1:
                    self._opcion_recomendaciones()
                elif opcion == 2:
                    self._opcion_explorar()
                elif opcion == 3:
                    self._opcion_visualizar()
                elif opcion == 4:
                    self._opcion_cineroulette()
                elif opcion == 5:
                    self._opcion_comparar()
                elif opcion == 6:
                    self._opcion_compatibilidad()
                elif opcion == 7:
                    self._opcion_evaluar()
                elif opcion == 8:
                    self._opcion_perfil()
                elif opcion == 9:
                    self._salir()
            except Exception as exc:
                print(f"\n[Error] {exc}\n")
                traceback.print_exc()
                input("Presiona Enter para continuar...")

    # ------------------------------------------------------------------
    # Opciones del menú
    # ------------------------------------------------------------------

    def _opcion_recomendaciones(self) -> None:
        limpiar_pantalla()
        imprimir_titulo("Tus Recomendaciones", ancho=60)
        n = self.perfil.cantidad_recomendaciones
        try:
            resp = input(
                f"¿Cuántas recomendaciones deseas? (default {n}): "
            ).strip()
            if resp:
                n = int(resp)
        except ValueError:
            pass

        recomendadas = self._obtener_recomendaciones(n)
        self.ultimas_recomendaciones = recomendadas
        for p in recomendadas:
            self.perfil.agregar_al_historial(
                p, {"modo": "recomendacion"}
            )

        filas = []
        for i, p in enumerate(recomendadas, 1):
            filas.append(
                {
                    "#": i,
                    "Título": p.titulo,
                    "Año": p.anio,
                    "Punt": round(p.puntuacion, 1),
                    "Géneros": ", ".join(p.generos[:2]),
                }
            )
        imprimir_tabla(filas, ["#", "Título", "Año", "Punt", "Géneros"])
        input("\nPresiona Enter para continuar...")

    def _opcion_explorar(self) -> None:
        limpiar_pantalla()
        imprimir_titulo("Explorar Catálogo", ancho=60)
        stats = estadisticas_catalogo(self.catalogo)
        print(
            f"Puntuación media: {stats['puntuacion']['media']:.2f} "
            f"(std: {stats['puntuacion']['std']:.2f})"
        )
        print(
            f"Popularidad media: {stats['popularidad']['media']:.2f} "
            f"(std: {stats['popularidad']['std']:.2f})"
        )
        print(f"Total géneros: {len(stats['distribucion_generos']['conteo'])}")
        print("\nTop 5 mejor calificadas:")
        for titulo, punt in stats["top_10_calificadas"][:5]:
            print(f"  {titulo}: {punt}")
        print("\nTop 5 más populares:")
        for titulo, pop in stats["top_10_populares"][:5]:
            print(f"  {titulo}: {pop}")
        input("\nPresiona Enter para continuar...")

    def _opcion_visualizar(self) -> None:
        limpiar_pantalla()
        imprimir_titulo("Generando Visualizaciones", ancho=60)
        print("1/5 Distribución de géneros...")
        grafico_distribucion_generos(self.catalogo)
        print("2/5 Tendencia anual...")
        grafico_tendencia_anual(self.catalogo)
        print("3/5 Top géneros...")
        grafico_top_generos(self.catalogo)
        print("4/5 Scatter popularidad...")
        grafico_scatter_popularidad(self.catalogo)
        if self.historial_entrenamiento is not None:
            print("5/5 Pérdida de entrenamiento...")
            grafico_perdida_entrenamiento(self.historial_entrenamiento)
        else:
            print(
                "5/5 No hay historial de entrenamiento "
                "(modelo cargado desde disco)."
            )
        print("\nGráficos guardados en output/")
        input("Presiona Enter para continuar...")

    def _opcion_cineroulette(self) -> None:
        limpiar_pantalla()
        imprimir_titulo("CineRoulette", ancho=60)
        generos_fav = set(self.perfil.generos_favoritos)

        candidatas = [
            p
            for p in self.catalogo
            if not (set(p.generos) & generos_fav)
        ]
        if len(candidatas) < 5:
            candidatas = [
                p
                for p in self.catalogo
                if not set(p.generos).issubset(generos_fav)
            ]
        if len(candidatas) < 5:
            candidatas = self.catalogo[:]

        seleccion = random.sample(candidatas, min(5, len(candidatas)))
        print("5 películas fuera de tu zona de confort:\n")
        filas = [
            {
                "#": i + 1,
                "Título": p.titulo,
                "Año": p.anio,
                "Géneros": ", ".join(p.generos[:2]),
            }
            for i, p in enumerate(seleccion)
        ]
        imprimir_tabla(filas, ["#", "Título", "Año", "Géneros"])
        input("\nPresiona Enter para continuar...")

    def _opcion_comparar(self) -> None:
        limpiar_pantalla()
        imprimir_titulo("Comparar Películas", ancho=60)
        titulo_busqueda = (
            input("Buscar título (parcial): ").strip().lower()
        )
        coincidencias = [
            p
            for p in self.catalogo
            if titulo_busqueda in p.titulo.lower()
        ]
        if len(coincidencias) < 2:
            print("Se necesitan al menos 2 coincidencias.")
            input("Presiona Enter...")
            return

        print(f"Se encontraron {len(coincidencias)} películas:")
        for i, p in enumerate(coincidencias[:10], 1):
            print(f"  {i}. {p.titulo} ({p.anio})")

        try:
            idx1 = (
                int(
                    input("Selecciona primera película (número): ").strip()
                )
                - 1
            )
            idx2 = (
                int(
                    input("Selecciona segunda película (número): ").strip()
                )
                - 1
            )
            p1 = coincidencias[idx1]
            p2 = coincidencias[idx2]
        except (ValueError, IndexError):
            print("Selección inválida.")
            input("Presiona Enter...")
            return

        filas = [
            {
                "Atributo": "Título",
                "Película 1": p1.titulo,
                "Película 2": p2.titulo,
            },
            {
                "Atributo": "Año",
                "Película 1": str(p1.anio),
                "Película 2": str(p2.anio),
            },
            {
                "Atributo": "Puntuación",
                "Película 1": str(p1.puntuacion),
                "Película 2": str(p2.puntuacion),
            },
            {
                "Atributo": "Popularidad",
                "Película 1": str(round(p1.popularidad, 2)),
                "Película 2": str(round(p2.popularidad, 2)),
            },
            {
                "Atributo": "Géneros",
                "Película 1": ", ".join(p1.generos),
                "Película 2": ", ".join(p2.generos),
            },
            {
                "Atributo": "Idioma",
                "Película 1": p1.idioma,
                "Película 2": p2.idioma,
            },
            {
                "Atributo": "Votos",
                "Película 1": str(p1.votos),
                "Película 2": str(p2.votos),
            },
        ]
        imprimir_tabla(filas, ["Atributo", "Película 1", "Película 2"])
        input("\nPresiona Enter para continuar...")

    def _opcion_compatibilidad(self) -> None:
        limpiar_pantalla()
        imprimir_titulo("Compatibilidad de Perfiles", ancho=60)
        nombre2 = input("Nombre del segundo usuario: ").strip()
        perfil2 = cargar_perfil(nombre2)
        if not perfil2:
            print(f"No se encontró perfil '{nombre2}'.")
            input("Presiona Enter...")
            return

        resultado = compatibilidad_perfiles(
            self.perfil, perfil2, self.catalogo
        )
        print(f"\nÍndice de compatibilidad: {resultado['indice_compatibilidad']}")
        print(
            f"Géneros en común: {', '.join(resultado['generos_comunes']) or 'Ninguno'}"
        )
        print(
            "Películas que les gustarían a ambos: "
            f"{len(resultado['peliculas_ambos'])}"
        )
        if resultado["peliculas_ambos"]:
            filas = [
                {
                    "Título": p.titulo,
                    "Año": p.anio,
                    "Punt": round(p.puntuacion, 1),
                }
                for p in resultado["peliculas_ambos"][:5]
            ]
            imprimir_tabla(filas, ["Título", "Año", "Punt"])
        input("\nPresiona Enter para continuar...")

    def _opcion_evaluar(self) -> None:
        limpiar_pantalla()
        imprimir_titulo("Evaluar Recomendaciones", ancho=60)
        if not self.ultimas_recomendaciones:
            print(
                "No hay recomendaciones previas. "
                "Genera algunas primero (opción 1)."
            )
            input("Presiona Enter...")
            return
        evaluar_recomendaciones(
            self.ultimas_recomendaciones,
            self.perfil.generos_favoritos,
        )
        input("\nPresiona Enter para continuar...")

    def _opcion_perfil(self) -> None:
        limpiar_pantalla()
        imprimir_titulo("Mi Perfil", ancho=60)
        print(self.perfil.resumen())
        print("\n[1] Editar preferencias")
        print("[2] Volver")
        try:
            sub = validar_entrada(
                "Opción:", tipo="int", minimo=1, maximo=2
            )
        except ValueError:
            return
        if sub == 1:
            self._editar_perfil()

    def _editar_perfil(self) -> None:
        """Permite modificar los atributos del perfil actual."""
        print("\nDejar en blanco para mantener el valor actual.")

        nuevo_gen = input(
            f"Géneros favoritos (actual: {', '.join(self.perfil.generos_favoritos)}): "
        ).strip()
        if nuevo_gen:
            self.perfil._generos_favoritos = [
                g.strip()
                for g in nuevo_gen.split(",")
                if g.strip()
            ]

        try:
            val = input(
                f"Año mínimo (actual {self.perfil.anio_min}): "
            ).strip()
            if val:
                self.perfil._anio_min = int(val)
        except ValueError:
            pass

        try:
            val = input(
                f"Año máximo (actual {self.perfil.anio_max}): "
            ).strip()
            if val:
                self.perfil._anio_max = int(val)
        except ValueError:
            pass

        try:
            val = input(
                f"Puntuación mínima (actual {self.perfil.puntuacion_minima}): "
            ).strip()
            if val:
                self.perfil._puntuacion_minima = float(val)
        except ValueError:
            pass

        try:
            val = input(
                f"Cantidad de recomendaciones (actual {self.perfil.cantidad_recomendaciones}): "
            ).strip()
            if val:
                self.perfil._cantidad_recomendaciones = int(val)
        except ValueError:
            pass

        guardar_perfil(self.perfil)
        print("[main] Perfil actualizado y guardado.")

    def _salir(self) -> None:
        """Guarda el perfil y termina la ejecución."""
        guardar_perfil(self.perfil)
        print("\n¡Hasta pronto!\n")
        sys.exit(0)


# ---------------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------------

def main() -> None:
    """Punto de entrada con manejo global de excepciones."""
    try:
        app = CineIntelliApp()
        app.iniciar()
    except KeyboardInterrupt:
        print("\n\n[main] Interrumpido por el usuario.")
        sys.exit(0)
    except Exception as exc:
        print("\n[ERROR CRÍTICO] Ocurrió un error inesperado.")
        print(f"Detalle: {exc}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
