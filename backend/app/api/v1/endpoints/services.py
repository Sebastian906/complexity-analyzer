"""
API Endpoints - Servicios

Endpoints REST para el módulo de servicios.
Incluye operaciones CRUD de algoritmos, análisis completo,
validación, exportación y gestión de caché.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Query, Path as PathParam
from app.schemas import (
    # Algorithm Schemas
    AlgorithmCreate,
    AlgorithmUpdate,
    Algorithm,
    AlgorithmMetadata,
    AlgorithmListRequest,
    AlgorithmSearchCriteria,
    AlgorithmResponse,
    AlgorithmListResponse,
    AlgorithmCategory,
    AlgorithmSortBy,
    
    # Analysis Schemas
    CompleteAnalysisRequest,
    CompleteAnalysisResult,
    BatchAnalysisRequest,
    BatchAnalysisResult,
    QuickAnalysisRequest,
    QuickAnalysisResult,
    
    # Validation Schemas
    ValidationRequest,
    CompleteValidationResult,
    ValidationLevel,
    
    # Export Schemas
    ExportRequest,
    ExportResult,
    BatchExportRequest,
    BatchExportResult,
    
    # Common Schemas
    BaseResponse,
    ErrorResponse,
)

from app.services import (
    AlgorithmService,
    AnalysisOrchestrator,
    ValidationService,
    ExportService,
    CacheService,
    CacheKey,
    generate_cache_key,
    get_cache_service,
)
from app.core.config import settings
from app.schemas import StatusEnum
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()

# INSTANCIAS DE SERVICIOS
algorithm_service = AlgorithmService()
analysis_orchestrator = AnalysisOrchestrator()
validation_service = ValidationService()
export_service = ExportService()

# ENDPOINTS - ALGORITMOS (CRUD)
@router.post(
    "/algorithms",
    response_model=AlgorithmResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear Algoritmo",
    description="Crea y almacena un nuevo algoritmo"
)
async def create_algorithm(request: AlgorithmCreate):
    """
    Crea un nuevo algoritmo.
    
    - Valida sintaxis del código
    - Almacena en disco
    - Extrae metadata automáticamente
    """
    try:
        result = await algorithm_service.create(request)

        return AlgorithmResponse(
            success=True,
            message="Algoritmo creado exitosamente",
            algorithm=Algorithm(
                id=result.algorithm.id,
                name=result.algorithm.name,
                description=result.algorithm.description,
                category=result.algorithm.category,
                tags=result.algorithm.tags,
                language=request.language,
                code=result.algorithm.code,
                info=result.algorithm.info or None,
                created_at=result.algorithm.created_at,
                updated_at=result.algorithm.updated_at,
                analyzed=result.algorithm.analyzed,
                analysis_count=result.algorithm.analysis_count,
                complexity_class=result.algorithm.complexity_class,
                big_o=result.algorithm.big_o,
            )
        )
    except Exception as e:
        logger.error(f"Error creando algoritmo: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get(
    "/algorithms/{algorithm_id}",
    response_model=AlgorithmResponse,
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

    return AlgorithmResponse(
        success=True,
        message="Algoritmo recuperado exitosamente",
        algorithm=Algorithm(
            id=result.algorithm.id,
            name=result.algorithm.name,
            description=result.algorithm.description,
            category=result.algorithm.category,
            tags=result.algorithm.tags,
            language=result.algorithm.language if hasattr(result.algorithm, 'language') else "pseudocode",
            code=result.algorithm.code,
            info=result.algorithm.info or None,
            created_at=result.algorithm.created_at,
            updated_at=result.algorithm.updated_at,
            analyzed=result.algorithm.analyzed,
            analysis_count=result.algorithm.analysis_count,
            complexity_class=result.algorithm.complexity_class,
            big_o=result.algorithm.big_o,
        )
    )

@router.put(
    "/algorithms/{algorithm_id}",
    response_model=AlgorithmResponse,
    summary="Actualizar Algoritmo",
    description="Actualiza un algoritmo existente"
)
async def update_algorithm(
    algorithm_id: str,
    request: AlgorithmUpdate
):
    """Actualiza un algoritmo (incrementa versión automáticamente)"""
    result = await algorithm_service.update(algorithm_id, request)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Algoritmo no encontrado: {algorithm_id}"
        )

    return AlgorithmResponse(
        success=True,
        message="Algoritmo actualizado exitosamente",
        algorithm=Algorithm(
            id=result.algorithm.id,
            name=result.algorithm.name,
            description=result.algorithm.description,
            category=result.algorithm.category,
            tags=result.algorithm.tags,
            language=result.algorithm.language if hasattr(result.algorithm, 'language') else "pseudocode",
            code=result.algorithm.code,
            info=result.algorithm.info or None,
            created_at=result.algorithm.created_at,
            updated_at=result.algorithm.updated_at,
            analyzed=result.algorithm.analyzed,
            analysis_count=result.algorithm.analysis_count,
            complexity_class=result.algorithm.complexity_class,
            big_o=result.algorithm.big_o,
        )
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

@router.post(
    "/algorithms/search",
    response_model=AlgorithmListResponse,
    summary="Buscar Algoritmos",
    description="Busca algoritmos con filtros y paginación"
)
async def search_algorithms(request: AlgorithmListRequest):
    """Busca algoritmos con criterios y paginación"""
    
    # Convertir a formato interno del servicio
    from app.services.algorithm_service import AlgorithmSearchCriteria as InternalCriteria
    
    internal_criteria = InternalCriteria(
        name=request.criteria.query if request.criteria else None,
        category=request.criteria.category if request.criteria else None,
        tags=request.criteria.tags if request.criteria else None,
        status=None,  # Mapear si es necesario
        author=None,
        limit=request.page_size,
        offset=(request.page - 1) * request.page_size
    )

    results = await algorithm_service.search(internal_criteria)

    # Convertir a AlgorithmMetadata del schema
    metadata_list = [
        AlgorithmMetadata(
            id=r.id,
            name=r.name,
            category=r.category,
            tags=r.tags,
            complexity_class=None,
            big_o=None,
            created_at=r.created_at,
            analyzed=r.analysis_count > 0,
        )
        for r in results
    ]

    total = len(results)  # En producción, hacer query de count
    total_pages = (total + request.page_size - 1) // request.page_size

    return AlgorithmListResponse(
        success=True,
        message="Búsqueda completada exitosamente",
        algorithms=metadata_list,
        total=total,
        page=request.page,
        page_size=request.page_size,
        total_pages=total_pages,
    )

@router.get(
    "/algorithms-stats",
    summary="Estadísticas de Algoritmos",
    description="Obtiene estadísticas del servicio de algoritmos"
)
async def get_algorithm_stats():
    """Obtiene estadísticas del servicio"""
    return algorithm_service.get_statistics()

# ENDPOINTS - ANÁLISIS COMPLETO
@router.post(
    "/analyze-complete",
    response_model=CompleteAnalysisResult,
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
        # Cache: verificar caché
        _cache = get_cache_service()
        _cache_key = generate_cache_key(
            CacheKey.ANALYSIS, request.code, analysis_type="orchestrator_complete"
        )
        _cached = await _cache.get(_cache_key)
        if _cached is not None:
            logger.info("Cache HIT para análisis completo (orchestrator)")
            return _cached

        result = await analysis_orchestrator.analyze_complete(request)

        # Incrementar contador si tiene algorithm_id
        if hasattr(request, 'algorithm_id') and request.algorithm_id:
            await algorithm_service.increment_analysis_count(request.algorithm_id)

        # Cache: almacenar resultado
        await _cache.set(_cache_key, result, ttl=settings.CACHE_TTL_ANALYSIS)

        return result

    except Exception as e:
        logger.error(f"Error en análisis completo: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post(
    "/analyze-batch",
    response_model=BatchAnalysisResult,
    summary="Análisis en Batch",
    description="Analiza múltiples algoritmos en paralelo"
)
async def analyze_batch(request: BatchAnalysisRequest):
    """Análisis en batch de múltiples algoritmos"""
    import asyncio
    import time
    from app.schemas.analysis_result import BatchAnalysisItemResult
    
    start_time = time.time()
    results = []
    successful = 0
    failed = 0
    
    async def analyze_item(item):
        """Analiza un item individual"""
        try:
            analysis_request = CompleteAnalysisRequest(
                code=item.code,
                language=item.language,
                algorithm_name=item.algorithm_name,
                analysis_type=request.analysis_type
            )
            result = await analysis_orchestrator.analyze(analysis_request)
            return BatchAnalysisItemResult(
                id=item.id,
                success=True,
                result=result,
                error=None
            )
        except Exception as e:
            logger.error(f"Error analizando item {item.id}: {e}")
            return BatchAnalysisItemResult(
                id=item.id,
                success=False,
                result=None,
                error=str(e)
            )
    
    try:
        if request.parallel:
            # Procesar en paralelo
            tasks = [analyze_item(item) for item in request.items]
            results = await asyncio.gather(*tasks)
        else:
            # Procesar secuencialmente
            for item in request.items:
                result = await analyze_item(item)
                results.append(result)
        
        # Contar resultados
        for result in results:
            if result.success:
                successful += 1
            else:
                failed += 1
        
        processing_time = (time.time() - start_time) * 1000
        
        return BatchAnalysisResult(
            success=True,
            message=f"Batch completado: {successful} exitosos, {failed} fallidos",
            results=list(results),
            total=len(request.items),
            successful=successful,
            failed=failed,
            processing_time_ms=processing_time
        )
    except Exception as e:
        logger.error(f"Error en batch analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post(
    "/analyze-quick",
    response_model=QuickAnalysisResult,
    summary="Análisis Rápido",
    description="Análisis simplificado y rápido"
)
async def analyze_quick(request: QuickAnalysisRequest):
    """Análisis rápido simplificado"""
    try:
        # Cache: verificar caché
        _cache = get_cache_service()
        _cache_key = generate_cache_key(
            CacheKey.ANALYSIS, request.code, analysis_type="orchestrator_quick"
        )
        _cached = await _cache.get(_cache_key)
        if _cached is not None:
            logger.info("Cache HIT para análisis rápido (orchestrator)")
            return _cached

        from app.schemas.analysis_request import AnalysisType
        
        # Crear request con análisis básico (solo complejidad)
        analysis_request = CompleteAnalysisRequest(
            code=request.code,
            analysis_type=AnalysisType.BASIC  # Solo complejidad básica
        )
        
        # Ejecutar análisis
        result = await analysis_orchestrator.analyze(analysis_request)
        
        # Extraer datos principales
        algorithm_name = result.algorithm_name if hasattr(result, 'algorithm_name') else "unknown"
        complexity = result.complexity if hasattr(result, 'complexity') else {}
        space = result.space if hasattr(result, 'space') else {}
        patterns = result.patterns if hasattr(result, 'patterns') else []
        
        # Obtener complejidades
        big_o = complexity.get('big_o', 'O(?)') if isinstance(complexity, dict) else 'O(?)'
        omega = complexity.get('omega', 'Ω(?)') if isinstance(complexity, dict) else 'Ω(?)'
        theta = complexity.get('theta') if isinstance(complexity, dict) else None
        space_complexity = space.get('total', 'O(1)') if isinstance(space, dict) else 'O(1)'
        
        # Patrón principal (si existe)
        primary_pattern = patterns[0].get('name') if patterns and isinstance(patterns, list) else None
        
        # Generar resumen
        summary = f"Complejidad temporal: {big_o}, espacial: {space_complexity}"
        
        _result = QuickAnalysisResult(
            success=True,
            message="Análisis rápido completado",
            algorithm_name=algorithm_name,
            big_o=big_o,
            omega=omega,
            theta=theta,
            space_complexity=space_complexity,
            primary_pattern=primary_pattern,
            summary=summary
        )

        # Cache: almacenar resultado
        await _cache.set(_cache_key, _result, ttl=settings.CACHE_TTL_ANALYSIS)

        return _result
    except Exception as e:
        logger.error(f"Error en análisis rápido: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# ENDPOINTS - VALIDACIÓN
@router.post(
    "/validate",
    response_model=CompleteValidationResult,
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
        
        # Convertir ValidationResult a CompleteValidationResult
        # (Aquí podrías necesitar mapear campos adicionales)
        return CompleteValidationResult(
            success=result.is_valid,
            message="Validación completada",
            timestamp=None,  # Agregar si es necesario
            is_valid=result.is_valid,
            errors=result.errors,
            warnings=result.warnings,
            info=result.infos,
            error_count=len(result.errors),
            warning_count=len(result.warnings),
            info_count=len(result.infos),
            hint_count=0,
            lines_analyzed=result.metadata.get("lines_count", 0),
            statements_analyzed=0,
            summary=f"Validación {'exitosa' if result.is_valid else 'fallida'}: {result.total_issues} issues encontrados",
            syntax=None,  # Mapear si está disponible
            semantic=None,
            structural=None,
            best_practices=None,
            overall_score=1.0 if result.is_valid else 0.5,
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

# ENDPOINTS - EXPORTACIÓN
@router.post(
    "/export",
    response_model=ExportResult,
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
    - Excel (pendiente)
    """
    try:
        result = await export_service.export(request)
        return result

    except Exception as e:
        logger.error(f"Error en exportación: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post(
    "/export-batch",
    response_model=BatchExportResult,
    summary="Exportación en Batch",
    description="Exporta múltiples resultados"
)
async def export_batch(request: BatchExportRequest):
    """Exportación en batch"""
    import time
    from app.schemas.export import BatchExportItemResult
    
    start_time = time.time()
    results = []
    successful = 0
    failed = 0
    total_size = 0
    
    try:
        for item in request.items:
            try:
                # Crear request individual de exportación
                export_request = ExportRequest(
                    analysis_id=item.analysis_id,
                    options=request.options,
                    filename=item.filename
                )
                
                # Ejecutar exportación
                result = await export_service.export(export_request)
                
                results.append(BatchExportItemResult(
                    analysis_id=item.analysis_id,
                    success=True,
                    result=result,
                    error=None
                ))
                successful += 1
                
                if result and hasattr(result, 'file_size_bytes'):
                    total_size += result.file_size_bytes or 0
                    
            except Exception as e:
                logger.error(f"Error exportando {item.analysis_id}: {e}")
                results.append(BatchExportItemResult(
                    analysis_id=item.analysis_id,
                    success=False,
                    result=None,
                    error=str(e)
                ))
                failed += 1
        
        processing_time = (time.time() - start_time) * 1000
        
        return BatchExportResult(
            success=True,
            message=f"Batch export completado: {successful} exitosos, {failed} fallidos",
            results=results,
            total=len(request.items),
            successful=successful,
            failed=failed,
            zip_created=False,  # ZIP no implementado aún
            zip_path=None,
            zip_size_bytes=None,
            total_size_bytes=total_size,
            processing_time_ms=processing_time
        )
    except Exception as e:
        logger.error(f"Error en batch export: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# ENDPOINTS - CACHÉ
@router.get(
    "/cache/stats",
    summary="Estadísticas de Caché",
    description="Obtiene estadísticas del servicio de caché"
)
async def get_cache_stats():
    """Obtiene estadísticas del caché"""
    cache = get_cache_service()
    stats = cache.get_statistics()

    return {
        "success": True,
        "total_entries": stats["total_entries"],
        "active_entries": stats["active_entries"],
        "expired_entries": stats["expired_entries"],
        "total_hits": stats["total_hits"],
        "avg_hits": stats["avg_hits"]
    }

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