# Documento de Transferencia Técnica — CineIntelli

**Fecha:** 2026-05-28
**Versión del proyecto:** 1.0.0 (funcional, completo)
**Autor original de la implementación:** Claude Opus 4.7 (Anthropic)
**Repositorio:** https://github.com/erikonta77/peliculas

---

# 1. VISIÓN GENERAL DEL PROYECTO

## Nombre del proyecto
**CineIntelli** — Sistema de Análisis y Recomendación de Películas

## Objetivo principal
Construir un sistema de recomendación de películas basado en contenido que procese datasets públicos (MovieLens / TMDB), genere recomendaciones personalizadas mediante embeddings neuronales (Autoencoder) o un motor clásico basado en reglas, y visualice estadísticas del catálogo.

## Problema que resuelve
Los usuarios necesitan descubrir películas alineadas a sus preferencias sin navegar catálogos masivos manualmente. CineIntelli filtra por géneros, años, puntuación e idioma; aprende representaciones latentes de las películas mediante un Autoencoder; y compara perfiles de usuario para sugerir contenido en grupo.

## Estado actual del proyecto
**COMPLETO Y FUNCIONAL.** Todas las funcionalidades solicitadas han sido implementadas, probadas y empujadas al repositorio remoto. El sistema ejecuta end-to-end desde consola sin errores.

## Nivel de avance aproximado
100% de las funcionalidades MVP entregadas:
- Carga y limpieza de datos (100%)
- Modelado de dominio POO (100%)
- Motor de recomendación clásico (100%)
- Autoencoder Keras + embeddings (100%)
- Visualización de 5 gráficos (100%)
- Menú interactivo CLI (100%)
- Tests básicos sin framework (100%)
- Documentación README (100%)

## Stack tecnológico completo

| Capa | Tecnología | Versión probada | Propósito |
|------|------------|-----------------|-----------|
| Lenguaje | Python | 3.11.2 | Lógica de negocio |
| Datos | Pandas | 3.0.3 | Carga, limpieza, agrupaciones |
| Numérico | NumPy | 2.4.6 | Vectorización, álgebra lineal |
| ML/Deep Learning | TensorFlow / Keras | 2.21.0 | Autoencoder para embeddings |
| ML Clásico | Scikit-learn | 1.8.0 | Preprocesamiento, métricas, similitud coseno |
| Visualización | Matplotlib + Seaborn | últimas compatibles | Gráficos estadísticos |
| Entrada/Salida | JSON, pickle, urllib | stdlib | Serialización y descarga |

## Arquitectura general

Arquitectura **modular monolítica** estilo "scripts Python con POO". No es un microservicio ni una app web; es una aplicación de consola (CLI) con separación de responsabilidades por módulo.

```
┌─────────────────────────────────────────────────────────────┐
│                         CineIntelli                          │
├─────────────────────────────────────────────────────────────┤
│  main.py           → Orquestador CLI (CineIntelliApp)        │
│  models.py         → Entidades de dominio (Pelicula, Perfil) │
│  data_loader.py    → ETL: CSV/JSON → list[Pelicula]          │
│  analytics.py      → Estadísticas + Autoencoder + Evaluación │
│  visualizer.py     → 5 generadores de gráficos PNG           │
│  utils.py          → Utilidades de consola (tablas, input)   │
│  test_basico.py    → 7 tests autoejecutables sin pytest      │
└─────────────────────────────────────────────────────────────┘
```

## Filosofía de diseño usada

1. **POO estricta:** Todas las entidades principales son clases con encapsulamiento, properties, type hints y docstrings.
2. **Inmutabilidad preferente:** Los objetos de dominio (Pelicula) no tienen setters públicos.
3. **Fail-soft:** Si TensorFlow no está instalado, el sistema degrada automáticamente al recomendador clásico sin crash.
4. **Persistencia simple:** Perfiles en JSON plano, modelo en `.keras`, preprocesadores en `.pkl`.
5. **Sin frameworks web innecesarios:** El alcance era CLI; no se agregó Flask/FastAPI/Django.

---

# 2. CONTEXTO FUNCIONAL

## Qué hace el sistema

CineIntelli permite a un usuario:
1. Crear un perfil con géneros favoritos, rango de años, puntuación mínima e idioma preferido.
2. Cargar un catálogo de películas (CSV/JSON) desde MovieLens o TMDB.
3. Recibir recomendaciones personalizadas mediante un Autoencoder que aprende embeddings de 16 dimensiones.
4. Explorar estadísticas del catálogo (tops, distribuciones, correlaciones).
5. Visualizar 5 tipos de gráficos estadísticos.
6. Jugar a "CineRoulette" (películas fuera del perfil habitual).
7. Comparar dos películas lado a lado.
8. Medir compatibilidad entre dos perfiles de usuario.
9. Evaluar la calidad de las recomendaciones con matriz de confusión.

## Cómo funciona (pipeline técnico)

```
1. Dataset CSV (MovieLens/TMDB/YBI)
   ↓
2. data_loader.py  → Limpieza (nulos → mediana/texto), normalización de
                     géneros al catálogo canónico español, eliminación de
                     duplicados por título+año
   ↓
3. models.Pelicula → Lista de objetos de dominio
   ↓
4. analytics.py    → Vectorización (one-hot géneros + MinMax puntuación/
                     popularidad + one-hot década) = matriz N×31
   ↓
5. Autoencoder     → Comprime a embeddings N×16
   ↓
6. Perfil usuario  → Vectorizado con mismos preprocesadores
   ↓
7. Similitud coseno→ Scores entre perfil y cada película
   ↓
8. Top-N ordenadas → Recomendaciones finales
```

