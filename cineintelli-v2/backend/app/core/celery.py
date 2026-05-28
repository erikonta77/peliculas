"""
Configuración de Celery para tareas en background
"""

from celery import Celery
from app.core.config import settings

# Crear instancia de Celery
celery_app = Celery(
    "cineintelli",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.enrichment",
        "app.tasks.scraping",
        "app.tasks.ml_training",
    ]
)

# Configuración
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hora máximo por tarea
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Beat schedule para tareas periódicas
celery_app.conf.beat_schedule = {
    "enrich-movies-daily": {
        "task": "app.tasks.enrichment.daily_movie_enrichment",
        "schedule": 86400.0,  # 24 horas
    },
    "sync-tmdb-popular": {
        "task": "app.tasks.scraping.sync_tmdb_popular",
        "schedule": 3600.0,  # 1 hora
    },
}
