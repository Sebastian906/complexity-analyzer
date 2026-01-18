"""
Analysis Result Schemas - DTOs para Resultados de Análisis

Schemas Pydantic para respuestas de análisis de algoritmos.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.schemas.common import (
    AnalysisMetadata,
    BaseResponse,
    ConfidenceLevelEnum,
    SourceLocation,
)
from app.schemas.complexity import (
    ComplexityAnalysis,
    RecurrenceEquation,
    SpaceComplexityAnalysis,
)
from app.schemas.pattern import PatternDetectionResult
from app.schemas.algorithm import AlgorithmInfo

# Line by Line Analysis
class LineExecution(BaseModel):
    """Información de ejecución de una línea"""
    line_number: int = Field(..., ge=1, description="Número de línea")
    code: str = Field(..., description="Código de la línea")
    execution_count: str = Field(..., description="Número de ejecuciones (notación Big O)")
    statement_type: str = Field(..., description="Tipo de statement")
    complexity_contribution: str = Field(
        ...,
        description="Contribución a la complejidad total"
    )
    explanation: str = Field(..., description="Explicación de las ejecuciones")
    location: Optional[SourceLocation] = Field(None, description="Ubicación en el código")
    
    class Config:
        json_schema_extra = {
            "example": {
                "line_number": 3,
                "code": "for i ← 1 to n do",
                "execution_count": "n",
                "statement_type": "for_loop",
                "complexity_contribution": "O(n)",
                "explanation": "El loop se ejecuta n veces",
                "location": {"line": 3, "column": 4}
            }
        }

class LineByLineAnalysis(BaseModel):
    """Resultado de análisis línea por línea"""
    lines: List[LineExecution] = Field(..., description="Análisis por línea")
    dominant_complexity: str = Field(..., description="Complejidad dominante del algoritmo")
    total_lines: int = Field(..., ge=0, description="Total de líneas analizadas")
    summary: str = Field(..., description="Resumen del análisis")
    
    class Config:
        json_schema_extra = {
            "example": {
                "lines": [
                    {
                        "line_number": 2,
                        "code": "for i ← 1 to n do",
                        "execution_count": "n",
                        "statement_type": "for_loop",
                        "complexity_contribution": "O(n)",
                        "explanation": "Loop ejecutado n veces"
                    }
                ],
                "dominant_complexity": "O(n²)",
                "total_lines": 7,
                "summary": "El algoritmo tiene complejidad O(n²) dominada por loops anidados"
            }
        }

# Visualization Results
class VisualizationResult(BaseModel):
    """Resultado de una visualización"""
    type: str = Field(..., description="Tipo de visualización")
    format: str = Field(..., description="Formato (svg, png, dot, mermaid)")
    content: Optional[str] = Field(None, description="Contenido de la visualización")
    file_path: Optional[str] = Field(None, description="Ruta al archivo generado")
    statistics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Estadísticas de la visualización"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata adicional")
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "recursion_tree",
                "format": "svg",
                "file_path": "/exports/fibonacci_tree.svg",
                "statistics": {
                    "total_nodes": 15,
                    "max_depth": 5,
                    "total_calls": 15
                },
                "metadata": {
                    "recursion_type": "binary",
                    "start_value": 5
                }
            }
        }

# Structure Detection Results
class StructureMatch(BaseModel):
    """Estructura de datos detectada"""
    structure_type: str = Field(..., description="Tipo de estructura")
    structure_name: str = Field(..., description="Nombre legible")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Nivel de confianza")
    confidence_level: ConfidenceLevelEnum = Field(..., description="Nivel de confianza")
    variables: List[str] = Field(default_factory=list, description="Variables detectadas")
    operations: List[str] = Field(
        default_factory=list,
        description="Operaciones identificadas"
    )
    reasoning: str = Field(..., description="Razonamiento de la detección")
    
    class Config:
        json_schema_extra = {
            "example": {
                "structure_type": "array",
                "structure_name": "Array/Lista",
                "confidence": 0.85,
                "confidence_level": "high",
                "variables": ["A"],
                "operations": ["Acceso: A[i]", "Iteración sobre A"],
                "reasoning": "Se encontraron 3 indicadores clave: Parámetro con corchetes, Acceso indexado, Iteración secuencial"
            }
        }

class StructureUsage(BaseModel):
    """Análisis de uso de una estructura"""
    operation_frequencies: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Frecuencia de cada operación"
    )
    most_frequent_operation: Optional[str] = Field(
        None,
        description="Operación más frecuente"
    )
    access_pattern: Optional[str] = Field(
        None,
        description="Patrón de acceso (sequential, random, etc.)"
    )
    total_operations: int = Field(0, ge=0, description="Total de operaciones")
    recommendations: List[str] = Field(
        default_factory=list,
        description="Recomendaciones de optimización"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "operation_frequencies": [
                    {"operation": "Acceso", "count": 5, "complexity": "O(1)"}
                ],
                "most_frequent_operation": "Acceso",
                "access_pattern": "sequential",
                "total_operations": 5,
                "recommendations": ["Acceso secuencial óptimo para arrays"]
            }
        }

class StructureDetectionResult(BaseModel):
    """Resultado completo de detección de estructuras"""
    structures_found: List[StructureMatch] = Field(
        default_factory=list,
        description="Estructuras detectadas"
    )
    primary_structure: Optional[StructureMatch] = Field(
        None,
        description="Estructura principal (mayor confianza)"
    )
    primary_usage: Optional[StructureUsage] = Field(
        None,
        description="Análisis de uso de la estructura principal"
    )
    summary: str = Field(..., description="Resumen de estructuras detectadas")
    
    class Config:
        json_schema_extra = {
            "example": {
                "structures_found": [
                    {
                        "structure_type": "array",
                        "structure_name": "Array/Lista",
                        "confidence": 0.85,
                        "confidence_level": "high"
                    }
                ],
                "primary_structure": {
                    "structure_type": "array",
                    "structure_name": "Array/Lista",
                    "confidence": 0.85
                },
                "summary": "Estructura principal: Array/Lista (confianza: 85%)"
            }
        }

# Complete Analysis Result
class CompleteAnalysisResult(BaseResponse):
    """Resultado de análisis completo"""
    # Información del algoritmo
    algorithm_name: str = Field(..., description="Nombre del algoritmo")
    algorithm_info: AlgorithmInfo = Field(..., description="Información extraída del algoritmo")
    
    # Análisis de complejidad
    complexity: Optional[ComplexityAnalysis] = Field(
        None,
        description="Análisis de complejidad temporal"
    )
    space_complexity: Optional[SpaceComplexityAnalysis] = Field(
        None,
        description="Análisis de complejidad espacial"
    )
    recurrence_temporal: Optional[RecurrenceEquation] = Field(
        None,
        description="Ecuación de recurrencia T(n)"
    )
    recurrence_spatial: Optional[RecurrenceEquation] = Field(
        None,
        description="Ecuación de recurrencia S(n)"
    )
    line_by_line: Optional[LineByLineAnalysis] = Field(
        None,
        description="Análisis línea por línea"
    )
    
    # Detección de patrones
    patterns: Optional[PatternDetectionResult] = Field(
        None,
        description="Patrones algorítmicos detectados"
    )
    
    # Detección de estructuras
    structures: Optional[StructureDetectionResult] = Field(
        None,
        description="Estructuras de datos detectadas"
    )
    
    # Visualizaciones
    visualizations: List[VisualizationResult] = Field(
        default_factory=list,
        description="Visualizaciones generadas"
    )
    
    # Metadata
    metadata: AnalysisMetadata = Field(..., description="Metadata del análisis")
    
    # Resumen ejecutivo
    summary: str = Field(..., description="Resumen ejecutivo del análisis")
    recommendations: List[str] = Field(
        default_factory=list,
        description="Recomendaciones de optimización"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Análisis completado exitosamente",
                "timestamp": "2025-01-17T10:30:00Z",
                "algorithm_name": "bubbleSort",
                "algorithm_info": {
                    "name": "bubbleSort",
                    "parameters": [{"name": "A", "is_array": True}],
                    "has_recursion": False,
                    "has_loops": True,
                    "max_nesting_depth": 2
                },
                "complexity": {
                    "big_o": "O(n²)",
                    "omega": "Ω(n)",
                    "theta": None,
                    "explanation": "Complejidad cuadrática debido a loops anidados"
                },
                "space_complexity": {
                    "total": "O(1)",
                    "input_space": "O(n)",
                    "auxiliary_space": "O(1)"
                },
                "patterns": {
                    "primary_pattern": {
                        "pattern_name": "Fuerza Bruta",
                        "confidence": 0.85
                    }
                },
                "structures": {
                    "primary_structure": {
                        "structure_name": "Array/Lista",
                        "confidence": 0.92
                    }
                },
                "summary": "Bubble Sort: O(n²) tiempo, O(1) espacio. Fuerza bruta con array.",
                "recommendations": [
                    "Considerar QuickSort o MergeSort para mejor rendimiento promedio",
                    "El algoritmo es estable pero ineficiente para datos grandes"
                ]
            }
        }

# Batch Analysis Result
class BatchAnalysisItemResult(BaseModel):
    """Resultado de análisis para un item del batch"""
    id: str = Field(..., description="ID del item")
    success: bool = Field(..., description="Si el análisis fue exitoso")
    result: Optional[CompleteAnalysisResult] = Field(
        None,
        description="Resultado del análisis (si fue exitoso)"
    )
    error: Optional[str] = Field(None, description="Error (si falló)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "1",
                "success": True,
                "result": {
                    "algorithm_name": "test",
                    "complexity": {"big_o": "O(n)"}
                }
            }
        }

class BatchAnalysisResult(BaseResponse):
    """Resultado de análisis batch"""
    results: List[BatchAnalysisItemResult] = Field(..., description="Resultados individuales")
    total: int = Field(..., ge=0, description="Total de items procesados")
    successful: int = Field(..., ge=0, description="Items exitosos")
    failed: int = Field(..., ge=0, description="Items fallidos")
    processing_time_ms: float = Field(..., ge=0, description="Tiempo total de procesamiento")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Batch analysis completado",
                "results": [
                    {"id": "1", "success": True},
                    {"id": "2", "success": True}
                ],
                "total": 2,
                "successful": 2,
                "failed": 0,
                "processing_time_ms": 1234.56
            }
        }

# Quick Analysis Result (simplificado)
class QuickAnalysisResult(BaseResponse):
    """Resultado de análisis rápido (simplificado)"""
    algorithm_name: str = Field(..., description="Nombre del algoritmo")
    big_o: str = Field(..., description="Complejidad Big O")
    omega: str = Field(..., description="Complejidad Omega")
    theta: Optional[str] = Field(None, description="Complejidad Theta")
    space_complexity: str = Field(..., description="Complejidad espacial")
    primary_pattern: Optional[str] = Field(None, description="Patrón principal detectado")
    summary: str = Field(..., description="Resumen breve")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Análisis rápido completado",
                "algorithm_name": "test",
                "big_o": "O(n)",
                "omega": "Ω(n)",
                "theta": "Θ(n)",
                "space_complexity": "O(1)",
                "primary_pattern": "Recursión Lineal",
                "summary": "Algoritmo lineal simple"
            }
        }