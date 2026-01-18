"""
Algorithm Schemas - DTOs para Algoritmos

Schemas Pydantic para representar algoritmos, sus propiedades y metadata.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import SourceLocation, validate_algorithm_name

# Enums
class AlgorithmCategory(str, Enum):
    """Categorías de algoritmos"""
    SORTING = "sorting"                    # Ordenamiento
    SEARCHING = "searching"                # Búsqueda
    GRAPH = "graph"                        # Grafos
    TREE = "tree"                          # Árboles
    DYNAMIC_PROGRAMMING = "dynamic_programming"  # Programación Dinámica
    GREEDY = "greedy"                      # Algoritmos Voraces
    DIVIDE_CONQUER = "divide_conquer"      # Divide y Vencerás
    BACKTRACKING = "backtracking"          # Backtracking
    RECURSION = "recursion"                # Recursión
    STRING = "string"                      # Cadenas
    MATHEMATICAL = "mathematical"          # Matemáticos
    OTHER = "other"                        # Otros

class AlgorithmComplexityClass(str, Enum):
    """Clases de complejidad"""
    CONSTANT = "constant"          # O(1)
    LOGARITHMIC = "logarithmic"    # O(log n)
    LINEAR = "linear"              # O(n)
    LINEARITHMIC = "linearithmic"  # O(n log n)
    QUADRATIC = "quadratic"        # O(n²)
    CUBIC = "cubic"                # O(n³)
    POLYNOMIAL = "polynomial"      # O(n^k)
    EXPONENTIAL = "exponential"    # O(2^n)
    FACTORIAL = "factorial"        # O(n!)

class LanguageType(str, Enum):
    """Tipos de lenguaje soportados"""
    PSEUDOCODE = "pseudocode"
    PYTHON = "python"

# Parameter Schema
class AlgorithmParameter(BaseModel):
    """Parámetro de un algoritmo"""
    name: str = Field(..., description="Nombre del parámetro")
    type: Optional[str] = Field(None, description="Tipo del parámetro (e.g., 'int', 'A[n]')")
    is_array: bool = Field(False, description="Si es un array")
    dimensions: List[Optional[str]] = Field(
        default_factory=list,
        description="Dimensiones del array (e.g., ['n', 'm'])"
    )
    is_object: bool = Field(False, description="Si es un objeto")
    object_type: Optional[str] = Field(None, description="Tipo de objeto (e.g., 'Node')")
    description: Optional[str] = Field(None, description="Descripción del parámetro")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "A",
                "type": "A[n]",
                "is_array": True,
                "dimensions": ["n"],
                "is_object": False,
                "description": "Array de entrada a ordenar"
            }
        }

# Algorithm Base Schema
class AlgorithmBase(BaseModel):
    """Schema base para algoritmos"""
    name: str = Field(..., min_length=1, max_length=100, description="Nombre del algoritmo")
    description: Optional[str] = Field(None, max_length=1000, description="Descripción")
    category: AlgorithmCategory = Field(
        AlgorithmCategory.OTHER,
        description="Categoría del algoritmo"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Tags para búsqueda y clasificación"
    )
    language: LanguageType = Field(
        LanguageType.PSEUDOCODE,
        description="Lenguaje del código"
    )
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        return validate_algorithm_name(v)
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        """Valida y normaliza tags"""
        # Convertir a minúsculas y eliminar duplicados
        normalized = [tag.lower().strip() for tag in v if tag.strip()]
        return list(set(normalized))

class AlgorithmCreate(AlgorithmBase):
    """Schema para crear un algoritmo"""
    code: str = Field(..., min_length=1, description="Código fuente del algoritmo")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Bubble Sort",
                "description": "Algoritmo de ordenamiento por burbuja",
                "category": "sorting",
                "tags": ["sorting", "quadratic", "simple"],
                "language": "pseudocode",
                "code": "algorithm bubbleSort(A[n])\nbegin\n  for i ← 1 to n-1 do\n    for j ← 1 to n-i do\n      if A[j] > A[j+1] then\n        swap(A[j], A[j+1])\nend"
            }
        }

class AlgorithmUpdate(BaseModel):
    """Schema para actualizar un algoritmo"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[AlgorithmCategory] = None
    tags: Optional[List[str]] = None
    code: Optional[str] = Field(None, min_length=1)
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if v is not None:
            return validate_algorithm_name(v)
        return v

# Algorithm Response Schema
class AlgorithmInfo(BaseModel):
    """Información extraída del algoritmo"""
    name: str = Field(..., description="Nombre del algoritmo")
    parameters: List[AlgorithmParameter] = Field(
        default_factory=list,
        description="Parámetros del algoritmo"
    )
    has_recursion: bool = Field(False, description="Si contiene recursión")
    has_loops: bool = Field(False, description="Si contiene loops")
    max_nesting_depth: int = Field(0, ge=0, description="Profundidad máxima de anidación")
    total_lines: int = Field(0, ge=0, description="Total de líneas de código")
    total_statements: int = Field(0, ge=0, description="Total de statements")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "bubbleSort",
                "parameters": [
                    {
                        "name": "A",
                        "type": "A[n]",
                        "is_array": True,
                        "dimensions": ["n"]
                    }
                ],
                "has_recursion": False,
                "has_loops": True,
                "max_nesting_depth": 2,
                "total_lines": 7,
                "total_statements": 5
            }
        }

