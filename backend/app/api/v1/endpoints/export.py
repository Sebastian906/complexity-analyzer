"""
Export Endpoints - API v1

Endpoints para exportar análisis de algoritmos en múltiples formatos.
"""

from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import FileResponse
from datetime import datetime
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
    ExportConfig,
    ExportData,
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
        
        algorithm = None
        analysis = None
        patterns = None
        
        # Mejor lógica para determinar source
        if request.analysis_id:
            # Opción 1: Usar análisis existente de DB
            algorithm = await Algorithm.get(request.analysis_id)
            if not algorithm:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Algoritmo no encontrado: {request.analysis_id}"
                )
            
            analysis = await AnalysisResult.find_one(
                AnalysisResult.algorithm_id == request.analysis_id
            )
            if not analysis:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No se encontró análisis para: {request.analysis_id}"
                )
            
            if ExportSection.PATTERNS in request.options.sections or ExportSection.ALL in request.options.sections:
                patterns = await PatternDetection.find_one(
                    PatternDetection.algorithm_id == request.analysis_id
                )
        
        elif request.code:
            # Opción 2: Analizar código en tiempo real
            from app.core.parser import PseudocodeParser
            from app.core.analyzer import AnalyzerEngine
            
            logger.info("Analizando código para exportación en tiempo real...")
            
            try:
                # Parsear código
                parser = PseudocodeParser()
                ast = parser.parse(request.code)

                # Analizar con el motor
                engine = AnalyzerEngine()
                analysis_result = engine.analyze(ast)

                # Crear objetos temporales para exportación
                algorithm_name = request.algorithm_name or (
                    ast.algorithm.name if ast.algorithm else "unknown"
                )

                # Usar un mock object más robusto
                class MockAlgorithm:
                    def __init__(self, name: str, code: str):
                        self.id = 'temp-export'
                        self.name = name
                        self.code = code
                        self.description = ''
                        self.category = 'other'
                        self.tags = []
                        self.language = 'pseudocode'
                        self.created_at = datetime.utcnow()
                        self.updated_at = datetime.utcnow()
                        self.analyzed = True
                        self.analysis_count = 0

                        # Campos adicionales que puede esperar el exportador
                        self.author = None
                        self.version = '1.0'
                        self.is_public = False
                        self.complexity_class = None
                        self.typical_use_cases = []
                
                class MockAnalysis:
                    def __init__(self, analysis_result):
                        self.algorithm_id = 'temp-export'
        
                        # Complejidades básicas
                        self.big_o = getattr(analysis_result, 'big_o', 'O(n)')
                        self.omega = getattr(analysis_result, 'omega', 'Ω(1)')
                        self.theta = getattr(analysis_result, 'theta', None)
                        self.space_complexity = getattr(analysis_result, 'space_complexity', 'O(1)')

                        self.temporal_recurrence = getattr(analysis_result, 'temporal_recurrence', None)
                        self.spatial_recurrence = getattr(analysis_result, 'spatial_recurrence', None)

                        # Propiedades del algoritmo
                        self.is_recursive = getattr(analysis_result, 'is_recursive', False)
                        self.recursion_depth = getattr(analysis_result, 'recursion_depth', 0)

                        # Timestamps
                        self.created_at = datetime.utcnow()
                        
                        self.analysis_time_ms = getattr(analysis_result, 'analysis_time_ms', 0.0)
                        self.analysis_time = self.analysis_time_ms / 1000.0  # Convertir a segundos

                        self.analyzer_version = '1.0.0'
                        self.analysis_method = 'static'
                        self.confidence_score = 0.95

                        # Análisis detallado
                        self.line_by_line = getattr(analysis_result, 'line_by_line', None)
                        self.recurrence_equation = getattr(analysis_result, 'recurrence_equation', None)
                        self.tight_bounds = getattr(analysis_result, 'tight_bounds', None)

                        # Casos adicionales
                        self.best_case = getattr(analysis_result, 'best_case', self.omega)
                        self.worst_case = getattr(analysis_result, 'worst_case', self.big_o)
                        self.average_case = getattr(analysis_result, 'average_case', self.theta)

                        self.total_lines = getattr(analysis_result, 'total_lines', 0)
                        self.total_operations = getattr(analysis_result, 'total_operations', 0)
                        self.loop_count = getattr(analysis_result, 'loop_count', 0)
                        self.conditional_count = getattr(analysis_result, 'conditional_count', 0)

                        self.variables_used = getattr(analysis_result, 'variables_used', [])
                        self.functions_called = getattr(analysis_result, 'functions_called', [])
                        self.max_nesting_depth = getattr(analysis_result, 'max_nesting_depth', 0)

                        # Metadata
                        self.metadata = {
                            'temporary_export': True,
                            'source': 'direct_code_analysis'
                        }

                        # Estadísticas
                        self.total_lines = 0
                        self.total_operations = 0
                        self.loop_count = 0
                        self.conditional_count = 0

                algorithm = MockAlgorithm(algorithm_name, request.code)
                analysis = MockAnalysis(analysis_result)
                patterns = None

            except Exception as parse_error:
                logger.error(f"Error analizando código: {parse_error}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "Error al analizar código",
                        "message": str(parse_error)
                    }
                )
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debe proporcionar 'analysis_id' o 'code'"
            )
        
        # Visualizaciones (opcional)
        visualizations = {} if request.options.include_visualizations else None
        
        # Generar nombre de archivo seguro
        safe_name = "".join(
            c if c.isalnum() or c in "._- " else "_" 
            for c in algorithm.name
        )
        output_filename = request.filename or f"{safe_name}.{request.options.format.value}"
        
        # Usar carpeta específica según formato
        format_dir = settings.get_export_path(request.options.format.value)
        output_path = format_dir / output_filename
        
        logger.debug(f"Export path: {output_path}")
        
        # Exportar usando la infraestructura
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
        
        # Preparar respuesta
        sections_included = [s.value for s in request.options.sections]
        
        # Manejar content para formatos de texto
        content = None
        if request.options.format in [ExportFormat.JSON, ExportFormat.MARKDOWN]:
            if result.output_path and result.output_path.exists():
                try:
                    content = result.output_path.read_text(encoding='utf-8')
                except Exception as e:
                    logger.warning(f"No se pudo leer contenido: {e}")
        
        return ExportResult(
            success=True,
            message="Exportación completada exitosamente",
            timestamp=datetime.utcnow(),
            format=request.options.format,
            filename=output_filename,
            file_path=str(result.output_path) if result.output_path else None,
            file_size_bytes=result.output_path.stat().st_size if result.output_path and result.output_path.exists() else None,
            content=content,
            sections_included=sections_included,
            visualizations_count=len(visualizations) if visualizations else 0,
            total_pages=None,
            generated_at=datetime.utcnow(),
            generation_time_ms=0,
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
        
        processing_time = (time.time() - start_time) * 1000
        
        return BatchExportResult(
            success=True,
            message=f"Batch export completado: {successful} exitosos, {failed} fallidos",
            timestamp=None,
            results=results,
            total=len(request.items),
            successful=successful,
            failed=failed,
            zip_created=False,
            zip_path=None,
            zip_size_bytes=None,
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
        # Extraer extensión del archivo
        file_ext = Path(filename).suffix.lstrip('.')
        
        # Mapeo de extensiones a subdirectorios
        ext_to_dir = {
            'json': 'json',
            'md': 'markdown',
            'pdf': 'pdf',
            'xlsx': 'excel',
            'csv': 'csv',
            'html': 'html',
            'svg': 'svg',
            'dot': 'dot',
            'mmd': 'mermaid',
            'html': 'html',
            'img': 'images',
            'txt': 'txt',
        }
        
        # Determinar subdirectorio
        subdir = ext_to_dir.get(file_ext, file_ext)
        file_path = settings.get_export_path(subdir) / filename
        
        if not file_path.exists():
            # Intentar buscar en EXPORTS_PATH base también
            file_path = settings.EXPORTS_PATH / filename
            if not file_path.exists():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Archivo no encontrado: {filename}"
                )
        
        # Validar seguridad: archivo debe estar en EXPORTS_PATH o subdirectorios
        exports_base = str(settings.EXPORTS_PATH.resolve())
        file_resolved = str(file_path.resolve())
        
        if not file_resolved.startswith(exports_base):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acceso denegado"
            )
        
        # Determinar media type
        media_types = {
            "pdf": "application/pdf",
            "json": "application/json",
            "md": "text/markdown",
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "csv": "text/csv",
            "html": "text/html",
            "svg": "image/svg+xml",
            "dot": "text/vnd.graphviz",
            "mmd": "text/plain",
        }
        
        media_type = media_types.get(file_ext, "application/octet-stream")
        
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