"""
Analizador Omega (Mejor Caso)

Implementa el análisis de complejidad temporal en el mejor caso.
Analiza el escenario óptimo de ejecución del algoritmo.
"""

from app.core.analyzer.complexity.base_analyzer import (
    BaseComplexityAnalyzer, ComplexityResult
)
from app.core.parser.ast_nodes import *

class OmegaAnalyzer(BaseComplexityAnalyzer):
    """Analizador de Omega (mejor caso)"""
    
    def analyze(self, ast: ASTNode) -> ComplexityResult:
        """Analiza el algoritmo completo"""
        self.logger.info(f"Analizando Omega de: {ast.algorithm.name}")
        
        # Analizar el cuerpo del algoritmo
        body_complexity = self.analyze_node(ast.algorithm.body)
        
        return ComplexityResult(
            complexity=body_complexity,
            notation="Ω",
            explanation=f"Complejidad del mejor caso: Ω({body_complexity})"
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
        Analiza un FOR loop (mejor caso).
        
        En el mejor caso, el loop podría ejecutarse 0 veces
        o el mínimo número de iteraciones.
        """
        # Analizar el cuerpo
        body_complexity = self.analyze_node(node.body)
        
        # En el mejor caso, el loop se ejecuta al menos 1 vez
        # (a menos que start > end, pero asumimos entrada válida)
        iterations = self._calculate_iterations(node.start, node.end)
        
        return self.combine_nested(iterations, body_complexity)
    
    def _calculate_iterations(self, start, end) -> str:
        """
        Calcula el número de iteraciones en el mejor caso.
        
        En el mejor caso, asumimos el mínimo número de iteraciones.
        """
        # Si start y end son literales
        if isinstance(start, LiteralNode) and isinstance(end, LiteralNode):
            start_val = start.value
            end_val = end.value
            iterations = max(1, end_val - start_val + 1)
            return str(iterations)
        
        # En el mejor caso, el loop podría ejecutarse 1 vez
        # Pero generalmente asumimos O(n) también para Omega
        return "n"
    
    def _analyze_while_loop(self, node: WhileLoopNode) -> str:
        """
        Analiza un WHILE loop (mejor caso).
        
        En el mejor caso, podría no ejecutarse (si la condición es false).
        """
        body_complexity = self.analyze_node(node.body)
        
        # En el mejor caso, podría ser O(1) si la condición es false desde el inicio
        # Pero típicamente asumimos al menos 1 iteración
        return body_complexity  # Mejor caso: 1 iteración
    
    def _analyze_repeat_loop(self, node: RepeatLoopNode) -> str:
        """Analiza un REPEAT loop (siempre se ejecuta al menos 1 vez)"""
        # Analizar todos los statements del body
        complexities = [self.analyze_node(stmt) for stmt in node.body]
        body_complexity = self.combine_sequential(complexities)
        
        # REPEAT siempre se ejecuta al menos 1 vez
        return body_complexity
    
    def _analyze_if_statement(self, node: IfStatementNode) -> str:
        """
        Analiza un IF statement (mejor caso).
        
        En el mejor caso, tomamos el mínimo entre then y else.
        """
        then_complexity = self.analyze_node(node.then_block)
        
        if node.else_block:
            else_complexity = self.analyze_node(node.else_block)
            
            # En el mejor caso, se ejecuta el más rápido
            if self._complexity_order(then_complexity) <= self._complexity_order(else_complexity):
                return then_complexity
            else:
                return else_complexity
        
        # Si no hay else, en el mejor caso no se ejecuta nada (condición false)
        return "1"