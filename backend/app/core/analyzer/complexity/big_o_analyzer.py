"""
Analizador Big O (Peor Caso)

Implementa el análisis de complejidad temporal en el peor caso.
Analiza loops, recursión, y estructuras de control para determinar O(n).
"""

from app.core.analyzer.complexity.base_analyzer import (
    BaseComplexityAnalyzer, ComplexityResult
)
from app.core.parser.ast_nodes import *


class BigOAnalyzer(BaseComplexityAnalyzer):
    """Analizador de Big O (peor caso)"""
    
    def analyze(self, ast: ASTNode) -> ComplexityResult:
        """Analiza el algoritmo completo"""
        self.logger.info(f"Analizando Big O de: {ast.algorithm.name}")
        
        # Analizar el cuerpo del algoritmo
        body_complexity = self.analyze_node(ast.algorithm.body)
        
        return ComplexityResult(
            complexity=body_complexity,
            notation="O",
            explanation=f"Complejidad del peor caso: O({body_complexity})"
        )
    
    def analyze_node(self, node: ASTNode) -> str:
        """Analiza un nodo específico"""
        if isinstance(node, BlockNode):
            return self.analyze_block(node)
        
        elif isinstance(node, ForLoopNode):
            return self._analyze_for_loop(node)
        
        elif isinstance(node, WhileLoopNode):
            return self._analyze_while_loop(node)
        
        elif isinstance(node, RepeatLoopNode):
            return self._analyze_repeat_loop(node)
        
        elif isinstance(node, IfStatementNode):
            return self._analyze_if_statement(node)
        
        elif isinstance(node, AssignmentNode):
            return "1"  # O(1)
        
        elif isinstance(node, CallStatementNode):
            # Analizar la complejidad de la función llamada
            return self._analyze_call(node)
        
        else:
            return "1"
    
    def _analyze_for_loop(self, node: ForLoopNode) -> str:
        """
        Analiza un FOR loop.
        
        FOR i ← 1 to n:
            body -> O(body)
        
        Resultado: O(n * body)
        """
        # Analizar el cuerpo
        body_complexity = self.analyze_node(node.body)
        
        # Determinar el número de iteraciones
        iterations = self._calculate_iterations(node.start, node.end)
        
        # Combinar: iterations * body_complexity
        return self.combine_nested(iterations, body_complexity)
    
    def _calculate_iterations(self, start, end) -> str:
        """
        Calcula el número de iteraciones de un loop.
        
        Analiza start y end para determinar la complejidad exacta.
        """
        # Si start y end son literales, podemos calcular exactamente
        if isinstance(start, LiteralNode) and isinstance(end, LiteralNode):
            start_val = start.value
            end_val = end.value
            iterations = end_val - start_val + 1
            # Si es un número pequeño constante, devolver como constante
            if iterations <= 10:
                return str(iterations)
            return "n"  # Número grande se considera O(n)
        
        # Si end es un identificador
        if isinstance(end, VariableNode):
            name = end.name.lower()
            # Variables comunes que representan tamaño
            if name in ('n', 'm', 'size', 'length', 'len', 'count'):
                return "n"
            # Si es una variable diferente, asumimos O(n) también
            return "n"
        
        # Si end es una expresión binaria (ej: n-1, n/2, n*n)
        if isinstance(end, BinaryOpNode):
            op = end.operator
            # Operaciones que reducen: n-1, n-k -> O(n)
            if op == "-":
                return "n"
            # Operaciones que dividen: n/2, n/k -> O(log n)? No, sigue siendo O(n) iteraciones
            if op == "/" or op == "//":
                # El loop sigue siendo lineal en términos del valor final
                return "n"
            # Operaciones que multiplican: n*n -> O(n^2)
            if op == "*":
                left = self._extract_term(end.left)
                right = self._extract_term(end.right)
                if left == "n" and right == "n":
                    return "n^2"
                return "n"
        
        # Por defecto, asumir O(n)
        return "n"
    
    def _extract_term(self, expr) -> str:
        """Extrae el término principal de una expresión"""
        if isinstance(expr, VariableNode):
            return expr.name.lower()
        if isinstance(expr, LiteralNode):
            return str(expr.value)
        return "n"  # Default
    
    def _analyze_while_loop(self, node: WhileLoopNode) -> str:
        """
        Analiza un WHILE loop.
        
        Más complejo porque depende de la condición.
        Analiza la condición para determinar iteraciones.
        """
        body_complexity = self.analyze_node(node.body)
        
        # Analizar la condición para determinar iteraciones
        iterations = self._analyze_while_condition(node.condition)
        
        return self.combine_nested(iterations, body_complexity)
    
    def _analyze_while_condition(self, condition) -> str:
        """
        Analiza la condición de un WHILE para estimar iteraciones.
        
        Heurísticas comunes:
        - i < n, i <= n -> O(n)
        - i < n*n, i <= n^2 -> O(n^2)  
        - i > 0, i >= 1 con i = i/2 -> O(log n)
        """
        if not isinstance(condition, BinaryOpNode):
            return "n"  # Default conservador
        
        op = condition.operator
        left = condition.left
        right = condition.right
        
        # Patrones de comparación: i < n, i <= n, i != n
        if op in ('<', '<=', '>', '>=', '!='):
            # Si el lado derecho es un identificador de tamaño
            if isinstance(right, VariableNode):
                name = right.name.lower()
                if name in ('n', 'm', 'size', 'length'):
                    return "n"
            
            # Si el lado derecho es una expresión multiplicativa
            if isinstance(right, BinaryOpNode) and right.operator == '*':
                left_term = self._extract_term(right.left)
                right_term = self._extract_term(right.right)
                if left_term == "n" and right_term == "n":
                    return "n^2"
            
            # Si el lado izquierdo > 0 (patrón de división)
            if isinstance(right, LiteralNode):
                if right.value in (0, 1):
                    # Podría ser un patrón logarítmico (i = i/2)
                    # Pero sin analizar el cuerpo, asumimos O(n) para ser conservador
                    return "n"
        
        return "n"  # Default conservador
    
    def _analyze_repeat_loop(self, node: RepeatLoopNode) -> str:
        """Analiza un REPEAT loop (similar a WHILE)"""
        # Analizar todos los statements del body
        complexities = [self.analyze_node(stmt) for stmt in node.body]
        body_complexity = self.combine_sequential(complexities)
        
        return self.combine_nested("n", body_complexity)
    
    def _analyze_if_statement(self, node: IfStatementNode) -> str:
        """
        Analiza un IF statement.
        
        En Big O (peor caso), tomamos el máximo entre then y else.
        """
        then_complexity = self.analyze_node(node.then_block)
        
        if node.else_block:
            else_complexity = self.analyze_node(node.else_block)
            
            # Tomar el máximo (peor caso)
            complexities = [then_complexity, else_complexity]
            return self.combine_sequential(complexities)
        
        return then_complexity
    
    def _analyze_call(self, node: CallStatementNode) -> str:
        """
        Analiza la complejidad de una llamada a función.
        
        Heurísticas:
        - Funciones conocidas tienen complejidad conocida
        - Funciones con argumentos de tamaño n: O(n) conservador
        - Sin más información: O(1)
        """
        func_name = node.function_name.lower()
        
        # Funciones comunes con complejidad conocida
        known_functions = {
            # O(1) - Acceso/operaciones simples
            'print': '1', 'println': '1', 'write': '1', 'read': '1',
            'push': '1', 'pop': '1', 'top': '1', 'peek': '1',
            'enqueue': '1', 'dequeue': '1', 'front': '1',
            'min': '1', 'max': '1', 'abs': '1', 'floor': '1', 'ceil': '1',
            'length': '1', 'size': '1', 'count': '1', 'empty': '1',
            'get': '1', 'set': '1', 'insert': '1', 'delete': '1',
            
            # O(n) - Operaciones lineales
            'copy': 'n', 'clone': 'n', 'reverse': 'n', 'fill': 'n',
            'find': 'n', 'search': 'n', 'contains': 'n', 'indexof': 'n',
            'sum': 'n', 'average': 'n', 'mean': 'n',
            
            # O(n log n) - Ordenamiento
            'sort': 'n log n', 'quicksort': 'n log n', 'mergesort': 'n log n',
            'heapsort': 'n log n', 'timsort': 'n log n',
            
            # O(n^2) - Ordenamiento cuadrático
            'bubblesort': 'n^2', 'insertionsort': 'n^2', 'selectionsort': 'n^2',
            
            # O(log n) - Búsqueda binaria
            'binarysearch': 'log n', 'bisect': 'log n',
        }
        
        if func_name in known_functions:
            return known_functions[func_name]
        
        # Si el nombre sugiere una operación de ordenamiento
        if 'sort' in func_name:
            return 'n log n'
        
        # Si el nombre sugiere búsqueda
        if 'search' in func_name or 'find' in func_name:
            return 'n'
        
        # Por defecto, asumir O(1) para funciones auxiliares simples
        return "1"