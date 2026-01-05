"""
Detectors Module - Detectores Específicos de Estructuras de Datos

Cada detector se especializa en identificar una estructura particular
mediante análisis del AST.

Detectores Implementados:
- ArrayDetector: Arrays y listas
- StackDetector: Pilas (LIFO)
- QueueDetector: Colas (FIFO)
- LinkedListDetector: Listas enlazadas
- DictionaryDetector: Diccionarios/Maps
- TreeDetector: Árboles
- GraphDetector: Grafos
- HashTableDetector: Tablas hash
"""

from app.core.data_structures.detectors.array_detector import ArrayDetector
from app.core.data_structures.detectors.stack_detector import StackDetector
from app.core.data_structures.detectors.queue_detector import QueueDetector
from app.core.data_structures.detectors.linked_list_detector import LinkedListDetector
from app.core.data_structures.detectors.dictionary_detector import DictionaryDetector
from app.core.data_structures.detectors.tree_detector import TreeDetector
from app.core.data_structures.detectors.graph_detector import GraphDetector
from app.core.data_structures.detectors.hash_table_detector import HashTableDetector

__all__ = [
    "ArrayDetector",
    "StackDetector",
    "QueueDetector",
    "LinkedListDetector",
    "DictionaryDetector",
    "TreeDetector",
    "GraphDetector",
    "HashTableDetector",
]