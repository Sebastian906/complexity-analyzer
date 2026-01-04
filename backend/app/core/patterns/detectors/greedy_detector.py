"""
Greedy Detector - Detecta algoritmos voraces (Greedy)

Identifica algoritmos que hacen elecciones localmente óptimas
en cada paso sin retroceder.
"""

from typing import Dict, Any

from app.core.parser.ast_nodes import ASTNode, AlgorithmNode, ForLoopNode, WhileLoopNode
from app.core.patterns.base_pattern import (
    BasePatternDetector,
    PatternType,
    PatternIndicator,
    PatternMatch
)
from app.core.patterns.pattern_matcher import PatternMatcher, get_algorithm_name

class GreedyDetector(BasePatternDetector):
    """
    Detector de algoritmos Greedy.

    Características:
    - Elecciones localmente óptimas
    - Iterativo (sin backtracking)
    - Selección en cada paso
    - Típicamente O(n log n)
    """

    def __init__(self):
        super().__init__()
        self.pattern_type = PatternType.GREEDY
        self.pattern_name = "Algoritmo Voraz (Greedy)"
        self.description = "Elecciones localmente óptimas sin retroceso"
        self.typical_complexity = "O(n log n)"

        self._indicators = [
            PatternIndicator(
                name="local_optimization",
                description="Selección de mejor opción local",
                found=False,
                weight=4.0
            ),
            PatternIndicator(
                name="iterative_approach",
                description="Enfoque iterativo (no recursivo)",
                found=False,
                weight=3.0
            ),
            PatternIndicator(
                name="no_backtracking",
                description="Sin retroceso en decisiones",
                found=False,
                weight=2.5
            ),
            PatternIndicator(
                name="selection_pattern",
                description="Patrón de selección/comparación",
                found=False,
                weight=2.0
            )
        ]

    def detect(self, ast: ASTNode) -> PatternMatch:
        """Detecta si el algoritmo usa enfoque Greedy"""
        analysis = self._analyze_structure(ast)

        indicators_found = []
        indicators_missing = []

        # 1. Optimización local (INDICADOR CRÍTICO para Greedy)
        local_opt = self._indicators[0]
        if analysis["has_local_optimization"]:
            local_opt.found = True
            local_opt.evidence = analysis["optimization_evidence"]
            indicators_found.append(local_opt)
        else:
            indicators_missing.append(local_opt)

        # 2. Enfoque iterativo
        iterative = self._indicators[1]
        if analysis["is_iterative"]:
            iterative.found = True
            iterative.evidence = f"{analysis['loops']} loop(s) sin recursión profunda"
            indicators_found.append(iterative)
        else:
            indicators_missing.append(iterative)

        # 3. Sin backtracking
        no_backtrack = self._indicators[2]
        if analysis["no_backtracking"]:
            no_backtrack.found = True
            no_backtrack.evidence = "No se detectó patrón de backtracking"
            indicators_found.append(no_backtrack)
        else:
            indicators_missing.append(no_backtrack)

        # 4. Patrón de selección
        selection = self._indicators[3]
        if analysis["has_selection_pattern"]:
            selection.found = True
            selection.evidence = f"{analysis['comparisons']} comparaciones detectadas"
            indicators_found.append(selection)
        else:
            indicators_missing.append(selection)

        confidence = self._calculate_confidence(indicators_found, indicators_missing)
        
        # AJUSTE CRÍTICO: Sin optimización local, no es un algoritmo Greedy verdadero
        # Los otros indicadores (iterativo, sin backtracking, comparaciones) son genéricos
        # y aplican a muchos otros patrones (Fuerza Bruta, ordenamiento simple, etc.)
        if not analysis["has_local_optimization"]:
            # Sin el indicador principal, penalizar severamente
            confidence = confidence * 0.3  # Reducir a máximo ~30% de la confianza original
        
        reasoning = self._build_reasoning(analysis, indicators_found)

        return self._create_match(
            confidence=confidence,
            indicators_found=indicators_found,
            indicators_missing=indicators_missing,
            reasoning=reasoning,
            **analysis
        )

    def _analyze_structure(self, ast: ASTNode) -> Dict[str, Any]:
        """Analiza la estructura del algoritmo"""
        algo_name = get_algorithm_name(ast)

        analysis = {
            "algorithm_name": algo_name,
            "has_local_optimization": False,
            "optimization_evidence": "",
            "is_iterative": False,
            "no_backtracking": True,
            "has_selection_pattern": False,
            "loops": 0,
            "comparisons": 0
        }

        # Contar loops
        analysis["loops"] = PatternMatcher._count_nodes_of_type(
            ast, (ForLoopNode, WhileLoopNode)
        )

        # Verificar si es iterativo (loops > 0, poca recursión)
        recursive_calls = 0
        if algo_name:
            result = PatternMatcher.has_recursive_calls(ast, algo_name)
            recursive_calls = result.metadata.get("call_count", 0)

        analysis["is_iterative"] = analysis["loops"] > 0 and recursive_calls <= 1

        # Detectar optimización local
        result = PatternMatcher.has_greedy_choice(ast)
        analysis["has_local_optimization"] = result.matched
        analysis["optimization_evidence"] = result.evidence
        analysis["comparisons"] = result.metadata.get("comparisons", 0)

        # Verificar selección
        analysis["has_selection_pattern"] = analysis["comparisons"] > 0

        # Verificar si hay backtracking
        if recursive_calls >= 2:
            analysis["no_backtracking"] = False

        return analysis

    def _build_reasoning(self, analysis: Dict[str, Any], indicators: list) -> str:
        """Construye explicación del razonamiento"""
        if not analysis["is_iterative"]:
            return "No se detectó enfoque iterativo, característico de algoritmos greedy."

        reasons = []

        if analysis["has_local_optimization"]:
            reasons.append("hace elecciones localmente óptimas")

        if analysis["loops"] > 0:
            reasons.append(f"usa {analysis['loops']} loop(s) iterativo(s)")

        if analysis["no_backtracking"]:
            reasons.append("sin retroceso en decisiones")

        if analysis["has_selection_pattern"]:
            reasons.append("con patrón de selección/comparación")

        if not reasons:
            return "Características de algoritmo greedy no claramente identificadas."

        return (
            f"El algoritmo usa enfoque Greedy: {', '.join(reasons)}. "
            f"Esto sugiere construcción incremental de solución mediante elecciones óptimas locales."
        )