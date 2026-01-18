"""
Analysis Request Schemas - DTOs para Requests de Análisis

Schemas Pydantic para solicitudes de análisis de algoritmos.
"""

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.algorithm import LanguageType

# Enums
class AnalysisType(str, Enum):
    """Tipos de análisis disponibles"""
    COMPLEXITY = "complexity"          # Solo complejidad
    PATTERNS = "patterns"              # Solo patrones
    STRUCTURES = "structures"          # Solo estructuras de datos
    VISUALIZATION = "visualization"    # Solo visualización
    COMPLETE = "complete"              # Análisis completo

class RecurrenceMethod(str, Enum):
    """Métodos para resolver ecuaciones de recurrencia"""
    AUTO = "auto"                      # Selección automática
    ITERATION = "iteration"            # Método de iteración
    RECURSION_TREE = "recursion_tree"  # Árbol de recursión
    MASTER_THEOREM = "master_theorem"  # Teorema maestro
    SUBSTITUTION = "substitution"      # Sustitución inteligente
    CHARACTERISTIC = "characteristic"  # Ecuación característica

class VisualizationType(str, Enum):
    """Tipos de visualización"""
    RECURSION_TREE = "recursion_tree"      # Árbol de recursión
    EXECUTION_FLOW = "execution_flow"      # Flujo de ejecución
    DATA_STRUCTURE = "data_structure"      # Estructura de datos
    CALL_GRAPH = "call_graph"              # Grafo de llamadas

# Base Analysis Request
class AnalysisRequest(BaseModel):
    """Request base para análisis"""
    code: str = Field(
        ...,
        min_length=1,
        max_length=100000,
        description="Código del algoritmo a analizar"
    )
    language: LanguageType = Field(
        LanguageType.PSEUDOCODE,
        description="Lenguaje del código"
    )
    algorithm_name: Optional[str] = Field(
        None,
        description="Nombre del algoritmo (opcional, se extrae del código si no se proporciona)"
    )
    
    @field_validator('code')
    @classmethod
    def validate_code(cls, v):
        """Valida el código"""
        if not v.strip():
            raise ValueError("El código no puede estar vacío")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": "algorithm bubbleSort(A[n])\nbegin\n  for i ← 1 to n-1 do\n    for j ← 1 to n-i do\n      if A[j] > A[j+1] then\n        swap(A[j], A[j+1])\nend",
                "language": "pseudocode",
                "algorithm_name": "Bubble Sort"
            }
        }

# Complexity Analysis Request
class ComplexityAnalysisOptions(BaseModel):
    """Opciones para análisis de complejidad"""
    analyze_temporal: bool = Field(
        True,
        description="Analizar complejidad temporal (Big O, Omega, Theta)"
    )
    analyze_spatial: bool = Field(
        True,
        description="Analizar complejidad espacial S(n)"
    )
    analyze_recurrence: bool = Field(
        True,
        description="Construir y resolver ecuaciones de recurrencia T(n) y S(n)"
    )
    recurrence_method: RecurrenceMethod = Field(
        RecurrenceMethod.AUTO,
        description="Método para resolver recurrencias"
    )
    analyze_line_by_line: bool = Field(
        True,
        description="Análisis línea por línea de ejecuciones"
    )
    calculate_tight_bounds: bool = Field(
        True,
        description="Calcular cotas ajustadas (Theta)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "analyze_temporal": True,
                "analyze_spatial": True,
                "analyze_recurrence": True,
                "recurrence_method": "auto",
                "analyze_line_by_line": True,
                "calculate_tight_bounds": True
            }
        }

class ComplexityAnalysisRequest(AnalysisRequest):
    """Request para análisis de complejidad"""
    options: ComplexityAnalysisOptions = Field(
        default_factory=ComplexityAnalysisOptions,
        description="Opciones de análisis"
    )

# Pattern Detection Request
class PatternDetectionOptions(BaseModel):
    """Opciones para detección de patrones"""
    min_confidence: float = Field(
        0.3,
        ge=0.0,
        le=1.0,
        description="Umbral mínimo de confianza para reportar patrones"
    )
    detect_all: bool = Field(
        True,
        description="Detectar todos los patrones (si False, solo el más probable)"
    )
    include_indicators: bool = Field(
        True,
        description="Incluir indicadores encontrados/faltantes en respuesta"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "min_confidence": 0.3,
                "detect_all": True,
                "include_indicators": True
            }
        }

class PatternDetectionRequest(AnalysisRequest):
    """Request para detección de patrones"""
    options: PatternDetectionOptions = Field(
        default_factory=PatternDetectionOptions,
        description="Opciones de detección"
    )

# Structure Detection Request
class StructureDetectionOptions(BaseModel):
    """Opciones para detección de estructuras"""
    min_confidence: float = Field(
        0.3,
        ge=0.0,
        le=1.0,
        description="Umbral mínimo de confianza"
    )
    analyze_usage: bool = Field(
        True,
        description="Analizar uso de las estructuras detectadas"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "min_confidence": 0.3,
                "analyze_usage": True
            }
        }

