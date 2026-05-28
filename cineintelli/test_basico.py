"""
CineIntelli - Tests básicos sin framework externo.

Ejecutar desde la carpeta del proyecto:
    python test_basico.py

Verifica la creación de entidades, carga de datos,
entrenamiento del modelo neuronal, similitud coseno,
evaluación y generación de gráficos.
"""

from __future__ import annotations

import os
import sys
import traceback
from typing import List

# ---------------------------------------------------------------------------
# 1. Creación de entidades
# ---------------------------------------------------------------------------

def test_crear_pelicula() -> bool:
    """Verifica que Pelicula se instancia correctamente."""
    print("[TEST] Creando Pelicula...")
    from models import Pelicula

    p = Pelicula(
        id=1,
        titulo="Inception",
        generos=["Ciencia Ficción", "Acción"],
        anio=2010,
        puntuacion=8.8,
        popularidad=95.5,
        idioma="en",
        descripcion="Un ladrón que roba secretos...",
        votos=15000,
    )
    assert p.id == 1
    assert p.titulo == "Inception"
    assert "Acción" in p.generos
    assert p.anio == 2010
    assert 0 <= p.puntuacion <= 10
    # es_popular ahora es un método que requiere umbral opcional
    assert p.es_popular() is False  # sin umbral retorna False
    assert p.es_popular(umbral_popularidad=50.0) is True  # 95.5 >= 50.0
    assert p.es_popular(umbral_popularidad=100.0) is False  # 95.5 < 100.0
    print("[PASS] Pelicula creada correctamente.\n")
    return True


def test_es_pelicula_popular() -> bool:
    """Verifica que el método es_pelicula_popular del Recomendador funciona correctamente."""
    print("[TEST] Verificando es_pelicula_popular...")
    from models import Pelicula, Perfil, Recomendador

    catalogo = [
        Pelicula(id=1, titulo="P1", generos=["Drama"], anio=2020, puntuacion=7.0, popularidad=10.0, idioma="en", descripcion="d", votos=100),
        Pelicula(id=2, titulo="P2", generos=["Drama"], anio=2020, puntuacion=7.0, popularidad=20.0, idioma="en", descripcion="d", votos=100),
        Pelicula(id=3, titulo="P3", generos=["Drama"], anio=2020, puntuacion=7.0, popularidad=30.0, idioma="en", descripcion="d", votos=100),
        Pelicula(id=4, titulo="P4", generos=["Drama"], anio=2020, puntuacion=7.0, popularidad=40.0, idioma="en", descripcion="d", votos=100),
        Pelicula(id=5, titulo="P5", generos=["Drama"], anio=2020, puntuacion=7.0, popularidad=50.0, idioma="en", descripcion="d", votos=100),
        Pelicula(id=6, titulo="P6", generos=["Drama"], anio=2020, puntuacion=7.0, popularidad=60.0, idioma="en", descripcion="d", votos=100),
        Pelicula(id=7, titulo="P7", generos=["Drama"], anio=2020, puntuacion=7.0, popularidad=70.0, idioma="en", descripcion="d", votos=100),
        Pelicula(id=8, titulo="P8", generos=["Drama"], anio=2020, puntuacion=7.0, popularidad=80.0, idioma="en", descripcion="d", votos=100),
        Pelicula(id=9, titulo="P9", generos=["Drama"], anio=2020, puntuacion=7.0, popularidad=90.0, idioma="en", descripcion="d", votos=100),
        Pelicula(id=10, titulo="P10", generos=["Drama"], anio=2020, puntuacion=7.0, popularidad=100.0, idioma="en", descripcion="d", votos=100),
    ]
    perfil = Perfil(nombre_usuario="test")
    recomendador = Recomendador(catalogo, perfil)

    # Percentil 75 de [10,20,30,40,50,60,70,80,90,100] = 80 (índice 7)
    umbral = recomendador._evaluar_umbral_popularidad()
    assert umbral == 80.0, f"Umbral esperado 80.0, obtenido {umbral}"

    # P1-P7 no son populares (< 80), P8-P10 sí son populares (>= 80)
    assert recomendador.es_pelicula_popular(catalogo[0]) is False  # P1: 10 < 80
    assert recomendador.es_pelicula_popular(catalogo[6]) is False  # P7: 70 < 80
    assert recomendador.es_pelicula_popular(catalogo[7]) is True   # P8: 80 >= 80
    assert recomendador.es_pelicula_popular(catalogo[9]) is True   # P10: 100 >= 80

    print("[PASS] es_pelicula_popular funciona correctamente.\n")
    return True


