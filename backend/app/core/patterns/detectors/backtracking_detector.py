"""
Backtracking Detector - Detecta algoritmos de Backtracking

Identifica algoritmos que exploran soluciones mediante prueba y error,
retrocediendo cuando una solución no es válida.
"""

from typing import Dict, Any

from app.core.parser.ast_nodes import ASTNode, AlgorithmNode
from app.core.patterns.base_pattern import (
    BasePatternDetector,
    PatternType,
    PatternIndicator,
    PatternMatch
)
from app.core.patterns.pattern_matcher import PatternMatcher, get_algorithm_name

class BacktrackingDetector(BasePatternDetector):
    """
    Detector de Backtracking.

    Características:
    - Recursión múltiple
    - Condiciones de validación (poda)
    - Construcción incremental de solución
    - Retroceso cuando no hay solución válida
    """

    def __init__(self):
        super().__init__()
        self.pattern_type = PatternType.BACKTRACKING
        self.pattern_name = "Backtracking"
        self.description = "Exploración con retroceso y poda"
        self.typical_complexity = "O(2^n) o O(n!)"

        self._indicators = [
            PatternIndicator(
                name="recursive_exploration",
                description="Exploración recursiva de posibilidades",
                found=False,
                weight=4.0
            ),
            PatternIndicator(
                name="pruning_conditions",
                description="Condiciones de poda",
                found=False,
                weight=3.5
            ),
            PatternIndicator(
                name="solution_validation",
                description="Validación de solución parcial",
                found=False,
                weight=3.0
            ),
            PatternIndicator(
                name="backtrack_mechanism",
                description="Mecanismo de retroceso",
                found=False,
                weight=2.5
            )
        ]

    def detect(self, ast: ASTNode) -> PatternMatch:
        """Detecta patrón de backtracking"""
        analysis = self._analyze_structure(ast)

        indicators_found = []
        indicators_missing = []

        # 1. Exploración recursiva
        recursive_exp = self._indicators[0]
        if analysis["has_recursive_exploration"]:
            recursive_exp.found = True
            recursive_exp.evidence = f"{analysis['recursive_calls']} llamadas recursivas"
            indicators_found.append(recursive_exp)
        else:
            indicators_missing.append(recursive_exp)

        # 2. Condiciones de poda
        pruning = self._indicators[1]
        if analysis["has_pruning"]:
            pruning.found = True
            pruning.evidence = f"{analysis['conditionals']} condiciones detectadas"
            indicators_found.append(pruning)
        else:
            indicators_missing.append(pruning)

        # 3. Validación
        validation = self._indicators[2]
        if analysis["has_validation"]:
            validation.found = True
            validation.evidence = "Patrón de validación detectado"
            indicators_found.append(validation)
        else:
            indicators_missing.append(validation)

        # 4. Backtrack
        backtrack = self._indicators[3]
        if analysis["has_backtrack_mechanism"]:
            backtrack.found = True
            backtrack.evidence = "Estructura de retroceso identificada"
            indicators_found.append(backtrack)
        else:
            indicators_missing.append(backtrack)

        confidence = self._calculate_confidence(indicators_found, indicators_missing)

        # Backtracking requiere TODOS los indicadores principales
        # Si falta exploración recursiva O poda O mecanismo de backtrack, no es backtracking
        critical_indicators = [
            analysis["has_recursive_exploration"],
            analysis["has_pruning"],
            analysis["has_backtrack_mechanism"]
        ]

        if not all(critical_indicators):
            # Penalizar severamente - máximo 20% de confianza
            confidence = min(confidence * 0.2, 0.2)

        reasoning = self._build_reasoning(analysis)

        return self._create_match(
            confidence=confidence,
            indicators_found=indicators_found,
            indicators_missing=indicators_missing,
            reasoning=reasoning,
            **analysis
        )

    def _analyze_structure(self, ast: ASTNode) -> Dict[str, Any]:
        """Analiza estructura de backtracking"""
        algo_name = get_algorithm_name(ast)

        analysis = {
            "algorithm_name": algo_name,
            "has_recursive_exploration": False,
            "has_pruning": False,
            "has_validation": False,
            "has_backtrack_mechanism": False,
            "recursive_calls": 0,
            "conditionals": 0
        }

        # Verificar recursión
        if algo_name:
            result = PatternMatcher.has_backtracking_pattern(ast, algo_name)
            analysis["has_recursive_exploration"] = result.matched
            analysis["recursive_calls"] = result.metadata.get("recursive_calls", 0)
            analysis["conditionals"] = result.metadata.get("conditionals", 0)

        # Backtracking típicamente tiene múltiples llamadas recursivas y condiciones
        analysis["has_pruning"] = analysis["conditionals"] > 0
        analysis["has_validation"] = analysis["conditionals"] > 0
        analysis["has_backtrack_mechanism"] = analysis["recursive_calls"] >= 2

        return analysis

    def _build_reasoning(self, analysis: Dict[str, Any]) -> str:
        """Construye razonamiento"""
        if analysis["recursive_calls"] < 2:
            return "No se detectó patrón de backtracking (requiere recursión múltiple)."

        return (
            f"El algoritmo usa Backtracking con {analysis['recursive_calls']} "
            f"llamadas recursivas y {analysis['conditionals']} condiciones de poda. "
            f"Esto sugiere exploración exhaustiva con retroceso."
        )