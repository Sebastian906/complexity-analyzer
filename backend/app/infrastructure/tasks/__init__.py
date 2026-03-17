"""
Tasks Infrastructure - Celery Workers

Expone la API pública del módulo de tareas asíncronas.

Uso desde los endpoints:
    from app.infrastructure.tasks import submit_analysis, get_task_status, is_celery_available
"""

"""Package API for tasks.

This module exposes wrappers that delegate to the implementation in
``app.infrastructure.tasks.celery_app`` but perform the availability
check using the package-level ``is_celery_available`` name. Tests patch
``app.infrastructure.tasks.is_celery_available`` (the package name), so
wrapping here ensures those patches are respected by callers that import
from the package.
"""

from importlib import import_module
from typing import Any, Dict, Optional

# Import the implementation module (celery_app). We keep a reference to
# the module so we can delegate calls to it.
_impl = import_module("app.infrastructure.tasks.celery_app")

# Re-export the celery_app object for consumers that need it
celery_app = getattr(_impl, "celery_app", None)


def is_celery_available() -> bool:  # re-exported name (hot-swappable in tests)
    return getattr(_impl, "is_celery_available")()


def submit_analysis(request_data: dict) -> Optional[str]:
    # Respect package-level is_celery_available (tests patch this name)
    if not is_celery_available():
        return None
    return getattr(_impl, "submit_analysis")(request_data)


def submit_batch(batch_data: list) -> Optional[str]:
    if not is_celery_available():
        return None
    return getattr(_impl, "submit_batch")(batch_data)


def get_task_status(task_id: str) -> Dict[str, Any]:
    if not is_celery_available():
        return {
            "task_id": task_id,
            "status": "unavailable",
            "error": "Celery no está habilitado en este servidor.",
        }
    return getattr(_impl, "get_task_status")(task_id)


__all__ = [
    "celery_app",
    "submit_analysis",
    "submit_batch",
    "get_task_status",
    "is_celery_available",
]