def test_crear_perfil() -> bool:
    """Verifica que Perfil se instancia y serializa correctamente."""
    print("[TEST] Creando Perfil...")
    from models import Perfil

    perfil = Perfil(
        nombre_usuario="test_user",
        generos_favoritos=["Drama", "Comedia"],
        anio_min=2000,
        anio_max=2025,
        puntuacion_minima=7.0,
        idioma="es",
        cantidad_recomendaciones=5,
    )
    assert perfil.nombre_usuario == "test_user"
    assert perfil.anio_min == 2000
    assert perfil.cantidad_recomendaciones == 5

    perfil.agregar_al_historial(
        type("P", (), {"id": 1, "titulo": "Test", "anio": 2020, "puntuacion": 8.0})(),
        {"genero": "Drama"},
    )
    assert len(perfil.historial) == 1
    assert "test_user" in perfil.resumen()
    print("[PASS] Perfil creado y serializado correctamente.\n")
    return True


# ---------------------------------------------------------------------------
# 2. Carga de dataset
# ---------------------------------------------------------------------------

def test_cargar_dataset() -> List:
    """Verifica que el dataset se carga sin errores."""
    print("[TEST] Cargando dataset...")
    from data_loader import cargar_dataset

    ruta = os.path.join("data", "tmdb_movies.csv")
    if not os.path.isfile(ruta):
        print("[SKIP] Dataset no encontrado, omitiendo test de carga.\n")
        return []

    catalogo = cargar_dataset(ruta)
    assert len(catalogo) > 0
    assert all(hasattr(p, "titulo") for p in catalogo)
    print(f"[PASS] Dataset cargado: {len(catalogo)} películas.\n")
    return catalogo


# ---------------------------------------------------------------------------
# 3. Modelo neuronal
# ---------------------------------------------------------------------------

def test_modelo_neuronal(catalogo: List) -> tuple:
    """Verifica que el Autoencoder entrena o carga sin excepciones."""
    print("[TEST] Entrenando / cargando modelo neuronal...")
    try:
        from analytics import construir_modelo_recomendacion
    except ImportError as exc:
        print(f"[SKIP] TensorFlow no disponible ({exc}).\n")
        return None, None, None, None

    encoder, matriz, preprocesadores, history = construir_modelo_recomendacion(
        catalogo
    )
    assert encoder is not None
    assert matriz.shape[0] == len(catalogo)
    assert matriz.shape[1] > 0
    print(f"[PASS] Modelo listo. Matriz shape: {matriz.shape}.\n")
    return encoder, matriz, preprocesadores, history


# ---------------------------------------------------------------------------
# 4. Similitud neuronal
# ---------------------------------------------------------------------------

