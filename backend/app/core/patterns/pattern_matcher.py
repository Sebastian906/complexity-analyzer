"""
Pattern Matcher - Matcher Genérico de Patrones

Proporciona utilidades para matching de patrones en el AST
usando técnicas de pattern matching estructural.
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass

from app.core.parser.ast_nodes import (
    ASTNode, 
    ProgramNode,
    AlgorithmNode,
    BlockNode,
    ForLoopNode, 
    WhileLoopNode,
    RepeatLoopNode,
    IfStatementNode,
    CallStatementNode,
    AssignmentNode,
    BinaryOpNode,
    ArrayAccessNode,
    VariableNode,
    LiteralNode,
    LValueNode,
    FunctionCallNode
)


def get_node_children(node: ASTNode) -> List[ASTNode]:
    """
    Obtiene los nodos hijos de cualquier nodo AST.
    
    Esta función proporciona una forma unificada de recorrer el AST
    usando los atributos específicos de cada tipo de nodo.
    
    Args:
        node: Cualquier nodo del AST
        
    Returns:
        Lista de nodos hijos
    """
    children = []
    
    # ProgramNode
    if isinstance(node, ProgramNode):
        if node.algorithm:
            children.append(node.algorithm)
        children.extend(node.classes)
        return children
    
    # AlgorithmNode
    if isinstance(node, AlgorithmNode):
        if node.body:
            children.append(node.body)
        return children
    
    # BlockNode
    if isinstance(node, BlockNode):
        return list(node.statements)
    
    # ForLoopNode
    if isinstance(node, ForLoopNode):
        children.append(node.start)
        children.append(node.end)
        if node.body:
            children.append(node.body)
        return children
    
    # WhileLoopNode
    if isinstance(node, WhileLoopNode):
        children.append(node.condition)
        if node.body:
            children.append(node.body)
        return children
    
    # RepeatLoopNode
    if isinstance(node, RepeatLoopNode):
        children.extend(node.body)  # body es una lista
        children.append(node.condition)
        return children
    
    # IfStatementNode
    if isinstance(node, IfStatementNode):
        children.append(node.condition)
        if node.then_block:
            children.append(node.then_block)
        if node.else_block:
            children.append(node.else_block)
        return children
    
    # AssignmentNode
    if isinstance(node, AssignmentNode):
        if node.target:
            children.append(node.target)
        if node.value:
            children.append(node.value)
        return children
    
    # CallStatementNode
    if isinstance(node, CallStatementNode):
        children.extend(node.arguments)
        return children
    
    # FunctionCallNode (expresión de llamada)
    if isinstance(node, FunctionCallNode):
        children.extend(node.arguments)
        return children
    
    # BinaryOpNode
    if isinstance(node, BinaryOpNode):
        if node.left:
            children.append(node.left)
        if node.right:
            children.append(node.right)
        return children
    
    # ArrayAccessNode
    if isinstance(node, ArrayAccessNode):
        if node.array:
            children.append(node.array)
        children.extend(node.indices)
        return children
    
    # LValueNode
    if isinstance(node, LValueNode):
        children.extend(node.indices)
        return children
    
    # Nodos hoja (sin hijos): VariableNode, LiteralNode, ParameterNode
    return children


def get_algorithm_name(ast: ASTNode) -> str:
    """
    Obtiene el nombre del algoritmo de un nodo AST.
    
    Maneja tanto ProgramNode como AlgorithmNode.
    
    Args:
        ast: Nodo AST (puede ser ProgramNode o AlgorithmNode)
        
    Returns:
        Nombre del algoritmo o string vacío si no se encuentra
    """
    if isinstance(ast, AlgorithmNode):
        return ast.name
    elif isinstance(ast, ProgramNode) and ast.algorithm:
        return ast.algorithm.name
    return ""


@dataclass
class MatchResult:
    """Resultado de un pattern match"""
    matched: bool
    confidence: float = 0.0
    evidence: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class PatternMatcher:
    """
    Utilidad para hacer pattern matching estructural en ASTs.
    
    Proporciona métodos convenientes para buscar patrones comunes
    en estructuras de algoritmos.
    """
    
    @staticmethod
    def has_nested_loops(node: ASTNode, min_depth: int = 2) -> MatchResult:
        """
        Detecta si hay loops anidados.
        
        Args:
            node: Nodo raíz
            min_depth: Profundidad mínima de anidación
        
        Returns:
            MatchResult indicando si se encontró el patrón
        """
        max_depth = PatternMatcher._count_loop_depth(node)
        
        matched = max_depth >= min_depth
        confidence = min(1.0, max_depth / (min_depth + 2))
        
        return MatchResult(
            matched=matched,
            confidence=confidence,
            evidence=f"Profundidad de loops: {max_depth}",
            metadata={"max_depth": max_depth}
        )
    
    @staticmethod
    def _count_loop_depth(node: ASTNode, current_depth: int = 0) -> int:
        """Helper: cuenta profundidad máxima de loops"""
        max_depth = current_depth
        
        is_loop = isinstance(node, (ForLoopNode, WhileLoopNode, RepeatLoopNode))
        
        if is_loop:
            current_depth += 1
            max_depth = current_depth
        
        for child in get_node_children(node):
            child_depth = PatternMatcher._count_loop_depth(child, current_depth)
            max_depth = max(max_depth, child_depth)

        return max_depth

    @staticmethod
    def has_recursive_calls(node: ASTNode, function_name: str) -> MatchResult:
        """
        Detecta llamadas recursivas.

        Args:
            node: Nodo raíz
            function_name: Nombre de la función a buscar

        Returns:
            MatchResult con información de las llamadas
        """
        calls = PatternMatcher._find_calls(node, function_name)

        matched = len(calls) > 0
        confidence = min(1.0, len(calls) / 3)  # Normalizado a 3 llamadas

        return MatchResult(
            matched=matched,
            confidence=confidence,
            evidence=f"Encontradas {len(calls)} llamadas recursivas",
            metadata={"call_count": len(calls), "call_locations": calls}
        )

    @staticmethod
    def _find_calls(node: ASTNode, func_name: str) -> List[str]:
        """Helper: encuentra todas las llamadas a una función.
        
        Busca tanto CallStatementNode (call func()) como FunctionCallNode (x := func()).
        """
        calls = []

        # CallStatementNode: call function(args)
        if isinstance(node, CallStatementNode):
            if node.function_name == func_name:
                calls.append(f"line {node.line if hasattr(node, 'line') else '?'}")
        
        # FunctionCallNode: x := function(args) - llamadas en expresiones
        if isinstance(node, FunctionCallNode):
            if node.function_name == func_name:
                calls.append(f"line {node.line if hasattr(node, 'line') else '?'}")

        for child in get_node_children(node):
            calls.extend(PatternMatcher._find_calls(child, func_name))

        return calls

    @staticmethod
    def has_conditional_recursion(node: ASTNode, func_name: str) -> MatchResult:
        """
        Detecta recursión dentro de condicionales (patrón divide y conquista).

        Args:
            node: Nodo raíz
            func_name: Nombre de la función

        Returns:
            MatchResult indicando si hay recursión condicional
        """
        conditional_calls = PatternMatcher._find_conditional_recursion(node, func_name)

        matched = len(conditional_calls) > 0
        confidence = min(1.0, len(conditional_calls) / 2)

        return MatchResult(
            matched=matched,
            confidence=confidence,
            evidence=f"Encontradas {len(conditional_calls)} llamadas recursivas en condicionales",
            metadata={"conditional_calls": conditional_calls}
        )

    @staticmethod
    def _find_conditional_recursion(node: ASTNode, func_name: str) -> List[str]:
        """Helper: encuentra recursión dentro de if statements"""
        calls = []

        if isinstance(node, IfStatementNode):
            # Buscar llamadas dentro del if
            then_calls = PatternMatcher._find_calls(node.then_block, func_name)

            if then_calls:
                calls.append(f"if-then branch")

            if node.else_block:
                else_calls = PatternMatcher._find_calls(node.else_block, func_name)
                if else_calls:
                    calls.append(f"if-else branch")

        for child in get_node_children(node):
            calls.extend(PatternMatcher._find_conditional_recursion(child, func_name))

        return calls

    @staticmethod
    def has_array_table(node: ASTNode) -> MatchResult:
        """
        Detecta uso de arrays como tablas (típico en DP).

        Args:
            node: Nodo raíz

        Returns:
            MatchResult indicando si se usan tablas
        """
        array_usage = PatternMatcher._analyze_array_usage(node)

        # Un array usado como tabla de DP típicamente:
        # 1. Tiene múltiples asignaciones (llenado de tabla)
        # 2. Se nombra con patrones típicos de DP (dp, memo, table, cache, etc.)
        
        dp_keywords = {'dp', 'memo', 'table', 'cache', 'tab', 'matriz', 'matrix', 'dist', 'cost'}
        
        tables = []
        for name, info in array_usage.items():
            # Un array es tabla si:
            # - Tiene múltiples asignaciones (>=2), O
            # - Tiene nombre típico de DP
            is_dp_name = any(kw in name.lower() for kw in dp_keywords)
            has_multiple_assigns = info["assignments"] >= 2
            has_accesses = info["accesses"] > 0
            
            if has_multiple_assigns or (is_dp_name and info["assignments"] > 0):
                tables.append(name)

        matched = len(tables) > 0
        confidence = min(1.0, len(tables) / 2)

        return MatchResult(
            matched=matched,
            confidence=confidence,
            evidence=f"Encontrados {len(tables)} arrays usados como tablas: {', '.join(tables)}",
            metadata={"tables": tables, "usage": array_usage}
        )

    @staticmethod
    def _analyze_array_usage(node: ASTNode) -> Dict[str, Dict[str, int]]:
        """Analiza cómo se usan los arrays.
        
        Detecta tanto ArrayAccessNode (lectura de arrays) como 
        LValueNode con índices (escritura a arrays).
        """
        usage = {}

        def _track(n: ASTNode):
            if isinstance(n, AssignmentNode):
                # Asignación a array - puede ser LValueNode con índices
                if isinstance(n.target, LValueNode) and n.target.indices:
                    # Es un LValueNode con índices: dp[i] := ...
                    array_name = n.target.name
                    if array_name:
                        if array_name not in usage:
                            usage[array_name] = {"assignments": 0, "accesses": 0}
                        usage[array_name]["assignments"] += 1
                elif isinstance(n.target, ArrayAccessNode):
                    # También manejar ArrayAccessNode por si acaso
                    array_name = PatternMatcher._get_array_name(n.target)
                    if array_name:
                        if array_name not in usage:
                            usage[array_name] = {"assignments": 0, "accesses": 0}
                        usage[array_name]["assignments"] += 1

            if isinstance(n, ArrayAccessNode):
                # Acceso a array (lectura): ... := dp[i] + dp[j]
                array_name = PatternMatcher._get_array_name(n)
                if array_name:
                    if array_name not in usage:
                        usage[array_name] = {"assignments": 0, "accesses": 0}
                    usage[array_name]["accesses"] += 1

            for child in get_node_children(n):
                _track(child)

        _track(node)
        return usage

    @staticmethod
    def _get_array_name(array_node: ArrayAccessNode) -> Optional[str]:
        """Extrae el nombre del array de un ArrayAccessNode"""
        if isinstance(array_node.array, VariableNode):
            return array_node.array.name
        return None

    @staticmethod
    def has_greedy_choice(node: ASTNode) -> MatchResult:
        """
        Detecta patrón de elección greedy (selección óptima en cada iteración).

        Algoritmos Greedy VERDADEROS tienen:
        - Selección explícita del mejor/mínimo/máximo elemento
        - Variables que rastrean el óptimo actual (min, max, best, optimal)
        - Operaciones de actualización condicional del óptimo
        - Típicamente UN loop principal, no loops anidados exhaustivos

        NO es Greedy si:
        - Solo tiene comparaciones para swap (eso es Fuerza Bruta)
        - Tiene loops anidados que exploran TODAS las combinaciones
        - Solo hace intercambios sin selección de óptimo

        Args:
            node: Nodo raíz

        Returns:
            MatchResult indicando si hay patrón greedy
        """
        loops = PatternMatcher._count_nodes_of_type(node, (ForLoopNode, WhileLoopNode))
        nested_depth = PatternMatcher._count_loop_depth(node)
        comparisons = PatternMatcher._count_comparison_operations(node)
        
        # Detectar patrones de selección óptima (min/max tracking)
        optimal_tracking = PatternMatcher._has_optimal_tracking(node)
        
        # Detectar si solo hace swaps (típico de ordenamiento por fuerza bruta)
        has_swap_pattern = PatternMatcher._has_swap_pattern(node)
        
        # Greedy típico:
        # - Tiene loops con comparaciones
        # - Tiene tracking de óptimo (variables min/max/best)
        # - NO tiene loops profundamente anidados para exploración exhaustiva
        # - NO es solo un patrón de swap
        
        is_greedy = False
        confidence = 0.0
        
        if optimal_tracking["has_tracking"]:
            # Tiene tracking de óptimo - muy probable Greedy
            is_greedy = True
            confidence = min(1.0, 0.6 + optimal_tracking["score"] * 0.4)
        elif loops > 0 and comparisons > 0 and nested_depth <= 1:
            # Un solo nivel de loop con comparaciones puede ser greedy
            is_greedy = True
            confidence = 0.4
        
        # Penalizar si parece fuerza bruta
        if has_swap_pattern and nested_depth >= 2:
            # Loops anidados con swaps = probablemente Bubble Sort u otro Fuerza Bruta
            confidence = max(0.0, confidence - 0.5)
            if confidence < 0.3:
                is_greedy = False
        
        if nested_depth >= 3:
            # Demasiados loops anidados - más probable Fuerza Bruta
            confidence = max(0.0, confidence - 0.3)

        return MatchResult(
            matched=is_greedy,
            confidence=confidence,
            evidence=f"{loops} loops con {comparisons} comparaciones" + 
                     (f", tracking óptimo detectado" if optimal_tracking["has_tracking"] else "") +
                     (f", patrón de swap detectado" if has_swap_pattern else ""),
            metadata={
                "loops": loops,
                "comparisons": comparisons,
                "nested_depth": nested_depth,
                "optimal_tracking": optimal_tracking,
                "has_swap_pattern": has_swap_pattern
            }
        )
    
    @staticmethod
    def _has_optimal_tracking(node: ASTNode) -> Dict[str, Any]:
        """
        Detecta si hay variables que rastrean un óptimo local.
        
        Patrones típicos:
        - min := ..., if x < min then min := x
        - max := ..., if x > max then max := x
        - best := ..., optimal := ...
        """
        optimal_keywords = {'min', 'max', 'best', 'optimal', 'selected', 'candidate', 
                           'minimo', 'maximo', 'mejor', 'optimo', 'menor', 'mayor'}
        
        found_vars = set()
        score = 0.0
        
        def _search(n: ASTNode):
            nonlocal score
            
            if isinstance(n, AssignmentNode):
                # Verificar si asigna a variable con nombre de óptimo
                if isinstance(n.target, (VariableNode, LValueNode)):
                    var_name = n.target.name if isinstance(n.target, VariableNode) else n.target.name
                    var_lower = var_name.lower()
                    
                    for keyword in optimal_keywords:
                        if keyword in var_lower:
                            found_vars.add(var_name)
                            score += 0.3
                            break
            
            for child in get_node_children(n):
                _search(child)
        
        _search(node)
        
        return {
            "has_tracking": len(found_vars) > 0,
            "variables": list(found_vars),
            "score": min(1.0, score)
        }
    
    @staticmethod
    def _has_swap_pattern(node: ASTNode) -> bool:
        """
        Detecta patrón de swap típico de Bubble Sort.
        
        Patrón: temp := A[i]; A[i] := A[j]; A[j] := temp
        """
        temp_vars = {'temp', 'tmp', 'aux', 'swap', 'temporal'}
        
        def _search(n: ASTNode) -> bool:
            if isinstance(n, AssignmentNode):
                # Buscar asignación a variable temporal
                if isinstance(n.target, (VariableNode, LValueNode)):
                    var_name = n.target.name if isinstance(n.target, VariableNode) else n.target.name
                    if var_name.lower() in temp_vars:
                        return True
            
            for child in get_node_children(n):
                if _search(child):
                    return True
            
            return False
        
        return _search(node)

    @staticmethod
    def _count_nodes_of_type(node: ASTNode, types: tuple) -> int:
        """Cuenta nodos de ciertos tipos"""
        count = 1 if isinstance(node, types) else 0

        for child in get_node_children(node):
            count += PatternMatcher._count_nodes_of_type(child, types)

        return count

    @staticmethod
    def _count_comparison_operations(node: ASTNode) -> int:
        """Cuenta operaciones de comparación"""
        count = 0

        if isinstance(node, BinaryOpNode):
            if node.operator in ["<", ">", "<=", ">=", "=", "!="]:
                count += 1

        for child in get_node_children(node):
            count += PatternMatcher._count_comparison_operations(child)

        return count

    @staticmethod
    def has_backtracking_pattern(node: ASTNode, func_name: str) -> MatchResult:
        """
        Detecta patrón de backtracking.

        Características:
        - Recursión múltiple
        - Condiciones de poda
        - Exploración de posibilidades

        Args:
            node: Nodo raíz
            func_name: Nombre de la función

        Returns:
            MatchResult indicando si hay backtracking
        """
        recursive_calls = len(PatternMatcher._find_calls(node, func_name))
        conditionals = PatternMatcher._count_nodes_of_type(node, (IfStatementNode,))

        # Backtracking típicamente tiene múltiples llamadas recursivas
        # dentro de condicionales (poda)
        has_pattern = recursive_calls >= 2 and conditionals > 0

        confidence = 0.0
        if has_pattern:
            confidence = min(1.0, (recursive_calls * conditionals) / 8)

        return MatchResult(
            matched=has_pattern,
            confidence=confidence,
            evidence=f"{recursive_calls} llamadas recursivas con {conditionals} condiciones",
            metadata={
                "recursive_calls": recursive_calls,
                "conditionals": conditionals
            }
        )

    @staticmethod
    def match_custom(
        node: ASTNode,
        predicate: Callable[[ASTNode], bool]
    ) -> MatchResult:
        """
        Permite hacer pattern matching custom.

        Args:
            node: Nodo raíz
            predicate: Función que retorna True si el patrón se encuentra

        Returns:
            MatchResult basado en el predicado
        """
        try:
            matched = predicate(node)
            return MatchResult(
                matched=matched,
                confidence=1.0 if matched else 0.0,
                evidence="Custom predicate match"
            )
        except Exception as e:
            return MatchResult(
                matched=False,
                confidence=0.0,
                evidence=f"Error en predicado: {str(e)}"
            )