"""
Recursive Detector - Detecta algoritmos recursivos

Identifica algoritmos que usan recursión como técnica principal.
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

class RecursiveDetector(BasePatternDetector):
    """
    Detector de algoritmos recursivos.

    Características:
    - Función que se llama a sí misma
    - Caso base para terminar la recursión
    - Puede ser recursión simple, múltiple o mutua
    """

    def __init__(self):
        super().__init__()
        self.pattern_type = PatternType.RECURSIVE
        self.pattern_name = "Recursión"
        self.description = "Función que se invoca a sí misma"
        self.typical_complexity = "Variable (depende del patrón)"

        self._indicators = [
            PatternIndicator(
                name="recursive_calls",
                description="Llamadas recursivas presentes",
                found=False,
                weight=4.0
            ),
            PatternIndicator(
                name="base_case",
                description="Caso base para terminar recursión",
                found=False,
                weight=3.0
            ),
            PatternIndicator(
                name="recursive_case",
                description="Caso recursivo que reduce el problema",
                found=False,
                weight=2.0
            ),
            PatternIndicator(
                name="tail_recursion",
                description="Recursión de cola (optimizable)",
                found=False,
                weight=1.0
            )
        ]

    def detect(self, ast: ASTNode) -> PatternMatch:
        """Detecta si el algoritmo es recursivo"""
        analysis = self._analyze_structure(ast)

        indicators_found = []
        indicators_missing = []

        # 1. Verificar llamadas recursivas
        recursive_calls = self._indicators[0]
        if analysis["recursive_call_count"] > 0:
            recursive_calls.found = True
            recursive_calls.evidence = (
                f"{analysis['recursive_call_count']} llamadas recursivas"
            )
            indicators_found.append(recursive_calls)
        else:
            indicators_missing.append(recursive_calls)

        # 2. Verificar caso base
        base_case = self._indicators[1]
        if analysis["has_base_case"]:
            base_case.found = True
            base_case.evidence = "Detectado condicional que actúa como caso base"
            indicators_found.append(base_case)
        else:
            indicators_missing.append(base_case)

        # 3. Verificar caso recursivo
        recursive_case = self._indicators[2]
        if analysis["recursive_call_count"] > 0 and analysis["has_base_case"]:
            recursive_case.found = True
            recursive_case.evidence = "Estructura recursiva completa detectada"
            indicators_found.append(recursive_case)
        else:
            indicators_missing.append(recursive_case)

        # 4. Verificar recursión de cola
        tail_recursion = self._indicators[3]
        if analysis["is_tail_recursive"]:
            tail_recursion.found = True
            tail_recursion.evidence = "Llamada recursiva es la última operación"
            indicators_found.append(tail_recursion)
        else:
            indicators_missing.append(tail_recursion)

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
        """Analiza la estructura recursiva"""
        from app.core.parser.ast_nodes import IfStatementNode, ProgramNode

        # Obtener nombre del algoritmo usando helper
        algo_name = get_algorithm_name(ast)

        analysis = {
            "algorithm_name": algo_name,
            "recursive_call_count": 0,
            "has_base_case": False,
            "is_tail_recursive": False,
            "recursion_type": "none"
        }

        # Buscar llamadas recursivas
        if algo_name:
            result = PatternMatcher.has_recursive_calls(ast, algo_name)
            analysis["recursive_call_count"] = result.metadata.get("call_count", 0)

        # Detectar caso base (condicional cerca del inicio)
        analysis["has_base_case"] = self._has_base_case(ast)

        # Detectar recursión de cola
        analysis["is_tail_recursive"] = self._is_tail_recursive(ast, algo_name)

        # Clasificar tipo de recursión
        if analysis["recursive_call_count"] == 1:
            analysis["recursion_type"] = "simple"
        elif analysis["recursive_call_count"] >= 2:
            analysis["recursion_type"] = "multiple"

        return analysis

    def _has_base_case(self, node: ASTNode) -> bool:
        """
        Detecta si hay un caso base.
        
        Busca un if que retorna o termina sin hacer llamadas recursivas.
        """
        from app.core.parser.ast_nodes import (
            IfStatementNode, 
            ReturnStatementNode,
            BlockNode
        )

        def _check_block_for_base(block_node: ASTNode) -> bool:
            """Verifica si un bloque es caso base (no tiene recursión)"""
            # Un caso base típicamente retorna directamente
            for child in get_node_children(block_node):
                if isinstance(child, ReturnStatementNode):
                    return True
            return False

        # Buscar if statements
        def _search(n: ASTNode) -> bool:
            if isinstance(n, IfStatementNode):
                # Verificar si el then_block es caso base
                if isinstance(n.then_block, BlockNode):
                    if _check_block_for_base(n.then_block):
                        return True

            # Recursivamente buscar en hijos
            for child in get_node_children(n):
                if _search(child):
                    return True

            return False

        return _search(node)

    def _is_tail_recursive(self, node: ASTNode, func_name: str) -> bool:
        """
        Detecta recursión de cola.
        
        En recursión de cola, la llamada recursiva es la última operación.
        """
        from app.core.parser.ast_nodes import (
            ReturnStatementNode,
            CallStatementNode,
            FunctionCallNode
        )

        # Buscar return statements con llamadas recursivas
        def _check_tail(n: ASTNode) -> bool:
            if isinstance(n, ReturnStatementNode):
                # Verificar si la expresión es una llamada recursiva
                if n.value and isinstance(n.value, FunctionCallNode):
                    if n.value.function_name == func_name:
                        return True

            for child in get_node_children(n):
                if _check_tail(child):
                    return True

            return False

        return _check_tail(node)

    def _build_reasoning(
        self,
        analysis: Dict[str, Any],
        indicators: list
    ) -> str:
        """Construye explicación del razonamiento"""
        if analysis["recursive_call_count"] == 0:
            return "No se detectaron llamadas recursivas en el algoritmo."

        reasons = []

        count = analysis["recursive_call_count"]
        reasons.append(f"{count} llamada(s) recursiva(s)")

        if analysis["has_base_case"]:
            reasons.append("con caso base definido")

        if analysis["is_tail_recursive"]:
            reasons.append("usando recursión de cola (optimizable)")

        recursion_type = analysis["recursion_type"]
        type_desc = {
            "simple": "recursión simple",
            "multiple": "recursión múltiple"
        }.get(recursion_type, "recursión")

        return (
            f"El algoritmo usa {type_desc}: {', '.join(reasons)}. "
            f"Esto indica una solución recursiva clara."
        )