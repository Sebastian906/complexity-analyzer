"""
Export Endpoints - API v1

Endpoints para exportar análisis de algoritmos en múltiples formatos.
"""

from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import FileResponse
from app.schemas import (
    # Export Schemas
    ExportRequest,
    ExportResult,
    ExportOptions,
    ExportFormat,
    ExportSection,
    ExportTemplate,
    BatchExportRequest,
    BatchExportResult,
    BatchExportItem,
    BatchExportItemResult,
    AvailableExportsResponse,
    ExportTemplateInfo,
    
    # Common
    BaseResponse,
)

from app.core.config import settings
from app.infrastructure.database.models.mongo import (
    Algorithm,
    AnalysisResult,
    PatternDetection
)
from app.infrastructure.export import (
    ExporterFactory,
    export_analysis,
    export_to_multiple_formats,
    PDF_AVAILABLE,
    EXCEL_AVAILABLE,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()

# ENDPOINTS
@router.get(
    "/formats",
    response_model=AvailableExportsResponse,
    summary="Listar formatos disponibles",
    description="Obtiene la lista de formatos de exportación soportados"
)
async def get_available_formats():
    """
    Lista todos los formatos de exportación disponibles.
    
    Indica qué formatos están disponibles y cuáles requieren
    dependencias opcionales.
    """
    available = ExporterFactory.get_available_formats()
    
    # Crear templates info
    templates = [
        ExportTemplateInfo(
            template=ExportTemplate.MINIMAL,
            name="Mínimal",
            description="Solo información básica y esencial",
            sections_included=[ExportSection.ALGORITHM_INFO, ExportSection.COMPLEXITY],
            suitable_for=["Vista rápida", "Referencia simple"],
        ),
        ExportTemplateInfo(
            template=ExportTemplate.STANDARD,
            name="Estándar",
            description="Información balanceada con detalles principales",
            sections_included=[
                ExportSection.ALGORITHM_INFO,
                ExportSection.COMPLEXITY,
                ExportSection.PATTERNS,
                ExportSection.RECOMMENDATIONS,
            ],
            suitable_for=["Documentación general", "Reportes técnicos"],
        ),
        ExportTemplateInfo(
            template=ExportTemplate.DETAILED,
            name="Detallado",
            description="Información completa con análisis profundo",
            sections_included=[
                ExportSection.ALGORITHM_INFO,
                ExportSection.COMPLEXITY,
                ExportSection.PATTERNS,
                ExportSection.STRUCTURES,
                ExportSection.LINE_BY_LINE,
                ExportSection.RECURRENCE,
                ExportSection.RECOMMENDATIONS,
            ],
            suitable_for=["Análisis académico", "Investigación"],
        ),
        ExportTemplateInfo(
            template=ExportTemplate.COMPLETE,
            name="Completo",
            description="Todo incluido con visualizaciones",
            sections_included=[ExportSection.ALL],
            suitable_for=["Documentación exhaustiva", "Presentaciones"],
        ),
        ExportTemplateInfo(
            template=ExportTemplate.ACADEMIC,
            name="Académico",
            description="Formato académico formal",
            sections_included=[
                ExportSection.ALGORITHM_INFO,
                ExportSection.COMPLEXITY,
                ExportSection.RECURRENCE,
                ExportSection.PATTERNS,
            ],
            suitable_for=["Papers", "Tesis", "Trabajos académicos"],
        ),
        ExportTemplateInfo(
            template=ExportTemplate.PROFESSIONAL,
            name="Profesional",
            description="Formato profesional para negocios",
            sections_included=[
                ExportSection.ALGORITHM_INFO,
                ExportSection.COMPLEXITY,
                ExportSection.RECOMMENDATIONS,
                ExportSection.VISUALIZATIONS,
            ],
            suitable_for=["Reportes empresariales", "Presentaciones a clientes"],
        ),
    ]
    
    return AvailableExportsResponse(
        success=True,
        message="Formatos y templates disponibles",
        timestamp=None,
        formats=list(available),
        templates=templates,
        sections=list(ExportSection),
    )

@router.post(
    "/export",
    response_model=ExportResult,
    status_code=status.HTTP_200_OK,
    summary="Exportar análisis",
    description="Exporta un análisis de algoritmo en el formato especificado"
)
async def export_algorithm_analysis(request: ExportRequest):
    """
    Exporta el análisis de un algoritmo en el formato especificado.
    
    - **analysis_id**: ID del algoritmo en MongoDB (requerido si no se pasa code)
    - **code**: Código a analizar y exportar (requerido si no se pasa analysis_id)
    - **options**: Opciones de exportación
    
    Returns:
        ExportResult con información del archivo generado
    """
    try:
        logger.info(f"Exportando análisis: format={request.options.format}")
        
        # Verificar que el formato esté disponible
        if not ExporterFactory.is_format_available(request.options.format):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Formato no disponible",
                    "format": request.options.format.value,
                    "available_formats": [f.value for f in ExporterFactory.get_available_formats()]
                }
            )
        
        # Determinar source: analysis_id o code
        algorithm = None
        analysis = None
        patterns = None
        
        if request.analysis_id:
            # Buscar el algoritmo en la base de datos
            algorithm = await Algorithm.get(request.analysis_id)
            if not algorithm:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Algoritmo no encontrado: {request.analysis_id}"
                )
            
            # Buscar el análisis asociado
            analysis = await AnalysisResult.find_one(
                AnalysisResult.algorithm_id == request.analysis_id
            )
            if not analysis:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No se encontró análisis para: {request.analysis_id}"
                )
            
            # Buscar patrones si está habilitado
            if ExportSection.PATTERNS in request.options.sections or ExportSection.ALL in request.options.sections:
                patterns = await PatternDetection.find_one(
                    PatternDetection.algorithm_id == request.analysis_id
                )
        
        elif request.code:
            # Analizar código en tiempo real
            from app.core.parser import parse_pseudocode
            from app.core.analyzer import AnalyzerEngine
            
            ast = parse_pseudocode(request.code)
            engine = AnalyzerEngine()
            analysis_result = engine.analyze(ast)
            
            # Crear objetos temporales para exportar
            # (En producción, usar modelos reales)
            algorithm = type('obj', (object,), {
                'name': request.algorithm_name or ast.algorithm.name,
                'code': request.code,
            })()
            
            analysis = type('obj', (object,), {
                'big_o': analysis_result.big_o,
                'omega': analysis_result.omega,
                'theta': analysis_result.theta,
            })()
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debe proporcionar 'analysis_id' o 'code'"
            )
        
        # Visualizaciones (opcional)
        visualizations = {} if request.options.include_visualizations else None
        
        # Generar nombre de archivo
        safe_name = "".join(c if c.isalnum() or c in "._- " else "_" for c in algorithm.name)
        output_filename = request.filename or f"{safe_name}.{request.options.format.value}"
        output_path = settings.EXPORTS_PATH / output_filename
        
        # Exportar
        from app.infrastructure.export import ExportConfig, ExportData
        from datetime import datetime
        
        export_data = ExportData(
            algorithm=algorithm,
            analysis=analysis,
            patterns=patterns,
            visualizations=visualizations or {}
        )
        
        config = ExportConfig(
            format=request.options.format,
            output_path=output_path,
            template=request.options.template,
            include_visualizations=request.options.include_visualizations,
            include_metadata=request.options.include_metadata,
        )
        
        exporter = ExporterFactory.create(request.options.format, config)
        result = exporter.export(export_data)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "Error durante la exportación",
                    "errors": result.errors
                }
            )
        
        # Preparar respuesta usando ExportResult del schema
        sections_included = [s.value for s in request.options.sections]
        
        return ExportResult(
            success=True,
            message="Exportación completada exitosamente",
            timestamp=datetime.utcnow(),
            format=request.options.format,
            filename=output_filename,
            file_path=str(result.output_path) if result.output_path else None,
            file_size_bytes=result.output_path.stat().st_size if result.output_path and result.output_path.exists() else None,
            content=result.output_path.read_text(encoding='utf-8') if request.options.format in [ExportFormat.JSON, ExportFormat.MARKDOWN] and result.output_path else None,
            sections_included=sections_included,
            visualizations_count=len(visualizations) if visualizations else 0,
            total_pages=None,
            generated_at=datetime.utcnow(),
            generation_time_ms=0,  # Calcular si es necesario
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error exportando: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )

