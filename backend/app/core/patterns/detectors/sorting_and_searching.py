"""
Sorting and Searching Detectors
Detectores para algoritmos de ordenamiento y búsqueda
"""

from typing import Dict, Any
from app.core.parser.ast_nodes import ASTNode, AlgorithmNode, AssignmentNode
from app.core.patterns.base_pattern import (
    BasePatternDetector, PatternType, PatternIndicator, PatternMatch
)
from app.core.patterns.pattern_matcher import PatternMatcher, get_node_children

class SortingDetector(BasePatternDetector):
    """Detector de algoritmos de ordenamiento"""

    def __init__(self):
        super().__init__()
        self.pattern_type = PatternType.SORTING
        self.pattern_name = "Ordenamiento"
        self.description = "Algoritmo de ordenamiento"
        self.typical_complexity = "O(n²) a O(n log n)"

        self._indicators = [
            PatternIndicator("swap_operations", "Operaciones de intercambio", False, 4.0),
            PatternIndicator("comparison_loop", "Loop de comparación", False, 3.5),
            PatternIndicator("array_reordering", "Reordenamiento de array", False, 3.0)
        ]

    def detect(self, ast: ASTNode) -> PatternMatch:
        """Detecta ordenamiento"""
        analysis = self._analyze_structure(ast)

        indicators_found = []
        indicators_missing = []

        swap_ind = self._indicators[0]
        if analysis["has_swaps"]:
            swap_ind.found = True
            swap_ind.evidence = f"{analysis['swap_count']} intercambios detectados"
            indicators_found.append(swap_ind)
        else:
            indicators_missing.append(swap_ind)

        comp_ind = self._indicators[1]
        if analysis["has_comparison_loops"]:
            comp_ind.found = True
            comp_ind.evidence = "Loops con comparaciones"
            indicators_found.append(comp_ind)
        else:
            indicators_missing.append(comp_ind)

        reorder_ind = self._indicators[2]
        if analysis["has_array_modification"]:
            reorder_ind.found = True
            reorder_ind.evidence = "Modificación de arrays detectada"
            indicators_found.append(reorder_ind)
        else:
            indicators_missing.append(reorder_ind)

        confidence = self._calculate_confidence(indicators_found, indicators_missing)
        reasoning = self._build_reasoning(analysis)

        return self._create_match(
            confidence=confidence,
            indicators_found=indicators_found,
            indicators_missing=indicators_missing,
            reasoning=reasoning
        )

    def _analyze_structure(self, ast: ASTNode) -> Dict[str, Any]:
        """Analiza estructura de ordenamiento"""
        analysis = {
            "has_swaps": False,
            "swap_count": 0,
            "has_comparison_loops": False,
            "has_array_modification": False
        }

        # Detectar intercambios (patrón temp = a; a = b; b = temp)
        swap_count = self._count_swaps(ast)
        analysis["has_swaps"] = swap_count > 0
        analysis["swap_count"] = swap_count

        # Detectar loops con comparaciones
        result = PatternMatcher.has_greedy_choice(ast)
        analysis["has_comparison_loops"] = result.matched

        # Detectar modificación de arrays
        table_result = PatternMatcher.has_array_table(ast)
        analysis["has_array_modification"] = table_result.matched

        return analysis

    def _count_swaps(self, node: ASTNode) -> int:
        """Cuenta operaciones de swap"""
        # Buscar patrón de 3 asignaciones consecutivas (swap típico)
        # Simplificado: contar asignaciones a arrays
        from app.core.parser.ast_nodes import ArrayAccessNode

        count = 0
        def _traverse(n: ASTNode):
            nonlocal count
            if isinstance(n, AssignmentNode):
                if isinstance(n.target, ArrayAccessNode):
                    count += 1
            for child in get_node_children(n):
                _traverse(child)

        _traverse(node)
        return count // 3  # Asumimos 3 asignaciones por swap

    def _build_reasoning(self, analysis: Dict[str, Any]) -> str:
        """Construye razonamiento"""
        if not analysis["has_swaps"]:
            return "No se detectó patrón claro de ordenamiento."

        return (
            f"El algoritmo presenta características de ordenamiento: "
            f"{analysis['swap_count']} intercambios, "
            f"loops con comparaciones y modificación de arrays."
        )

class SearchingDetector(BasePatternDetector):
    """Detector de algoritmos de búsqueda"""

    def __init__(self):
        super().__init__()
        self.pattern_type = PatternType.SEARCHING
        self.pattern_name = "Búsqueda"
        self.description = "Algoritmo de búsqueda"
        self.typical_complexity = "O(log n) a O(n)"

        self._indicators = [
            PatternIndicator("search_condition", "Condición de búsqueda", False, 4.0),
            PatternIndicator("element_comparison", "Comparación de elementos", False, 3.5),
            PatternIndicator("early_return", "Retorno anticipado", False, 3.0)
        ]

    def detect(self, ast: ASTNode) -> PatternMatch:
        """Detecta búsqueda"""
        analysis = self._analyze_structure(ast)

        indicators_found = []
        indicators_missing = []

        for ind in self._indicators:
            if analysis.get("has_search_pattern"):
                ind.found = True
                indicators_found.append(ind)
            else:
                indicators_missing.append(ind)

        confidence = self._calculate_confidence(indicators_found, indicators_missing)
        reasoning = "Patrón de búsqueda con comparaciones y posible retorno anticipado"

        return self._create_match(
            confidence=confidence,
            indicators_found=indicators_found,
            indicators_missing=indicators_missing,
            reasoning=reasoning
        )

    def _analyze_structure(self, ast: ASTNode) -> Dict[str, Any]:
        """Analiza estructura de búsqueda"""
        from app.core.parser.ast_nodes import IfStatementNode, ReturnStatementNode

        # Buscar if con return (patrón de búsqueda exitosa)
        has_search = False

        def _traverse(node: ASTNode):
            nonlocal has_search
            if isinstance(node, IfStatementNode):
                for child in get_node_children(node.then_block):
                    if isinstance(child, ReturnStatementNode):
                        has_search = True
                        return
            for child in get_node_children(node):
                _traverse(child)

        _traverse(ast)

        return {"has_search_pattern": has_search}