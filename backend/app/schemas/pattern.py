"""
Pattern Schemas - DTOs para Detección de Patrones

Schemas Pydantic para representar patrones algorítmicos detectados.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, model_validator

from app.schemas.common import ConfidenceLevelEnum

# Enums
class PatternType(str, Enum):
    """Tipos de patrones algorítmicos"""
    BRUTE_FORCE = "brute_force"
    RECURSIVE = "recursive"
    DIVIDE_AND_CONQUER = "divide_and_conquer"
    DYNAMIC_PROGRAMMING = "dynamic_programming"
    GREEDY = "greedy"
    BACKTRACKING = "backtracking"
    BRANCH_AND_BOUND = "branch_and_bound"
    SORTING = "sorting"
    SEARCHING = "searching"
    QUANTUM = "quantum"
    BIO_INSPIRED = "bio_inspired"
    APPROXIMATION = "approximation"

# Pattern Indicator
class PatternIndicator(BaseModel):
    """Indicador de un patrón"""
    name: str = Field(..., description="Nombre del indicador")
    description: str = Field(..., description="Descripción del indicador")
    found: bool = Field(..., description="Si el indicador fue encontrado")
    weight: float = Field(..., ge=0.0, le=1.0, description="Peso en el cálculo de confianza")
    evidence: Optional[str] = Field(None, description="Evidencia encontrada en el código")
    location: Optional[str] = Field(None, description="Ubicación en el AST")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "nested_loops",
                "description": "Loops anidados profundos (>= 2 niveles)",
                "found": True,
                "weight": 0.4,
                "evidence": "for i ← 1 to n do; for j ← 1 to n do",
                "location": "lines 2-5"
            }
        }

# Pattern Match
class PatternMatch(BaseModel):
    """Patrón detectado"""
    pattern_type: PatternType = Field(..., description="Tipo de patrón")
    pattern_name: str = Field(..., description="Nombre legible del patrón")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Nivel de confianza")
    confidence_level: ConfidenceLevelEnum = Field(..., description="Nivel categórico de confianza")
    
    indicators_found: List[PatternIndicator] = Field(
        default_factory=list,
        description="Indicadores encontrados"
    )
    indicators_missing: List[PatternIndicator] = Field(
        default_factory=list,
        description="Indicadores no encontrados"
    )
    
    reasoning: str = Field(..., description="Razonamiento de la detección")
    typical_complexity: Optional[str] = Field(
        None,
        description="Complejidad típica de este patrón"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata adicional específica del patrón"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "pattern_type": "brute_force",
                "pattern_name": "Fuerza Bruta",
                "confidence": 0.85,
                "confidence_level": "high",
                "indicators_found": [
                    {
                        "name": "nested_loops",
                        "description": "Loops anidados",
                        "found": True,
                        "weight": 0.4,
                        "evidence": "for i...for j..."
                    }
                ],
                "indicators_missing": [
                    {
                        "name": "memoization",
                        "description": "Tabla de memoización",
                        "found": False,
                        "weight": 0.3
                    }
                ],
                "reasoning": "Se detectaron 3 indicadores clave: loops anidados, exploración exhaustiva, ausencia de optimización",
                "typical_complexity": "O(n²) a O(2^n)",
                "metadata": {
                    "nesting_depth": 2,
                    "has_pruning": False
                }
            }
        }

# Scored Pattern
class ScoredPattern(BaseModel):
    """Patrón con score ajustado y ranking"""
    pattern: PatternMatch = Field(..., description="Patrón detectado")
    raw_score: float = Field(..., ge=0.0, le=1.0, description="Score sin ajustar")
    adjusted_score: float = Field(..., ge=0.0, le=1.0, description="Score ajustado")
    final_score: float = Field(..., ge=0.0, le=1.0, description="Score final (con penalizaciones)")
    
    # Ajustes
    confidence_bonus: float = Field(0.0, description="Bonus por alta confianza")
    missing_penalty: float = Field(0.0, description="Penalización por indicadores faltantes")
    conflict_penalty: float = Field(0.0, description="Penalización por conflictos")
    
    # Conflictos
    conflicts: List[str] = Field(
        default_factory=list,
        description="Patrones en conflicto"
    )
    
    rank: Optional[int] = Field(None, ge=1, description="Ranking (1 = más probable)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "pattern": {
                    "pattern_type": "divide_and_conquer",
                    "pattern_name": "Divide y Vencerás",
                    "confidence": 0.92
                },
                "raw_score": 0.92,
                "adjusted_score": 1.0,
                "final_score": 0.95,
                "confidence_bonus": 0.08,
                "missing_penalty": 0.0,
                "conflict_penalty": 0.05,
                "conflicts": ["brute_force"],
                "rank": 1
            }
        }

# Pattern Detection Result
class PatternDetectionResult(BaseModel):
    """Resultado completo de detección de patrones"""
    patterns_found: List[PatternMatch] = Field(
        default_factory=list,
        description="Todos los patrones detectados"
    )
    scored_patterns: List[ScoredPattern] = Field(
        default_factory=list,
        description="Patrones con scoring y ranking"
    )
    
    primary_pattern: Optional[ScoredPattern] = Field(
        None,
        description="Patrón principal (mayor score)"
    )
    confident_patterns: List[ScoredPattern] = Field(
        default_factory=list,
        description="Patrones con alta confianza (>= 0.7)"
    )
    
    summary: str = Field(..., description="Resumen de patrones detectados")
    pattern_count: int = Field(0, ge=0, description="Total de patrones detectados")

    high_confidence_count: int = Field(
        default=0, 
        ge=0, 
        description="Número de patrones con alta confianza"
    )

    statistics: Optional["PatternStatistics"] = Field(
        None,
        description="Estadísticas de detección"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata del análisis"
    )
    
    # model_validator FUERA de los campos, como método de clase
    @model_validator(mode='after')
    def compute_high_confidence_count(self):
        """Calcula automáticamente high_confidence_count si no se provee"""
        if self.high_confidence_count == 0 and self.confident_patterns:
            self.high_confidence_count = len(self.confident_patterns)
        return self
    
    @property
    def has_patterns(self) -> bool:
        """Si se detectaron patrones"""
        return self.pattern_count > 0
    
    @property
    def primary_pattern_name(self) -> Optional[str]:
        """Nombre del patrón principal"""
        return self.primary_pattern.pattern.pattern_name if self.primary_pattern else None
    
    @property
    def primary_confidence(self) -> float:
        """Confianza del patrón principal"""
        return self.primary_pattern.final_score if self.primary_pattern else 0.0

    class Config:
        json_schema_extra = {
            "example": {
                "patterns_found": [
                    {
                        "pattern_type": "divide_and_conquer",
                        "pattern_name": "Divide y Vencerás",
                        "confidence": 0.92
                    },
                    {
                        "pattern_type": "recursive",
                        "pattern_name": "Recursión",
                        "confidence": 0.88
                    }
                ],
                "scored_patterns": [
                    {
                        "pattern": {"pattern_name": "Divide y Vencerás"},
                        "final_score": 0.95,
                        "rank": 1
                    }
                ],
                "primary_pattern": {
                    "pattern": {"pattern_name": "Divide y Vencerás"},
                    "final_score": 0.95
                },
                "confident_patterns": [
                    {"pattern": {"pattern_name": "Divide y Vencerás"}}
                ],
                "summary": "Patrón principal: Divide y Vencerás (confianza: 95%). También detectado: Recursión (88%).",
                "pattern_count": 2,
                "high_confidence_count": 1,
                "metadata": {
                    "analysis_time_ms": 45.2,
                    "detectors_used": 12
                }
            }
        }

# Pattern Statistics
class PatternStatistics(BaseModel):
    """Estadísticas de detección de patrones"""
    total_patterns_detected: int = Field(..., ge=0, description="Total de patrones detectados")
    high_confidence_patterns: int = Field(..., ge=0, description="Patrones con alta confianza")
    medium_confidence_patterns: int = Field(..., ge=0, description="Patrones con confianza media")
    low_confidence_patterns: int = Field(..., ge=0, description="Patrones con confianza baja")
    
    pattern_types_found: List[PatternType] = Field(
        default_factory=list,
        description="Tipos de patrones encontrados"
    )
    most_confident_pattern: Optional[str] = Field(
        None,
        description="Patrón con mayor confianza"
    )
    average_confidence: float = Field(..., ge=0.0, le=1.0, description="Confianza promedio")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_patterns_detected": 12,
                "high_confidence_patterns": 2,
                "medium_confidence_patterns": 5,
                "low_confidence_patterns": 5,
                "pattern_types_found": ["divide_and_conquer", "recursive"],
                "most_confident_pattern": "Divide y Vencerás",
                "average_confidence": 0.65
            }
        }

# Pattern Comparison
class PatternComparison(BaseModel):
    """Comparación entre dos patrones"""
    pattern1: str = Field(..., description="Primer patrón")
    pattern2: str = Field(..., description="Segundo patrón")
    
    similarity: float = Field(..., ge=0.0, le=1.0, description="Similitud entre patrones")
    
    common_indicators: List[str] = Field(
        default_factory=list,
        description="Indicadores en común"
    )
    unique_to_pattern1: List[str] = Field(
        default_factory=list,
        description="Indicadores únicos del primer patrón"
    )
    unique_to_pattern2: List[str] = Field(
        default_factory=list,
        description="Indicadores únicos del segundo patrón"
    )
    
    are_mutually_exclusive: bool = Field(
        False,
        description="Si los patrones son mutuamente excluyentes"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "pattern1": "Divide y Vencerás",
                "pattern2": "Recursión",
                "similarity": 0.75,
                "common_indicators": ["recursive_calls", "base_case"],
                "unique_to_pattern1": ["problem_division", "combine_solutions"],
                "unique_to_pattern2": [],
                "are_mutually_exclusive": False
            }
        }

# Pattern Recommendation
class PatternRecommendation(BaseModel):
    """Recomendación de patrón alternativo"""
    current_pattern: str = Field(..., description="Patrón actual detectado")
    recommended_pattern: str = Field(..., description="Patrón recomendado")
    
    reason: str = Field(..., description="Razón de la recomendación")
    benefits: List[str] = Field(default_factory=list, description="Beneficios del cambio")
    trade_offs: List[str] = Field(default_factory=list, description="Trade-offs a considerar")
    
    difficulty: str = Field(
        ...,
        description="Dificultad de implementación (fácil/media/difícil)"
    )
    expected_improvement: Optional[str] = Field(
        None,
        description="Mejora esperada en complejidad"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "current_pattern": "Fuerza Bruta",
                "recommended_pattern": "Programación Dinámica",
                "reason": "El problema tiene subproblemas superpuestos",
                "benefits": [
                    "Reducción de O(2^n) a O(n²)",
                    "Evita recálculos innecesarios"
                ],
                "trade_offs": [
                    "Requiere espacio adicional O(n²)",
                    "Mayor complejidad de implementación"
                ],
                "difficulty": "media",
                "expected_improvement": "De O(2^n) a O(n²)"
            }
        }