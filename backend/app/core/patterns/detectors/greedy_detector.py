"""
Greedy Detector - Detecta algoritmos voraces (Greedy)

Identifica algoritmos que hacen elecciones localmente óptimas
en cada paso sin retroceder.
"""

import ast
from typing import Dict, Any

from app.core.parser.ast_nodes import (
    ASTNode, AlgorithmNode, ForLoopNode, WhileLoopNode,
    AssignmentNode, BlockNode, CallStatementNode
)
from app.core.patterns.base_pattern import (
    BasePatternDetector,
    PatternType,
    PatternIndicator,
    PatternMatch
)
from app.core.patterns.pattern_matcher import PatternMatcher, get_algorithm_name, get_node_children

class GreedyDetector(BasePatternDetector):
    """Detector de algoritmos Greedy"""

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
                weight=0.80
            ),
            PatternIndicator(
                name="iterative_approach",
                description="Enfoque iterativo (no recursivo)",
                found=False,
                weight=0.60
            ),
            PatternIndicator(
                name="no_backtracking",
                description="Sin retroceso en decisiones",
                found=False,
                weight=0.50
            ),
            PatternIndicator(
                name="selection_pattern",
                description="Patrón de selección/comparación",
                found=False,
                weight=0.40
            )
        ]

    def detect(self, ast: ASTNode) -> PatternMatch:
        """Detecta Greedy con penalización para backtracking"""
        algo_name = get_algorithm_name(ast)
        analysis = self._analyze_structure(ast)

        indicators_found = []
        indicators_missing = []

        # 1. Optimización local
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
        
        # PENALIZACIONES CRÍTICAS
        
        # 1. Si NO tiene optimización local, NO es greedy
        if not analysis["has_local_optimization"]:
            confidence = confidence * 0.20  # Penalización 80%
        
        # 2. Si hay reversión de estado, NO es greedy (es backtracking)
        if self._has_state_reversal(ast):
            confidence = confidence * 0.05  # Penalización 95%
        
        # 3. Si hay recursión dentro de loops, probablemente backtracking
        if algo_name and self._has_recursion_in_loops(ast, algo_name):
            confidence = confidence * 0.10  # Penalización 90%
        
        # 4. GENÉRICO: Si tiene división de espacio, NO es Greedy
        if self._has_space_division_pattern(ast):
            confidence = confidence * 0.05  # Penalización 95%
        
        reasoning = self._build_reasoning(analysis, indicators_found)
        
        return self._create_match(
            confidence=confidence,
            indicators_found=indicators_found,
            indicators_missing=indicators_missing,
            reasoning=reasoning,
            **analysis
        )

    def _analyze_structure(self, ast: ASTNode) -> Dict[str, Any]:
        """Analiza estructura"""
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

        analysis["loops"] = PatternMatcher._count_nodes_of_type(
            ast, (ForLoopNode, WhileLoopNode)
        )

        recursive_calls = 0
        if algo_name:
            result = PatternMatcher.has_recursive_calls(ast, algo_name)
            recursive_calls = result.metadata.get("call_count", 0)

        analysis["is_iterative"] = analysis["loops"] > 0 and recursive_calls <= 1

        result = PatternMatcher.has_greedy_choice(ast)
        analysis["has_local_optimization"] = result.matched
        analysis["optimization_evidence"] = result.evidence
        analysis["comparisons"] = result.metadata.get("comparisons", 0)

        analysis["has_selection_pattern"] = analysis["comparisons"] > 0

        if recursive_calls >= 2:
            analysis["no_backtracking"] = False

        return analysis

    def _has_state_reversal(self, ast: ASTNode) -> bool:
        """
        Detecta reversión de estado (patrón backtracking).
        
        Greedy NUNCA retrocede, backtracking SÍ.
        Busca: assign → ... → assign al mismo lugar
        """
        def _search_in_block(block: BlockNode) -> bool:
            if not isinstance(block, BlockNode):
                return False
            
            statements = block.statements
            seen_targets = set()
            
            for stmt in statements:
                if isinstance(stmt, AssignmentNode):
                    target = self._get_target_name(stmt)
                    if target:
                        if target in seen_targets:
                            # Ya se asignó a este target antes = reversión
                            return True
                        seen_targets.add(target)
            
            return False
        
        # Buscar en todos los bloques
        def _traverse(node):
            if isinstance(node, BlockNode):
                if _search_in_block(node):
                    return True
            
            for child in get_node_children(node):
                if _traverse(child):
                    return True
            return False
        
        return _traverse(ast)

    def _get_target_name(self, assign: AssignmentNode) -> str:
        """Obtiene nombre del target de asignación"""
        if hasattr(assign.target, 'name'):
            return assign.target.name
        return None

    def _has_recursion_in_loops(self, ast: ASTNode, func_name: str) -> bool:
        """
        Detecta recursión dentro de loops (típico backtracking).
        
        Greedy típicamente NO tiene recursión en loops.
        """
        def _has_recursive_call(node: ASTNode) -> bool:
            if isinstance(node, CallStatementNode):
                if node.function_name == func_name:
                    return True
            
            for child in get_node_children(node):
                if _has_recursive_call(child):
                    return True
            return False
        
        def _search_loops(node: ASTNode) -> bool:
            if isinstance(node, (ForLoopNode, WhileLoopNode)):
                if _has_recursive_call(node.body):
                    return True
            
            for child in get_node_children(node):
                if _search_loops(child):
                    return True
            return False
        
        return _search_loops(ast)

    def _build_reasoning(self, analysis: Dict[str, Any], indicators: list) -> str:
        """Construye razonamiento"""
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
            f"Construye solución mediante elecciones óptimas locales."
        )
    
    def _has_space_division_pattern(self, ast: ASTNode) -> bool:
        """
        Detecta patrón genérico de DIVISIÓN DE ESPACIO DE BÚSQUEDA.

        Características:
        - Variables que representan rangos (low/high, inicio/fin, left/right)
        - Cálculo de punto medio (mid, medio, center)
        - Actualización de rangos basada en comparaciones

        Este patrón es común en:
        - Binary Search
        - Ternary Search
        - Interpolation Search
        - Exponential Search

        NO ES GREEDY porque:
        - Greedy hace elección óptima LOCAL sin considerar todo el espacio
        - División de espacio REDUCE sistemáticamente el espacio completo
        """
        from app.core.parser.ast_nodes import AssignmentNode, BinaryOpNode

        # Palabras clave genéricas para variables de rango
        range_keywords = {
            'low', 'high', 'left', 'right', 'inicio', 'fin',
            'start', 'end', 'begin', 'limite', 'bound'
        }

        # Palabras clave para punto medio
        midpoint_keywords = {
            'mid', 'medio', 'center', 'centro', 'pivot', 'middle'
        }

        has_range_vars = False
        has_midpoint_calculation = False
        has_range_update = False

        def _search(node: ASTNode):
            nonlocal has_range_vars, has_midpoint_calculation, has_range_update

            if isinstance(node, AssignmentNode):
                if hasattr(node.target, 'name'):
                    var_name = node.target.name.lower()

                    # Detectar variables de rango
                    if any(kw in var_name for kw in range_keywords):
                        has_range_vars = True

                    # Detectar cálculo de punto medio
                    if any(kw in var_name for kw in midpoint_keywords):
                        if isinstance(node.value, BinaryOpNode):
                            # mid = (a + b) / 2 o mid = (a + b) // 2
                            if node.value.operator in ['/', 'div', '//', 'DIV']:
                                has_midpoint_calculation = True

                    # Detectar actualización de rangos
                    if any(kw in var_name for kw in range_keywords):
                        if isinstance(node.value, BinaryOpNode):
                            # low = mid + 1 o high = mid - 1
                            if node.value.operator in ['+', '-']:
                                has_range_update = True

            for child in get_node_children(node):
                _search(child)

        _search(ast)

        # Requiere los 3 componentes para ser considerado división de espacio
        return has_range_vars and has_midpoint_calculation and has_range_update