"""
Divide and Conquer Detector - Detecta algoritmos Divide y Vencerás

Identifica algoritmos que dividen el problema en subproblemas,
los resuelven recursivamente y combinan las soluciones.
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

class DivideConquerDetector(BasePatternDetector):
    """
    Detector de algoritmos Divide y Vencerás.
    
    Características:
    - División del problema en subproblemas
    - Resolución recursiva de subproblemas
    - Combinación de soluciones
    - Típicamente O(n log n)
    """

    def __init__(self):
        super().__init__()
        self.pattern_type = PatternType.DIVIDE_AND_CONQUER
        self.pattern_name = "Divide y Vencerás"
        self.description = "División en subproblemas y combinación de soluciones"
        self.typical_complexity = "O(n log n)"

        self._indicators = [
            PatternIndicator(
                name="problem_division",
                description="División del problema en partes",
                found=False,
                weight=4.0
            ),
            PatternIndicator(
                name="recursive_solution",
                description="Resolución recursiva de subproblemas",
                found=False,
                weight=3.5
            ),
            PatternIndicator(
                name="solution_combination",
                description="Combinación de soluciones parciales",
                found=False,
                weight=3.0
            ),
            PatternIndicator(
                name="base_case",
                description="Caso base para problemas pequeños",
                found=False,
                weight=2.5
            ),
            PatternIndicator(
                name="balanced_division",
                description="División balanceada (n/2)",
                found=False,
                weight=2.0
            )
        ]

    def detect(self, ast: ASTNode) -> PatternMatch:
        """Detecta si el algoritmo usa Divide y Vencerás"""
        analysis = self._analyze_structure(ast)

        indicators_found = []
        indicators_missing = []

        # 1. División del problema
        division = self._indicators[0]
        if analysis["has_division"]:
            division.found = True
            division.evidence = analysis["division_evidence"]
            indicators_found.append(division)
        else:
            indicators_missing.append(division)

        # 2. Solución recursiva
        recursive = self._indicators[1]
        if analysis["recursive_calls"] >= 2:
            recursive.found = True
            recursive.evidence = f"{analysis['recursive_calls']} llamadas recursivas"
            indicators_found.append(recursive)
        else:
            indicators_missing.append(recursive)

        # 3. Combinación de soluciones
        combination = self._indicators[2]
        if analysis["has_combination"]:
            combination.found = True
            combination.evidence = "Detectada combinación de resultados parciales"
            indicators_found.append(combination)
        else:
            indicators_missing.append(combination)

        # 4. Caso base
        base_case = self._indicators[3]
        if analysis["has_base_case"]:
            base_case.found = True
            base_case.evidence = "Caso base identificado"
            indicators_found.append(base_case)
        else:
            indicators_missing.append(base_case)

        # 5. División balanceada
        balanced = self._indicators[4]
        if analysis["is_balanced_division"]:
            balanced.found = True
            balanced.evidence = "División parece ser O(n/2)"
            indicators_found.append(balanced)
        else:
            indicators_missing.append(balanced)

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
        from app.core.parser.ast_nodes import (
            IfStatementNode,
            BinaryOpNode,
            CallStatementNode
        )

        # Obtener nombre del algoritmo usando helper
        algo_name = get_algorithm_name(ast)

        analysis = {
            "algorithm_name": algo_name,
            "recursive_calls": 0,
            "has_division": False,
            "division_evidence": "",
            "has_combination": False,
            "has_base_case": False,
            "is_balanced_division": False
        }

        # Contar llamadas recursivas
        if algo_name:
            result = PatternMatcher.has_recursive_calls(ast, algo_name)
            analysis["recursive_calls"] = result.metadata.get("call_count", 0)

        # Detectar división del problema
        division_info = self._detect_division(ast, algo_name)
        analysis["has_division"] = division_info["found"]
        analysis["division_evidence"] = division_info["evidence"]
        analysis["is_balanced_division"] = division_info["is_balanced"]

        # Detectar combinación
        analysis["has_combination"] = self._detect_combination(ast)

        # Detectar caso base
        analysis["has_base_case"] = self._detect_base_case(ast)

        return analysis

    def _detect_division(self, node: ASTNode, func_name: str) -> Dict[str, Any]:
        """
        Detecta si hay división del problema.
        
        Busca llamadas recursivas con argumentos reducidos.
        """
        from app.core.parser.ast_nodes import (
            CallStatementNode,
            BinaryOpNode,
            LiteralNode
        )

        division_info = {
            "found": False,
            "evidence": "",
            "is_balanced": False
        }

        # Buscar llamadas recursivas con división
        def _search(n: ASTNode) -> bool:
            if isinstance(n, CallStatementNode):
                if n.function_name == func_name:
                    # Verificar si los argumentos sugieren división
                    for arg in n.arguments:
                        # Buscar operaciones de división (n/2, n-1, etc)
                        if self._is_division_expression(arg):
                            division_info["found"] = True
                            division_info["evidence"] = "Llamadas recursivas con argumentos reducidos"

                            # Verificar si es división balanceada (n/2)
                            if self._is_balanced_division_expression(arg):
                                division_info["is_balanced"] = True

                            return True

            for child in get_node_children(n):
                if _search(child):
                    return True

            return False

        _search(node)
        return division_info

    def _is_division_expression(self, node: ASTNode) -> bool:
        """Verifica si una expresión representa división del problema"""
        from app.core.parser.ast_nodes import BinaryOpNode

        if isinstance(node, BinaryOpNode):
            # n/2, n/k, n-1, etc
            if node.operator in ["/", "-", "div"]:
                return True

        return False

    def _is_balanced_division_expression(self, node: ASTNode) -> bool:
        """Verifica si es división balanceada (n/2)"""
        from app.core.parser.ast_nodes import BinaryOpNode, LiteralNode

        if isinstance(node, BinaryOpNode):
            if node.operator == "/" or node.operator == "div":
                # Verificar si divide por 2
                if isinstance(node.right, LiteralNode):
                    if node.right.value == 2:
                        return True

        return False

    def _detect_combination(self, node: ASTNode) -> bool:
        """
        Detecta si hay combinación de resultados.

        Busca operaciones después de las llamadas recursivas
        que combinan los resultados.
        """
        from app.core.parser.ast_nodes import (
            AssignmentNode,
            BinaryOpNode,
            ReturnStatementNode
        )

        # Buscar assignments o returns que usen múltiples variables
        # (posibles resultados de llamadas recursivas)
        def _search(n: ASTNode) -> bool:
            if isinstance(n, (AssignmentNode, ReturnStatementNode)):
                # Verificar si la expresión combina valores
                expr = n.value if isinstance(n, AssignmentNode) else n.value
                if expr and isinstance(expr, BinaryOpNode):
                    # Hay una operación binaria, posible combinación
                    return True

            for child in get_node_children(n):
                if _search(child):
                    return True

            return False

        return _search(node)

    def _detect_base_case(self, node: ASTNode) -> bool:
        """Detecta caso base"""
        from app.core.parser.ast_nodes import (
            IfStatementNode,
            ReturnStatementNode,
            BlockNode
        )

        def _search(n: ASTNode) -> bool:
            if isinstance(n, IfStatementNode):
                # Verificar si el then_block retorna sin recursión
                if isinstance(n.then_block, BlockNode):
                    for child in get_node_children(n.then_block):
                        if isinstance(child, ReturnStatementNode):
                            return True

            for child in get_node_children(n):
                if _search(child):
                    return True

            return False

        return _search(node)

    def _build_reasoning(
        self,
        analysis: Dict[str, Any],
        indicators: list
    ) -> str:
        """Construye explicación del razonamiento"""
        if analysis["recursive_calls"] < 2:
            return "No se detectó patrón de Divide y Vencerás (requiere múltiples llamadas recursivas)."

        reasons = []

        if analysis["has_division"]:
            reasons.append("divide el problema en subproblemas")

        if analysis["recursive_calls"] >= 2:
            reasons.append(f"resuelve {analysis['recursive_calls']} subproblemas recursivamente")

        if analysis["has_combination"]:
            reasons.append("combina las soluciones parciales")

        if analysis["is_balanced_division"]:
            reasons.append("con división balanceada (O(n/2))")

        if len(reasons) == 0:
            return "Características de Divide y Vencerás no claramente identificadas."

        return (
            f"El algoritmo sigue el patrón Divide y Vencerás: "
            f"{', '.join(reasons)}. "
            f"Esto sugiere complejidad típica de O(n log n)."
        )