class Algorithm(AlgorithmBase):
    """Schema completo de un algoritmo (response)"""
    id: str = Field(..., description="ID único del algoritmo")
    code: str = Field(..., description="Código fuente")
    info: Optional[AlgorithmInfo] = Field(None, description="Información extraída")
    
    # Metadata
    created_at: datetime = Field(..., description="Fecha de creación")
    updated_at: datetime = Field(..., description="Fecha de última actualización")
    analyzed: bool = Field(False, description="Si ha sido analizado")
    analysis_count: int = Field(0, ge=0, description="Número de veces analizado")
    
    # Complejidad (si está disponible)
    complexity_class: Optional[AlgorithmComplexityClass] = Field(
        None,
        description="Clase de complejidad"
    )
    big_o: Optional[str] = Field(None, description="Notación Big O")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "algo_123456",
                "name": "Bubble Sort",
                "description": "Algoritmo de ordenamiento por burbuja",
                "category": "sorting",
                "tags": ["sorting", "quadratic"],
                "language": "pseudocode",
                "code": "algorithm bubbleSort(A[n])\n...",
                "info": {
                    "name": "bubbleSort",
                    "parameters": [{"name": "A", "is_array": True}],
                    "has_recursion": False,
                    "has_loops": True,
                    "max_nesting_depth": 2
                },
                "created_at": "2025-01-17T10:00:00Z",
                "updated_at": "2025-01-17T10:00:00Z",
                "analyzed": True,
                "analysis_count": 3,
                "complexity_class": "quadratic",
                "big_o": "O(n²)"
            }
        }

class AlgorithmMetadata(BaseModel):
    """Metadata resumida de un algoritmo (para listados)"""
    id: str = Field(..., description="ID del algoritmo")
    name: str = Field(..., description="Nombre")
    category: AlgorithmCategory = Field(..., description="Categoría")
    tags: List[str] = Field(default_factory=list, description="Tags")
    complexity_class: Optional[AlgorithmComplexityClass] = None
    big_o: Optional[str] = None
    created_at: datetime = Field(..., description="Fecha de creación")
    analyzed: bool = Field(False, description="Si ha sido analizado")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "algo_123456",
                "name": "Bubble Sort",
                "category": "sorting",
                "tags": ["sorting", "quadratic"],
                "complexity_class": "quadratic",
                "big_o": "O(n²)",
                "created_at": "2025-01-17T10:00:00Z",
                "analyzed": True
            }
        }

# Search and Filter Schemas
class AlgorithmSearchCriteria(BaseModel):
    """Criterios de búsqueda de algoritmos"""
    query: Optional[str] = Field(None, description="Búsqueda por texto libre")
    category: Optional[AlgorithmCategory] = Field(None, description="Filtrar por categoría")
    tags: Optional[List[str]] = Field(None, description="Filtrar por tags (OR)")
    complexity_class: Optional[AlgorithmComplexityClass] = Field(
        None,
        description="Filtrar por clase de complejidad"
    )
    analyzed_only: bool = Field(False, description="Solo algoritmos ya analizados")
    min_date: Optional[datetime] = Field(None, description="Fecha mínima de creación")
    max_date: Optional[datetime] = Field(None, description="Fecha máxima de creación")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "sort",
                "category": "sorting",
                "tags": ["quadratic"],
                "complexity_class": "quadratic",
                "analyzed_only": True
            }
        }

class AlgorithmSortBy(str, Enum):
    """Campos por los que ordenar algoritmos"""
    NAME = "name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    COMPLEXITY = "complexity"
    ANALYSIS_COUNT = "analysis_count"

class AlgorithmListRequest(BaseModel):
    """Request para listar algoritmos"""
    criteria: Optional[AlgorithmSearchCriteria] = None
    sort_by: AlgorithmSortBy = Field(
        AlgorithmSortBy.CREATED_AT,
        description="Campo por el que ordenar"
    )
    ascending: bool = Field(False, description="Orden ascendente (True) o descendente (False)")
    page: int = Field(1, ge=1, description="Número de página")
    page_size: int = Field(20, ge=1, le=100, description="Elementos por página")

# Response Schemas
class AlgorithmResponse(BaseModel):
    """Response al crear/obtener un algoritmo"""
    success: bool = Field(True, description="Indica éxito de la operación")
    message: str = Field(..., description="Mensaje descriptivo")
    algorithm: Algorithm = Field(..., description="Datos del algoritmo")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Algoritmo creado exitosamente",
                "algorithm": {
                    "id": "algo_123456",
                    "name": "Bubble Sort",
                    "code": "..."
                }
            }
        }

class AlgorithmListResponse(BaseModel):
    """Response al listar algoritmos"""
    success: bool = Field(True)
    message: str = Field(...)
    algorithms: List[AlgorithmMetadata] = Field(..., description="Lista de algoritmos")
    total: int = Field(..., ge=0, description="Total de resultados")
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1)
    total_pages: int = Field(..., ge=0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Algoritmos recuperados exitosamente",
                "algorithms": [
                    {
                        "id": "algo_1",
                        "name": "Bubble Sort",
                        "category": "sorting"
                    }
                ],
                "total": 15,
                "page": 1,
                "page_size": 20,
                "total_pages": 1
            }
        }