## Flujo completo del usuario

1. Ejecuta `python main.py`.
2. Ve el banner ASCII de CineIntelli.
3. Ingresa su nombre de usuario.
4. El sistema carga su perfil JSON previo o crea uno nuevo.
5. Descarga automáticamente el dataset TMDB si no existe localmente.
6. El sistema entrena o carga el Autoencoder.
7. Muestra un dashboard con top 3 recomendaciones.
8. Presenta el menú de 9 opciones.
9. El usuario interactúa en bucle hasta elegir "Salir".

## Casos de uso importantes

| ID | Caso de uso | Actor | Módulos involucrados |
|----|-------------|-------|---------------------|
| UC1 | Obtener recomendaciones personalizadas | Usuario | main, analytics, models |
| UC2 | Explorar estadísticas del catálogo | Usuario | analytics, visualizer |
| UC3 | Generar gráficos | Usuario | visualizer |
| UC4 | Descubrir películas fuera del perfil | Usuario | main, models |
| UC5 | Comparar dos películas | Usuario | main, utils |
| UC6 | Medir compatibilidad con otro usuario | Usuario | main, analytics |
| UC7 | Evaluar calidad de recomendaciones | Sistema/Usuario | analytics |

## Reglas de negocio

1. **Normalización de géneros:** Todos los géneros se traducen a un catálogo canónico de 20 géneros en español (Acción, Aventura, Animación, Comedia, Crimen, Documental, Drama, Fantasía, Terror, Historia, Música, Misterio, Romance, Ciencia Ficción, Thriller, Western, Familiar, Biográfico, Deportes, Guerra).
2. **Limpieza de nulos:** Numéricos → mediana; texto → `"Desconocido"`.
3. **Eliminación de duplicados:** Por combinación única de `título + año`.
4. **Filtrado de perfil:** AND lógico entre año ∈ [min, max], puntuación ≥ mínima, idioma coincide (o "cualquiera"), género ∩ favoritos ≠ ∅.
5. **Relevancia clásica:** Ponderada 30% puntuación + 30% popularidad + 25% géneros + 15% proximidad temporal.
6. **Autoencoder:** Si existe `output/modelo_recomendador.keras`, se carga; si no, se entrena con 50 epochs, Adam, MSE.

## Restricciones importantes

- **CLI únicamente:** No hay API REST ni interfaz web.
- **Dataset local:** Depende de `data/tmdb_movies.csv` o descarga automática de un URL fijo (YBI Foundation).
- **TensorFlow opcional:** Sin TF, solo funciona el recomendador clásico (no hay embeddings neuronales).
- **Sin base de datos relacional:** Todo es archivos planos (CSV, JSON, .keras, .pkl).

---

# 3. ESTRUCTURA DEL PROYECTO

## Estructura de carpetas

```
cineintelli/
├── main.py                  # Punto de entrada, menú interactivo, orquestador
├── models.py                # Pelicula, Perfil, Recomendador
├── data_loader.py           # Carga CSV/JSON, limpieza, normalización géneros
├── analytics.py             # Estadísticas, Autoencoder, evaluación, compatibilidad
├── visualizer.py            # 5 funciones de gráficos matplotlib/seaborn
├── utils.py                 # Utilidades de consola (tablas, validación, perfiles JSON)
├── test_basico.py           # 7 tests sin pytest (assert + print)
├── requirements.txt         # Dependencias pip
├── README.md                # Documentación pública
├── TRANSFERENCIA_TECNICA.md # Este documento
├── .gitignore               # Ignora venv, datos locales, outputs
│
├── data/
│   ├── .gitkeep
│   └── tmdb_movies.csv      # Dataset de ejemplo (4760 películas, ~23 MB)
│
├── output/
│   ├── .gitkeep
│   ├── modelo_recomendador.keras   # Modelo Keras entrenado
│   ├── preprocessors.pkl           # Scalers + encoders serializados
│   └── *.png                       # Gráficos generados (timestamp)
│
└── profiles/
    ├── .gitkeep
    └── {nombre_usuario}.json       # Perfiles serializados
```

## Responsabilidad de cada módulo

### `models.py` — Dominio puro
- `Pelicula`: Entidad inmutable con 9 atributos, serialización `to_dict/from_dict`, `__str__`, `__repr__`, property `es_popular` (stub que requiere catálogo).
- `Perfil`: Entidad mutable con preferencias del usuario, historial de recomendaciones aceptadas, método `resumen()` con estadísticas.
- `Recomendador`: Motor clásico. Filtra por criterios del perfil, calcula relevancia ponderada (0-1), ordena y retorna top-N. También expone `peliculas_destacadas(genero, n)`.

### `data_loader.py` — Ingesta y ETL
- `cargar_dataset(ruta)`: Detecta CSV/JSON por extensión, normaliza nombres de columnas de MovieLens/TMDB, limpia nulos, elimina duplicados, traduce géneros al catálogo canónico español. Retorna `list[Pelicula]`.
- `descargar_dataset_ejemplo()`: Descarga el CSV de muestra desde `https://raw.githubusercontent.com/YBI-Foundation/Dataset/main/Movies%20Recommendation.csv` y lo guarda en `data/tmdb_movies.csv`.
- `generar_informe_calidad(stats)`: Retorna string formateado con métricas del proceso de limpieza.

