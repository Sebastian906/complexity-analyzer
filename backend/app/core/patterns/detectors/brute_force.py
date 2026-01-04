"""
Brute Force Detector - Detecta algoritmos de fuerza bruta

Identifica algoritmos que exploran exhaustivamente todas las posibilidades
sin optimización.
"""

from typing import Dict, Any

from app.core.parser.ast_nodes import ASTNode, ForLoopNode, WhileLoopNode
from app.core.patterns.base_pattern import (
    BasePatternDetector,
    PatternType,
    PatternIndicator,
    PatternMatch
)
from app.core.patterns.pattern_matcher import PatternMatcher, get_algorithm_name

class BruteForceDetector(BasePatternDetector):
    """
    Detector de algoritmos de fuerza bruta.
    
    Características:
    - Exploración exhaustiva de todas las posibilidades
    - Múltiples loops anidados (típicamente 2+)
    - No hay optimización ni poda
    - Complejidad exponencial o factorial típica
    - Patrones de swap en algoritmos de ordenamiento
    """

    def __init__(self):
        super().__init__()
        self.pattern_type = PatternType.BRUTE_FORCE
        self.pattern_name = "Fuerza Bruta"
        self.description = "Exploración exhaustiva sin optimización"
        self.typical_complexity = "O(n²) a O(2^n)"

        self._indicators = [
            PatternIndicator(
                name="nested_loops",
                description="Múltiples loops anidados",
                found=False,
                weight=3.0
            ),
            PatternIndicator(
                name="no_pruning",
                description="Sin condiciones de poda",
                found=False,
                weight=2.0
            ),
            PatternIndicator(
                name="exhaustive_search",
                description="Búsqueda exhaustiva de soluciones",
                found=False,
                weight=2.5
            ),
            PatternIndicator(
                name="no_memoization",
                description="Sin memoización",
                found=False,
                weight=1.5
            ),
            PatternIndicator(
                name="swap_pattern",
                description="Patrón de intercambio (swap)",
                found=False,
                weight=2.5
            )
        ]

    def detect(self, ast: ASTNode) -> PatternMatch:
        """Detecta si el algoritmo usa fuerza bruta"""
        analysis = self._analyze_structure(ast)

        indicators_found = []
        indicators_missing = []

        # 1. Verificar loops anidados
        nested_loops = self._indicators[0]
        if analysis["max_loop_depth"] >= 2:
            nested_loops.found = True
            nested_loops.evidence = f"Profundidad de anidación: {analysis['max_loop_depth']}"
            indicators_found.append(nested_loops)
        else:
            indicators_missing.append(nested_loops)

        # 2. Verificar ausencia de poda (pocas condicionales en relación a loops)
        no_pruning = self._indicators[1]
        pruning_ratio = analysis["conditionals"] / max(analysis["loops"], 1)
        if pruning_ratio < 0.5:  # Pocas condiciones = poca poda
            no_pruning.found = True
            no_pruning.evidence = f"Ratio poda: {pruning_ratio:.2f}"
            indicators_found.append(no_pruning)
        else:
            indicators_missing.append(no_pruning)

        # 3. Verificar búsqueda exhaustiva (muchos loops)
        exhaustive = self._indicators[2]
        if analysis["loops"] >= 2:
            exhaustive.found = True
            exhaustive.evidence = f"{analysis['loops']} loops encontrados"
            indicators_found.append(exhaustive)
        else:
            indicators_missing.append(exhaustive)

        # 4. Verificar ausencia de memoización
        no_memo = self._indicators[3]
        if not analysis["has_memoization"]:
            no_memo.found = True
            no_memo.evidence = "No se detectó memoización"
            indicators_found.append(no_memo)
        else:
            indicators_missing.append(no_memo)
        
        # 5. Verificar patrón de swap (típico de ordenamiento por fuerza bruta)
        swap_pattern = self._indicators[4]
        if analysis["has_swap_pattern"]:
            swap_pattern.found = True
            swap_pattern.evidence = "Patrón de intercambio detectado (temp := A[i]; A[i] := A[j]; A[j] := temp)"
            indicators_found.append(swap_pattern)
        else:
            indicators_missing.append(swap_pattern)

        # Calcular confianza
        confidence = self._calculate_confidence(indicators_found, indicators_missing)

        # Reasoning
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
        from app.core.parser.ast_nodes import IfStatementNode, AlgorithmNode

        # Obtener nombre del algoritmo usando helper
        algo_name = get_algorithm_name(ast)

        analysis = {
            "loops": 0,
            "max_loop_depth": 0,
            "conditionals": 0,
            "has_memoization": False,
            "has_swap_pattern": False,
            "algorithm_name": algo_name
        }

        # Contar loops
        result = PatternMatcher.has_nested_loops(ast, min_depth=1)
        analysis["max_loop_depth"] = result.metadata.get("max_depth", 0)
        analysis["loops"] = self._count_all_loops(ast)

        # Contar condicionales
        analysis["conditionals"] = PatternMatcher._count_nodes_of_type(
            ast, (IfStatementNode,)
        )

        # Verificar memoización
        analysis["has_memoization"] = self._has_memoization(ast)
        
        # Verificar patrón de swap (típico de ordenamiento por fuerza bruta)
        analysis["has_swap_pattern"] = PatternMatcher._has_swap_pattern(ast)

        return analysis

    def _count_all_loops(self, node: ASTNode) -> int:
        """Cuenta todos los loops (no solo anidados)"""
        from app.core.parser.ast_nodes import RepeatLoopNode

        return PatternMatcher._count_nodes_of_type(
            node,
            (ForLoopNode, WhileLoopNode, RepeatLoopNode)
        )

    def _build_reasoning(
        self,
        analysis: Dict[str, Any],
        indicators: list
    ) -> str:
        """Construye explicación del razonamiento"""
        reasons = []

        if analysis["max_loop_depth"] >= 2:
            reasons.append(
                f"loops anidados con profundidad {analysis['max_loop_depth']}"
            )

        if analysis["loops"] >= 2:
            reasons.append(f"múltiples loops ({analysis['loops']} total)")

        if not analysis["has_memoization"]:
            reasons.append("sin optimización via memoización")
        
        if analysis["has_swap_pattern"]:
            reasons.append("patrón de intercambio (swap) típico de ordenamiento")

        if len(reasons) == 0:
            return "No se detectaron características claras de fuerza bruta"

        return (
            f"El algoritmo presenta características de fuerza bruta: "
            f"{', '.join(reasons)}. "
            f"Esto sugiere exploración exhaustiva sin optimización."
        )