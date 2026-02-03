"""
Analizador Base Abstracto

Define la interfaz base para todos los analizadores de complejidad.
Implementa el patrón Strategy para diferentes tipos de análisis.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from dataclasses import dataclass

from app.core.parser.ast_nodes import (
    ASTNode, ForLoopNode, WhileLoopNode, RepeatLoopNode,
    IfStatementNode, AssignmentNode, CallStatementNode, BlockNode
)
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class ComplexityResult:
    """Resultado del análisis de complejidad"""
    complexity: str  # "n", "n^2", "log n", etc.
    notation: str    # "O", "Ω", "Θ"
    explanation: str = ""
    confidence: float = 1.0
    
    def __str__(self):
        return f"{self.notation}({self.complexity})"


class BaseComplexityAnalyzer(ABC):
    """
    Clase base abstracta para analizadores de complejidad.
    
    Todos los analizadores (BigO, Omega, Theta) heredan de esta clase.
    """
    
    def __init__(self):
        self.logger = setup_logger(self.__class__.__name__)
    
    @abstractmethod
    def analyze(self, ast: ASTNode) -> ComplexityResult:
        """Analiza el AST completo y retorna la complejidad"""
        pass
    
    @abstractmethod
    def analyze_node(self, node: ASTNode) -> str:
        """Analiza un nodo específico del AST"""
        pass
    
    # Métodos compartidos por todos los analizadores
    
    def analyze_block(self, block: BlockNode) -> str:
        """
        Analiza un bloque de statements.
        
        Regla: O(f(n)) + O(g(n)) = O(max(f(n), g(n)))
        """
        if not block.statements:
            return "1"
        
        complexities = [self.analyze_node(stmt) for stmt in block.statements]
        return self.combine_sequential(complexities)
    
    def combine_sequential(self, complexities: List[str]) -> str:
        """
        Combina complejidades secuenciales (suma).
        
        Toma el término dominante.
        """
        if not complexities:
            return "1"
        
        # Ordenar por complejidad (de menor a mayor)
        sorted_comp = sorted(complexities, key=self._complexity_order, reverse=True)
        
        # Retornar el dominante
        return sorted_comp[0]
    
    def combine_nested(self, outer: str, inner: str) -> str:
        """
        Combina complejidades anidadas (multiplicación).
        
        O(f(n)) * O(g(n)) = O(f(n) * g(n))
        """
        # Casos especiales
        if outer == "1":
            return inner
        if inner == "1":
            return outer
        
        # Multiplicar
        return self._multiply_complexities(outer, inner)
    
    def _complexity_order(self, complexity: str) -> int:
        """Ordena complejidades para comparación (menor a mayor)"""
        order_map = {
            "1": 0,
            "log n": 1,
            "sqrt n": 2,
            "n": 3,
            "n log n": 4,
            "n^2": 5,
            "n^3": 6,
            "2^n": 7,
            "n!": 8,
        }
        return order_map.get(complexity, 999)
    
    def _multiply_complexities(self, c1: str, c2: str) -> str:
        """Multiplica dos complejidades"""
        # Simplificaciones comunes
        if c1 == "n" and c2 == "n":
            return "n^2"
        if c1 == "n" and c2 == "n^2":
            return "n^3"
        if c1 == "n^2" and c2 == "n":
            return "n^3"
        if c1 == "n" and c2 == "n^3":
            return "n^4"
        if c1 == "n^3" and c2 == "n":
            return "n^4"
        if c1 == "n^2" and c2 == "n^2":
            return "n^4"
        if c1 == "n" and c2 == "log n":
            return "n log n"
        if c1 == "log n" and c2 == "n":
            return "n log n"
        if c1 == "n^2" and c2 == "log n":
            return "n^2 log n"
        if c1 == "log n" and c2 == "n^2":
            return "n^2 log n"
        
        # Por ahora, retornar concatenación
        return f"{c1} * {c2}"