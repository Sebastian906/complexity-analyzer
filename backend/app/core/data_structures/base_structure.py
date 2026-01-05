"""
Base Structure - Interface Base para Detectores de Estructuras de Datos

Proporciona la clase base abstracta y tipos de datos compartidos para todos
los detectores de estructuras de datos.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any

from app.core.parser.ast_nodes import ASTNode

class StructureType(Enum):
    """Tipos de estructuras de datos detectables"""
    ARRAY = "array"
    STACK = "stack"
    QUEUE = "queue"
    LINKED_LIST = "linked_list"
    DICTIONARY = "dictionary"
    TREE = "tree"
    GRAPH = "graph"
    HASH_TABLE = "hash_table"
    SET = "set"
    HEAP = "heap"
    MATRIX = "matrix"

class ConfidenceLevel(Enum):
    """Niveles de confianza en la detección"""
    VERY_HIGH = "very_high"  # 0.90 - 1.00
    HIGH = "high"            # 0.75 - 0.89
    MEDIUM = "medium"        # 0.50 - 0.74
    LOW = "low"              # 0.30 - 0.49
    VERY_LOW = "very_low"    # 0.00 - 0.29

@dataclass
class StructureIndicator:
    """
    Indicador de una estructura de datos.

    Representa una característica o patrón que sugiere el uso de una
    estructura específica.
    """
    name: str
    description: str
    found: bool = False
    weight: float = 1.0
    evidence: Optional[str] = None

    def __repr__(self) -> str:
        status = "✓" if self.found else "✗"
        return f"{status} {self.name} (peso: {self.weight})"

@dataclass
class OperationComplexity:
    """
    Complejidad de operaciones sobre una estructura.
    """
    operation: str
    best_case: str = "O(1)"
    average_case: str = "O(1)"
    worst_case: str = "O(1)"
    space: str = "O(1)"

    def __repr__(self) -> str:
        return f"{self.operation}: Best={self.best_case}, Avg={self.average_case}, Worst={self.worst_case}"

@dataclass
class StructureMatch:
    """
    Resultado de detección de una estructura de datos.

    Contiene toda la información sobre una estructura detectada incluyendo
    confianza, indicadores, operaciones y complejidades.
    """
    structure_type: StructureType
    structure_name: str
    confidence: float
    confidence_level: ConfidenceLevel = field(init=False)

    # Variables identificadas
    variables: List[str] = field(default_factory=list)

    # Indicadores encontrados y faltantes
    indicators_found: List[StructureIndicator] = field(default_factory=list)
    indicators_missing: List[StructureIndicator] = field(default_factory=list)

    # Operaciones detectadas
    operations: List[str] = field(default_factory=list)

    # Complejidades de operaciones
    operation_complexities: List[OperationComplexity] = field(default_factory=list)

    # Explicación del razonamiento
    reasoning: str = ""

    # Características específicas
    properties: Dict[str, Any] = field(default_factory=dict)

    # Evidencia del código
    code_evidence: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Calcula el nivel de confianza basado en el score"""
        if self.confidence >= 0.90:
            self.confidence_level = ConfidenceLevel.VERY_HIGH
        elif self.confidence >= 0.75:
            self.confidence_level = ConfidenceLevel.HIGH
        elif self.confidence >= 0.50:
            self.confidence_level = ConfidenceLevel.MEDIUM
        elif self.confidence >= 0.30:
            self.confidence_level = ConfidenceLevel.LOW
        else:
            self.confidence_level = ConfidenceLevel.VERY_LOW

    def get_summary(self) -> str:
        """Retorna un resumen legible del match"""
        vars_str = ", ".join(self.variables) if self.variables else "N/A"
        ops_str = ", ".join(self.operations[:5]) if self.operations else "ninguna"
        
        summary = f"""
            Estructura: {self.structure_name}
            Confianza: {self.confidence:.2%} ({self.confidence_level.value})
            Variables: {vars_str}
            Operaciones: {ops_str}
            Indicadores: {len(self.indicators_found)}/{len(self.indicators_found) + len(self.indicators_missing)}
        """
        return summary.strip()

class BaseStructureDetector(ABC):
    """
    Clase base abstracta para detectores de estructuras de datos.

    Todos los detectores específicos deben heredar de esta clase e implementar
    el método detect().
    """

    def __init__(self):
        self.structure_type: StructureType = StructureType.ARRAY
        self.structure_name: str = "Estructura Base"
        self.description: str = ""
        self.indicators: List[StructureIndicator] = []
        self.operation_complexities: List[OperationComplexity] = []

    @abstractmethod
    def detect(self, ast: ASTNode) -> Optional[StructureMatch]:
        """
        Detecta si el AST contiene esta estructura de datos.

        Args:
            ast: Nodo raíz del Abstract Syntax Tree

        Returns:
            StructureMatch si se detecta, None si no
        """
        pass

    def _calculate_confidence(self, indicators: List[StructureIndicator]) -> float:
        """
        Calcula el score de confianza basado en indicadores.

        Args:
            indicators: Lista de indicadores evaluados

        Returns:
            Score de confianza entre 0.0 y 1.0
        """
        if not indicators:
            return 0.0

        total_weight = sum(ind.weight for ind in indicators)
        found_weight = sum(ind.weight for ind in indicators if ind.found)

        if total_weight == 0:
            return 0.0

        return found_weight / total_weight

    def _split_indicators(
        self, 
        indicators: List[StructureIndicator]
    ) -> tuple[List[StructureIndicator], List[StructureIndicator]]:
        """
        Separa indicadores encontrados de los faltantes.

        Args:
            indicators: Lista de todos los indicadores

        Returns:
            Tupla (found, missing)
        """
        found = [ind for ind in indicators if ind.found]
        missing = [ind for ind in indicators if not ind.found]
        return found, missing

    def _build_reasoning(
        self,
        found: List[StructureIndicator],
        missing: List[StructureIndicator]
    ) -> str:
        """
        Construye el razonamiento de la detección.

        Args:
            found: Indicadores encontrados
            missing: Indicadores faltantes

        Returns:
            String con el razonamiento
        """
        reasoning_parts = []

        if found:
            reasoning_parts.append(
                f"Se encontraron {len(found)} indicadores clave: " +
                ", ".join(ind.name for ind in found[:3])
            )

        if missing:
            reasoning_parts.append(
                f"Faltan {len(missing)} indicadores opcionales: " +
                ", ".join(ind.name for ind in missing[:2])
            )

        return ". ".join(reasoning_parts)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.structure_name}>"