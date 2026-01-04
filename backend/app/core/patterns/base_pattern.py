"""
Base Pattern - Interface para Detectores de Patrones

Define la interfaz abstracta que deben implementar todos los detectores
de patrones algorítmicos.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any, Optional

from app.core.parser.ast_nodes import ASTNode
from app.core.patterns.pattern_matcher import get_node_children

class PatternType(str, Enum):
    """Tipos de patrones algorítmicos detectables"""
    BRUTE_FORCE = "brute_force"
    RECURSIVE = "recursive"
    DIVIDE_AND_CONQUER = "divide_and_conquer"
    DYNAMIC_PROGRAMMING = "dynamic_programming"
    GREEDY = "greedy"
    BACKTRACKING = "backtracking"
    BRANCH_AND_BOUND = "branch_and_bound"
    SORTING = "sorting"
    SEARCHING = "searching"
    QUANTUM = "quantum"
    BIO_INSPIRED = "bio_inspired"
    APPROXIMATION = "approximation"

class ConfidenceLevel(str, Enum):
    """Niveles de confianza en la detección"""
    VERY_LOW = "very_low"      # < 0.3
    LOW = "low"                # 0.3 - 0.5
    MEDIUM = "medium"          # 0.5 - 0.7
    HIGH = "high"              # 0.7 - 0.9
    VERY_HIGH = "very_high"    # >= 0.9

@dataclass
class PatternIndicator:
    """
    Indicador individual de un patrón.

    Representa una característica o señal específica que sugiere
    la presencia de un patrón.
    """
    name: str
    description: str
    found: bool
    weight: float = 1.0
    evidence: Optional[str] = None
    location: Optional[str] = None  # Línea o nodo AST donde se encontró

    def __str__(self) -> str:
        status = "✓" if self.found else "✗"
        return f"{status} {self.name}: {self.description}"

@dataclass
class PatternMatch:
    """
    Resultado de la detección de un patrón.

    Encapsula toda la información sobre un patrón detectado,
    incluyendo confianza, evidencias e indicadores.
    """
    pattern_type: PatternType
    pattern_name: str
    confidence: float
    confidence_level: ConfidenceLevel

    # Indicadores que se encontraron
    indicators_found: List[PatternIndicator]

    # Indicadores que no se encontraron pero se esperaban
    indicators_missing: List[PatternIndicator]

    # Explicación del porqué se detectó este patrón
    reasoning: str

    # Complejidad típica asociada con este patrón
    typical_complexity: Optional[str] = None

    # Metadatos adicionales
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

        # Calcular nivel de confianza si no se proporcionó
        if isinstance(self.confidence_level, str):
            self.confidence_level = self._calculate_confidence_level()

    def _calculate_confidence_level(self) -> ConfidenceLevel:
        """Calcula el nivel de confianza basado en el score"""
        if self.confidence >= 0.9:
            return ConfidenceLevel.VERY_HIGH
        elif self.confidence >= 0.7:
            return ConfidenceLevel.HIGH
        elif self.confidence >= 0.5:
            return ConfidenceLevel.MEDIUM
        elif self.confidence >= 0.3:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW

    @property
    def is_confident(self) -> bool:
        """Retorna True si la confianza es alta (>= 0.7)"""
        return self.confidence >= 0.7

    @property
    def total_indicators(self) -> int:
        """Total de indicadores evaluados"""
        return len(self.indicators_found) + len(self.indicators_missing)

    @property
    def found_ratio(self) -> float:
        """Proporción de indicadores encontrados"""
        total = self.total_indicators
        return len(self.indicators_found) / total if total > 0 else 0.0

class BasePatternDetector(ABC):
    """
    Clase base abstracta para todos los detectores de patrones.

    Define la interfaz común que deben implementar todos los detectores
    específicos de patrones algorítmicos.
    """

    def __init__(self):
        self.pattern_type: PatternType = None
        self.pattern_name: str = ""
        self.description: str = ""
        self.typical_complexity: str = ""

        # Indicadores que se buscarán
        self._indicators: List[PatternIndicator] = []

    @abstractmethod
    def detect(self, ast: ASTNode) -> PatternMatch:
        """
        Detecta si el patrón está presente en el AST.

        Args:
            ast: Nodo raíz del Abstract Syntax Tree

        Returns:
            PatternMatch con el resultado de la detección
        """
        pass

    @abstractmethod
    def _analyze_structure(self, ast: ASTNode) -> Dict[str, Any]:
        """
        Analiza la estructura del AST buscando características del patrón.

        Args:
            ast: Nodo raíz del AST

        Returns:
            Diccionario con características encontradas
        """
        pass

    def _calculate_confidence(
        self,
        indicators_found: List[PatternIndicator],
        indicators_missing: List[PatternIndicator]
    ) -> float:
        """
        Calcula el score de confianza basado en indicadores.
        
        Formula: suma de pesos de indicadores encontrados / suma total de pesos

        Args:
            indicators_found: Lista de indicadores encontrados
            indicators_missing: Lista de indicadores no encontrados

        Returns:
            Score entre 0.0 y 1.0
        """
        total_weight = sum(
            ind.weight for ind in indicators_found + indicators_missing
        )

        if total_weight == 0:
            return 0.0

        found_weight = sum(ind.weight for ind in indicators_found)

        return found_weight / total_weight

    def _create_match(
        self,
        confidence: float,
        indicators_found: List[PatternIndicator],
        indicators_missing: List[PatternIndicator],
        reasoning: str,
        **metadata
    ) -> PatternMatch:
        """
        Helper para crear un PatternMatch.

        Args:
            confidence: Score de confianza (0.0 - 1.0)
            indicators_found: Indicadores encontrados
            indicators_missing: Indicadores faltantes
            reasoning: Explicación de la detección
            **metadata: Metadatos adicionales

        Returns:
            PatternMatch configurado
        """
        return PatternMatch(
            pattern_type=self.pattern_type,
            pattern_name=self.pattern_name,
            confidence=confidence,
            confidence_level=self._get_confidence_level(confidence),
            indicators_found=indicators_found,
            indicators_missing=indicators_missing,
            reasoning=reasoning,
            typical_complexity=self.typical_complexity,
            metadata=metadata
        )

    def _get_confidence_level(self, confidence: float) -> ConfidenceLevel:
        """Mapea score a nivel de confianza"""
        if confidence >= 0.9:
            return ConfidenceLevel.VERY_HIGH
        elif confidence >= 0.7:
            return ConfidenceLevel.HIGH
        elif confidence >= 0.5:
            return ConfidenceLevel.MEDIUM
        elif confidence >= 0.3:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW

    def _find_recursive_calls(self, node: ASTNode, func_name: str) -> int:
        """
        Encuentra llamadas recursivas en el AST.

        Args:
            node: Nodo a analizar
            func_name: Nombre de la función a buscar

        Returns:
            Número de llamadas recursivas encontradas
        """
        from app.core.parser.ast_nodes import CallStatementNode

        count = 0

        if isinstance(node, CallStatementNode):
            if node.function_name == func_name:
                count += 1

        # Recursivamente buscar en hijos
        for child in get_node_children(node):
            count += self._find_recursive_calls(child, func_name)

        return count

    def _count_nested_loops(self, node: ASTNode) -> int:
        """
        Cuenta la profundidad máxima de loops anidados.

        Args:
            node: Nodo a analizar

        Returns:
            Profundidad máxima de anidación
        """
        from app.core.parser.ast_nodes import ForLoopNode, WhileLoopNode, RepeatLoopNode

        max_depth = 0
        current_depth = 0

        def _traverse(n: ASTNode, depth: int):
            nonlocal max_depth

            if isinstance(n, (ForLoopNode, WhileLoopNode, RepeatLoopNode)):
                depth += 1
                max_depth = max(max_depth, depth)

            for child in get_node_children(n):
                _traverse(child, depth)

        _traverse(node, current_depth)
        return max_depth

    def _has_memoization(self, node: ASTNode) -> bool:
        """
        Detecta si hay memoización (arrays/dicts usados para almacenar resultados).

        Args:
            node: Nodo a analizar

        Returns:
            True si se detecta memoización
        """
        from app.core.parser.ast_nodes import (
            AssignmentNode, 
            ArrayAccessNode,
            VariableNode
        )

        # Buscar patrones como: memo[i] = ...
        # o: if memo[i] != -1 then ...

        memo_arrays = set()

        def _traverse(n: ASTNode):
            if isinstance(n, AssignmentNode):
                # Check si el target es array access
                if isinstance(n.target, ArrayAccessNode):
                    array_name = n.target.array.name if isinstance(n.target.array, VariableNode) else None
                    if array_name:
                        memo_arrays.add(array_name)
                # También verificar si target es LValueNode con indices
                elif hasattr(n.target, 'access_type') and n.target.access_type == 'array':
                    memo_arrays.add(n.target.name)
            
            for child in get_node_children(n):
                _traverse(child)

        _traverse(node)

        return len(memo_arrays) > 0

    def __str__(self) -> str:
        return f"{self.pattern_name} Detector"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(type={self.pattern_type.value})>"