"""
Export Endpoints - API v1

Endpoints para exportar análisis de algoritmos en múltiples formatos.
"""

from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field

from app.core.config import settings
from app.infrastructure.database.models.mongo import (
    Algorithm,
    AnalysisResult,
    PatternDetection
)
from app.infrastructure.export import (
    ExportFormat,
    ExporterFactory,
    export_analysis,
    export_to_multiple_formats,
    PDF_AVAILABLE,
    EXCEL_AVAILABLE,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()

# SCHEMAS
class ExportRequest(BaseModel):
    """Request para exportar un análisis"""
    algorithm_id: str = Field(..., description="ID del algoritmo en MongoDB")
    format: ExportFormat = Field(..., description="Formato de exportación")
    include_patterns: bool = Field(default=True, description="Incluir detección de patrones")
    include_visualizations: bool = Field(default=True, description="Incluir visualizaciones")
    
    class Config:
        json_schema_extra = {
            "example": {
                "algorithm_id": "507f1f77bcf86cd799439011",
                "format": "pdf",
                "include_patterns": True,
                "include_visualizations": True
            }
        }

class ExportMultipleRequest(BaseModel):
    """Request para exportar a múltiples formatos"""
    algorithm_id: str = Field(..., description="ID del algoritmo")
    formats: List[ExportFormat] = Field(..., description="Lista de formatos")
    include_patterns: bool = Field(default=True)
    include_visualizations: bool = Field(default=True)
    
    class Config:
        json_schema_extra = {
            "example": {
                "algorithm_id": "507f1f77bcf86cd799439011",
                "formats": ["json", "pdf", "markdown"],
                "include_patterns": True,
                "include_visualizations": True
            }
        }

class ExportResponse(BaseModel):
    """Response de exportación exitosa"""
    success: bool = True
    format: ExportFormat
    file_path: Optional[str] = None
    file_size_bytes: Optional[int] = None
    download_url: Optional[str] = None
    content: Optional[str] = None  # Para formatos de texto

class ExportMultipleResponse(BaseModel):
    """Response de exportación múltiple"""
    success: bool = True
    results: dict = Field(..., description="Resultados por formato")
    total_files: int
    successful: int
    failed: int

# ENDPOINTS
@router.get(
    "/formats",
    response_model=dict,
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
    
    return {
        "success": True,
        "formats": {
            "available": [f.value for f in available],
            "all": [f.value for f in ExportFormat],
            "optional_dependencies": {
                "pdf": {
                    "available": PDF_AVAILABLE,
                    "package": "reportlab"
                },
                "excel": {
                    "available": EXCEL_AVAILABLE,
                    "package": "openpyxl"
                }
            }
        }
    }

@router.post(
    "/export",
    response_model=ExportResponse,
    status_code=status.HTTP_200_OK,
    summary="Exportar análisis",
    description="Exporta un análisis de algoritmo en el formato especificado"
)
async def export_algorithm_analysis(request: ExportRequest):
    """
    Exporta el análisis de un algoritmo en el formato especificado.
    
    - **algorithm_id**: ID del algoritmo en MongoDB
    - **format**: Formato de exportación (json, pdf, markdown, etc.)
    - **include_patterns**: Incluir detección de patrones
    - **include_visualizations**: Incluir visualizaciones generadas
    
    Returns:
        ExportResponse con información del archivo generado
    """
    try:
        logger.info(f"Exportando algoritmo {request.algorithm_id} a {request.format}")
        
        # Verificar que el formato esté disponible
        if not ExporterFactory.is_format_available(request.format):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Formato no disponible",
                    "format": request.format.value,
                    "available_formats": [f.value for f in ExporterFactory.get_available_formats()]
                }
            )
        
        # Buscar el algoritmo en la base de datos
        algorithm = await Algorithm.get(request.algorithm_id)
        if not algorithm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Algoritmo no encontrado: {request.algorithm_id}"
            )
        
        # Buscar el análisis asociado
        analysis = await AnalysisResult.find_one(
            AnalysisResult.algorithm_id == request.algorithm_id
        )
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No se encontró análisis para el algoritmo: {request.algorithm_id}"
            )
        
        # Buscar patrones si está habilitado
        patterns = None
        if request.include_patterns:
            patterns = await PatternDetection.find_one(
                PatternDetection.algorithm_id == request.algorithm_id
            )
        
        # TODO: Cargar visualizaciones si están implementadas
        visualizations = {} if request.include_visualizations else None
        
        # Generar nombre de archivo
        safe_name = "".join(c if c.isalnum() or c in "._- " else "_" for c in algorithm.name)
        output_path = settings.EXPORTS_PATH / f"{safe_name}.{request.format.value}"
        
        # Exportar
        result = export_analysis(
            algorithm=algorithm,
            analysis=analysis,
            patterns=patterns,
            visualizations=visualizations,
            format=request.format,
            output_path=str(output_path)
        )
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "Error durante la exportación",
                    "errors": result.errors
                }
            )
        
        # Preparar respuesta
        response = ExportResponse(
            success=True,
            format=request.format,
            file_path=str(result.output_path) if result.output_path else None,
            download_url=f"/api/v1/export/download/{result.output_path.name}" if result.output_path else None
        )
        
        # Agregar contenido para formatos de texto
        if request.format in [ExportFormat.JSON, ExportFormat.MARKDOWN]:
            if result.output_path and result.output_path.exists():
                response.content = result.output_path.read_text(encoding='utf-8')
                response.file_size_bytes = result.output_path.stat().st_size
        elif result.output_path and result.output_path.exists():
            response.file_size_bytes = result.output_path.stat().st_size
        
        logger.info(f"Exportación exitosa: {result.output_path}")
        return response
        
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
    response_model=ExportMultipleResponse,
    status_code=status.HTTP_200_OK,
    summary="Exportar a múltiples formatos",
    description="Exporta un análisis a múltiples formatos simultáneamente"
)
async def export_multiple_formats(request: ExportMultipleRequest):
    """
    Exporta el análisis a múltiples formatos simultáneamente.
    
    Útil para generar un paquete completo de documentación.
    """
    try:
        logger.info(f"Exportación múltiple para {request.algorithm_id}: {request.formats}")
        
        # Buscar datos
        algorithm = await Algorithm.get(request.algorithm_id)
        if not algorithm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Algoritmo no encontrado: {request.algorithm_id}"
            )
        
        analysis = await AnalysisResult.find_one(
            AnalysisResult.algorithm_id == request.algorithm_id
        )
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No se encontró análisis para: {request.algorithm_id}"
            )
        
        patterns = None
        if request.include_patterns:
            patterns = await PatternDetection.find_one(
                PatternDetection.algorithm_id == request.algorithm_id
            )
        
        visualizations = {} if request.include_visualizations else None
        
        # Exportar a múltiples formatos
        results = export_to_multiple_formats(
            algorithm=algorithm,
            analysis=analysis,
            patterns=patterns,
            visualizations=visualizations,
            formats=request.formats,
            output_dir=str(settings.EXPORTS_PATH)
        )
        
        # Procesar resultados
        response_results = {}
        successful = 0
        failed = 0
        
        for format_type, result in results.items():
            if result.success:
                successful += 1
                response_results[format_type.value] = {
                    "success": True,
                    "file_path": str(result.output_path) if result.output_path else None,
                    "file_size": result.output_path.stat().st_size if result.output_path and result.output_path.exists() else None
                }
            else:
                failed += 1
                response_results[format_type.value] = {
                    "success": False,
                    "errors": result.errors
                }
        
        return ExportMultipleResponse(
            success=True,
            results=response_results,
            total_files=len(results),
            successful=successful,
            failed=failed
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