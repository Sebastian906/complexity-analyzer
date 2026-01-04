"""
Complexity Module - Análisis de complejidad temporal

Proporciona analizadores para calcular Big O, Omega, Theta
y cotas ajustadas de algoritmos.

Exports principales:
    - BigOAnalyzer: Análisis de peor caso O(n)
    - OmegaAnalyzer: Análisis de mejor caso Ω(n)
    - ThetaAnalyzer: Análisis de caso promedio Θ(n)
    - TightBoundsCalculator: Verificación de cotas fuertes
    - ComplexityCalculator: Orquestador de todos los análisis
"""

from app.core.analyzer.complexity.base_analyzer import (
    BaseComplexityAnalyzer,
    ComplexityResult
)

from app.core.analyzer.complexity.big_o_analyzer import BigOAnalyzer

from app.core.analyzer.complexity.omega_analyzer import OmegaAnalyzer

from app.core.analyzer.complexity.theta_analyzer import ThetaAnalyzer

from app.core.analyzer.complexity.tight_bounds import (
    TightBoundsCalculator,
    TightBoundResult
)

from app.core.analyzer.complexity.complexity_calculator import ComplexityCalculator

__all__ = [
    # Base
    "BaseComplexityAnalyzer",
    "ComplexityResult",
    
    # Analizadores
    "BigOAnalyzer",
    "OmegaAnalyzer",
    "ThetaAnalyzer",
    
    # Cotas fuertes
    "TightBoundsCalculator",
    "TightBoundResult",
    
    # Orquestador
    "ComplexityCalculator",
]
