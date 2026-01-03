"""
Analizador Theta (Caso Promedio)

Implementa el análisis de complejidad temporal en el caso promedio.
Theta existe solo cuando Big O = Omega (cota ajustada).
"""

from app.core.analyzer.complexity.base_analyzer import (
    BaseComplexityAnalyzer, ComplexityResult
)
from app.core.parser.ast_nodes import *


class ThetaAnalyzer(BaseComplexityAnalyzer):
    """
    Analizador de Theta (caso promedio).
    
    Theta existe solo si O = Ω (cota ajustada).
    """
    
    def analyze(self, ast: ASTNode) -> ComplexityResult:
        """Analiza el algoritmo completo"""
        self.logger.info(f"Analizando Theta de: {ast.algorithm.name}")
        
        # Analizar el cuerpo del algoritmo
        body_complexity = self.analyze_node(ast.algorithm.body)
        
        return ComplexityResult(
            complexity=body_complexity,
            notation="Θ",
            explanation=f"Complejidad del caso promedio: Θ({body_complexity})"
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
            return "1"
        
        elif isinstance(node, CallStatementNode):
            return "1"
        
        else:
            return "1"
    
    def _analyze_for_loop(self, node: ForLoopNode) -> str:
        """
        Analiza un FOR loop (caso promedio).
        
        En el caso promedio, asumimos la complejidad típica.
        """
        body_complexity = self.analyze_node(node.body)
        iterations = self._calculate_iterations(node.start, node.end)
        
        return self.combine_nested(iterations, body_complexity)
    
    def _calculate_iterations(self, start, end) -> str:
        """Calcula iteraciones en caso promedio"""
        if isinstance(start, LiteralNode) and isinstance(end, LiteralNode):
            start_val = start.value
            end_val = end.value
            iterations = end_val - start_val + 1
            return str(iterations)
        
        return "n"
    
    def _analyze_while_loop(self, node: WhileLoopNode) -> str:
        """Analiza un WHILE loop (caso promedio)"""
        body_complexity = self.analyze_node(node.body)
        return self.combine_nested("n", body_complexity)
    
    def _analyze_repeat_loop(self, node: RepeatLoopNode) -> str:
        """Analiza un REPEAT loop"""
        complexities = [self.analyze_node(stmt) for stmt in node.body]
        body_complexity = self.combine_sequential(complexities)
        
        return self.combine_nested("n", body_complexity)
    
    def _analyze_if_statement(self, node: IfStatementNode) -> str:
        """
        Analiza un IF statement (caso promedio).
        
        En el caso promedio, consideramos ambas ramas con probabilidad.
        Para simplificar, tomamos el máximo como en Big O.
        """
        then_complexity = self.analyze_node(node.then_block)
        
        if node.else_block:
            else_complexity = self.analyze_node(node.else_block)
            complexities = [then_complexity, else_complexity]
            return self.combine_sequential(complexities)
        
        return then_complexity