**Mapeo de columnas soportado:**
- `title/titulo/movie_title` → `titulo`
- `genres/generos/movie_genre` → `generos`
- `release_date/anio/movie_release_date` → `anio`
- `vote_average/puntuacion/movie_vote` → `puntuacion`
- `popularity/popularidad/movie_popularity` → `popularidad`
- `original_language/idioma/movie_language` → `idioma`
- `overview/descripcion/movie_overview` → `descripcion`
- `vote_count/votos/movie_vote_count` → `votos`
- `id/movie_id` → `id`

**Normalización de géneros:**
Soporta pipe-separated (`Action|Adventure`), JSON string con lista de objetos (`[{"name":"Action"}]`), lista de strings, y fallback por reconocimiento de substrings ordenados por longitud descendente (para que "science fiction" se matchee antes que "fiction").

### `analytics.py` — ML y métricas
- `estadisticas_catalogo(catalogo)`: Media/mediana/std de puntuación/popularidad, distribución por género (conteo + %), distribución por década, top 10 populares/calificadas.
- `tendencias_temporales(catalogo)`: Géneros en ascenso (últimos 5 años vs década anterior), año de mayor producción por género, correlación año vs puntuación media (`np.corrcoef`).
- `construir_modelo_recomendacion(catalogo)`: **Función crítica.** Entrena o carga el Autoencoder. Retorna `(encoder, matriz_X, preprocesadores, history)`.
- `similitud_neuronal(encoder, vector_perfil, catalogo_vectorizado)`: Genera embeddings y calcula similitud coseno. Retorna lista de scores.
- `evaluar_recomendaciones(recomendadas, generos_esperados)`: Matriz de confusión, precisión y recall globales, y métricas por género esperado.
- `compatibilidad_perfiles(p1, p2, catalogo)`: Índice Jaccard de géneros, intersección de filtros, películas que satisfacen ambos perfiles.
- `generar_informe_tendencias(catalogo)`: Texto legible con hallazgos clave.

### `visualizer.py` — Gráficos
- `grafico_distribucion_generos`: Barras horizontales `Blues_r`, valores anotados, guarda PNG.
- `grafico_tendencia_anual`: Línea de puntuación media por año + `fill_between` de std + línea de tendencia `np.polyfit`.
- `grafico_top_generos`: Barras agrupadas (mejor calificada vs más popular) por top-N géneros, paleta `muted`.
- `grafico_scatter_popularidad`: Scatter puntuación vs popularidad, tamaño por votos, color por género principal, regresión superpuesta (`regplot` con `scatter=False`).
- `grafico_perdida_entrenamiento(history)`: Loss y val_loss por época, anotación de la época de menor val_loss.

Todas usan estilo `whitegrid`, 150 dpi, `figsize` configurable, guardan en `output/` con timestamp, y cierran figura con `plt.close()`.

### `utils.py` — Consola y persistencia
- `limpiar_pantalla()`: `clear` (Linux/macOS) o `cls` (Windows).
- `imprimir_titulo(texto, ancho)`: Recuadro ASCII con `╔═╗`.
- `imprimir_tabla(lista_dicts, columnas)`: Tabla con bordes `+---+`, anchos auto-calculados.
- `validar_entrada(prompt, tipo, min, max, opciones)`: Lee input, valida tipo, rango y opciones permitidas. Hasta 3 reintentos; lanza `ValueError` si se agotan.
- `cargar_perfil(nombre)` / `guardar_perfil(perfil)`: JSON en `profiles/{nombre}.json`.

### `main.py` — Orquestador
Clase `CineIntelliApp` con estado encapsulado:
- `catalogo`, `perfil`, `encoder`, `matriz_catalogo`, `preprocesadores`, `historial_entrenamiento`, `ultimas_recomendaciones`.
- Métodos `_cargar_perfil_usuario`, `_cargar_datos`, `_configurar_modelo`, `_mostrar_dashboard`.
- `_menu_principal()` con bucle de 9 opciones.
- Degradación graceful: si `import tensorflow` falla, usa `Recomendador` clásico.

---

# 4. RESUMEN TÉCNICO DETALLADO

## Lógica implementada

### Motor clásico (Recomendador)
1. **Filtrado:** Aplica restricciones duras del perfil (año, puntuación, idioma, géneros).
2. **Scoring:** Para cada película filtrada, calcula relevancia ponderada:
   - `norm_puntuacion = p.puntuacion / max_puntuacion`
   - `norm_popularidad = p.popularidad / max_popularidad`
   - `score_generos = |intersección| / |unión|` (0 si no hay géneros favoritos)
   - `score_anio = 1 - distancia_al_centro / rango_años`
   - `relevancia = 0.30*norm_puntuacion + 0.30*norm_popularidad + 0.25*score_generos + 0.15*score_anio`
3. **Ranking:** Ordena descendente y toma top-N.

### Motor neuronal (Autoencoder)
1. **Vectorización:**
   - Géneros: `MultiLabelBinarizer` → one-hot (~20 dims).
   - Puntuación: `MinMaxScaler` → [0, 1].
   - Popularidad: `MinMaxScaler` → [0, 1].
   - Década: one-hot manual según décadas únicas del catálogo.
   - Resultado: matriz `X` de shape `(N, 31)` para el dataset actual.
