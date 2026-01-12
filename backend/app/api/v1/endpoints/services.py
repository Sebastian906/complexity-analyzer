"""
API Endpoints - Servicios

Endpoints REST para el módulo de servicios.
Incluye operaciones CRUD de algoritmos, análisis completo,
validación, exportación y gestión de caché.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Query, Path as PathParam
from pydantic import BaseModel, Field

from app.services import (
    AlgorithmService,
    AlgorithmCreateRequest,
    AlgorithmUpdateRequest,
    AlgorithmSearchCriteria,
    AlgorithmCategory,
    AlgorithmStatus,
    AnalysisOrchestrator,
    CompleteAnalysisRequest,
    ValidationService,
    ValidationRequest,
    ValidationLevel,
    ExportService,
    ExportRequest,
    ExportFormat,
    ExportOptions,
    CacheService,
    get_cache_service,
)
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()

# Instancias de servicios (en producción, usar dependency injection)
algorithm_service = AlgorithmService()
analysis_orchestrator = AnalysisOrchestrator()
validation_service = ValidationService()
export_service = ExportService()

# Schemas de Response
class AlgorithmResponse(BaseModel):
    """Response de algoritmo"""
    id: str
    name: str
    category: Optional[str]
    tags: List[str]
    status: str
    created_at: str
    lines_of_code: int

class AlgorithmDetailResponse(AlgorithmResponse):
    """Response detallado de algoritmo"""
    code: str
    description: Optional[str]
    author: Optional[str]
    version: int
    analysis_count: int

class ValidationResponse(BaseModel):
    """Response de validación"""
    is_valid: bool
    level: str
    total_issues: int
    errors: List[dict]
    warnings: List[dict]
    infos: List[dict]

class ExportResponse(BaseModel):
    """Response de exportación"""
    success: bool
    format: str
    size_bytes: int
    file_path: Optional[str]
    content: Optional[str]

class CacheStatsResponse(BaseModel):
    """Response de estadísticas de caché"""
    total_entries: int
    active_entries: int
    expired_entries: int
    total_hits: int
    avg_hits: float

# Endpoints - Algoritmos
@router.post(
    "/algorithms",
    response_model=AlgorithmResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear Algoritmo",
    description="Crea y almacena un nuevo algoritmo"
)
async def create_algorithm(request: AlgorithmCreateRequest):
    """
    Crea un nuevo algoritmo.
    
    - Valida sintaxis del código
    - Almacena en disco
    - Extrae metadata automáticamente
    """
    try:
        result = await algorithm_service.create(request)

        return AlgorithmResponse(
            id=result.metadata.id,
            name=result.metadata.name,
            category=result.metadata.category.value if result.metadata.category else None,
            tags=result.metadata.tags,
            status=result.metadata.status.value,
            created_at=result.metadata.created_at.isoformat(),
            lines_of_code=result.metadata.lines_of_code
        )
    except Exception as e:
        logger.error(f"Error creando algoritmo: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get(
    "/algorithms/{algorithm_id}",
    response_model=AlgorithmDetailResponse,
    summary="Obtener Algoritmo",
    description="Obtiene un algoritmo por ID"
)
async def get_algorithm(
    algorithm_id: str = PathParam(..., description="ID del algoritmo")
):
    """Obtiene un algoritmo específico con su código completo"""
    result = await algorithm_service.get(algorithm_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Algoritmo no encontrado: {algorithm_id}"
        )

    return AlgorithmDetailResponse(
        id=result.metadata.id,
        name=result.metadata.name,
        code=result.code,
        description=result.metadata.description,
        category=result.metadata.category.value if result.metadata.category else None,
        tags=result.metadata.tags,
        status=result.metadata.status.value,
        author=result.metadata.author,
        created_at=result.metadata.created_at.isoformat(),
        version=result.metadata.version,
        lines_of_code=result.metadata.lines_of_code,
        analysis_count=result.metadata.analysis_count
    )

@router.put(
    "/algorithms/{algorithm_id}",
    response_model=AlgorithmResponse,
    summary="Actualizar Algoritmo",
    description="Actualiza un algoritmo existente"
)
async def update_algorithm(
    algorithm_id: str,
    request: AlgorithmUpdateRequest
):
    """Actualiza un algoritmo (incrementa versión automáticamente)"""
    result = await algorithm_service.update(algorithm_id, request)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Algoritmo no encontrado: {algorithm_id}"
        )

    return AlgorithmResponse(
        id=result.metadata.id,
        name=result.metadata.name,
        category=result.metadata.category.value if result.metadata.category else None,
        tags=result.metadata.tags,
        status=result.metadata.status.value,
        created_at=result.metadata.created_at.isoformat(),
        lines_of_code=result.metadata.lines_of_code
    )

@router.delete(
    "/algorithms/{algorithm_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar Algoritmo",
    description="Elimina un algoritmo"
)
async def delete_algorithm(algorithm_id: str):
    """Elimina un algoritmo permanentemente"""
    deleted = await algorithm_service.delete(algorithm_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Algoritmo no encontrado: {algorithm_id}"
        )

@router.get(
    "/algorithms",
    response_model=List[AlgorithmResponse],
    summary="Listar Algoritmos",
    description="Lista algoritmos con paginación y filtros"
)
async def search_algorithms(
    name: Optional[str] = Query(None, description="Filtrar por nombre"),
    category: Optional[AlgorithmCategory] = Query(None, description="Filtrar por categoría"),
    status: Optional[AlgorithmStatus] = Query(None, description="Filtrar por estado"),
    tags: Optional[str] = Query(None, description="Filtrar por tags (separados por coma)"),
    limit: int = Query(10, ge=1, le=100, description="Límite de resultados"),
    offset: int = Query(0, ge=0, description="Offset para paginación")
):
    """Lista algoritmos con filtros opcionales"""
    criteria = AlgorithmSearchCriteria(
        name=name,
        category=category,
        status=status,
        tags=tags.split(",") if tags else None,
        limit=limit,
        offset=offset
    )

    results = await algorithm_service.search(criteria)

    return [
        AlgorithmResponse(
            id=r.id,
            name=r.name,
            category=r.category.value if r.category else None,
            tags=r.tags,
            status=r.status.value,
            created_at=r.created_at.isoformat(),
            lines_of_code=r.lines_of_code
        )
        for r in results
    ]

@router.get(
    "/algorithms-stats",
    summary="Estadísticas de Algoritmos",
    description="Obtiene estadísticas del servicio de algoritmos"
)
async def get_algorithm_stats():
    """Obtiene estadísticas del servicio"""
    return algorithm_service.get_statistics()

# Endpoints - Análisis Completo
@router.post(
    "/analyze-complete",
    status_code=status.HTTP_200_OK,
    summary="Análisis Completo",
    description="Ejecuta análisis completo de un algoritmo (todos los módulos)"
)
async def analyze_complete(request: CompleteAnalysisRequest):
    """
    Ejecuta análisis completo integrando:
    - Parsing
    - Análisis de complejidad
    - Detección de patrones
    - Detección de estructuras
    - Generación de visualizaciones
    """
    try:
        result = await analysis_orchestrator.analyze_complete(request)

        # Convertir a dict serializable
        response = {
            "success": result.success,
            "status": result.status.value,
            "algorithm_name": result.algorithm_name,
            "total_duration": result.total_duration,
            "steps": [
                {
                    "step": s.step.value,
                    "success": s.success,
                    "duration": s.duration,
                    "error": s.error
                }
                for s in result.steps
            ],
            "complexity_result": result.complexity_result,
            "patterns_result": result.patterns_result,
            "structures_result": result.structures_result,
            "visualizations_result": result.visualizations_result,
            "summary": result.summary,
            "metadata": result.metadata,
            "errors": result.errors,
            "warnings": result.warnings,
        }

        # Incrementar contador si tiene algorithm_id
        if request.algorithm_id:
            await algorithm_service.increment_analysis_count(request.algorithm_id)

        return response

    except Exception as e:
        logger.error(f"Error en análisis completo: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Endpoints - Validación
@router.post(
    "/validate",
    response_model=ValidationResponse,
    summary="Validar Código",
    description="Valida código en múltiples niveles"
)
async def validate_code(request: ValidationRequest):
    """
    Valida código pseudocódigo en el nivel especificado.

    Niveles disponibles:
    - SYNTAX: Solo sintaxis
    - SEMANTIC: Sintaxis + semántica
    - STRUCTURAL: + límites estructurales
    - COMPLETE: Todas las validaciones + best practices
    """
    try:
        result = await validation_service.validate(request)

        return ValidationResponse(
            is_valid=result.is_valid,
            level=result.level.value,
            total_issues=result.total_issues,
            errors=[
                {
                    "severity": e.severity.value,
                    "message": e.message,
                    "line": e.line,
                    "rule": e.rule,
                    "suggestion": e.suggestion
                }
                for e in result.errors
            ],
            warnings=[
                {
                    "severity": w.severity.value,
                    "message": w.message,
                    "line": w.line,
                    "rule": w.rule,
                    "suggestion": w.suggestion
                }
                for w in result.warnings
            ],
            infos=[
                {
                    "severity": i.severity.value,
                    "message": i.message,
                    "line": i.line,
                    "rule": i.rule,
                    "suggestion": i.suggestion
                }
                for i in result.infos
            ]
        )

    except Exception as e:
        logger.error(f"Error en validación: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post(
    "/validate/quick",
    summary="Validación Rápida",
    description="Validación rápida solo sintaxis (true/false)"
)
async def quick_validate(code: str = Query(..., description="Código a validar")):
    """Validación rápida solo sintaxis"""
    try:
        is_valid = await validation_service.quick_validate(code)
        return {"is_valid": is_valid}
    except Exception as e:
        return {"is_valid": False, "error": str(e)}

# Endpoints - Exportación
@router.post(
    "/export",
    response_model=ExportResponse,
    summary="Exportar Resultados",
    description="Exporta resultados de análisis en formato especificado"
)
async def export_results(request: ExportRequest):
    """
    Exporta resultados en el formato especificado.

    Formatos soportados:
    - JSON
    - Markdown
    - HTML
    - TXT
    - PDF (pendiente)
    """
    try:
        result = await export_service.export(request)

        return ExportResponse(
            success=result.success,
            format=result.format.value,
            size_bytes=result.size_bytes,
            file_path=str(result.file_path) if result.file_path else None,
            content=result.content if not result.file_path else None
        )

    except Exception as e:
        logger.error(f"Error en exportación: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Endpoints - Caché
@router.get(
    "/cache/stats",
    response_model=CacheStatsResponse,
    summary="Estadísticas de Caché",
    description="Obtiene estadísticas del servicio de caché"
)
async def get_cache_stats():
    """Obtiene estadísticas del caché"""
    cache = get_cache_service()
    stats = cache.get_statistics()

    return CacheStatsResponse(
        total_entries=stats["total_entries"],
        active_entries=stats["active_entries"],
        expired_entries=stats["expired_entries"],
        total_hits=stats["total_hits"],
        avg_hits=stats["avg_hits"]
    )

@router.delete(
    "/cache/clear",
    summary="Limpiar Caché",
    description="Limpia el caché (total o por prefijo)"
)
async def clear_cache(
    prefix: Optional[str] = Query(None, description="Prefijo a limpiar (opcional)")
):
    """Limpia el caché"""
    cache = get_cache_service()
    count = await cache.clear(prefix=prefix)

    return {
        "success": True,
        "entries_cleared": count,
        "prefix": prefix
    }

@router.post(
    "/cache/cleanup",
    summary="Limpiar Expirados",
    description="Limpia entradas expiradas del caché"
)
async def cleanup_cache():
    """Limpia solo entradas expiradas"""
    cache = get_cache_service()
    count = await cache.cleanup_expired()

    return {
        "success": True,
        "expired_cleaned": count
    }