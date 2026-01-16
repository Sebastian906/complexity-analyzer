"""
Sorting and Searching Detectors
Detectores para algoritmos de ordenamiento y búsqueda
"""

from typing import Dict, Any
from app.core.parser.ast_nodes import ASTNode, AlgorithmNode, AssignmentNode, BinaryOpNode
from app.core.patterns.base_pattern import (
    BasePatternDetector, PatternType, PatternIndicator, PatternMatch
)
from app.core.patterns.pattern_matcher import PatternMatcher, get_node_children, get_algorithm_name

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

        swap_count = self._count_swaps(ast)
        analysis["has_swaps"] = swap_count > 0
        analysis["swap_count"] = swap_count

        result = PatternMatcher.has_greedy_choice(ast)
        analysis["has_comparison_loops"] = result.matched

        table_result = PatternMatcher.has_array_table(ast)
        analysis["has_array_modification"] = table_result.matched

        return analysis

    def _count_swaps(self, node: ASTNode) -> int:
        """Cuenta operaciones de swap"""
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
        return count // 3

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
            PatternIndicator(
                "search_structure", 
                "Estructura de búsqueda clara", 
                False, 
                4.0
            ),
            PatternIndicator(
                "target_comparison", 
                "Comparación con valor objetivo", 
                False, 
                3.5
            ),
            PatternIndicator(
                "early_return", 
                "Retorno anticipado al encontrar", 
                False, 
                3.0
            ),
        ]

    def detect(self, ast: ASTNode) -> PatternMatch:
        """Detecta búsqueda con criterios ESTRICTOS"""
        analysis = self._analyze_structure(ast)

        indicators_found = []
        indicators_missing = []

        search_struct = self._indicators[0]
        if analysis.get("has_search_structure"):
            search_struct.found = True
            search_struct.evidence = "Estructura de búsqueda detectada"
            indicators_found.append(search_struct)
        else:
            indicators_missing.append(search_struct)

        target_comp = self._indicators[1]
        if analysis.get("has_target_comparison"):
            target_comp.found = True
            target_comp.evidence = "Comparación con objetivo"
            indicators_found.append(target_comp)
        else:
            indicators_missing.append(target_comp)

        early_ret = self._indicators[2]
        if analysis.get("has_early_return"):
            early_ret.found = True
            early_ret.evidence = "Return anticipado"
            indicators_found.append(early_ret)
        else:
            indicators_missing.append(early_ret)

        confidence = self._calculate_confidence(indicators_found, indicators_missing)

        # PENALIZACIONES CRÍTICAS 

        # Si tiene recursión múltiple, NO es búsqueda simple
        if analysis.get("recursive_calls", 0) >= 2:
            confidence = confidence * 0.05  # PENALIZACIÓN MÁS AGRESIVA: 95%

        # Si tiene loops sobre candidatos con recursión
        if analysis.get("has_candidate_loop"):
            confidence = confidence * 0.10  # PENALIZACIÓN 90%

        # Si NO tiene comparación con objetivo, NO puede ser búsqueda
        if not analysis.get("has_target_comparison"):
            confidence = confidence * 0.15  # PENALIZACIÓN 85%

        # NUEVA: Si solo compara con literales (n <= 1), NO es búsqueda
        if analysis.get("has_early_return") and not analysis.get("has_target_comparison"):
            confidence = confidence * 0.10

        reasoning = self._build_reasoning(analysis)

        return self._create_match(
            confidence=confidence,
            indicators_found=indicators_found,
            indicators_missing=indicators_missing,
            reasoning=reasoning
        )

    def _analyze_structure(self, ast: ASTNode) -> Dict[str, Any]:
        """Analiza estructura de ordenamiento"""
        from app.core.parser.ast_nodes import (
            IfStatementNode, ReturnStatementNode, 
            BinaryOpNode, ForLoopNode, WhileLoopNode
        )

        algo_name = get_algorithm_name(ast)

        analysis = {
            "has_search_structure": False,
            "has_target_comparison": False,
            "has_early_return": False,
            "recursive_calls": 0,
            "has_candidate_loop": False,
        }

        # Contar llamadas recursivas
        if algo_name:
            result = PatternMatcher.has_recursive_calls(ast, algo_name)
            analysis["recursive_calls"] = result.metadata.get("call_count", 0)

        # NUEVA REGLA: Si tiene 2+ llamadas recursivas, NO es búsqueda
        if analysis["recursive_calls"] >= 2:
            return analysis  # Retornar temprano

        # Detectar loops con recursión
        loops = PatternMatcher._count_nodes_of_type(ast, (ForLoopNode, WhileLoopNode))
        analysis["has_candidate_loop"] = loops > 0 and analysis["recursive_calls"] > 0

        # Buscar estructura de búsqueda
        has_comparison = False
        has_early_return = False
        has_target_variable = False  # NUEVO

        def _traverse(node: ASTNode):
            nonlocal has_comparison, has_early_return, has_target_variable

            if isinstance(node, IfStatementNode):
                if isinstance(node.condition, BinaryOpNode):
                    if node.condition.operator in ['=', '==', '<', '>', '<=', '>=']:
                        has_comparison = True

                        # NUEVO: Verificar si compara con parámetro (target)
                        # Fibonacci compara 'n <= 1', búsqueda compara 'A[mid] = x'
                        if self._is_target_comparison(node.condition):
                            has_target_variable = True

                for child in get_node_children(node.then_block):
                    if isinstance(child, ReturnStatementNode):
                        has_early_return = True

            for child in get_node_children(node):
                _traverse(child)

        _traverse(ast)

        # Solo es búsqueda si:
        # 1. Tiene comparación + return anticipado
        # 2. NO tiene recursión múltiple (>= 2)
        # 3. NO tiene loops de exploración con recursión
        # 4. NUEVO: Tiene comparación con variable objetivo
        analysis["has_search_structure"] = (
            has_comparison and 
            has_early_return and
            not (analysis["recursive_calls"] >= 2) and
            not (analysis["has_candidate_loop"]) and
            has_target_variable  # NUEVO
        )
        analysis["has_target_comparison"] = has_target_variable  # CAMBIO
        analysis["has_early_return"] = has_early_return

        return analysis

    def _is_target_comparison(self, condition: BinaryOpNode) -> bool:
        """
        NUEVO: Verifica si es comparación con variable objetivo.

        Búsqueda real: A[mid] = x  (compara con parámetro)
        Fibonacci: n <= 1  (compara con literal)
        """
        from app.core.parser.ast_nodes import (
            ArrayAccessNode, VariableNode, LiteralNode, LValueNode
        )

        # Verificar si uno de los lados es array access o variable
        # y el otro es un parámetro (no literal)
        left = condition.left
        right = condition.right

        # Si ambos lados son literales, NO es búsqueda de target
        if isinstance(left, LiteralNode) and isinstance(right, LiteralNode):
            return False

        # Si uno es literal y el otro es variable simple (n <= 1), NO es búsqueda
        if isinstance(left, VariableNode) and isinstance(right, LiteralNode):
            return False
        if isinstance(right, VariableNode) and isinstance(left, LiteralNode):
            return False

        # Si hay array access, probablemente es búsqueda
        if isinstance(left, ArrayAccessNode) or isinstance(right, ArrayAccessNode):
            return True

        # Si hay dos variables (x = y), podría ser búsqueda
        if isinstance(left, VariableNode) and isinstance(right, VariableNode):
            return True

        return False

    def _build_reasoning(self, analysis: Dict[str, Any]) -> str:
        """Razonamiento mejorado"""
        if analysis["recursive_calls"] >= 2:
            return (
                "Tiene recursión múltiple, NO es un algoritmo de búsqueda simple. "
                "Es más probable que sea un algoritmo recursivo de árbol (como Fibonacci)."
            )
        
        if analysis["has_candidate_loop"]:
            return "Tiene loops de exploración con recursión, típico de backtracking, no búsqueda."
        
        if not analysis["has_target_comparison"]:
            return (
                "No se detectó comparación con valor objetivo (target). "
                "Búsqueda requiere comparar elementos con un valor buscado. "
                "Esto parece ser un algoritmo recursivo diferente."
            )
        
        if not analysis["has_search_structure"]:
            return "No se detectó estructura clara de búsqueda."
        
        return "Algoritmo de búsqueda con comparaciones y return anticipado."