2. **Arquitectura:**
   - Encoder: `Input → Dense(64, relu) → Dense(32, relu) → Dense(16, relu)` (bottleneck).
   - Decoder: `Dense(32, relu) → Dense(64, relu) → Dense(n_features, sigmoid)`.
   - Optimizador: Adam. Pérdida: MSE.
3. **Entrenamiento:** 50 epochs, batch 32, validation_split=0.1, verbose=0.
4. **Persistencia:** Modelo en `output/modelo_recomendador.keras`, preprocesadores en `output/preprocessors.pkl`.
5. **Inferencia:** El encoder comprime perfil y catálogo a 16D; similitud coseno entre embeddings.

### Vectorización del perfil para similitud neuronal
Dado que un `Perfil` no es una `Pelicula`, se construye un vector artificial:
- **Géneros:** `perfil.generos_favoritos` via `mlb.transform`.
- **Puntuación:** `perfil.puntuacion_minima` (escalada).
- **Popularidad:** mediana de popularidad del catálogo completo (escalada).
- **Década:** década central del rango `[anio_min, anio_max]`.

**Nota importante:** Esta es una aproximación pragmática. Un enfoque más sofisticado requeriría que el usuario califique películas individuales para construir un vector promedio real.

## Algoritmos usados

- **Filtrado:** Restricciones duras con intersección de conjuntos.
- **Ranking clásico:** Ponderación lineal con normalización min-max implícita.
- **Embeddings:** Autoencoder denso fully-connected (no convolucional ni recurrente).
- **Similitud:** Coseno (`sklearn.metrics.pairwise.cosine_similarity`).
- **Evaluación:** Confusion matrix binaria (coincide con géneros esperados vs no coincide).
- **Tendencias:** Correlación de Pearson (`np.corrcoef`), regresión lineal (`np.polyfit`).

## Patrones de diseño

- **Entity:** `Pelicula`, `Perfil`.
- **Repository-like:** `data_loader.cargar_dataset` (abstrae el origen de datos).
- **Strategy:** Motor clásico vs neuronal seleccionado en runtime según disponibilidad de TensorFlow.
- **Facade:** `CineIntelliApp` simplifica la interacción entre 6 módulos.
- **Factory method:** `Perfil.from_dict`, `Pelicula.from_dict`.

## Decisiones arquitectónicas y razones

1. **CLI en lugar de Web:** El requerimiento fue específicamente CLI. Agregar una web layer habría multiplicado la complejidad sin valor añadido para el MVP.
2. **JSON plano para perfiles:** No se necesita ACID ni consultas complejas; JSON es suficiente y portable.
3. **Autoencoder en lugar de TF-IDF puro:** Aunque la descripción inicial mencionaba TF-IDF + coseno, el usuario solicitó explícitamente un Autoencoder Keras en `analytics.py`. El Autoencoder captura interacciones no lineales entre géneros, puntuación, popularidad y década, algo que TF-IDF no haría con estas features mixtas.
4. **Pickle para preprocesadores:** `MinMaxScaler` y `MultiLabelBinarizer` no son serializables nativamente a JSON sin perder estado interno. Pickle es la solución estándar de scikit-learn.
5. **Dataset YBI Foundation:** Se probaron múltiples URLs del dataset TMDB 5000 movies en GitHub raw; todas devolvieron 404. La URL de YBI Foundation (`Movies Recommendation.csv`) fue la única confiable encontrada. Este dataset usa nombres de columnas tipo `Movie_Title`, `Movie_Genre`, etc., lo cual requirió expandir el `MAPEO_COLUMNAS`.

## Optimizaciones realizadas

- **Lazy evaluation del umbral de popularidad:** `Recomendador._evaluar_umbral_popularidad()` se calcula una sola vez y se cachea.
- **Reutilización del modelo:** El Autoencoder se entrena una sola vez y se carga desde disco en ejecuciones posteriores.
- **Pandas copy() explícito:** Después de `df.rename()`, se usa `.copy()` para evitar el problema `SettingWithCopy` de pandas que bloqueaba asignaciones posteriores.

## Trade-offs aceptados

- **Aproximación del vector de perfil:** Como no hay ratings explícitos del usuario, se usa un vector sintético. Esto puede producir recomendaciones menos precisas que un sistema con feedback explícito.
- **Evaluación simplificada:** La matriz de confusión tiene `y_pred = [1, 1, ...]` porque todas las películas fueron "predichas" como recomendadas. Esto hace que recall siempre sea 1.0 y la métrica sea esencialmente "qué proporción de las recomendadas coinciden con géneros esperados". Se aceptó porque no hay un ground truth objetivo de "buena" recomendación en este dataset.
- **Sin tests unitarios formales:** `test_basico.py` usa asserts y prints en lugar de pytest/unittest. Se aceptó para evitar agregar dependencias de dev innecesarias para un proyecto académico.

---

# 5. ESTADO ACTUAL EXACTO

## Qué funciona correctamente

- ✅ Carga de dataset CSV/JSON con limpieza completa.
- ✅ Normalización de géneros a 20 categorías canónicas en español.
- ✅ Creación y persistencia de perfiles JSON.
- ✅ Motor de recomendación clásico (filtrado + scoring + ranking).
- ✅ Autoencoder Keras: entrenamiento, guardado, carga, inferencia.
- ✅ Similitud coseno sobre embeddings de 16D.
- ✅ Dashboard de inicio con top 3 recomendaciones.
- ✅ Menú interactivo completo (9 opciones).
- ✅ 5 visualizaciones generando PNG correctamente.
- ✅ Evaluación con matriz de confusión, precisión y recall.
- ✅ Compatibilidad de perfiles con índice Jaccard.
- ✅ CineRoulette (películas fuera del perfil).
- ✅ Comparación de películas con tabla tabular.
- ✅ Tests básicos: 7/7 pasando.
- ✅ Degradación graceful sin TensorFlow.
- ✅ Push exitoso a GitHub.

