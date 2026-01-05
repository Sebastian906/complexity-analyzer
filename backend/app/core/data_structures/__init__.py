"""
Data Structures Module - Módulo de Detección de Estructuras de Datos

Proporciona detección automática de estructuras de datos utilizadas
en algoritmos mediante análisis estático del AST.

Estructuras soportadas:
- Arrays/Listas
- Pilas (Stacks)
- Colas (Queues)
- Listas Enlazadas
- Diccionarios/Maps
- Árboles
- Grafos
- Tablas Hash

Exports principales:
    - StructureIdentifier: Identificador principal
    - StructureMatch: Resultado de detección
    - StructureType: Enum de tipos de estructuras
    - identify_structures: Helper function para uso rápido
"""

# Base
from app.core.data_structures.base_structure import (
    BaseStructureDetector,
    StructureType,
    StructureMatch,
    StructureIndicator,
    OperationComplexity,
    ConfidenceLevel
)

# Identificador Principal
from app.core.data_structures.structure_identifier import (
    StructureIdentifier,
    StructureDetectionResult,
    identify_structures
)

# Usage Analyzer
from app.core.data_structures.usage_analyzer import (
    UsageAnalyzer,
    StructureUsage,
    analyze_structure_usage
)

# Detectores Específicos
from app.core.data_structures.detectors.array_detector import ArrayDetector
from app.core.data_structures.detectors.stack_detector import StackDetector
from app.core.data_structures.detectors.queue_detector import QueueDetector
from app.core.data_structures.detectors.linked_list_detector import LinkedListDetector
from app.core.data_structures.detectors.dictionary_detector import DictionaryDetector
from app.core.data_structures.detectors.tree_detector import TreeDetector
from app.core.data_structures.detectors.graph_detector import GraphDetector
from app.core.data_structures.detectors.hash_table_detector import HashTableDetector

__all__ = [
    # Base
    "BaseStructureDetector",
    "StructureType",
    "StructureMatch",
    "StructureIndicator",
    "OperationComplexity",
    "ConfidenceLevel",

    # Identificador
    "StructureIdentifier",
    "StructureDetectionResult",
    "identify_structures",

    # Usage Analyzer
    "UsageAnalyzer",
    "StructureUsage",
    "analyze_structure_usage",

    # Detectores
    "ArrayDetector",
    "StackDetector",
    "QueueDetector",
    "LinkedListDetector",
    "DictionaryDetector",
    "TreeDetector",
    "GraphDetector",
    "HashTableDetector",
]