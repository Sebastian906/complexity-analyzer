"""
Divide and Conquer Detector - Detecta algoritmos Divide y Vencerás

Identifica algoritmos que dividen el problema en subproblemas,
los resuelven recursivamente y combinan las soluciones.
"""

from typing import Dict, Any

from app.core.parser.ast_nodes import (
    ASTNode, AlgorithmNode, AssignmentNode, BinaryOpNode, BlockNode, LiteralNode,
    CallStatementNode, IfStatementNode, ReturnStatementNode,
    ForLoopNode, FunctionCallNode, WhileLoopNode
)
from app.core.patterns.base_pattern import (
    BasePatternDetector,
    PatternType,
    PatternIndicator,
    PatternMatch
)
from app.core.patterns.pattern_matcher import PatternMatcher, get_node_children, get_algorithm_name

class DivideConquerDetector(BasePatternDetector):
    """Detector de algoritmos Divide y Vencerás"""

    def __init__(self):
        super().__init__()
        self.pattern_type = PatternType.DIVIDE_AND_CONQUER
        self.pattern_name = "Divide y Vencerás"
        self.description = "División en subproblemas independientes y combinación"
        self.typical_complexity = "O(n log n)"

        self._indicators = [
            PatternIndicator(
                name="problem_division",
                description="División clara del problema (n/2, mid, partición)",
                found=False,
                weight=0.23
            ),
            PatternIndicator(
                name="recursive_solution",
                description="Resolución recursiva de subproblemas INDEPENDIENTES",
                found=False,
                weight=0.20
            ),
            PatternIndicator(
                name="solution_combination",
                description="Combinación de soluciones parciales",
                found=False,
                weight=0.17
            ),
            PatternIndicator(
                name="base_case",
                description="Caso base para problemas pequeños",
                found=False,
                weight=0.12
            ),
            PatternIndicator(
                name="balanced_division",
                description="División balanceada (O(n/2) típicamente)",
                found=False,
                weight=0.12
            ),
            PatternIndicator(
                name="no_exhaustive_search",
                description="SIN exploración exhaustiva (no es backtracking)",
                found=False,
                weight=0.15
            ),
        ]

    def detect(self, ast: ASTNode) -> PatternMatch:
        """Detecta si el algoritmo usa Divide y Vencerás"""
        analysis = self._analyze_structure(ast)

        indicators_found = []
        indicators_missing = []

        # 1. División del problema (CRÍTICO)
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
            recursive.evidence = f"{analysis['recursive_calls']} llamadas recursivas a subproblemas"
            indicators_found.append(recursive)
        else:
            indicators_missing.append(recursive)

        # 3. Combinación de soluciones
        combination = self._indicators[2]
        if analysis["has_combination"]:
            combination.found = True
            combination.evidence = "Combinación de resultados detectada"
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
            balanced.evidence = "División parece ser O(n/2) - balanceada"
            indicators_found.append(balanced)
        else:
            indicators_missing.append(balanced)

        # 6. NO es exploración exhaustiva
        no_exhaustive = self._indicators[5]
        if not analysis["has_exhaustive_loops"]:
            no_exhaustive.found = True
            no_exhaustive.evidence = "Sin loops de exploración exhaustiva"
            indicators_found.append(no_exhaustive)
        else:
            indicators_missing.append(no_exhaustive)

        # Calcular confianza
        confidence = self._calculate_confidence(indicators_found, indicators_missing)

        # AJUSTES DE CONFIANZA
        
        # BOOST si tiene los 3 elementos clave de D&C
        if (analysis["has_division"] and 
            analysis["recursive_calls"] >= 2 and 
            not analysis["has_exhaustive_loops"]):
            confidence = min(confidence * 1.3, 0.95)
        
        # BOOST adicional si división es balanceada
        if analysis["is_balanced_division"]:
            confidence = min(confidence * 1.15, 0.95)
        
        # BOOST CRÍTICO si es D&C iterativo (Binary Search)
        if analysis.get("is_iterative_dc", False):
            confidence = min(confidence * 1.5, 0.95)  # BOOST 50%
        
        # PENALIZACIÓN si tiene loops exhaustivos (parece backtracking)
        if analysis["has_exhaustive_loops"]:
            confidence = confidence * 0.4
        
        # PENALIZACIÓN si no hay división clara
        if not analysis["has_division"]:
            confidence = min(confidence * 0.3, 0.3)

        # CONSTRUIR REASONING ANTES DE USARLO (FIX CRÍTICO)
        reasoning = self._build_reasoning(analysis, indicators_found)
        
        # Si es D&C iterativo, agregar al reasoning
        if analysis.get("is_iterative_dc", False):
            reasoning += " Detectado como D&C iterativo (ej: Binary Search)."

        return self._create_match(
            confidence=confidence,
            indicators_found=indicators_found,
            indicators_missing=indicators_missing,
            reasoning=reasoning,
            **analysis
        )

    def _analyze_structure(self, ast: ASTNode) -> Dict[str, Any]:
        """Analiza estructura con detección"""
        algo_name = get_algorithm_name(ast)

        analysis = {
            "algorithm_name": algo_name,
            "recursive_calls": 0,
            "has_division": False,
            "division_evidence": "",
            "has_combination": False,
            "has_base_case": False,
            "is_balanced_division": False,
            "has_exhaustive_loops": False,
            "is_iterative_dc": False,
        }

        # Contar llamadas recursivas
        if algo_name:
            result = PatternMatcher.has_recursive_calls(ast, algo_name)
            analysis["recursive_calls"] = result.metadata.get("call_count", 0)

        # NUEVO: Detectar D&C iterativo
        analysis["is_iterative_dc"] = self._is_iterative_divide_conquer(ast)

        # Detectar división del problema
        division_info = self._detect_division(ast, algo_name)
        analysis["has_division"] = division_info["found"]
        analysis["division_evidence"] = division_info["evidence"]
        analysis["is_balanced_division"] = division_info["is_balanced"]

        # Detectar combinación
        analysis["has_combination"] = self._detect_combination(ast)

        # Detectar caso base
        analysis["has_base_case"] = self._detect_base_case(ast)

        # Detectar loops exhaustivos
        analysis["has_exhaustive_loops"] = self._has_exhaustive_loops(ast)

        return analysis

    def _is_iterative_divide_conquer(self, ast: ASTNode) -> bool:
        """
        Detecta D&C iterativo.
        
        Requiere:
        - Loop (while/for)
        - Al menos 2 variables de rango DIFERENTES (low Y high)
        - Cálculo de punto medio
        """
        from app.core.parser.ast_nodes import (
            WhileLoopNode, ForLoopNode, AssignmentNode, BinaryOpNode
        )
        
        # Variables genéricas de rango
        range_vars = {
            'low', 'high', 'left', 'right', 'inicio', 'fin',
            'start', 'end', 'l', 'r', 'i', 'j', 'izq', 'der'
        }
        
        # Variables de punto medio
        midpoint_vars = {
            'mid', 'medio', 'center', 'pivot', 'm', 'p'
        }
        
        has_range_vars = set()
        has_midpoint_calc = False
        has_loop = False
        
        def _search(node: ASTNode):
            nonlocal has_midpoint_calc, has_loop
            
            # Detectar loops
            if isinstance(node, (WhileLoopNode, ForLoopNode)):
                has_loop = True
            
            if isinstance(node, AssignmentNode):
                if hasattr(node.target, 'name'):
                    var_name = node.target.name.lower()
                    
                    # Detectar variables de rango
                    for rv in range_vars:
                        if rv in var_name:
                            has_range_vars.add(rv)
                    
                    # Detectar cálculo de punto medio
                    for mv in midpoint_vars:
                        if mv in var_name:
                            if isinstance(node.value, BinaryOpNode):
                                # mid = (low + high) / 2
                                if node.value.operator in ['/', 'div', '//', '+']:
                                    has_midpoint_calc = True
            
            for child in get_node_children(node):
                _search(child)
        
        _search(ast)
        
        # Requiere: loop + al menos 2 variables de rango diferentes + punto medio
        return has_loop and len(has_range_vars) >= 2 and has_midpoint_calc

    def _detect_division(self, node: ASTNode, func_name: str) -> Dict[str, Any]:
        """Detecta si hay división del problema"""
        division_info = {
            "found": False,
            "evidence": "",
            "is_balanced": False
        }

        # Buscar variables típicas de división
        division_vars = set()
        
        def _search_division_patterns(n: ASTNode):
            if isinstance(n, AssignmentNode):
                if hasattr(n, 'value') and isinstance(n.value, BinaryOpNode):
                    # mid = (left + right) / 2
                    if n.value.operator in ['/', 'div']:
                        if isinstance(n.value.right, LiteralNode) and n.value.right.value == 2:
                            division_vars.add("binary_division")
                            division_info["is_balanced"] = True
                        else:
                            division_vars.add("division")
            
            # Llamadas a partition/split
            if isinstance(n, (CallStatementNode, FunctionCallNode)):
                func_called = n.function_name if hasattr(n, 'function_name') else None
                if func_called and any(kw in func_called.lower() for kw in ['partition', 'split', 'divide']):
                    division_vars.add("partition_call")
            
            for child in get_node_children(n):
                _search_division_patterns(child)
        
        _search_division_patterns(node)
        
        # Llamadas recursivas con argumentos reducidos
        if func_name:
            recursive_with_reduction = self._has_recursive_with_reduction(node, func_name)
            if recursive_with_reduction:
                division_vars.add("recursive_reduction")
        
        # Evaluar evidencia
        if division_vars:
            division_info["found"] = True
            
            if "binary_division" in division_vars:
                division_info["evidence"] = "División binaria detectada (n/2)"
                division_info["is_balanced"] = True
            elif "partition_call" in division_vars:
                division_info["evidence"] = "Llamada a función de partición"
            elif "recursive_reduction" in division_vars:
                division_info["evidence"] = "Llamadas recursivas con argumentos reducidos"
            else:
                division_info["evidence"] = "División del problema detectada"

        return division_info

    def _has_recursive_with_reduction(self, node: ASTNode, func_name: str) -> bool:
        """Verifica si hay llamadas recursivas con argumentos reducidos"""
        def _search(n: ASTNode) -> bool:
            if isinstance(n, CallStatementNode):
                if n.function_name == func_name:
                    for arg in n.arguments:
                        if isinstance(arg, BinaryOpNode):
                            if arg.operator in ['-', '/', 'div']:
                                return True
            
            for child in get_node_children(n):
                if _search(child):
                    return True
            return False
        
        return _search(node)

    def _detect_combination(self, node: ASTNode) -> bool:
        """Detecta si hay combinación de resultados"""
        from app.core.parser.ast_nodes import AssignmentNode, ReturnStatementNode
        
        def _search(n: ASTNode) -> bool:
            if isinstance(n, (AssignmentNode, ReturnStatementNode)):
                expr = n.value if isinstance(n, AssignmentNode) else n.value
                if expr and isinstance(expr, BinaryOpNode):
                    return True
                
                if isinstance(expr, FunctionCallNode):
                    if any(kw in expr.function_name.lower() for kw in ['merge', 'combine', 'concat']):
                        return True
            
            for child in get_node_children(n):
                if _search(child):
                    return True
            return False
        
        return _search(node)

    def _detect_base_case(self, node: ASTNode) -> bool:
        """Detecta caso base"""
        def _search(n: ASTNode) -> bool:
            if isinstance(n, IfStatementNode):
                if isinstance(n.then_block, BlockNode):
                    for child in get_node_children(n.then_block):
                        if isinstance(child, ReturnStatementNode):
                            return True
            
            for child in get_node_children(n):
                if _search(child):
                    return True
            return False
        
        return _search(node)

    def _has_exhaustive_loops(self, node: ASTNode) -> bool:
        """Detecta si hay loops que sugieren exploración exhaustiva"""
        loops = PatternMatcher._count_nodes_of_type(node, (ForLoopNode, WhileLoopNode))
        return loops >= 2

    def _build_reasoning(
        self,
        analysis: Dict[str, Any],
        indicators: list
    ) -> str:
        """Construye explicación del razonamiento"""
        if analysis["recursive_calls"] < 2:
            return "No es Divide y Conquista: requiere al menos 2 llamadas recursivas a subproblemas."
        
        if not analysis["has_division"]:
            return "No se detectó división clara del problema, característica esencial de D&C."
        
        if analysis["has_exhaustive_loops"]:
            return (
                "Tiene loops que sugieren exploración exhaustiva, "
                "lo cual es más característico de Backtracking que de Divide y Conquista."
            )

        reasons = []

        if analysis["has_division"]:
            reasons.append(f"divide el problema ({analysis['division_evidence']})")

        if analysis["recursive_calls"] >= 2:
            reasons.append(f"resuelve {analysis['recursive_calls']} subproblemas recursivamente")

        if analysis["has_combination"]:
            reasons.append("combina las soluciones parciales")

        if analysis["is_balanced_division"]:
            reasons.append("con división balanceada (O(n/2))")

        return (
            f"El algoritmo sigue el patrón Divide y Vencerás clásico: "
            f"{', '.join(reasons)}. "
            f"Esto sugiere complejidad típica de O(n log n)."
        )