## Qué está parcialmente implementado

- **Property `Pelicula.es_popular`:** Siempre retorna `False` porque no tiene acceso al catálogo completo. El cálculo real del percentil 75 está en `Recomendador._evaluar_umbral_popularidad()`, pero nunca se conecta a la propiedad. Esto es un stub documentado.

## Qué NO funciona

- ❌ Nada crítico. El sistema es funcional end-to-end.

## Qué falta por desarrollar

- No hay funcionalidades pendientes del alcance original. Posibles mejoras futuras (fuera de scope):
  - Filtrado colaborativo (user-user o item-item).
  - Interfaz web (Flask/FastAPI + React).
  - Más datasets (MovieLens ratings para filtrado híbrido).
  - Tests formales con pytest y cobertura.
  - CI/CD con GitHub Actions.
  - Dockerización.

## Qué estaba haciendo justo antes de terminar

Se acababa de crear `test_basico.py` y `README.md`, ejecutar los tests (7/7 pasaron), y empujar el último commit (`17dd90b`) al repositorio remoto.

---

# 6. BUGS Y PROBLEMAS CONOCIDOS

## Bugs actuales

| Bug | Severidad | Descripción |
|-----|-----------|-------------|
| `Pelicula.es_popular` siempre `False` | Baja | Es un stub intencional documentado. No afecta el flujo principal porque el recomendador clásico no usa esta propiedad. |

## Errores frecuentes encontrados durante desarrollo

1. **`ModuleNotFoundError: No module named 'models'`**
   - **Causa:** Ejecutar scripts desde directorio incorrecto. Los imports son relativos al directorio del proyecto.
   - **Solución:** Siempre ejecutar desde `cineintelli/` o ajustar `sys.path`.

2. **`ValueError: all the input arrays must have same number of dimensions`** en `np.hstack`
   - **Causa:** `scaler.transform()` retorna array 2D `(1,1)`, pero al indexar `[0]` se obtenía 1D `(1,)`. `np.hstack` rechaza mezclar 1D y 2D.
   - **Solución:** Usar `[0, 0]` para extraer el escalar, luego reconstruir como 1D con `np.concatenate([..., [valor], ...])`.

3. **`SettingWithCopyWarning` / asignaciones ignoradas en pandas**
   - **Causa:** Después de `df.rename()`, pandas en modo "vista" ignoraba asignaciones posteriores tras un `apply`.
   - **Solución:** Agregar `.copy()` explícito después de `rename()`.

4. **`pd.to_datetime` no ejecutaba porque `dtype == object` era `False`**
   - **Causa:** En pandas 2.x con strings, `dtype` puede ser `str` en lugar de `object`. La comparación `df["col"].dtype == object` fallaba silenciosamente.
   - **Solución:** Reemplazar por `pd.api.types.is_string_dtype(df["col"])`.

## Edge cases problemáticos

- **Perfil sin géneros favoritos:** El sistema asume `generos_favoritos = []` como "todos los géneros". En `Recomendador`, `score_generos = 1.0` cuando no hay géneros favoritos. En el Autoencoder, el vector de géneros es todo ceros, lo cual puede producir recomendaciones poco específicas (observado en tests con perfil `TestUser` vacío: recomendó películas de baja puntuación como "The Real Cancun").
- **Dataset con fechas malformadas:** `pd.to_datetime(errors="coerce", dayfirst=True)` maneja esto, pero fechas ambiguas como `01-02-1995` pueden interpretarse como 2 de enero en lugar de 1 de febrero si `dayfirst=True` no es suficiente. Con el dataset actual no ha sido problema.

## Problemas técnicos pendientes

- Ninguno crítico.

---

# 7. DECISIONES IMPORTANTES TOMADAS

## Decisiones técnicas clave

1. **Uso de Autoencoder Keras en lugar de TF-IDF + coseno puro**
   - **Por qué:** El usuario solicitó explícitamente un Autoencoder con arquitectura densa en `analytics.py`. Además, TF-IDF no tiene sentido con features numéricas mixtas (puntuación, popularidad, año); el Autoencoder aprende representaciones latentes de todo el vector de características.

2. **Catálogo canónico de géneros en español**
   - **Por qué:** El requerimiento especificó normalización a 20 géneros en español. Esto facilita la interfaz de usuario en español pero introduce complejidad de traducción (`MAPEO_GENEROS`).

3. **JSON para perfiles, pickle para preprocesadores, .keras para modelo**
   - **Por qué:** Cada formato es el más apropiado para su contenido. JSON es human-readable para perfiles; pickle preserva el estado interno de scalers; `.keras` es el formato nativo de Keras.

4. **Menú CLI con `input()` en lugar de librerías como `click` o `rich`**
   - **Por qué:** Minimizar dependencias. El menú es funcional con `input()` + prints formateados.

## Librerías elegidas y por qué

