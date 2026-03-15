"""
Endpoints de Análisis Asíncrono

Ubicación: app/api/v1/endpoints/analysis_async.py

Añade tres rutas al módulo de análisis:
    POST /analysis/async        → envía a Celery, retorna 202 + task_id
    POST /analysis/batch-async  → envía batch a Celery, retorna 202 + task_id
    GET  /analysis/task/{id}    → consulta estado/resultado de tarea

Cuándo usar estos endpoints vs los síncronos:
    - Síncrono (/analyze-complete): análisis < 3s, respuesta inmediata
    - Async (/async): análisis con LLM validation, visualizaciones pesadas
    - Batch (/batch-async): procesar 5+ algoritmos a la vez
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

# Importar desde infrastructure/tasks (ubicación correcta)
from app.infrastructure.tasks import (
    get_task_status,
    is_celery_available,
    submit_analysis,
    submit_batch,
)
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

async_router = APIRouter()

# Schemas
class AsyncAnalysisRequest(BaseModel):
    """Request para análisis asíncrono individual."""
    code: str = Field(..., description="Código pseudocódigo a analizar")
    analyze_complexity: bool = True
    analyze_patterns: bool = True
    analyze_structures: bool = True
    generate_visualizations: bool = False

    class Config:
        json_schema_extra = {
            "example": {
                "code": "algorithm mergeSort(A[n])\nbegin\n  ...\nend",
                "analyze_complexity": True,
                "analyze_patterns": True,
                "generate_visualizations": False,
            }
        }

class BatchAsyncRequest(BaseModel):
    """Request para análisis batch asíncrono."""

    class AlgorithmItem(BaseModel):
        code: str = Field(..., description="Código pseudocódigo")
        name: str = Field(default="", description="Nombre descriptivo")
        options: Optional[Dict[str, Any]] = None

    algorithms: List[AlgorithmItem] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Lista de algoritmos a analizar (máximo 100 por request)",
    )

class TaskSubmittedResponse(BaseModel):
    """Respuesta cuando una tarea se acepta correctamente."""
    task_id: str
    status: str = "submitted"
    message: str
    poll_url: str

# Endpoints 
@async_router.post(
    "/async",
    response_model=TaskSubmittedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Análisis Asíncrono",
    description=(
        "Envía un análisis al worker Celery y retorna 202 Accepted inmediatamente "
        "con un task_id. El análisis corre en background. "
        "Consultar resultado con GET /analysis/task/{task_id}. "
        "Usar cuando el análisis puede tardar más de 3 segundos."
    ),
)
async def submit_async_analysis(
    request: AsyncAnalysisRequest,
) -> TaskSubmittedResponse:
    """Envía análisis a Celery. Retorna 202 con task_id para polling."""
    if not is_celery_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "CeleryUnavailable",
                "message": (
                    "El worker de análisis asíncrono no está activo. "
                    "Para análisis síncronos usar POST /analysis/analyze-complete."
                ),
            },
        )

    request_data = request.model_dump()
    task_id = submit_analysis(request_data)

    if task_id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "TaskSubmissionFailed"},
        )

    logger.info(f"Análisis asíncrono aceptado: task_id={task_id}")
    return TaskSubmittedResponse(
        task_id=task_id,
        message="Análisis en progreso. Usar poll_url para consultar el resultado.",
        poll_url=f"/api/v1/analysis/task/{task_id}",
    )

@async_router.post(
    "/batch-async",
    response_model=TaskSubmittedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Análisis Batch Asíncrono",
    description=(
        "Envía múltiples algoritmos para análisis paralelo en Celery. "
        "Máximo 100 algoritmos por request. "
        "Consultar resultado con GET /analysis/task/{task_id}."
    ),
)
async def submit_batch_analysis(
    request: BatchAsyncRequest,
) -> TaskSubmittedResponse:
    """Envía batch de análisis a Celery. Retorna 202 con task_id."""
    if not is_celery_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "CeleryUnavailable"},
        )

    batch_data = [item.model_dump() for item in request.algorithms]
    task_id = submit_batch(batch_data)

    if task_id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "BatchSubmissionFailed"},
        )

    count = len(batch_data)
    logger.info(f"Batch asíncrono aceptado: {count} algoritmos, task_id={task_id}")
    return TaskSubmittedResponse(
        task_id=task_id,
        message=f"Batch de {count} algoritmos en progreso.",
        poll_url=f"/api/v1/analysis/task/{task_id}",
    )

@async_router.get(
    "/task/{task_id}",
    summary="Estado de Tarea Asíncrona",
    description=(
        "Consulta el estado y resultado de una tarea Celery. "
        "Estados posibles: PENDING, STARTED, SUCCESS, FAILURE, RETRY. "
        "Polling recomendado: cada 1s los primeros 10s, luego cada 5s."
    ),
)
async def get_task_result(task_id: str) -> Dict[str, Any]:
    """Retorna el estado actual y resultado (si completó) de una tarea."""
    if not is_celery_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "CeleryUnavailable"},
        )
    return get_task_status(task_id)