"""
Dynamic Programming Detector - Detecta algoritmos de Programación Dinámica

Identifica algoritmos que usan DP mediante memoización o tabulación
para resolver problemas con subestructura óptima y subproblemas solapados.
"""

from typing import Dict, Any

from app.core.parser.ast_nodes import ASTNode, AlgorithmNode
from app.core.patterns.base_pattern import (
    BasePatternDetector,
    PatternType,
    PatternIndicator,
    PatternMatch
)
from app.core.patterns.pattern_matcher import PatternMatcher, get_node_children, get_algorithm_name

class DynamicProgrammingDetector(BasePatternDetector):
    """
    Detector de algoritmos de Programación Dinámica.

    Características:
    - Memoización o tabla para almacenar resultados
    - Subproblemas solapados
    - Subestructura óptima
    - Típicamente O(n²) o O(n*m)
    """

    def __init__(self):
        super().__init__()
        self.pattern_type = PatternType.DYNAMIC_PROGRAMMING
        self.pattern_name = "Programación Dinámica"
        self.description = "Optimización mediante memoización o tabulación"
        self.typical_complexity = "O(n²) o O(n*m)"

        self._indicators = [
            PatternIndicator(
                name="memoization_table",
                description="Array/tabla para almacenar resultados",
                found=False,
                weight=0.80
            ),
            PatternIndicator(
                name="table_filling",
                description="Llenado sistemático de tabla",
                found=False,
                weight=0.70
            ),
            PatternIndicator(
                name="overlapping_subproblems",
                description="Reutilización de soluciones anteriores",
                found=False,
                weight=0.60
            ),
            PatternIndicator(
                name="optimal_substructure",
                description="Construcción de solución óptima desde subsoluciones",
                found=False,
                weight=0.50
            ),
            PatternIndicator(
                name="bottom_up",
                description="Enfoque bottom-up (iterativo)",
                found=False,
                weight=0.40
            )
        ]

    def detect(self, ast: ASTNode) -> PatternMatch:
        """Detecta si el algoritmo usa Programación Dinámica"""
        analysis = self._analyze_structure(ast)

        indicators_found = []
        indicators_missing = []

        # 1. Memoización / tabla
        memo_table = self._indicators[0]
        if analysis["has_memoization_table"]:
            memo_table.found = True
            memo_table.evidence = f"Arrays detectados: {', '.join(analysis['memo_arrays'])}"
            indicators_found.append(memo_table)
        else:
            indicators_missing.append(memo_table)

        # 2. Llenado de tabla
        table_filling = self._indicators[1]
        if analysis["has_table_filling"]:
            table_filling.found = True
            table_filling.evidence = "Patrón de llenado sistemático detectado"
            indicators_found.append(table_filling)
        else:
            indicators_missing.append(table_filling)

        # 3. Subproblemas solapados
        overlapping = self._indicators[2]
        if analysis["has_overlapping_subproblems"]:
            overlapping.found = True
            overlapping.evidence = "Accesos múltiples a mismos índices"
            indicators_found.append(overlapping)
        else:
            indicators_missing.append(overlapping)

        # 4. Subestructura óptima
        optimal = self._indicators[3]
        if analysis["has_optimal_substructure"]:
            optimal.found = True
            optimal.evidence = "Combinación de soluciones parciales"
            indicators_found.append(optimal)
        else:
            indicators_missing.append(optimal)

        # 5. Bottom-up
        bottom_up = self._indicators[4]
        if analysis["is_bottom_up"]:
            bottom_up.found = True
            bottom_up.evidence = "Enfoque iterativo (bottom-up)"
            indicators_found.append(bottom_up)
        else:
            indicators_missing.append(bottom_up)

        # Calcular confianza
        confidence = self._calculate_confidence(indicators_found, indicators_missing)

        # PENALIZACIÓN si parece swap en lugar de DP
        if analysis["has_memoization_table"] and not analysis.get("has_overlapping_subproblems"):
            # Array usado pero sin reutilización clara = probablemente NO es DP
            confidence = confidence * 0.3  # Penalización 70%

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
        from app.core.parser.ast_nodes import (
            ForLoopNode,
            WhileLoopNode,
            AssignmentNode,
            ArrayAccessNode,
            IfStatementNode
        )

        # Obtener nombre del algoritmo usando helper
        algo_name = get_algorithm_name(ast)

        analysis = {
            "algorithm_name": algo_name,
            "has_memoization_table": False,
            "memo_arrays": [],
            "has_table_filling": False,
            "has_overlapping_subproblems": False,
            "has_optimal_substructure": False,
            "is_bottom_up": False,
            "dp_approach": "none"
        }

        # Detectar memoización / tabla
        table_info = PatternMatcher.has_array_table(ast)
        analysis["has_memoization_table"] = table_info.matched
        if table_info.matched:
            analysis["memo_arrays"] = table_info.metadata.get("tables", [])

        # Detectar llenado de tabla
        analysis["has_table_filling"] = self._detect_table_filling(ast)

        # Detectar subproblemas solapados
        analysis["has_overlapping_subproblems"] = self._detect_overlapping_subproblems(ast)

        # Detectar subestructura óptima
        analysis["has_optimal_substructure"] = self._detect_optimal_substructure(ast)

        # Determinar si es bottom-up o top-down
        loops = PatternMatcher._count_nodes_of_type(ast, (ForLoopNode, WhileLoopNode))
        recursive_calls = 0
        if algo_name:
            result = PatternMatcher.has_recursive_calls(ast, algo_name)
            recursive_calls = result.metadata.get("call_count", 0)

        if loops > 0 and recursive_calls == 0:
            analysis["is_bottom_up"] = True
            analysis["dp_approach"] = "bottom_up"
        elif recursive_calls > 0 and analysis["has_memoization_table"]:
            analysis["dp_approach"] = "top_down"

        # Verificar que no sea solo modificación de array sin reutilización
        if analysis["has_memoization_table"]:
            # Verificar si hay LECTURA de valores previos del array
            # (no solo escritura como en bubble sort)
            has_reuse = self._has_subproblem_reuse(ast, analysis["memo_arrays"])

            if not has_reuse:
                # Es un array modificado pero no hay reutilización de subproblemas
                # Probablemente NO es DP
                analysis["has_memoization_table"] = False
                analysis["memo_arrays"] = []

        return analysis
    
    def _has_subproblem_reuse(self, ast: ASTNode, array_names: list) -> bool:
        """
        Verifica si hay reutilización REAL de subproblemas.

        DP verdadero: dp[i] = dp[i-1] + dp[i-2]  (LEE valores previos)
        NO DP: A[j] = A[j+1]  (solo swap, no reutiliza soluciones)
        """
        from app.core.parser.ast_nodes import AssignmentNode, ArrayAccessNode, BinaryOpNode

        reuse_count = 0

        def _search(node: ASTNode):
            nonlocal reuse_count

            if isinstance(node, AssignmentNode):
                # Verificar si el valor (right side) lee del mismo array
                target_name = None
                if hasattr(node.target, 'name'):
                    target_name = node.target.name

                if target_name in array_names:
                    # Verificar si el value referencia el mismo array
                    # Pero con un índice DIFERENTE (típico de DP)
                    if self._references_different_index(node.value, target_name, node.target):
                        reuse_count += 1

            for child in get_node_children(node):
                _search(child)

        _search(ast)

        # Si hay al menos 1 reutilización real, probablemente es DP
        return reuse_count >= 1

    def _references_different_index(self, expr: ASTNode, array_name: str, target) -> bool:
        """
        Verifica si la expresión referencia el array con un índice diferente.

        Ejemplo DP: dp[i] = dp[i-1] + dp[i-2]
        - target: dp[i]
        - expr: contiene dp[i-1] y dp[i-2] (índices diferentes)

        Ejemplo NO DP (swap): A[j] = A[j+1]
        - target: A[j]
        - expr: A[j+1] (índice diferente PERO es swap, no reutilización)
        """
        from app.core.parser.ast_nodes import BinaryOpNode, ArrayAccessNode

        # Contar referencias al array en la expresión
        references = []

        def _collect_refs(node: ASTNode):
            if isinstance(node, ArrayAccessNode):
                if node.array_name == array_name:
                    # Guardar índice
                    index_expr = str(node.indices[0]) if node.indices else ""
                    references.append(index_expr)

            for child in get_node_children(node):
                _collect_refs(child)

        _collect_refs(expr)

        # Si hay 2+ referencias (dp[i-1] + dp[i-2]), probablemente es DP
        # Si hay 1 referencia (A[j+1]), probablemente es swap
        return len(references) >= 2

    def _detect_table_filling(self, node: ASTNode) -> bool:
        """
        Detecta patrón de llenado sistemático de tabla.

        Busca loops que asignan valores a arrays de manera ordenada.
        Considera tanto ArrayAccessNode como LValueNode con índices.
        """
        from app.core.parser.ast_nodes import (
            ForLoopNode,
            AssignmentNode,
            ArrayAccessNode,
            BlockNode,
            LValueNode
        )

        def _search(n: ASTNode) -> bool:
            if isinstance(n, ForLoopNode):
                # Verificar si dentro del loop hay asignaciones a arrays
                if isinstance(n.body, BlockNode):
                    for child in get_node_children(n.body):
                        if isinstance(child, AssignmentNode):
                            # Verificar LValueNode con índices (dp[i] := ...)
                            if isinstance(child.target, LValueNode) and child.target.indices:
                                return True
                            # También verificar ArrayAccessNode
                            if isinstance(child.target, ArrayAccessNode):
                                return True

            for child in get_node_children(n):
                if _search(child):
                    return True

            return False

        return _search(node)

    def _detect_overlapping_subproblems(self, node: ASTNode) -> bool:
        """
        Detecta si hay subproblemas solapados.

        Busca:
        1. Condiciones que verifican si un resultado ya fue calculado
        2. Asignaciones a un array que referencian el mismo array
        """
        from app.core.parser.ast_nodes import (
            IfStatementNode,
            BinaryOpNode,
            ArrayAccessNode,
            AssignmentNode,
            LValueNode
        )

        # Método 1: Verificar condiciones con acceso a array (patrón memoización)
        def _check_memo_condition(n: ASTNode) -> bool:
            if isinstance(n, IfStatementNode):
                condition = n.condition
                if isinstance(condition, BinaryOpNode):
                    if self._has_array_access(condition):
                        return True

            for child in get_node_children(n):
                if _check_memo_condition(child):
                    return True
            return False

        # Método 2: Verificar si un array es asignado y también referenciado
        # Patrón: dp[i] := expresión_con_dp
        def _check_self_reference(n: ASTNode, array_names: set) -> bool:
            if isinstance(n, AssignmentNode):
                target_name = None
                if isinstance(n.target, LValueNode) and n.target.indices:
                    target_name = n.target.name
                elif isinstance(n.target, ArrayAccessNode):
                    target_name = n.target.array_name
                
                if target_name:
                    # Verificar si el valor referencia el mismo array
                    if self._expression_references_array(n.value, target_name):
                        return True
            
            for child in get_node_children(n):
                if _check_self_reference(child, array_names):
                    return True
            return False
        
        # Obtener arrays detectados
        table_info = PatternMatcher.has_array_table(node)
        array_names = set(table_info.metadata.get("tables", []))

        return _check_memo_condition(node) or _check_self_reference(node, array_names)
    
    def _expression_references_array(self, expr: ASTNode, array_name: str) -> bool:
        """
        Verifica si una expresión referencia un array específico.
        
        Busca tanto ArrayAccessNode como identificadores directos (debido a
        limitaciones del parser que a veces simplifica dp[i] a dp).
        """
        from app.core.parser.ast_nodes import ArrayAccessNode, VariableNode, BinaryOpNode
        
        if expr is None:
            return False
        
        # Caso 1: ArrayAccessNode directo
        if isinstance(expr, ArrayAccessNode):
            if expr.array_name == array_name:
                return True
        
        # Caso 2: El parser a veces simplifica dp[i] a solo el string "dp"
        if isinstance(expr, str) and expr == array_name:
            return True
        
        if isinstance(expr, VariableNode):
            if expr.name == array_name:
                return True
        
        # Caso 3: BinaryOpNode - verificar left y right
        if isinstance(expr, BinaryOpNode):
            left = getattr(expr, 'left', None)
            right = getattr(expr, 'right', None)
            
            # left/right pueden ser strings o nodos
            if isinstance(left, str) and left == array_name:
                return True
            if isinstance(right, str) and right == array_name:
                return True
            
            if self._expression_references_array(left, array_name):
                return True
            if self._expression_references_array(right, array_name):
                return True
        
        # Recursivo para otros hijos
        for child in get_node_children(expr):
            if self._expression_references_array(child, array_name):
                return True
        
        return False

    def _has_array_access(self, node: ASTNode) -> bool:
        """Verifica si un nodo contiene acceso a array"""
        from app.core.parser.ast_nodes import ArrayAccessNode

        if isinstance(node, ArrayAccessNode):
            return True

        for child in get_node_children(node):
            if self._has_array_access(child):
                return True

        return False

    def _detect_optimal_substructure(self, node: ASTNode) -> bool:
        """
        Detecta subestructura óptima.
        
        Busca:
        1. Asignaciones que usan min/max
        2. Asignaciones a un array que combinan valores del mismo array
        3. Patrones donde dp[i] = f(dp[...]) incluso si el parser simplifica
        """
        from app.core.parser.ast_nodes import (
            AssignmentNode,
            BinaryOpNode,
            ArrayAccessNode,
            FunctionCallNode,
            LValueNode
        )

        # Obtener arrays de tabla
        table_info = PatternMatcher.has_array_table(node)
        table_names = set(table_info.metadata.get("tables", []))

        def _search(n: ASTNode) -> bool:
            if isinstance(n, AssignmentNode):
                # Verificar si el target es un array
                target_name = None
                if isinstance(n.target, LValueNode) and n.target.indices:
                    target_name = n.target.name
                elif isinstance(n.target, ArrayAccessNode):
                    target_name = n.target.array_name
                
                if target_name and target_name in table_names:
                    expr = n.value
                    
                    # Caso 1: Uso de min/max
                    if isinstance(expr, FunctionCallNode):
                        if expr.function_name.lower() in ["min", "max"]:
                            return True
                    
                    # Caso 2: Operación que referencia el mismo array
                    if isinstance(expr, BinaryOpNode):
                        # Cuenta referencias al array en la expresión
                        ref_count = self._count_array_references(expr, target_name)
                        if ref_count >= 2:
                            return True

            for child in get_node_children(n):
                if _search(child):
                    return True

            return False

        return _search(node)
    
    def _count_array_references(self, expr: ASTNode, array_name: str) -> int:
        """
        Cuenta cuántas veces se referencia un array en una expresión.
        
        Maneja tanto ArrayAccessNode como strings (debido a simplificaciones del parser).
        """
        from app.core.parser.ast_nodes import ArrayAccessNode, VariableNode, BinaryOpNode
        
        if expr is None:
            return 0
        
        count = 0
        
        # ArrayAccessNode directo
        if isinstance(expr, ArrayAccessNode):
            if expr.array_name == array_name:
                count += 1
        
        # String directo (parser simplifica dp[i] a "dp")
        if isinstance(expr, str) and expr == array_name:
            count += 1
        
        if isinstance(expr, VariableNode):
            if expr.name == array_name:
                count += 1
        
        # BinaryOpNode - verificar left y right
        if isinstance(expr, BinaryOpNode):
            left = getattr(expr, 'left', None)
            right = getattr(expr, 'right', None)
            
            if isinstance(left, str) and left == array_name:
                count += 1
            else:
                count += self._count_array_references(left, array_name)
            
            if isinstance(right, str) and right == array_name:
                count += 1
            else:
                count += self._count_array_references(right, array_name)
            
            return count
        
        # Recursivo para otros hijos
        for child in get_node_children(expr):
            count += self._count_array_references(child, array_name)
        
        return count

    def _build_reasoning(
        self,
        analysis: Dict[str, Any],
        indicators: list
    ) -> str:
        """Construye explicación del razonamiento"""
        if not analysis["has_memoization_table"]:
            return "No se detectó tabla de memoización, característica principal de DP."

        reasons = []

        if analysis["memo_arrays"]:
            arrays = ", ".join(analysis["memo_arrays"])
            reasons.append(f"usa tabla(s) de memoización ({arrays})")

        if analysis["has_table_filling"]:
            reasons.append("con llenado sistemático")

        if analysis["has_overlapping_subproblems"]:
            reasons.append("reutiliza soluciones de subproblemas")

        if analysis["has_optimal_substructure"]:
            reasons.append("construye solución óptima desde subsoluciones")

        approach = {
            "bottom_up": "enfoque bottom-up (iterativo)",
            "top_down": "enfoque top-down (memoización recursiva)"
        }.get(analysis["dp_approach"], "")

        if approach:
            reasons.append(approach)

        if len(reasons) == 0:
            return "Se detectó tabla pero no están claras todas las características de DP."

        return (
            f"El algoritmo usa Programación Dinámica: "
            f"{', '.join(reasons)}. "
            f"Esto sugiere optimización de problemas con subproblemas solapados."
        )