- **TensorFlow/Keras:** Única opción viable para el Autoencoder solicitado. PyTorch hubiera sido igual de válido, pero Keras tiene una API más declarativa para redes densas simples.
- **Scikit-learn:** Estándar de facto para preprocesamiento (`MinMaxScaler`, `MultiLabelBinarizer`) y métricas (`confusion_matrix`, `cosine_similarity`).
- **Pandas:** Estándar para manipulación tabular. Permite limpieza vectorizada eficiente.
- **Seaborn:** Abstracción sobre Matplotlib que reduce código repetitivo para gráficos estadísticos.

## Librerías descartadas

- **Pytest / unittest:** Descartado para el MVP para mantener cero dependencias de desarrollo. Los tests se implementaron con `assert` nativo.
- **Flask / FastAPI / Django:** Descartado porque el alcance era CLI exclusivamente.
- **SQLAlchemy / SQLite:** Descartado porque JSON plano es suficiente para perfiles y el dataset es un CSV.
- **Click / Rich / Inquirer:** Descartado para el menú CLI para evitar dependencias adicionales.

## Enfoques que fallaron

1. **URL del dataset TMDB 5000 movies:** Se probaron ~10 URLs de GitHub raw conocidas (`justmarkham`, `codebasics`, `rounakbanik`, etc.). Todas devolvieron 404. Se tuvo que recurrir al dataset de YBI Foundation.
2. **Token de GitHub para push:** El primer token proporcionado no tenía permisos de escritura (`repo` scope), por lo que el push falló con 403. Se resolvió con un segundo token con los permisos correctos.

## Cosas que NO deben cambiarse

- **El catálogo canónico de 20 géneros en español:** Está hardcodeado en `data_loader.py` (`GENEROS_CANONICOS`) y es la base de toda la vectorización. Cambiarlo rompería la compatibilidad con perfiles existentes y el modelo entrenado.
- **La arquitectura del Autoencoder (64→32→16):** Si se cambian las dimensiones, los modelos `.keras` guardados previamente serán incompatibles.
- **El orden de features en el vector:** `generos_onehot | puntuacion | popularidad | decada_onehot`. Cualquier cambio en este orden requiere reentrenar el modelo desde cero.

## Suposiciones importantes

- El dataset siempre tendrá las columnas mapeadas en `MAPEO_COLUMNAS`.
- El usuario ejecuta desde el directorio `cineintelli/` para que los imports relativos funcionen.
- TensorFlow, si está instalado, es compatible con la arquitectura densa simple usada.

---

# 8. CONFIGURACIÓN Y ENTORNO

## Variables de entorno necesarias

Ninguna obligatoria. El sistema usa rutas relativas:
- `data/` para datasets
- `output/` para modelos y gráficos
- `profiles/` para perfiles JSON

**Opcional:** `TF_CPP_MIN_LOG_LEVEL=2` ya se setea en `analytics.py` para suprimir logs de TensorFlow.

## Configuración requerida

1. Python 3.11+ (probado en 3.11.2).
2. Instalar dependencias:
```bash
pip install -r requirements.txt
```
Contenido de `requirements.txt`:
```
pandas
matplotlib
seaborn
scikit-learn
numpy
tensorflow
```

3. Si TensorFlow no está disponible, el sistema funciona igual pero sin embeddings neuronales.

## Cómo ejecutar el proyecto

```bash
cd cineintelli
python main.py
```

O con redirección de input para pruebas no interactivas:
```bash
echo -e "TestUser\n9\n" | python main.py
```

## Cómo correr tests

```bash
cd cineintelli
python test_basico.py
```

Salida esperada: `7/7 tests pasados`.

## Requisitos del sistema

- **RAM:** Mínimo 2 GB. El dataset es pequeño (~23 MB, 4760 filas) y el modelo es una red densa ligera.
- **Disco:** ~100 MB para entorno + dataset + modelo + gráficos.
- **GPU:** No requerida. TensorFlow usará CPU automáticamente si no detecta CUDA.
- **OS:** Linux (probado en Debian 12 / Linux 6.1.0-47-cloud-amd64). Debería funcionar en macOS y Windows con ajustes menores (`limpiar_pantalla` ya detecta la plataforma).

## Versiones importantes probadas

- Python: 3.11.2
- Pandas: 3.0.3
- NumPy: 2.4.6
- Scikit-learn: 1.8.0
- TensorFlow: 2.21.0
- Matplotlib: compatible con seaborn instalado
- Seaborn: última estable

---

# 9. APIs Y COMUNICACIÓN

## Endpoints / APIs externas

El sistema **no expone endpoints propios** (es CLI puro).

**Integración externa única:**
- **Descarga de dataset:** `urllib.request.urlretrieve` a `https://raw.githubusercontent.com/YBI-Foundation/Dataset/main/Movies%20Recommendation.csv`
- **Método:** HTTP GET directo.
- **Sin autenticación** requerida para este URL.
- **Sin rate limits** significativos para GitHub raw en repos públicos.

## Contratos de datos

### Entrada: Dataset CSV esperado
El sistema soporta múltiples nombres de columnas (ver `MAPEO_COLUMNAS` en `data_loader.py`). Las columnas requeridas son:
- `id` / `movie_id`
- `title` / `titulo` / `movie_title`
- `genres` / `generos` / `movie_genre`
- `release_date` / `anio` / `movie_release_date`
- `vote_average` / `puntuacion` / `movie_vote`
- `popularity` / `popularidad` / `movie_popularity`
- `original_language` / `idioma` / `movie_language`
- `overview` / `descripcion` / `movie_overview`
- `vote_count` / `votos` / `movie_vote_count`