def test_similitud_neuronal(encoder, matriz, preprocesadores, catalogo) -> bool:
    """Verifica que similitud_neuronal retorna scores entre 0 y 1."""
    print("[TEST] Calculando similitud neuronal...")
    from analytics import similitud_neuronal
    import numpy as np

    # Vectorizar una película como "perfil" de prueba
    proc = preprocesadores
    generos_vec = proc["mlb"].transform([[catalogo[0].generos[0]]])[0]
    punt_val = proc["scaler_punt"].transform([[catalogo[0].puntuacion]])[0, 0]
    pop_val = proc["scaler_pop"].transform([[catalogo[0].popularidad]])[0, 0]
    decada = (catalogo[0].anio // 10) * 10
    decada_onehot = np.zeros(len(proc["decadas_unique"]))
    idx = proc["decada_map"].get(decada, 0)
    decada_onehot[idx] = 1

    vector_perfil = np.concatenate([generos_vec, [punt_val], [pop_val], decada_onehot])
    scores = similitud_neuronal(encoder, vector_perfil, matriz)

    assert len(scores) == len(catalogo)
    assert all(0.0 <= s <= 1.0 for s in scores)
    print(f"[PASS] {len(scores)} scores calculados, rango [0, 1].\n")
    return True


# ---------------------------------------------------------------------------
# 5. Evaluación de recomendaciones
# ---------------------------------------------------------------------------

def test_evaluar_recomendaciones(catalogo) -> bool:
    """Verifica que evaluar_recomendaciones genera matriz de confusión."""
    print("[TEST] Evaluando recomendaciones...")
    from analytics import evaluar_recomendaciones

    recomendadas = catalogo[:10]
    generos_esperados = ["Drama", "Comedia"]
    resultado = evaluar_recomendaciones(recomendadas, generos_esperados)

    assert "confusion_matrix" in resultado
    assert "precision_global" in resultado
    assert "recall_global" in resultado
    assert "por_genero" in resultado
    print("[PASS] Evaluación completada sin errores.\n")
    return True


# ---------------------------------------------------------------------------
# 6. Visualizaciones
# ---------------------------------------------------------------------------

def test_generar_graficos(catalogo, history) -> bool:
    """Verifica que los 5 gráficos se generan y guardan en disco."""
    print("[TEST] Generando gráficos...")
    from visualizer import (
        grafico_distribucion_generos,
        grafico_tendencia_anual,
        grafico_top_generos,
        grafico_scatter_popularidad,
        grafico_perdida_entrenamiento,
    )

    rutas = []
    rutas.append(grafico_distribucion_generos(catalogo))
    rutas.append(grafico_tendencia_anual(catalogo))
    rutas.append(grafico_top_generos(catalogo, top_n=5))
    rutas.append(grafico_scatter_popularidad(catalogo))

    if history is not None:
        rutas.append(grafico_perdida_entrenamiento(history))
    else:
        print("[INFO] Sin historial Keras; omitiendo gráfico de pérdida.")
        rutas.append(None)

    for r in rutas:
        if r is not None:
            assert os.path.isfile(r), f"No se generó: {r}"

    print(f"[PASS] {sum(1 for r in rutas if r)} gráficos guardados en output/.\n")
    return True


# ---------------------------------------------------------------------------
# Orquestador
# ---------------------------------------------------------------------------

def run_all() -> None:
    """Ejecuta todos los tests en orden."""
    print("=" * 60)
    print("  CINEINTELLI — TESTS BÁSICOS")
    print("=" * 60)
    print()

    resultados = []

    try:
        resultados.append(("Pelicula", test_crear_pelicula()))
    except Exception as exc:
        resultados.append(("Pelicula", False))
        traceback.print_exc()

    try:
        resultados.append(("es_pelicula_popular", test_es_pelicula_popular()))
    except Exception as exc:
        resultados.append(("es_pelicula_popular", False))
        traceback.print_exc()

    try:
        resultados.append(("Perfil", test_crear_perfil()))
    except Exception as exc:
        resultados.append(("Perfil", False))
        traceback.print_exc()

    catalogo = []
    try:
        catalogo = test_cargar_dataset()
        resultados.append(("Dataset", len(catalogo) > 0))
    except Exception as exc:
        resultados.append(("Dataset", False))
        traceback.print_exc()

    encoder = matriz = preprocesadores = history = None
    if catalogo:
        try:
            encoder, matriz, preprocesadores, history = test_modelo_neuronal(
                catalogo
            )
            resultados.append(("Modelo", encoder is not None))
        except Exception as exc:
            resultados.append(("Modelo", False))
            traceback.print_exc()

    if encoder is not None and matriz is not None:
        try:
            resultados.append(
                ("Similitud", test_similitud_neuronal(encoder, matriz, preprocesadores, catalogo))
            )
        except Exception as exc:
            resultados.append(("Similitud", False))
            traceback.print_exc()
    else:
        resultados.append(("Similitud", False))
        print("[SKIP] Similitud neuronal (sin modelo).\n")

    if catalogo:
        try:
            resultados.append(
                ("Evaluación", test_evaluar_recomendaciones(catalogo))
            )
        except Exception as exc:
            resultados.append(("Evaluación", False))
            traceback.print_exc()
    else:
        resultados.append(("Evaluación", False))

    if catalogo:
        try:
            resultados.append(
                ("Gráficos", test_generar_graficos(catalogo, history))
            )
        except Exception as exc:
            resultados.append(("Gráficos", False))
            traceback.print_exc()
    else:
        resultados.append(("Gráficos", False))

    print("=" * 60)
    print("  RESUMEN")
    print("=" * 60)
    for nombre, ok in resultados:
        estado = "✓ PASS" if ok else "✗ FAIL"
        print(f"  {estado:<10} {nombre}")
    total = len(resultados)
    pasados = sum(1 for _, ok in resultados if ok)
    print(f"\n  Total: {pasados}/{total} tests pasados.")
    print("=" * 60)
    sys.exit(0 if pasados == total else 1)


if __name__ == "__main__":
    run_all()
