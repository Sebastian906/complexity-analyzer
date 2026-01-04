"""
Patterns Module - Módulo de Detección de Patrones Algorítmicos

Proporciona detección automática de patrones y técnicas algorítmicas
mediante análisis estático del AST.

Patrones soportados:
- Fuerza Bruta
- Recursión
- Divide y Vencerás
- Programación Dinámica
- Greedy (Voraz)
- Backtracking
- Branch and Bound
- Ordenamiento
- Búsqueda
- Algoritmos Cuánticos
- Algoritmos Bio-inspirados
- Algoritmos de Aproximación

Exports principales:
    - PatternDetector: Detector principal que orquesta todo
    - PatternMatch: Resultado de detección de un patrón
    - PatternType: Enum de tipos de patrones
    - ScoredPattern: Patrón con score ajustado
    - PatternDetectionResult: Resultado completo del análisis
"""

# Base
from app.core.patterns.base_pattern import (
    BasePatternDetector,
    PatternType,
    PatternMatch,
    PatternIndicator,
    ConfidenceLevel
)

# Pattern Matcher
from app.core.patterns.pattern_matcher import PatternMatcher, MatchResult

# Scoring
from app.core.patterns.pattern_scorer import PatternScorer, ScoredPattern

# Detector Principal
from app.core.patterns.pattern_detector import (
    PatternDetector,
    PatternDetectionResult
)

# Detectores Específicos
from app.core.patterns.detectors.brute_force import BruteForceDetector
from app.core.patterns.detectors.recursive_detector import RecursiveDetector
from app.core.patterns.detectors.divide_conquer_detector import DivideConquerDetector
from app.core.patterns.detectors.dynamic_programming_detector import DynamicProgrammingDetector
from app.core.patterns.detectors.greedy_detector import GreedyDetector
from app.core.patterns.detectors.backtracking_detector import BacktrackingDetector
from app.core.patterns.detectors.branch_bound_detector import BranchBoundDetector
from app.core.patterns.detectors.sorting_and_searching import SortingDetector, SearchingDetector
from app.core.patterns.detectors.advanced_patterns import (
    QuantumAlgorithmsDetector,
    BioInspiredDetector,
    ApproximationDetector
)

__all__ = [
    # Base
    "BasePatternDetector",
    "PatternType",
    "PatternMatch",
    "PatternIndicator",
    "ConfidenceLevel",
    
    # Matcher
    "PatternMatcher",
    "MatchResult",
    
    # Scoring
    "PatternScorer",
    "ScoredPattern",
    
    # Detector Principal
    "PatternDetector",
    "PatternDetectionResult",
    
    # Detectores implementados
    "BruteForceDetector",
    "RecursiveDetector",
    "DivideConquerDetector",
    "DynamicProgrammingDetector",
    "GreedyDetector",
    "BacktrackingDetector",
    "BranchBoundDetector",
    "SortingDetector",
    "SearchingDetector",
    "QuantumAlgorithmsDetector",
    "BioInspiredDetector",
    "ApproximationDetector",
]

# Función helper para uso rápido
def detect_patterns(ast, min_confidence: float = 0.3) -> PatternDetectionResult:
    """
    Helper function para detectar patrones rápidamente.
    
    Args:
        ast: Abstract Syntax Tree del algoritmo
        min_confidence: Umbral mínimo de confianza
    
    Returns:
        PatternDetectionResult con todos los patrones
    
    Example:
        >>> from app.core.parser import parse_pseudocode
        >>> from app.core.patterns import detect_patterns
        >>> 
        >>> ast = parse_pseudocode(code)
        >>> result = detect_patterns(ast)
        >>> 
        >>> print(result.primary_pattern_name)
        >>> print(result.summary)
    """
    detector = PatternDetector()
    return detector.detect(ast, min_confidence)