### Salida: Perfil JSON
```json
{
  "nombre_usuario": "TestUser",
  "generos_favoritos": [],
  "anio_min": 1900,
  "anio_max": 2100,
  "puntuacion_minima": 0.0,
  "idioma": "cualquiera",
  "cantidad_recomendaciones": 10,
  "historial": []
}
```

---

# 10. BASE DE DATOS

## Esquema de persistencia

**No hay base de datos relacional.** La persistencia es mediante archivos planos:

### Perfiles (`profiles/{nombre}.json`)
- Formato: JSON plano.
- Esquema: ver contrato de salida arriba.
- Índices: ninguno; se accede por nombre de archivo.
- Validaciones: `Perfil.from_dict` requiere las claves esperadas; usa valores por defecto si faltan.

### Dataset (`data/tmdb_movies.csv`)
- Formato: CSV separado por comas.
- No es persistente en el repo (`.gitignore` ignora `data/*.csv`).
- Se regenera vía `descargar_dataset_ejemplo()` si no existe.

### Modelo (`output/modelo_recomendador.keras`)
- Formato: Keras native format.
- Contiene: Pesos + arquitectura del Autoencoder completo.

### Preprocesadores (`output/preprocessors.pkl`)
- Formato: Python pickle.
- Contiene: Diccionario con `mlb`, `scaler_punt`, `scaler_pop`, `decadas_unique`, `decada_map`.
- **Advertencia de seguridad:** pickle puede ejecutar código malicioso si el archivo es comprometido. Solo cargar archivos generados por el propio sistema.

---

# 11. FRONTEND

## Estado del frontend

**NO EXISTE.** El proyecto es una aplicación de consola pura (CLI).

La "interfaz de usuario" consiste en:
- Impresiones de texto con `print()`.
- Tablas ASCII dibujadas con caracteres `+`, `-`, `|`.
- Recuadros decorativos con `╔═╗`.
- Inputs por teclado via `input()`.
- Gráficos exportados como archivos PNG en `output/`.

**No hay HTML, CSS, JS, ni framework de UI.**

---

# 12. BACKEND

## Arquitectura backend

**NO HAY SERVIDOR BACKEND.** Es un script Python monolítico que se ejecuta localmente.

Sin embargo, la lógica de "backend" está distribuida en los módulos:

### Servicios internos

| Servicio | Módulo | Responsabilidad |
|----------|--------|-----------------|
| Ingesta de datos | `data_loader.py` | Carga, limpieza, normalización |
| Motor de recomendación clásico | `models.py` → `Recomendador` | Filtrado + scoring lineal |
| Motor de recomendación neuronal | `analytics.py` | Autoencoder + similitud coseno |
| Estadísticas | `analytics.py` | Métricas descriptivas y tendencias |
| Visualización | `visualizer.py` | Generación de PNG |
| Persistencia | `utils.py` | JSON de perfiles |

### Seguridad

- **No hay autenticación de red.** Los perfiles son locales y no encriptados.
- **No hay sanitización de input** más allá de `validar_entrada()` que verifica tipos, rangos y opciones permitidas.
- **Pickle warning:** `preprocessors.pkl` es un vector de deserialización inseguro. No descargar archivos `.pkl` de fuentes no confiables.

### Logging

- No se usa el módulo `logging` de Python.
- Se usa `print()` con prefijos descriptivos: `[main]`, `[analytics]`, `[data_loader]`.
- Esto es suficiente para un CLI académico pero insuficiente para producción.

### Manejo de errores

- **Global:** `main()` envuelve todo en `try/except` que imprime traceback y sale con código 1.
- **Por función:** Cada opción del menú tiene su propio `try/except` interno en `_menu_principal()`.
- **Degradación graceful:** ImportError de TensorFlow capturado en `main.py`; el sistema continúa con el recomendador clásico.

---

# 13. TESTING

## Tests existentes

Archivo: `test_basico.py`

| # | Test | Qué verifica |
|---|------|--------------|
| 1 | `test_crear_pelicula` | Instanciación y atributos de `Pelicula` |
| 2 | `test_crear_perfil` | Instanciación, historial y `resumen()` de `Perfil` |
| 3 | `test_cargar_dataset` | Carga exitosa del CSV, retorna >0 películas |
| 4 | `test_modelo_neuronal` | Entrenamiento/carga del Autoencoder sin excepciones |
| 5 | `test_similitud_neuronal` | Scores entre 0 y 1, cantidad igual al catálogo |
| 6 | `test_evaluar_recomendaciones` | Confusion matrix generada sin errores |
| 7 | `test_generar_graficos` | 4-5 PNG creados y existen en disco |

**Resultado actual:** 7/7 pasando.

## Qué falta testear

- Tests de integración del menú completo (simulación de inputs de usuario).
- Tests unitarios de `data_loader` con datasets corruptos o faltantes.
- Tests de `visualizer` verificando contenido de los PNG (actualmente solo verifica existencia).
- Tests de performance con catálogos grandes (>100k películas).
- Tests de edge cases: perfil vacío, dataset vacío, columna faltante.

## Estrategia de testing actual

- **Manual + assert nativo.** Sin framework de testing.
- Cada test es independiente pero comparte el dataset cargado para eficiencia.

## Tests frágiles

- `test_generar_graficos` depende de que el directorio `output/` exista y sea escribible.
- `test_modelo_neuronal` y `test_similitud_neuronal` se saltan silenciosamente si TensorFlow no está instalado (marcan como FAIL en el resumen final).