@router.post(
    "/export/multiple",
    response_model=BatchExportResult,
    status_code=status.HTTP_200_OK,
    summary="Exportar a múltiples formatos",
    description="Exporta un análisis a múltiples formatos simultáneamente"
)
async def export_multiple_formats(request: BatchExportRequest):
    """
    Exporta el análisis a múltiples formatos simultáneamente.
    
    Útil para generar un paquete completo de documentación.
    """
    try:
        logger.info(f"Exportación múltiple: {len(request.items)} items")
        
        results = []
        successful = 0
        failed = 0
        total_size = 0
        
        import time
        start_time = time.time()
        
        for item in request.items:
            try:
                # Crear ExportRequest individual
                individual_request = ExportRequest(
                    analysis_id=item.analysis_id,
                    code=None,
                    algorithm_name=None,
                    options=request.options,
                    filename=item.filename,
                    output_path=None,
                )
                
                # Exportar
                result = await export_algorithm_analysis(individual_request)
                
                results.append(BatchExportItemResult(
                    analysis_id=item.analysis_id,
                    success=True,
                    result=result,
                    error=None,
                ))
                
                successful += 1
                if result.file_size_bytes:
                    total_size += result.file_size_bytes
                    
            except Exception as e:
                logger.error(f"Error exportando item {item.analysis_id}: {e}")
                results.append(BatchExportItemResult(
                    analysis_id=item.analysis_id,
                    success=False,
                    result=None,
                    error=str(e),
                ))
                failed += 1
        
        # Crear ZIP si se solicita
        zip_created = False
        zip_path = None
        zip_size = None
        
        if request.create_zip and successful > 0:
            # TODO: Implementar creación de ZIP
            pass
        
        processing_time = (time.time() - start_time) * 1000
        
        return BatchExportResult(
            success=True,
            message=f"Batch export completado: {successful} exitosos, {failed} fallidos",
            timestamp=None,
            results=results,
            total=len(request.items),
            successful=successful,
            failed=failed,
            zip_created=zip_created,
            zip_path=zip_path,
            zip_size_bytes=zip_size,
            total_size_bytes=total_size,
            processing_time_ms=processing_time,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error en exportación múltiple: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )

