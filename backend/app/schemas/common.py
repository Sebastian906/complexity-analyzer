"""
Schemas Comunes - DTOs Compartidos

Schemas Pydantic reutilizables en todo el proyecto.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

# Enums Comunes
class StatusEnum(str, Enum):
    """Estados generales del sistema"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ConfidenceLevelEnum(str, Enum):
    """Niveles de confianza"""
    VERY_LOW = "very_low"      # < 0.3
    LOW = "low"                # 0.3 - 0.5
    MEDIUM = "medium"          # 0.5 - 0.7
    HIGH = "high"              # 0.7 - 0.9
    VERY_HIGH = "very_high"    # >= 0.9

class ComplexityNotationEnum(str, Enum):
    """Notaciones de complejidad"""
    BIG_O = "big_o"           # O(n) - Peor caso
    OMEGA = "omega"           # Ω(n) - Mejor caso
    THETA = "theta"           # Θ(n) - Caso promedio
    LITTLE_O = "little_o"     # o(n) - Cota superior no ajustada
    LITTLE_OMEGA = "little_omega"  # ω(n) - Cota inferior no ajustada

# Base Response Schema
class BaseResponse(BaseModel):
    """Schema base para todas las responses"""
    success: bool = Field(..., description="Indica si la operación fue exitosa")
    message: Optional[str] = Field(None, description="Mensaje descriptivo")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp de la response")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Operación completada exitosamente",
                "timestamp": "2025-01-17T10:30:00Z"
            }
        }

class ErrorDetail(BaseModel):
    """Detalle de un error"""
    type: str = Field(..., description="Tipo de error")
    message: str = Field(..., description="Mensaje del error")
    code: Optional[str] = Field(None, description="Código de error")
    field: Optional[str] = Field(None, description="Campo que causó el error")
    details: Optional[Dict[str, Any]] = Field(None, description="Detalles adicionales")

class ErrorResponse(BaseResponse):
    """Response para errores"""
    success: bool = Field(False, description="Siempre False para errores")
    error: ErrorDetail = Field(..., description="Detalle del error")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "message": "Error al procesar la solicitud",
                "timestamp": "2025-01-17T10:30:00Z",
                "error": {
                    "type": "ValidationError",
                    "message": "El código proporcionado contiene errores de sintaxis",
                    "code": "SYNTAX_ERROR",
                    "field": "code",
                    "details": {
                        "line": 5,
                        "column": 12,
                        "expected": "end"
                    }
                }
            }
        }

# Pagination
class PaginationParams(BaseModel):
    """Parámetros de paginación"""
    page: int = Field(1, ge=1, description="Número de página (1-indexed)")
    page_size: int = Field(20, ge=1, le=100, description="Elementos por página")
    
    @property
    def skip(self) -> int:
        """Calcula el offset para la consulta"""
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        """Alias para page_size"""
        return self.page_size

class PaginatedResponse(BaseModel):
    """Response con paginación"""
    items: List[Any] = Field(..., description="Lista de elementos")
    total: int = Field(..., ge=0, description="Total de elementos disponibles")
    page: int = Field(..., ge=1, description="Página actual")
    page_size: int = Field(..., ge=1, description="Elementos por página")
    total_pages: int = Field(..., ge=0, description="Total de páginas")
    has_next: bool = Field(..., description="Hay página siguiente")
    has_prev: bool = Field(..., description="Hay página anterior")
    
    @classmethod
    def create(
        cls,
        items: List[Any],
        total: int,
        pagination: PaginationParams
    ) -> "PaginatedResponse":
        """Factory method para crear response paginada"""
        total_pages = (total + pagination.page_size - 1) // pagination.page_size
        
        return cls(
            items=items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=total_pages,
            has_next=pagination.page < total_pages,
            has_prev=pagination.page > 1
        )

