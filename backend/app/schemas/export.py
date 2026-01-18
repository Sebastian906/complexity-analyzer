"""
Export Schemas - DTOs para Exportación de Resultados

Schemas Pydantic para exportar resultados de análisis.
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import BaseResponse

# Enums
class ExportFormat(str, Enum):
    """Formatos de exportación disponibles"""
    JSON = "json"
    MARKDOWN = "markdown"
    PDF = "pdf"
    EXCEL = "excel"
    HTML = "html"
    CSV = "csv"
    DOT = "dot"              # Graphviz
    MERMAID = "mermaid"      # Mermaid diagrams
    SVG = "svg"              # SVG graphics
    TXT = "txt"              # Plain text

class ExportSection(str, Enum):
    """Secciones que se pueden exportar"""
    ALGORITHM_INFO = "algorithm_info"
    COMPLEXITY = "complexity"
    PATTERNS = "patterns"
    STRUCTURES = "structures"
    VISUALIZATIONS = "visualizations"
    LINE_BY_LINE = "line_by_line"
    RECURRENCE = "recurrence"
    RECOMMENDATIONS = "recommendations"
    ALL = "all"

class ExportTemplate(str, Enum):
    """Templates predefinidos de exportación"""
    MINIMAL = "minimal"          # Solo información básica
    STANDARD = "standard"        # Información estándar
    DETAILED = "detailed"        # Información detallada
    COMPLETE = "complete"        # Todo incluido
    ACADEMIC = "academic"        # Formato académico
    PROFESSIONAL = "professional"  # Formato profesional

# Export Options
class ExportOptions(BaseModel):
    """Opciones de exportación"""
    # Secciones a incluir
    sections: List[ExportSection] = Field(
        default_factory=lambda: [ExportSection.ALL],
        description="Secciones a incluir en la exportación"
    )
    
    # Template
    template: ExportTemplate = Field(
        ExportTemplate.STANDARD,
        description="Template a usar"
    )
    
    # Formato
    format: ExportFormat = Field(..., description="Formato de exportación")
    
    # Visualizaciones
    include_visualizations: bool = Field(
        True,
        description="Incluir visualizaciones"
    )
    embed_visualizations: bool = Field(
        True,
        description="Embeber visualizaciones en el documento (vs referencias)"
    )
    visualization_format: str = Field(
        "svg",
        description="Formato de visualizaciones (svg, png)"
    )
    
    # Metadata
    include_metadata: bool = Field(
        True,
        description="Incluir metadata del análisis"
    )
    include_timestamp: bool = Field(
        True,
        description="Incluir timestamps"
    )
    
    # Formato del documento
    pretty_print: bool = Field(
        True,
        description="Formateo legible (para JSON, etc.)"
    )
    include_table_of_contents: bool = Field(
        False,
        description="Incluir tabla de contenidos (PDF, HTML, Markdown)"
    )
    
    # Personalización
    title: Optional[str] = Field(None, description="Título del documento")
    author: Optional[str] = Field(None, description="Autor del documento")
    company: Optional[str] = Field(None, description="Compañía/Institución")
    
    class Config:
        json_schema_extra = {
            "example": {
                "sections": ["all"],
                "template": "standard",
                "format": "pdf",
                "include_visualizations": True,
                "embed_visualizations": True,
                "visualization_format": "svg",
                "include_metadata": True,
                "pretty_print": True,
                "include_table_of_contents": True,
                "title": "Análisis de Bubble Sort",
                "author": "Juan Pérez"
            }
        }

# Export Request
class ExportRequest(BaseModel):
    """Request para exportar resultados"""
    # ID del análisis a exportar (si ya existe)
    analysis_id: Optional[str] = Field(None, description="ID de análisis existente")
    
    # O código para analizar y exportar directamente
    code: Optional[str] = Field(None, description="Código a analizar y exportar")
    algorithm_name: Optional[str] = Field(None, description="Nombre del algoritmo")
    
    # Opciones
    options: ExportOptions = Field(..., description="Opciones de exportación")
    
    # Output
    filename: Optional[str] = Field(
        None,
        description="Nombre del archivo de salida (sin extensión)"
    )
    output_path: Optional[str] = Field(
        None,
        description="Ruta completa de salida"
    )
    
    from pydantic import model_validator

    @model_validator(mode="after")
    def check_analysis_id_or_code(cls, values):
        if not values.analysis_id and not values.code:
            raise ValueError("Debe proporcionar 'analysis_id' o 'code'")
        return values
    
    class Config:
        json_schema_extra = {
            "example": {
                "analysis_id": "analysis_123456",
                "options": {
                    "format": "pdf",
                    "template": "professional",
                    "title": "Análisis de Bubble Sort"
                },
                "filename": "bubble_sort_analysis"
            }
        }

# Export Result
class ExportResult(BaseResponse):
    """Resultado de exportación"""
    format: ExportFormat = Field(..., description="Formato exportado")
    
    # Archivo
    filename: str = Field(..., description="Nombre del archivo generado")
    file_path: Optional[str] = Field(None, description="Ruta completa del archivo")
    file_size_bytes: Optional[int] = Field(None, ge=0, description="Tamaño del archivo")
    
    # Contenido (para formatos de texto)
    content: Optional[str] = Field(
        None,
        description="Contenido del export (para JSON, Markdown, etc.)"
    )
    
    # Estadísticas
    sections_included: List[str] = Field(
        default_factory=list,
        description="Secciones incluidas"
    )
    visualizations_count: int = Field(
        0,
        ge=0,
        description="Número de visualizaciones incluidas"
    )
    total_pages: Optional[int] = Field(
        None,
        ge=0,
        description="Total de páginas (para PDF)"
    )
    
    # Metadata
    generated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp de generación"
    )
    generation_time_ms: float = Field(
        ...,
        ge=0,
        description="Tiempo de generación en milisegundos"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Exportación completada exitosamente",
                "format": "pdf",
                "filename": "bubble_sort_analysis.pdf",
                "file_path": "/exports/pdf/bubble_sort_analysis.pdf",
                "file_size_bytes": 245678,
                "sections_included": [
                    "algorithm_info",
                    "complexity",
                    "patterns",
                    "visualizations"
                ],
                "visualizations_count": 2,
                "total_pages": 8,
                "generated_at": "2025-01-17T10:30:00Z",
                "generation_time_ms": 1234.56
            }
        }

# Batch Export
class BatchExportItem(BaseModel):
    """Item individual para exportación batch"""
    analysis_id: str = Field(..., description="ID del análisis")
    filename: Optional[str] = Field(None, description="Nombre del archivo")
    
    class Config:
        json_schema_extra = {
            "example": {
                "analysis_id": "analysis_123",
                "filename": "algorithm_1"
            }
        }

class BatchExportRequest(BaseModel):
    """Request para exportación en batch"""
    items: List[BatchExportItem] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Items a exportar (máx 50)"
    )
    
    # Opciones comunes
    options: ExportOptions = Field(..., description="Opciones para todos los exports")
    
    # Output
    output_directory: Optional[str] = Field(
        None,
        description="Directorio de salida"
    )
    create_zip: bool = Field(
        False,
        description="Crear archivo ZIP con todos los exports"
    )
    zip_filename: Optional[str] = Field(
        None,
        description="Nombre del archivo ZIP"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {"analysis_id": "analysis_1", "filename": "algo_1"},
                    {"analysis_id": "analysis_2", "filename": "algo_2"}
                ],
                "options": {
                    "format": "pdf",
                    "template": "standard"
                },
                "output_directory": "/exports/batch",
                "create_zip": True,
                "zip_filename": "all_analyses"
            }
        }

class BatchExportItemResult(BaseModel):
    """Resultado de exportación de un item del batch"""
    analysis_id: str = Field(..., description="ID del análisis")
    success: bool = Field(..., description="Si la exportación fue exitosa")
    result: Optional[ExportResult] = Field(
        None,
        description="Resultado del export (si fue exitoso)"
    )
    error: Optional[str] = Field(None, description="Error (si falló)")

class BatchExportResult(BaseResponse):
    """Resultado de exportación batch"""
    results: List[BatchExportItemResult] = Field(..., description="Resultados individuales")
    
    total: int = Field(..., ge=0, description="Total de items procesados")
    successful: int = Field(..., ge=0, description="Items exitosos")
    failed: int = Field(..., ge=0, description="Items fallidos")
    
    # ZIP
    zip_created: bool = Field(False, description="Si se creó archivo ZIP")
    zip_path: Optional[str] = Field(None, description="Ruta del archivo ZIP")
    zip_size_bytes: Optional[int] = Field(None, ge=0, description="Tamaño del ZIP")
    
    # Estadísticas
    total_size_bytes: int = Field(0, ge=0, description="Tamaño total de todos los archivos")
    processing_time_ms: float = Field(..., ge=0, description="Tiempo total de procesamiento")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Batch export completado",
                "results": [
                    {"analysis_id": "analysis_1", "success": True},
                    {"analysis_id": "analysis_2", "success": True}
                ],
                "total": 2,
                "successful": 2,
                "failed": 0,
                "zip_created": True,
                "zip_path": "/exports/all_analyses.zip",
                "zip_size_bytes": 512000,
                "total_size_bytes": 490000,
                "processing_time_ms": 5678.90
            }
        }

# Export Templates Info
class ExportTemplateInfo(BaseModel):
    """Información sobre un template de exportación"""
    template: ExportTemplate = Field(..., description="Identificador del template")
    name: str = Field(..., description="Nombre legible")
    description: str = Field(..., description="Descripción del template")
    
    sections_included: List[ExportSection] = Field(
        ...,
        description="Secciones incluidas por defecto"
    )
    suitable_for: List[str] = Field(
        default_factory=list,
        description="Casos de uso recomendados"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "template": "professional",
                "name": "Profesional",
                "description": "Template profesional con formato formal",
                "sections_included": [
                    "algorithm_info",
                    "complexity",
                    "patterns",
                    "visualizations",
                    "recommendations"
                ],
                "suitable_for": [
                    "Reportes empresariales",
                    "Documentación técnica",
                    "Presentaciones a clientes"
                ]
            }
        }

class AvailableExportsResponse(BaseResponse):
    """Response con formatos y templates disponibles"""
    formats: List[ExportFormat] = Field(..., description="Formatos disponibles")
    templates: List[ExportTemplateInfo] = Field(..., description="Templates disponibles")
    sections: List[ExportSection] = Field(..., description="Secciones exportables")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Opciones de exportación disponibles",
                "formats": ["json", "pdf", "markdown", "html"],
                "templates": [
                    {
                        "template": "standard",
                        "name": "Estándar",
                        "description": "Template estándar con información balanceada"
                    }
                ],
                "sections": ["algorithm_info", "complexity", "patterns"]
            }
        }