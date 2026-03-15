"""
Tasks Infrastructure - Celery Workers

Expone la API pública del módulo de tareas asíncronas.

Uso desde los endpoints:
    from app.infrastructure.tasks import submit_analysis, get_task_status, is_celery_available
"""

from app.infrastructure.tasks.celery_app import (
    celery_app,
    submit_analysis,
    submit_batch,
    get_task_status,
    is_celery_available,
)

__all__ = [
    "celery_app",
    "submit_analysis",
    "submit_batch",
    "get_task_status",
    "is_celery_available",
]