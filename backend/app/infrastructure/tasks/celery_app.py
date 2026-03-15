"""
Celery App - Worker para análisis de larga duración

Ubicación: app/infrastructure/tasks/celery_app.py

Por qué aquí y no en app/celery_app.py:
    Celery es infraestructura de mensajería (usa Redis como broker).
    Igual que los adaptadores LLM o los clientes de base de datos,
    pertenece a infrastructure/. Los endpoints usan las funciones
    helpers de este módulo sin conocer los detalles de Celery.

Arquitectura del flujo async:
    Cliente → POST /analysis/async
                    ↓ (retorna 202 + task_id inmediatamente)
              submit_analysis()
                    ↓
              Celery broker (Redis DB 1)
                    ↓
              Worker (proceso separado)
                    ↓
              analyze_algorithm_task()
                    → AnalysisOrchestrator.analyze_complete()
                    ↓
              Redis DB 2 (result backend)
                    ↓
    Cliente → GET /analysis/task/{task_id} → resultado

Arrancar el worker (en terminal separada al FastAPI):
    celery -A app.infrastructure.tasks.celery_app worker \\
           --loglevel=info \\
           --concurrency=4 \\
           -Q complexity_analyzer

Requisitos previos:
    pip install celery[redis]
    CELERY_ENABLED=true en .env
    Redis corriendo (el mismo que usa el caché del proyecto)
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Importación opcional de Celery 
try:
    from celery import Celery
    from celery.result import AsyncResult
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    Celery = None        # type: ignore[misc,assignment]
    AsyncResult = None   # type: ignore[misc,assignment]

# Configuración
def _build_config() -> dict:
    """Construye configuración de Celery desde settings."""
    try:
        from app.core.config import settings
        broker = getattr(
            settings,
            "CELERY_BROKER_URL",
            f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/1",
        )
        backend = getattr(
            settings,
            "CELERY_RESULT_BACKEND",
            f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/2",
        )
        task_timeout = getattr(settings, "CELERY_TASK_TIMEOUT", 300)
    except Exception:
        broker = "redis://localhost:6379/1"
        backend = "redis://localhost:6379/2"
        task_timeout = 300

    return {
        "broker_url": broker,
        "result_backend": backend,
        "task_serializer": "json",
        "result_serializer": "json",
        "accept_content": ["json"],
        "timezone": "UTC",
        "enable_utc": True,
        # Resultados disponibles 24 horas
        "result_expires": 86400,
        # Reintentar conexión al arrancar si el broker no está listo
        "broker_connection_retry_on_startup": True,
        # Tiempo límite por tarea
        "task_soft_time_limit": task_timeout - 60,  # SIGTERM con 1 min de margen
        "task_time_limit": task_timeout,              # SIGKILL
        # Un análisis por worker a la vez (son CPU-bound)
        "worker_prefetch_multiplier": 1,
        # Ack después de completar — no perder tareas si el worker muere a mitad
        "task_acks_late": True,
        # Cola dedicada para este proyecto
        "task_default_queue": "complexity_analyzer",
    }

def _create_app() -> Optional[Any]:
    """Crea la app Celery si está disponible y habilitada."""
    if not CELERY_AVAILABLE:
        logger.info(
            "Celery no instalado. "
            "Para análisis async: pip install celery[redis]"
        )
        return None

    try:
        from app.core.config import settings
        if not getattr(settings, "CELERY_ENABLED", False):
            logger.info(
                "Celery deshabilitado (CELERY_ENABLED=false). "
                "Todos los análisis serán síncronos."
            )
            return None
    except Exception:
        return None

    config = _build_config()
    app = Celery("complexity_analyzer")
    app.config_from_object(config)

    host_port = config["broker_url"].split("@")[-1]
    logger.info(f"Celery configurado → broker: {host_port}")
    return app

# Instancia global — None si Celery no está disponible o deshabilitado
celery_app = _create_app()

# Tareas registradas
def _get_analyze_task():
    """Retorna la tarea de análisis individual. None si Celery no está activo."""
    if celery_app is None:
        return None

    @celery_app.task(
        name="complexity_analyzer.analyze_algorithm",
        bind=True,
        max_retries=3,
        default_retry_delay=5,
        queue="complexity_analyzer",
    )
    def analyze_algorithm(self, request_data: dict) -> dict:
        """
        Analiza un algoritmo en background.

        Args:
            request_data: CompleteAnalysisRequest serializado como dict.
                          El endpoint lo serializa con .model_dump() antes
                          de enviar a Celery (JSON-serializable).

        Returns:
            CompleteAnalysisResult serializado como dict.
        """
        import asyncio
        from app.services.analysis_orchestrator import AnalysisOrchestrator
        from app.schemas import CompleteAnalysisRequest

        logger.info(f"[Celery] Iniciando análisis: task_id={self.request.id}")

        try:
            request = CompleteAnalysisRequest(**request_data)

            # Celery workers son síncronos — crear event loop para código async
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                orchestrator = AnalysisOrchestrator()
                result = loop.run_until_complete(
                    orchestrator.analyze_complete(request)
                )
                return result.model_dump()
            finally:
                loop.close()

        except Exception as exc:
            logger.error(
                f"[Celery] Error en task_id={self.request.id}: {exc}"
            )
            try:
                raise self.retry(exc=exc, countdown=5)
            except self.MaxRetriesExceededError:
                return {
                    "success": False,
                    "error": str(exc),
                    "task_id": self.request.id,
                }

    return analyze_algorithm

def _get_batch_task():
    """Retorna la tarea de análisis batch. None si Celery no está activo."""
    if celery_app is None:
        return None

    @celery_app.task(
        name="complexity_analyzer.analyze_batch",
        bind=True,
        max_retries=1,
        default_retry_delay=10,
        queue="complexity_analyzer",
    )
    def analyze_batch(self, batch_data: list) -> dict:
        """
        Analiza múltiples algoritmos en background.

        Args:
            batch_data: Lista de dicts con {code, name, options}.
        """
        import asyncio
        from app.parallel.batch_analyzer import BatchAnalyzer, AnalysisJob

        logger.info(
            f"[Celery] Iniciando batch: {len(batch_data)} algoritmos, "
            f"task_id={self.request.id}"
        )

        try:
            jobs = [
                AnalysisJob(
                    code=item["code"],
                    name=item.get("name", ""),
                    options=item.get("options"),
                    metadata=item.get("metadata", {}),
                )
                for item in batch_data
            ]

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                analyzer = BatchAnalyzer()
                result = loop.run_until_complete(analyzer.analyze_batch(jobs))
                return result.to_dict()
            finally:
                loop.close()

        except Exception as exc:
            logger.error(
                f"[Celery] Error en batch task_id={self.request.id}: {exc}"
            )
            return {
                "success": False,
                "error": str(exc),
                "task_id": self.request.id,
                "total": len(batch_data),
            }

    return analyze_batch

# API pública para los endpoints
def submit_analysis(request_data: dict) -> Optional[str]:
    """
    Envía un análisis al worker Celery.

    Args:
        request_data: CompleteAnalysisRequest.model_dump()

    Returns:
        task_id (string) si se envió, None si Celery no está disponible.
    """
    task_fn = _get_analyze_task()
    if task_fn is None:
        return None
    task = task_fn.delay(request_data)
    logger.info(f"Análisis enviado a Celery: task_id={task.id}")
    return task.id

def submit_batch(batch_data: list) -> Optional[str]:
    """
    Envía un batch al worker Celery.

    Args:
        batch_data: Lista de dicts con {code, name, options}

    Returns:
        task_id (string) si se envió, None si Celery no está disponible.
    """
    task_fn = _get_batch_task()
    if task_fn is None:
        return None
    task = task_fn.delay(batch_data)
    logger.info(
        f"Batch enviado a Celery: {len(batch_data)} jobs, task_id={task.id}"
    )
    return task.id

def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    Obtiene el estado de una tarea Celery.

    Args:
        task_id: ID retornado por submit_analysis() o submit_batch()

    Returns:
        Dict con:
            task_id: el mismo ID recibido
            status:  PENDING | STARTED | SUCCESS | FAILURE | RETRY
            result:  resultado si status == SUCCESS
            error:   mensaje de error si status == FAILURE
    """
    if not CELERY_AVAILABLE or celery_app is None:
        return {
            "task_id": task_id,
            "status": "unavailable",
            "error": "Celery no está habilitado en este servidor.",
        }

    result = AsyncResult(task_id, app=celery_app)
    response: Dict[str, Any] = {
        "task_id": task_id,
        "status": result.status,
    }

    if result.ready():
        if result.successful():
            response["result"] = result.result
        else:
            response["error"] = str(result.result)
            response["traceback"] = result.traceback

    return response

def is_celery_available() -> bool:
    """True si Celery está instalado, habilitado y el broker está configurado."""
    return CELERY_AVAILABLE and celery_app is not None