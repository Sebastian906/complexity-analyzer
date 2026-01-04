"""
Branch and Bound Detector - Detecta algoritmos Branch and Bound

Similar a backtracking pero con poda basada en cotas (bounds).
"""

from typing import Dict, Any
from app.core.parser.ast_nodes import ASTNode, AlgorithmNode
from app.core.patterns.base_pattern import (
    BasePatternDetector, PatternType, PatternIndicator, PatternMatch
)
from app.core.patterns.pattern_matcher import PatternMatcher, get_algorithm_name

class BranchBoundDetector(BasePatternDetector):
    """Detector de Branch and Bound"""

    def __init__(self):
        super().__init__()
        self.pattern_type = PatternType.BRANCH_AND_BOUND
        self.pattern_name = "Branch and Bound"
        self.description = "Exploración con cotas y poda"
        self.typical_complexity = "Variable (depende de poda)"

        self._indicators = [
            PatternIndicator("bound_tracking", "Seguimiento de cotas", False, 4.0),
            PatternIndicator("branch_exploration", "Exploración de ramas", False, 3.5),
            PatternIndicator("pruning_by_bound", "Poda por cota", False, 3.0),
            PatternIndicator("best_solution_tracking", "Seguimiento de mejor solución", False, 2.5)
        ]

    def detect(self, ast: ASTNode) -> PatternMatch:
        """Detecta Branch and Bound"""
        analysis = self._analyze_structure(ast)

        indicators_found = []
        indicators_missing = []

        # Analizar indicadores básicamente igual que backtracking
        # pero buscando variables que rastreen "best" o "bound"
        for ind in self._indicators:
            # Simplificado: usar backtracking como proxy
            if analysis.get("has_backtracking_structure"):
                ind.found = True
                indicators_found.append(ind)
            else:
                indicators_missing.append(ind)

        confidence = self._calculate_confidence(indicators_found, indicators_missing)
        reasoning = "Patrón similar a backtracking con posible seguimiento de cotas"

        return self._create_match(
            confidence=confidence,
            indicators_found=indicators_found,
            indicators_missing=indicators_missing,
            reasoning=reasoning
        )

    def _analyze_structure(self, ast: ASTNode) -> Dict[str, Any]:
        """Análisis simplificado"""
        algo_name = get_algorithm_name(ast)

        # Branch and Bound es difícil de detectar estáticamente
        # Se detecta mejor con LLM o análisis semántico profundo
        analysis = {"has_backtracking_structure": False}

        if algo_name:
            result = PatternMatcher.has_backtracking_pattern(ast, algo_name)
            analysis["has_backtracking_structure"] = result.matched

        return analysis