# Metadata
class TimingMetadata(BaseModel):
    """Metadata de timing para operaciones"""
    started_at: datetime = Field(..., description="Timestamp de inicio")
    completed_at: Optional[datetime] = Field(None, description="Timestamp de finalización")
    duration_ms: Optional[float] = Field(None, ge=0, description="Duración en milisegundos")
    
    @field_validator('duration_ms')
    @classmethod
    def calculate_duration(cls, v, info):
        """Calcula duración si no se proporciona"""
        if v is None and info.data.get('started_at') and info.data.get('completed_at'):
            delta = info.data['completed_at'] - info.data['started_at']
            return delta.total_seconds() * 1000
        return v

class ResourceMetadata(BaseModel):
    """Metadata de recursos utilizados"""
    memory_used_mb: Optional[float] = Field(None, ge=0, description="Memoria utilizada en MB")
    cpu_time_ms: Optional[float] = Field(None, ge=0, description="Tiempo de CPU en ms")
    nodes_analyzed: Optional[int] = Field(None, ge=0, description="Nodos del AST analizados")
    operations_count: Optional[int] = Field(None, ge=0, description="Operaciones realizadas")

class AnalysisMetadata(BaseModel):
    """Metadata completa de análisis"""
    timing: TimingMetadata = Field(..., description="Información de timing")
    resources: Optional[ResourceMetadata] = Field(None, description="Recursos utilizados")
    version: str = Field("1.0.0", description="Versión del analizador")
    environment: Optional[str] = Field(None, description="Entorno de ejecución")

# Source 
class SourceLocation(BaseModel):
    """Ubicación en código fuente"""
    line: int = Field(..., ge=1, description="Número de línea")
    column: int = Field(..., ge=0, description="Número de columna")
    end_line: Optional[int] = Field(None, ge=1, description="Línea final")
    end_column: Optional[int] = Field(None, ge=0, description="Columna final")
    
    def __str__(self) -> str:
        if self.end_line and self.end_column:
            return f"{self.line}:{self.column}-{self.end_line}:{self.end_column}"
        return f"{self.line}:{self.column}"

class CodeSnippet(BaseModel):
    """Fragmento de código con contexto"""
    code: str = Field(..., description="Código fuente")
    location: Optional[SourceLocation] = Field(None, description="Ubicación en el código")
    context_before: Optional[List[str]] = Field(None, description="Líneas de contexto antes")
    context_after: Optional[List[str]] = Field(None, description="Líneas de contexto después")

# Statistics
class Statistics(BaseModel):
    """Estadísticas generales"""
    count: int = Field(0, ge=0, description="Conteo total")
    min_value: Optional[float] = Field(None, description="Valor mínimo")
    max_value: Optional[float] = Field(None, description="Valor máximo")
    avg_value: Optional[float] = Field(None, description="Valor promedio")
    median_value: Optional[float] = Field(None, description="Valor mediano")
    std_deviation: Optional[float] = Field(None, ge=0, description="Desviación estándar")

# Common Validators
def validate_complexity_notation(value: str) -> str:
    """Valida formato de notación de complejidad"""
    import re
    pattern = r'^[OΩΘoω]\([^)]+\)$'
    if not re.match(pattern, value):
        raise ValueError(f"Formato de complejidad inválido: {value}")
    return value

def validate_algorithm_name(value: str) -> str:
    """Valida nombre de algoritmo"""
    if not value or not value.strip():
        raise ValueError("El nombre del algoritmo no puede estar vacío")
    
    if len(value) > 100:
        raise ValueError("El nombre del algoritmo es demasiado largo (máx 100 caracteres)")
    
    return value.strip()

# Helper Functions
def create_success_response(message: str, **kwargs) -> Dict[str, Any]:
    """Helper para crear response exitosa"""
    return {
        "success": True,
        "message": message,
        "timestamp": datetime.utcnow(),
        **kwargs
    }

def create_error_response(
    error_type: str,
    message: str,
    code: Optional[str] = None,
    field: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Helper para crear response de error"""
    return {
        "success": False,
        "message": message,
        "timestamp": datetime.utcnow(),
        "error": {
            "type": error_type,
            "message": message,
            "code": code,
            "field": field,
            "details": details
        }
    }