---

# 14. PRIORIDADES ACTUALES

### 1. Qué debe hacerse primero

**Nada crítico.** El MVP está completo. Si se requiere continuar:

1. **Corregir `Pelicula.es_popular`:** Conectar la propiedad con el cálculo real del percentil 75 del catálogo (actualmente stub).
2. **Agregar tests formales:** Migrar `test_basico.py` a pytest con fixtures y mocks.
3. **Validar robustez del menú:** Probar todas las 9 opciones con inputs extremos (strings donde espera int, índices fuera de rango, etc.).

### 2. Qué puede esperar

- Interfaz web (FastAPI + HTML simple).
- Dockerización.
- CI/CD básico.
- Más datasets (MovieLens ratings para filtrado colaborativo híbrido).

### 3. Qué sería una mejora futura

- Sistema de ratings explícitos del usuario (estrellas 1-5) para entrenar un modelo híbrido.
- Búsqueda fuzzy de títulos con `fuzzywuzzy` o `thefuzz`.
- Internacionalización (i18n) de géneros y UI.
- Caché de recomendaciones para evitar recalcular.

### 4. Qué es deuda técnica

- Uso de `print()` en lugar de `logging`.
- Acceso a atributos privados (`_generos_favoritos`) desde `main.py` al editar perfil.
- Uso de `pickle` para preprocesadores (riesgo de seguridad).
- Falta de tests unitarios formales.
- No hay manejo de concurrencia (aunque para CLI monousuario no es necesario).

---

# 15. INSTRUCCIONES PARA LA SIGUIENTE IA

## Cómo continuar

1. **Lee este documento primero** (`TRANSFERENCIA_TECNICA.md`).
2. **Lee `README.md`** para la visión de usuario.
3. **Lee `models.py`** para entender las entidades de dominio.
4. **Lee `main.py`** para entender el flujo de la aplicación.
5. **Ejecuta `python test_basico.py`** desde `cineintelli/` para verificar que todo funciona en tu entorno.
6. **Si vas a agregar features:** Sigue la convención de un módulo por responsabilidad. No acoples lógica de UI en `analytics.py` ni lógica de ML en `utils.py`.

## Qué evitar

- **NO agregues frameworks web** sin consultar al usuario primero; el alcance es CLI.
- **NO cambies el catálogo canónico de géneros** sin reentrenar el modelo y migrar perfiles existentes.
- **NO cambies el orden de features** en el vector del Autoencoder sin reentrenar desde cero.
- **NO uses `git add -A`** sin revisar; hay archivos locales grandes (`.venv`, `data/*.csv`, `output/`) que deben respetar `.gitignore`.
- **NO asumas que `pd.read_csv` retorna `dtype: object` para strings.** En pandas 3.x puede ser `dtype: str`. Usa `pd.api.types.is_string_dtype()`.

## Qué revisar primero

Si reportan un bug:
1. Revisa si es un problema de `SettingWithCopy` en pandas (¿falta `.copy()`?).
2. Revisa si es un problema de dtype (`str` vs `object`).
3. Revisa si TensorFlow está instalado y es compatible.
4. Revisa que el script se ejecute desde `cineintelli/`.

## Qué archivos son delicados

- `analytics.py` (líneas 186-290): La lógica del Autoencoder. Un cambio en la arquitectura invalida modelos guardados.
- `data_loader.py` (líneas 27-90): `MAPEO_COLUMNAS` y `MAPEO_GENEROS`. Cambios aquí afectan toda la pipeline ETL.
- `main.py` (líneas 160-180): La vectorización del perfil para similitud neuronal. Debe mantenerse sincronizada con `_vectorizar_catalogo` en `analytics.py`.

## Qué convenciones seguir

- **Type hints en todos los métodos públicos.**
- **Docstrings descriptivas** con Args/Returns.
- **Encapsulamiento:** Prefiere properties sobre atributos públicos en entidades de dominio.
- **Manejo de excepciones:** Captura específica, no genérica. Propaga `ValueError` para inputs inválidos.
- **Commits descriptivos** en español (convención del proyecto).

---

# 16. RESUMEN ULTRA CORTO

## Estado actual en 10 líneas

- Sistema CLI de recomendación de películas 100% funcional.
- Procesa datasets TMDB/MovieLens, limpia datos y normaliza géneros a español.
- Motor dual: clásico (filtrado + scoring) y neuronal (Autoencoder 64→32→16 + coseno).
- Menú interactivo con 9 opciones: recomendaciones, estadísticas, gráficos, CineRoulette, comparación, compatibilidad, evaluación, perfil, salir.
- 5 visualizaciones PNG generadas correctamente.
- 7 tests básicos pasando sin pytest.
- Degradación graceful si TensorFlow no está instalado.
- Perfiles persistentes en JSON, modelo en `.keras`, preprocesadores en `.pkl`.
- Código empujado a GitHub; requiere ejecución desde directorio `cineintelli/`.
- Documentación completa en README.md y este documento.

## Próximo paso exacto recomendado

**Corregir `Pelicula.es_popular` para que use el percentil 75 real del catálogo** (conectándola con `Recomendador._evaluar_umbral_popularidad()` o pasando el catálogo como parámetro opcional).

## Principal bloqueo actual

**Ninguno.** El proyecto está completo y operativo. Cualquier continuación es mejora incremental, no corrección de bloqueos.
