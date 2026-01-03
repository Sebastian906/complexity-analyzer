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
            # Por ahora, asumimos O(1)
            # TODO: Analizar la complejidad de la función llamada
            return "1"
        
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
        
        Por ahora, asumimos que es O(n).
        TODO: Analizar start y end para determinar la complejidad exacta.
        """
        # Si start y end son literales, podemos calcular exactamente
        if isinstance(start, LiteralNode) and isinstance(end, LiteralNode):
            start_val = start.value
            end_val = end.value
            iterations = end_val - start_val + 1
            return str(iterations)
        
        # Si end es una variable (ej: n), asumir O(n)
        return "n"
    
    def _analyze_while_loop(self, node: WhileLoopNode) -> str:
        """
        Analiza un WHILE loop.
        
        Más complejo porque depende de la condición.
        Por ahora, asumimos O(n).
        """
        body_complexity = self.analyze_node(node.body)
        
        # TODO: Analizar la condición para determinar iteraciones
        return self.combine_nested("n", body_complexity)
    
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