@router.get(
    "/download/{filename}",
    summary="Descargar archivo exportado",
    description="Descarga un archivo previamente exportado"
)
async def download_export(filename: str):
    """
    Descarga un archivo exportado.
    
    Args:
        filename: Nombre del archivo a descargar
    """
    try:
        file_path = settings.EXPORTS_PATH / filename
        
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Archivo no encontrado: {filename}"
            )
        
        # Validar que el archivo esté dentro de EXPORTS_PATH (seguridad)
        if not str(file_path.resolve()).startswith(str(settings.EXPORTS_PATH.resolve())):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acceso denegado"
            )
        
        # Determinar media type basado en extensión
        media_types = {
            ".pdf": "application/pdf",
            ".json": "application/json",
            ".md": "text/markdown",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".csv": "text/csv",
            ".html": "text/html",
            ".svg": "image/svg+xml",
            ".dot": "text/vnd.graphviz",
        }
        
        media_type = media_types.get(file_path.suffix, "application/octet-stream")
        
        return FileResponse(
            path=file_path,
            media_type=media_type,
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error descargando archivo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error descargando archivo: {str(e)}"
        )

@router.delete(
    "/cleanup",
    summary="Limpiar archivos exportados",
    description="Elimina archivos exportados antiguos"
)
async def cleanup_exports(
    older_than_days: int = Query(default=7, ge=1, le=365, description="Días de antigüedad")
):
    """
    Limpia archivos exportados más antiguos que X días.
    
    Args:
        older_than_days: Eliminar archivos más antiguos que este número de días
    """
    try:
        import time
        from datetime import datetime, timedelta

        cutoff_time = time.time() - (older_than_days * 86400)
        deleted_count = 0
        deleted_size = 0

        for file_path in settings.EXPORTS_PATH.iterdir():
            if file_path.is_file():
                if file_path.stat().st_mtime < cutoff_time:
                    file_size = file_path.stat().st_size
                    file_path.unlink()
                    deleted_count += 1
                    deleted_size += file_size

        logger.info(f"Limpieza completada: {deleted_count} archivos, {deleted_size} bytes")

        return {
            "success": True,
            "deleted_files": deleted_count,
            "deleted_size_bytes": deleted_size,
            "deleted_size_mb": round(deleted_size / (1024 * 1024), 2),
            "cutoff_days": older_than_days
        }

    except Exception as e:
        logger.exception(f"Error en limpieza: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en limpieza: {str(e)}"
        )