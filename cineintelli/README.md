# CineIntelli

Sistema de análisis y recomendación de películas desarrollado en Python.

Procesa datasets públicos (MovieLens / TMDB), aplica similitud coseno sobre vectores TF-IDF y embeddings neuronales para generar recomendaciones personalizadas, y visualiza estadísticas del catálogo con Matplotlib y Seaborn. Arquitectura modular con Programación Orientada a Objetos.

---

## Stack Tecnológico

| Tecnología | Uso principal |
|------------|---------------|
| **Python 3.11+** | Lenguaje base |
| **Pandas** | Carga, limpieza y transformación de datos |
| **NumPy** | Vectorización y operaciones numéricas |
| **TensorFlow / Keras** | Autoencoder para embeddings de películas |
| **Scikit-learn** | Preprocesamiento, métricas y similitud coseno |
| **Matplotlib & Seaborn** | Visualización estadística del catálogo |

---

## Requisitos e Instalación

1. Clonar el repositorio:

```bash
git clone https://github.com/erikonta77/peliculas.git
cd cineintelli
```

2. Crear un entorno virtual (recomendado):

```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows
```

3. Instalar dependencias:

```bash
pip install -r requirements.txt
```

> **Nota:** TensorFlow es opcional. Si no está instalado, el sistema degrada automáticamente al recomendador clásico basado en reglas.

---

## Cómo Ejecutar

### Modo interactivo (menú principal)

```bash
python main.py
```

El flujo de inicio:
1. Muestra el banner ASCII de CineIntelli.
2. Solicita el nombre de usuario y carga o crea un perfil personalizado.
3. Descarga automáticamente el dataset de ejemplo si no existe localmente.
4. Entrena o carga el modelo neuronal (Autoencoder).
5. Muestra un dashboard con el total de películas, géneros disponibles y las top 3 recomendaciones para el perfil actual.
6. Presenta el menú principal de 9 opciones.

### Ejecutar tests básicos

```bash
python test_basico.py
```

Verifica la creación de entidades, carga de datos, entrenamiento del modelo, similitud neuronal, evaluación y generación de gráficos.

---

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                         CineIntelli                          │
├─────────────────────────────────────────────────────────────┤
│  main.py                                                      │
│   ├── Banner + Menú interactivo                               │
│   ├── CineIntelliApp (orquestador)                            │
│   │    ├── _cargar_perfil_usuario()                           │
│   │    ├── _cargar_datos()          → data_loader.py          │
│   │    ├── _configurar_modelo()     → analytics.py            │
│   │    ├── _mostrar_dashboard()                               │
│   │    └── _menu_principal()        → 9 opciones              │
├─────────────────────────────────────────────────────────────┤
│  models.py                                                    │
│   ├── Pelicula           (entidad de dominio)                 │
│   ├── Perfil             (preferencias de usuario)            │
│   └── Recomendador       (filtrado + puntuación de relevancia)│
├─────────────────────────────────────────────────────────────┤
│  data_loader.py                                               │
│   ├── cargar_dataset()         (CSV/JSON → list[Pelicula])    │
│   ├── descargar_dataset_ejemplo()                             │
│   └── generar_informe_calidad()                               │
├─────────────────────────────────────────────────────────────┤
│  analytics.py                                                 │
│   ├── estadisticas_catalogo()                                 │
│   ├── tendencias_temporales()                                 │
│   ├── construir_modelo_recomendacion()  → Autoencoder Keras   │
│   ├── similitud_neuronal()          → embeddings + coseno     │
│   ├── evaluar_recomendaciones()     → confusion matrix        │
│   ├── compatibilidad_perfiles()     → índice Jaccard          │
│   └── generar_informe_tendencias()                            │
├─────────────────────────────────────────────────────────────┤
│  visualizer.py                                                │
│   ├── grafico_distribucion_generos()                          │
│   ├── grafico_tendencia_anual()                               │
│   ├── grafico_top_generos()                                   │
│   ├── grafico_scatter_popularidad()                           │
│   └── grafico_perdida_entrenamiento()                         │
├─────────────────────────────────────────────────────────────┤
│  utils.py                                                     │
│   ├── limpiar_pantalla(), imprimir_titulo(), imprimir_tabla() │
│   ├── validar_entrada()        (3 reintentos)                 │
│   └── cargar_perfil() / guardar_perfil()   (JSON)             │
└─────────────────────────────────────────────────────────────┘
```

---

## Modelo de IA: Autoencoder para Embeddings de Películas

El corazón inteligente de CineIntelli es un **Autoencoder** construido con TensorFlow/Keras que aprende representaciones densas (embeddings) de cada película a partir de sus características vectorizadas.

### Vectorización de entrada

Cada película se representa como un vector numérico que combina:

| Característica | Técnica | Dimensión |
|----------------|---------|-----------|
| Géneros | MultiLabelBinarizer (one-hot) | ~20 |
| Puntuación | MinMaxScaler | 1 |
| Popularidad | MinMaxScaler | 1 |
| Década de estreno | One-hot encoding | variable |

### Arquitectura del Autoencoder

```
Input (n_features)
    ↓
Dense(64, relu)
    ↓
Dense(32, relu)
    ↓
Dense(16, relu)   ←  Embedding latente (bottleneck)
    ↓
Dense(32, relu)
    ↓
Dense(64, relu)
    ↓
Dense(n_features, sigmoid)   ← Reconstrucción
```

- **Encoder:** comprime el vector de entrada a un espacio latente de **16 dimensiones**.
- **Decoder:** reconstruye el vector original desde el embedding.
- **Entrenamiento:** 50 épocas, optimizador Adam, pérdida MSE.

### Recomendación neuronal

Para generar recomendaciones, el perfil del usuario también se vectoriza con los mismos preprocesadores. Luego:

1. El encoder comprime el perfil y todas las películas a embeddings de 16D.
2. Se calcula la **similitud coseno** entre el embedding del perfil y cada película.
3. Las películas con mayor score se presentan ordenadas.

El modelo se guarda en `output/modelo_recomendador.keras` y se reutiliza en ejecuciones posteriores sin necesidad de reentrenar.

---

## Autores

- **Carlos Erik Carvajal Cañas**
- **Miguel José Lamus Rincón**

---

*Proyecto académico de sistemas de recomendación basados en contenido.*