class StructureDetectionRequest(AnalysisRequest):
    """Request para detección de estructuras de datos"""
    options: StructureDetectionOptions = Field(
        default_factory=StructureDetectionOptions,
        description="Opciones de detección"
    )

# Visualization Request
class VisualizationOptions(BaseModel):
    """Opciones para visualización"""
    types: List[VisualizationType] = Field(
        default_factory=lambda: [VisualizationType.RECURSION_TREE],
        description="Tipos de visualización a generar"
    )
    max_depth: int = Field(
        10,
        ge=1,
        le=20,
        description="Profundidad máxima para árboles de recursión"
    )
    max_nodes: int = Field(
        100,
        ge=1,
        le=1000,
        description="Número máximo de nodos en visualizaciones"
    )
    start_value: Optional[int] = Field(
        None,
        description="Valor inicial para simulación (e.g., n=8 para fibonacci)"
    )
    format: str = Field(
        "svg",
        description="Formato de salida (svg, png, dot, mermaid)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "types": ["recursion_tree", "execution_flow"],
                "max_depth": 10,
                "max_nodes": 100,
                "start_value": 8,
                "format": "svg"
            }
        }

class VisualizationRequest(AnalysisRequest):
    """Request para generación de visualizaciones"""
    options: VisualizationOptions = Field(
        default_factory=VisualizationOptions,
        description="Opciones de visualización"
    )

# Complete Analysis Request
class CompleteAnalysisRequest(AnalysisRequest):
    """Request para análisis completo"""
    # Opciones de complejidad
    analyze_complexity: bool = Field(True, description="Incluir análisis de complejidad")
    complexity_options: ComplexityAnalysisOptions = Field(
        default_factory=ComplexityAnalysisOptions,
        description="Opciones de complejidad"
    )
    
    # Opciones de patrones
    analyze_patterns: bool = Field(True, description="Incluir detección de patrones")
    pattern_options: PatternDetectionOptions = Field(
        default_factory=PatternDetectionOptions,
        description="Opciones de patrones"
    )
    
    # Opciones de estructuras
    analyze_structures: bool = Field(True, description="Incluir detección de estructuras")
    structure_options: StructureDetectionOptions = Field(
        default_factory=StructureDetectionOptions,
        description="Opciones de estructuras"
    )
    
    # Opciones de visualización
    generate_visualizations: bool = Field(
        False,
        description="Generar visualizaciones (puede ser costoso)"
    )
    visualization_options: VisualizationOptions = Field(
        default_factory=VisualizationOptions,
        description="Opciones de visualización"
    )
    
    # Opciones generales
    use_cache: bool = Field(
        True,
        description="Usar caché si hay resultado previo disponible"
    )
    validate_before_analyze: bool = Field(
        True,
        description="Validar código antes de analizar"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": "algorithm mergeSort(A[n])\nbegin\n  if n > 1 then\n  begin\n    mid ← n/2\n    call mergeSort(A[1..mid])\n    call mergeSort(A[mid+1..n])\n    call merge(A, mid)\n  end\nend",
                "language": "pseudocode",
                "algorithm_name": "Merge Sort",
                "analyze_complexity": True,
                "analyze_patterns": True,
                "analyze_structures": True,
                "generate_visualizations": True,
                "use_cache": True,
                "validate_before_analyze": True
            }
        }

# Batch Analysis Request
class BatchAnalysisItem(BaseModel):
    """Item individual para análisis batch"""
    id: str = Field(..., description="ID único para el item")
    code: str = Field(..., min_length=1, description="Código a analizar")
    language: LanguageType = Field(LanguageType.PSEUDOCODE)
    algorithm_name: Optional[str] = None

class BatchAnalysisRequest(BaseModel):
    """Request para análisis en batch"""
    items: List[BatchAnalysisItem] = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Lista de algoritmos a analizar (máx 10)"
    )
    analysis_type: AnalysisType = Field(
        AnalysisType.COMPLETE,
        description="Tipo de análisis a realizar"
    )
    parallel: bool = Field(
        True,
        description="Procesar en paralelo (más rápido)"
    )
    
    @field_validator('items')
    @classmethod
    def validate_unique_ids(cls, v):
        """Valida que los IDs sean únicos"""
        ids = [item.id for item in v]
        if len(ids) != len(set(ids)):
            raise ValueError("Los IDs deben ser únicos")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {
                        "id": "1",
                        "code": "algorithm test1(n)\nbegin\n  x ← 1\nend",
                        "language": "pseudocode"
                    },
                    {
                        "id": "2",
                        "code": "algorithm test2(n)\nbegin\n  for i ← 1 to n do\n    x ← x + 1\nend",
                        "language": "pseudocode"
                    }
                ],
                "analysis_type": "complete",
                "parallel": True
            }
        }

# Quick Analysis Request (para testing rápido)
class QuickAnalysisRequest(BaseModel):
    """Request simplificado para análisis rápido"""
    code: str = Field(..., min_length=1, description="Código a analizar")
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": "algorithm test(n)\nbegin\n  for i ← 1 to n do\n    x ← x + 1\nend"
            }
        }