"""
Complexity Schemas - DTOs para Análisis de Complejidad

Schemas Pydantic para representar complejidades algorítmicas.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import validate_complexity_notation

# Enums
class ComplexityClass(str, Enum):
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

class RecurrenceType(str, Enum):
    """Tipos de recurrencia"""
    LINEAR = "linear"              # T(n) = T(n-1) + f(n)
    BINARY = "binary"              # T(n) = 2T(n/2) + f(n)
    MULTIPLE = "multiple"          # T(n) = aT(n/b) + f(n)
    NESTED = "nested"              # Recursión anidada
    TAIL = "tail"                  # Recursión de cola

class SolutionMethod(str, Enum):
    """Métodos de solución de recurrencias"""
    ITERATION = "iteration"
    RECURSION_TREE = "recursion_tree"
    MASTER_THEOREM = "master_theorem"
    SUBSTITUTION = "substitution"
    CHARACTERISTIC = "characteristic"

# Basic Complexity
class Complexity(BaseModel):
    """Representación de una complejidad"""
    notation: str = Field(..., description="Notación de complejidad (e.g., 'O(n²)')")
    complexity_class: Optional[ComplexityClass] = Field(
        None,
        description="Clase de complejidad"
    )
    explanation: str = Field(..., description="Explicación de la complejidad")
    dominant_term: Optional[str] = Field(
        None,
        description="Término dominante de la expresión"
    )
    
    @field_validator('notation')
    @classmethod
    def validate_notation(cls, v):
        return validate_complexity_notation(v)
    
    class Config:
        json_schema_extra = {
            "example": {
                "notation": "O(n²)",
                "complexity_class": "quadratic",
                "explanation": "Complejidad cuadrática debido a loops anidados",
                "dominant_term": "n²"
            }
        }

# Temporal Complexity Analysis
class ComplexityAnalysis(BaseModel):
    """Análisis completo de complejidad temporal"""
    big_o: str = Field(..., description="Notación Big O (peor caso)")
    omega: str = Field(..., description="Notación Omega (mejor caso)")
    theta: Optional[str] = Field(None, description="Notación Theta (caso promedio/cota ajustada)")
    
    big_o_class: Optional[ComplexityClass] = Field(None, description="Clase Big O")
    omega_class: Optional[ComplexityClass] = Field(None, description="Clase Omega")
    theta_class: Optional[ComplexityClass] = Field(None, description="Clase Theta")
    
    explanation: str = Field(..., description="Explicación del análisis")
    reasoning: List[str] = Field(
        default_factory=list,
        description="Razonamiento paso a paso"
    )
    
    has_tight_bound: bool = Field(
        False,
        description="Si existe cota ajustada (Theta)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "big_o": "O(n²)",
                "omega": "Ω(n)",
                "theta": None,
                "big_o_class": "quadratic",
                "omega_class": "linear",
                "explanation": "Peor caso cuadrático por loops anidados, mejor caso lineal si ya está ordenado",
                "reasoning": [
                    "Loop externo ejecuta n veces",
                    "Loop interno ejecuta hasta n-i veces",
                    "Total: n*(n-1)/2 ≈ n²/2 = O(n²)"
                ],
                "has_tight_bound": False
            }
        }

# Space Complexity Analysis
class SpaceComplexityAnalysis(BaseModel):
    """Análisis de complejidad espacial"""
    total: str = Field(..., description="Complejidad espacial total S(n)")
    input_space: str = Field(..., description="Espacio de entrada")
    auxiliary_space: str = Field(..., description="Espacio auxiliar")
    recursion_space: Optional[str] = Field(
        None,
        description="Espacio de pila de recursión"
    )
    
    explanation: str = Field(..., description="Explicación del uso de espacio")
    breakdown: Dict[str, str] = Field(
        default_factory=dict,
        description="Desglose detallado por componente"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "total": "O(n)",
                "input_space": "O(n)",
                "auxiliary_space": "O(1)",
                "recursion_space": "O(log n)",
                "explanation": "Espacio lineal debido a la entrada, auxiliar constante, recursión logarítmica",
                "breakdown": {
                    "input_array": "O(n)",
                    "temp_variables": "O(1)",
                    "call_stack": "O(log n)"
                }
            }
        }

# Recurrence Equations
class RecurrenceEquation(BaseModel):
    """Ecuación de recurrencia"""
    equation: str = Field(..., description="Ecuación en notación matemática")
    base_case: str = Field(..., description="Caso base")
    recursion_pattern: RecurrenceType = Field(..., description="Tipo de recurrencia")
    
    # Parámetros de la ecuación
    a: Optional[int] = Field(None, description="Número de llamadas recursivas")
    b: Optional[int] = Field(None, description="Factor de división del problema")
    f_n: Optional[str] = Field(None, description="Función de trabajo no recursivo")
    
    explanation: str = Field(..., description="Explicación de la ecuación")
    
    class Config:
        json_schema_extra = {
            "example": {
                "equation": "T(n) = 2T(n/2) + O(n)",
                "base_case": "T(1) = O(1)",
                "recursion_pattern": "binary",
                "a": 2,
                "b": 2,
                "f_n": "O(n)",
                "explanation": "Divide el problema en 2 mitades y combina en tiempo lineal"
            }
        }

class RecurrenceSolution(BaseModel):
    """Solución de una ecuación de recurrencia"""
    complexity: str = Field(..., description="Complejidad resultante")
    complexity_class: Optional[ComplexityClass] = Field(None)
    method_used: SolutionMethod = Field(..., description="Método de solución utilizado")
    steps: List[str] = Field(..., description="Pasos de la solución")
    verification: Optional[str] = Field(
        None,
        description="Verificación de la solución (por inducción si aplica)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "complexity": "O(n log n)",
                "complexity_class": "linearithmic",
                "method_used": "master_theorem",
                "steps": [
                    "Ecuación: T(n) = 2T(n/2) + O(n)",
                    "Identificar: a=2, b=2, f(n)=n",
                    "Calcular: log_b(a) = log_2(2) = 1",
                    "Caso 2 del Teorema Maestro: f(n) = Θ(n^log_b(a))",
                    "Por tanto: T(n) = Θ(n log n)"
                ],
                "verification": "Verificado por inducción matemática"
            }
        }

# Tight Bounds
class TightBoundResult(BaseModel):
    """Resultado de cálculo de cotas ajustadas"""
    has_tight_bound: bool = Field(..., description="Si existe cota ajustada")
    theta: Optional[str] = Field(None, description="Notación Theta si existe")
    little_o: Optional[str] = Field(None, description="Notación little-o")
    little_omega: Optional[str] = Field(None, description="Notación little-omega")
    
    explanation: str = Field(..., description="Explicación del resultado")
    conditions: List[str] = Field(
        default_factory=list,
        description="Condiciones para las cotas"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "has_tight_bound": True,
                "theta": "Θ(n²)",
                "little_o": "o(n³)",
                "little_omega": "ω(n)",
                "explanation": "Existe cota ajustada porque O(n²) = Ω(n²)",
                "conditions": [
                    "Peor caso y mejor caso coinciden",
                    "No hay variabilidad en la entrada que afecte la complejidad"
                ]
            }
        }

# Complexity Comparison
class ComplexityComparison(BaseModel):
    """Comparación de complejidades"""
    notation1: str = Field(..., description="Primera notación")
    notation2: str = Field(..., description="Segunda notación")
    comparison: str = Field(
        ...,
        description="Resultado de comparación (<, >, =, incomparable)"
    )
    explanation: str = Field(..., description="Explicación de la comparación")
    
    class Config:
        json_schema_extra = {
            "example": {
                "notation1": "O(n)",
                "notation2": "O(n²)",
                "comparison": "<",
                "explanation": "O(n) es asintóticamente menor que O(n²)"
            }
        }

# Complexity Summary
class ComplexitySummary(BaseModel):
    """Resumen de complejidad de un algoritmo"""
    algorithm_name: str = Field(..., description="Nombre del algoritmo")
    
    # Temporal
    temporal: ComplexityAnalysis = Field(..., description="Complejidad temporal")
    
    # Espacial
    spatial: SpaceComplexityAnalysis = Field(..., description="Complejidad espacial")
    
    # Recurrencias
    temporal_recurrence: Optional[RecurrenceEquation] = Field(
        None,
        description="Ecuación T(n)"
    )
    temporal_solution: Optional[RecurrenceSolution] = Field(
        None,
        description="Solución de T(n)"
    )
    
    spatial_recurrence: Optional[RecurrenceEquation] = Field(
        None,
        description="Ecuación S(n)"
    )
    spatial_solution: Optional[RecurrenceSolution] = Field(
        None,
        description="Solución de S(n)"
    )
    
    # Cotas ajustadas
    tight_bounds: Optional[TightBoundResult] = Field(
        None,
        description="Análisis de cotas ajustadas"
    )
    
    # Resumen
    summary: str = Field(..., description="Resumen ejecutivo")
    performance_category: str = Field(
        ...,
        description="Categoría de rendimiento (excelente/bueno/aceptable/pobre)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "algorithm_name": "Merge Sort",
                "temporal": {
                    "big_o": "O(n log n)",
                    "omega": "Ω(n log n)",
                    "theta": "Θ(n log n)",
                    "has_tight_bound": True
                },
                "spatial": {
                    "total": "O(n)",
                    "input_space": "O(n)",
                    "auxiliary_space": "O(n)",
                    "recursion_space": "O(log n)"
                },
                "temporal_recurrence": {
                    "equation": "T(n) = 2T(n/2) + O(n)",
                    "base_case": "T(1) = O(1)",
                    "recursion_pattern": "binary"
                },
                "temporal_solution": {
                    "complexity": "O(n log n)",
                    "method_used": "master_theorem"
                },
                "summary": "Algoritmo eficiente con complejidad linearítmica estable",
                "performance_category": "excelente"
            }
        }