"""
Complexity Mapper - Mapeo de Estructuras a Complejidades

Mapea estructuras de datos detectadas a sus complejidades
para operaciones comunes (inserción, búsqueda, eliminación, etc.).

Proporciona información precisa sobre la complejidad temporal y espacial
de operaciones en diferentes estructuras de datos.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

from app.core.data_structures.base_structure import StructureType
from app.utils.logger import get_logger

logger = get_logger(__name__)

# OPERATION TYPES
class OperationType(str, Enum):
    """Tipos de operaciones en estructuras de datos"""
    ACCESS = "access"           # Acceso a elemento
    SEARCH = "search"           # Búsqueda
    INSERT = "insert"           # Inserción
    DELETE = "delete"           # Eliminación
    APPEND = "append"           # Agregar al final
    PREPEND = "prepend"         # Agregar al inicio
    POP = "pop"                 # Eliminar del final
    SHIFT = "shift"             # Eliminar del inicio
    PEEK = "peek"               # Ver elemento sin eliminar
    UPDATE = "update"           # Actualizar elemento
    TRAVERSE = "traverse"       # Recorrido completo
    SORT = "sort"               # Ordenamiento
    MERGE = "merge"             # Fusión

# COMPLEXITY DATA
@dataclass
class OperationComplexity:
    """Complejidad de una operación específica"""
    best_case: str              # Mejor caso (Omega)
    average_case: str           # Caso promedio (Theta)
    worst_case: str             # Peor caso (Big O)
    space_complexity: str       # Complejidad espacial
    notes: Optional[str] = None # Notas adicionales


@dataclass
class StructureComplexities:
    """Complejidades de todas las operaciones de una estructura"""
    structure_name: str
    structure_type: StructureType
    operations: Dict[OperationType, OperationComplexity]
    space_complexity: str       # Complejidad espacial general
    description: str

# COMPLEXITY MAPPER
class ComplexityMapper:
    """
    Mapea estructuras de datos a sus complejidades de operaciones.
    
    Proporciona información detallada sobre la complejidad temporal
    y espacial de operaciones comunes en diferentes estructuras.
    """
    
    # Mapeo completo de complejidades
    COMPLEXITY_MAP: Dict[StructureType, StructureComplexities] = {
        
        # ARRAY / LISTA
        StructureType.ARRAY: StructureComplexities(
            structure_name="Array/Lista",
            structure_type=StructureType.ARRAY,
            space_complexity="O(n)",
            description="Colección ordenada de elementos con acceso indexado",
            operations={
                OperationType.ACCESS: OperationComplexity(
                    best_case="Θ(1)",
                    average_case="Θ(1)",
                    worst_case="O(1)",
                    space_complexity="O(1)",
                    notes="Acceso directo por índice"
                ),
                OperationType.SEARCH: OperationComplexity(
                    best_case="Ω(1)",
                    average_case="Θ(n)",
                    worst_case="O(n)",
                    space_complexity="O(1)",
                    notes="Búsqueda lineal en array no ordenado"
                ),
                OperationType.INSERT: OperationComplexity(
                    best_case="Ω(1)",
                    average_case="Θ(n)",
                    worst_case="O(n)",
                    space_complexity="O(1)",
                    notes="O(1) al final, O(n) en posición arbitraria"
                ),
                OperationType.DELETE: OperationComplexity(
                    best_case="Ω(1)",
                    average_case="Θ(n)",
                    worst_case="O(n)",
                    space_complexity="O(1)",
                    notes="O(1) al final, O(n) en posición arbitraria"
                ),
                OperationType.APPEND: OperationComplexity(
                    best_case="Θ(1)",
                    average_case="Θ(1)",
                    worst_case="O(1)",
                    space_complexity="O(1)",
                    notes="Amortizado O(1) con dynamic array"
                ),
            }
        ),
        
        # STACK (PILA)
        StructureType.STACK: StructureComplexities(
            structure_name="Stack (Pila)",
            structure_type=StructureType.STACK,
            space_complexity="O(n)",
            description="LIFO - Last In First Out",
            operations={
                OperationType.PEEK: OperationComplexity(
                    best_case="Θ(1)",
                    average_case="Θ(1)",
                    worst_case="O(1)",
                    space_complexity="O(1)",
                    notes="Ver elemento del tope"
                ),
                OperationType.INSERT: OperationComplexity(
                    best_case="Θ(1)",
                    average_case="Θ(1)",
                    worst_case="O(1)",
                    space_complexity="O(1)",
                    notes="Push al tope"
                ),
                OperationType.DELETE: OperationComplexity(
                    best_case="Θ(1)",
                    average_case="Θ(1)",
                    worst_case="O(1)",
                    space_complexity="O(1)",
                    notes="Pop del tope"
                ),
                OperationType.SEARCH: OperationComplexity(
                    best_case="Ω(1)",
                    average_case="Θ(n)",
                    worst_case="O(n)",
                    space_complexity="O(1)",
                    notes="Requiere pop hasta encontrar"
                ),
            }
        ),
        
        # QUEUE (COLA)
        StructureType.QUEUE: StructureComplexities(
            structure_name="Queue (Cola)",
            structure_type=StructureType.QUEUE,
            space_complexity="O(n)",
            description="FIFO - First In First Out",
            operations={
                OperationType.PEEK: OperationComplexity(
                    best_case="Θ(1)",
                    average_case="Θ(1)",
                    worst_case="O(1)",
                    space_complexity="O(1)",
                    notes="Ver primer elemento"
                ),
                OperationType.INSERT: OperationComplexity(
                    best_case="Θ(1)",
                    average_case="Θ(1)",
                    worst_case="O(1)",
                    space_complexity="O(1)",
                    notes="Enqueue al final"
                ),
                OperationType.DELETE: OperationComplexity(
                    best_case="Θ(1)",
                    average_case="Θ(1)",
                    worst_case="O(1)",
                    space_complexity="O(1)",
                    notes="Dequeue del inicio"
                ),
                OperationType.SEARCH: OperationComplexity(
                    best_case="Ω(1)",
                    average_case="Θ(n)",
                    worst_case="O(n)",
                    space_complexity="O(1)",
                    notes="Búsqueda lineal"
                ),
            }
        ),
        
        # LINKED LIST
        StructureType.LINKED_LIST: StructureComplexities(
            structure_name="Linked List",
            structure_type=StructureType.LINKED_LIST,
            space_complexity="O(n)",
            description="Lista enlazada simple o doble",
            operations={
                OperationType.ACCESS: OperationComplexity(
                    best_case="Ω(1)",
                    average_case="Θ(n)",
                    worst_case="O(n)",
                    space_complexity="O(1)",
                    notes="Requiere traversal"
                ),
                OperationType.SEARCH: OperationComplexity(
                    best_case="Ω(1)",
                    average_case="Θ(n)",
                    worst_case="O(n)",
                    space_complexity="O(1)",
                    notes="Búsqueda lineal"
                ),
                OperationType.INSERT: OperationComplexity(
                    best_case="Ω(1)",
                    average_case="Θ(1)",
                    worst_case="O(1)",
                    space_complexity="O(1)",
                    notes="O(1) en head/tail, O(n) en posición arbitraria"
                ),
                OperationType.DELETE: OperationComplexity(
                    best_case="Ω(1)",
                    average_case="Θ(1)",
                    worst_case="O(1)",
                    space_complexity="O(1)",
                    notes="O(1) si se tiene referencia al nodo"
                ),
            }
        ),
        
        # HASH TABLE
        StructureType.HASH_TABLE: StructureComplexities(
            structure_name="Hash Table (Diccionario)",
            structure_type=StructureType.HASH_TABLE,
            space_complexity="O(n)",
            description="Tabla hash con función de hash",
            operations={
                OperationType.SEARCH: OperationComplexity(
                    best_case="Ω(1)",
                    average_case="Θ(1)",
                    worst_case="O(n)",
                    space_complexity="O(1)",
                    notes="O(n) en caso de muchas colisiones"
                ),
                OperationType.INSERT: OperationComplexity(
                    best_case="Ω(1)",
                    average_case="Θ(1)",
                    worst_case="O(n)",
                    space_complexity="O(1)",
                    notes="Amortizado O(1) con buen factor de carga"
                ),
                OperationType.DELETE: OperationComplexity(
                    best_case="Ω(1)",
                    average_case="Θ(1)",
                    worst_case="O(n)",
                    space_complexity="O(1)",
                    notes="Depende de la resolución de colisiones"
                ),
                OperationType.ACCESS: OperationComplexity(
                    best_case="Ω(1)",
                    average_case="Θ(1)",
                    worst_case="O(n)",
                    space_complexity="O(1)",
                    notes="Similar a búsqueda"
                ),
            }
        ),
        
        # BINARY SEARCH TREE
        StructureType.BINARY_TREE: StructureComplexities(
            structure_name="Binary Search Tree",
            structure_type=StructureType.BINARY_TREE,
            space_complexity="O(n)",
            description="Árbol binario de búsqueda",
            operations={
                OperationType.SEARCH: OperationComplexity(
                    best_case="Ω(1)",
                    average_case="Θ(log n)",
                    worst_case="O(n)",
                    space_complexity="O(1)",
                    notes="O(n) en árbol desbalanceado"
                ),
                OperationType.INSERT: OperationComplexity(
                    best_case="Ω(1)",
                    average_case="Θ(log n)",
                    worst_case="O(n)",
                    space_complexity="O(1)",
                    notes="O(n) en árbol desbalanceado"
                ),
                OperationType.DELETE: OperationComplexity(
                    best_case="Ω(1)",
                    average_case="Θ(log n)",
                    worst_case="O(n)",
                    space_complexity="O(1)",
                    notes="O(n) en árbol desbalanceado"
                ),
                OperationType.TRAVERSE: OperationComplexity(
                    best_case="Θ(n)",
                    average_case="Θ(n)",
                    worst_case="O(n)",
                    space_complexity="O(h)",
                    notes="h = altura del árbol (espacio para recursión)"
                ),
            }
        ),
        
        # HEAP
        StructureType.HEAP: StructureComplexities(
            structure_name="Heap (Montículo)",
            structure_type=StructureType.HEAP,
            space_complexity="O(n)",
            description="Min-heap o Max-heap",
            operations={
                OperationType.ACCESS: OperationComplexity(
                    best_case="Θ(1)",
                    average_case="Θ(1)",
                    worst_case="O(1)",
                    space_complexity="O(1)",
                    notes="Solo el mínimo/máximo"
                ),
                OperationType.SEARCH: OperationComplexity(
                    best_case="Ω(1)",
                    average_case="Θ(n)",
                    worst_case="O(n)",
                    space_complexity="O(1)",
                    notes="Búsqueda lineal"
                ),
                OperationType.INSERT: OperationComplexity(
                    best_case="Ω(1)",
                    average_case="Θ(log n)",
                    worst_case="O(log n)",
                    space_complexity="O(1)",
                    notes="Heapify up"
                ),
                OperationType.DELETE: OperationComplexity(
                    best_case="Ω(log n)",
                    average_case="Θ(log n)",
                    worst_case="O(log n)",
                    space_complexity="O(1)",
                    notes="Extract min/max + heapify down"
                ),
            }
        ),
        
        # GRAPH
        StructureType.GRAPH: StructureComplexities(
            structure_name="Graph (Grafo)",
            structure_type=StructureType.GRAPH,
            space_complexity="O(V + E)",
            description="Grafo (lista de adyacencia o matriz)",
            operations={
                OperationType.ACCESS: OperationComplexity(
                    best_case="Θ(1)",
                    average_case="Θ(1)",
                    worst_case="O(1)",
                    space_complexity="O(1)",
                    notes="Acceso a vértice (lista de adyacencia)"
                ),
                OperationType.SEARCH: OperationComplexity(
                    best_case="Ω(1)",
                    average_case="Θ(V + E)",
                    worst_case="O(V + E)",
                    space_complexity="O(V)",
                    notes="DFS o BFS"
                ),
                OperationType.INSERT: OperationComplexity(
                    best_case="Θ(1)",
                    average_case="Θ(1)",
                    worst_case="O(1)",
                    space_complexity="O(1)",
                    notes="Agregar arista (lista de adyacencia)"
                ),
                OperationType.DELETE: OperationComplexity(
                    best_case="Θ(1)",
                    average_case="Θ(E)",
                    worst_case="O(E)",
                    space_complexity="O(1)",
                    notes="Eliminar vértice requiere actualizar aristas"
                ),
                OperationType.TRAVERSE: OperationComplexity(
                    best_case="Θ(V + E)",
                    average_case="Θ(V + E)",
                    worst_case="O(V + E)",
                    space_complexity="O(V)",
                    notes="DFS o BFS completo"
                ),
            }
        ),
    }
    
    @classmethod
    def get_structure_complexities(
        cls,
        structure_type: StructureType
    ) -> Optional[StructureComplexities]:
        """
        Obtener todas las complejidades de una estructura.
        
        Args:
            structure_type: Tipo de estructura
        
        Returns:
            StructureComplexities con toda la información
        
        Example:
            >>> mapper = ComplexityMapper()
            >>> complexities = mapper.get_structure_complexities(StructureType.ARRAY)
            >>> print(complexities.operations[OperationType.ACCESS].worst_case)
            'O(1)'
        """
        return cls.COMPLEXITY_MAP.get(structure_type)
    
    @classmethod
    def get_operation_complexity(
        cls,
        structure_type: StructureType,
        operation: OperationType
    ) -> Optional[OperationComplexity]:
        """
        Obtener complejidad de una operación específica.
        
        Args:
            structure_type: Tipo de estructura
            operation: Tipo de operación
        
        Returns:
            OperationComplexity o None si no existe
        
        Example:
            >>> mapper = ComplexityMapper()
            >>> complexity = mapper.get_operation_complexity(
            ...     StructureType.HASH_TABLE,
            ...     OperationType.SEARCH
            ... )
            >>> print(complexity.average_case)  # 'Θ(1)'
        """
        structure_complexities = cls.get_structure_complexities(structure_type)
        if not structure_complexities:
            return None
        
        return structure_complexities.operations.get(operation)
    
    @classmethod
    def get_worst_case(
        cls,
        structure_type: StructureType,
        operation: OperationType
    ) -> Optional[str]:
        """
        Obtener solo el peor caso de una operación.
        
        Args:
            structure_type: Tipo de estructura
            operation: Tipo de operación
        
        Returns:
            str con notación Big O o None
        """
        complexity = cls.get_operation_complexity(structure_type, operation)
        return complexity.worst_case if complexity else None
    
    @classmethod
    def compare_structures(
        cls,
        operation: OperationType,
        structures: List[StructureType]
    ) -> Dict[StructureType, str]:
        """
        Comparar complejidad de una operación entre varias estructuras.
        
        Args:
            operation: Operación a comparar
            structures: Lista de estructuras a comparar
        
        Returns:
            Dict con estructura -> peor caso
        
        Example:
            >>> mapper = ComplexityMapper()
            >>> comparison = mapper.compare_structures(
            ...     OperationType.SEARCH,
            ...     [StructureType.ARRAY, StructureType.HASH_TABLE]
            ... )
            >>> print(comparison)
            {StructureType.ARRAY: 'O(n)', StructureType.HASH_TABLE: 'O(1)'}
        """
        result = {}
        
        for structure in structures:
            worst_case = cls.get_worst_case(structure, operation)
            if worst_case:
                result[structure] = worst_case
        
        return result
    
    @classmethod
    def get_space_complexity(cls, structure_type: StructureType) -> Optional[str]:
        """
        Obtener complejidad espacial general de una estructura.
        
        Args:
            structure_type: Tipo de estructura
        
        Returns:
            str con notación Big O
        """
        structure_complexities = cls.get_structure_complexities(structure_type)
        return structure_complexities.space_complexity if structure_complexities else None
    
    @classmethod
    def generate_summary(cls, structure_type: StructureType) -> str:
        """
        Generar resumen de complejidades de una estructura.
        
        Args:
            structure_type: Tipo de estructura
        
        Returns:
            str con resumen formateado
        """
        complexities = cls.get_structure_complexities(structure_type)
        if not complexities:
            return f"No hay información de complejidad para {structure_type}"
        
        summary_lines = [
            f"=== {complexities.structure_name} ===",
            f"Descripción: {complexities.description}",
            f"Complejidad Espacial: {complexities.space_complexity}",
            "",
            "Operaciones:",
        ]
        
        for operation, complexity in complexities.operations.items():
            summary_lines.append(f"  {operation.value.capitalize()}:")
            summary_lines.append(f"    - Peor caso: {complexity.worst_case}")
            summary_lines.append(f"    - Caso promedio: {complexity.average_case}")
            summary_lines.append(f"    - Mejor caso: {complexity.best_case}")
            if complexity.notes:
                summary_lines.append(f"    - Notas: {complexity.notes}")
            summary_lines.append("")
        
        return "\n".join(summary_lines)

# HELPER FUNCTIONS
def map_structure_to_complexity(
    structure_type: StructureType,
    operation: OperationType
) -> Optional[OperationComplexity]:
    """
    Helper function para mapeo rápido.
    
    Args:
        structure_type: Tipo de estructura
        operation: Tipo de operación
    
    Returns:
        OperationComplexity o None
    
    Example:
        >>> from app.core.data_structures.complexity_mapper import map_structure_to_complexity
        >>> complexity = map_structure_to_complexity(
        ...     StructureType.STACK,
        ...     OperationType.INSERT
        ... )
        >>> print(complexity.worst_case)  # 'O(1)'
    """
    return ComplexityMapper.get_operation_complexity(structure_type, operation)