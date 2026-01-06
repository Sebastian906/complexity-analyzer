"""
Tree Builder - Constructor de Árboles Genéricos

Proporciona estructuras base y utilidades para construir
árboles de visualización (recursión, estructuras de datos, etc.).
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar
from enum import Enum
from collections import deque

from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class NodeType(str, Enum):
    """Tipos de nodos en un árbol"""
    ROOT = "root"           # Nodo raíz
    INTERNAL = "internal"   # Nodo interno
    LEAF = "leaf"           # Nodo hoja
    CALL = "call"           # Llamada de función
    RETURN = "return"       # Retorno de función
    OPERATION = "operation" # Operación
    DECISION = "decision"   # Decisión/condicional
    LOOP = "loop"           # Bucle
    DATA = "data"           # Dato/valor

@dataclass
class TreeNode:
    """
    Nodo genérico de árbol.
    
    Clase base para todos los nodos de árboles de visualización.
    Soporta jerarquía de nodos, metadatos y conversión a diccionario.
    
    Attributes:
        id: Identificador único del nodo
        label: Etiqueta visible del nodo
        node_type: Tipo de nodo
        value: Valor asociado al nodo
        depth: Profundidad en el árbol
        parent: Nodo padre (opcional)
        children: Lista de nodos hijos
        metadata: Metadatos adicionales
    """
    id: str
    label: str
    node_type: NodeType = NodeType.INTERNAL
    value: Any = None
    depth: int = 0
    parent: Optional["TreeNode"] = field(default=None, repr=False)
    children: List["TreeNode"] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_child(self, child: "TreeNode") -> "TreeNode":
        """
        Agrega un nodo hijo.
        
        Args:
            child: Nodo hijo a agregar
            
        Returns:
            TreeNode: El nodo hijo agregado (para encadenamiento)
        """
        child.parent = self
        child.depth = self.depth + 1
        self.children.append(child)
        return child
    
    def add_children(self, children: List["TreeNode"]) -> None:
        """
        Agrega múltiples nodos hijos.
        
        Args:
            children: Lista de nodos hijos a agregar
        """
        for child in children:
            self.add_child(child)
    
    def remove_child(self, child: "TreeNode") -> bool:
        """
        Elimina un nodo hijo.
        
        Args:
            child: Nodo hijo a eliminar
            
        Returns:
            bool: True si se eliminó, False si no existía
        """
        if child in self.children:
            self.children.remove(child)
            child.parent = None
            return True
        return False
    
    def is_root(self) -> bool:
        """Verifica si es nodo raíz"""
        return self.parent is None
    
    def is_leaf(self) -> bool:
        """Verifica si es nodo hoja"""
        return len(self.children) == 0
    
    def max_depth(self) -> int:
        """
        Calcula la profundidad máxima del subárbol.
        
        Returns:
            int: Profundidad máxima desde este nodo
        """
        if not self.children:
            return self.depth
        return max(child.max_depth() for child in self.children)
    
    def height(self) -> int:
        """
        Calcula la altura del subárbol (desde este nodo).
        
        Returns:
            int: Altura del subárbol
        """
        if not self.children:
            return 0
        return 1 + max(child.height() for child in self.children)
    
    def size(self) -> int:
        """
        Cuenta el número total de nodos en el subárbol.
        
        Returns:
            int: Número total de nodos
        """
        return 1 + sum(child.size() for child in self.children)
    
    def count_leaves(self) -> int:
        """
        Cuenta el número de hojas en el subárbol.
        
        Returns:
            int: Número de hojas
        """
        if self.is_leaf():
            return 1
        return sum(child.count_leaves() for child in self.children)
    
    def get_path_to_root(self) -> List["TreeNode"]:
        """
        Obtiene el camino desde este nodo hasta la raíz.
        
        Returns:
            List[TreeNode]: Lista de nodos desde este hasta la raíz
        """
        path = [self]
        current = self.parent
        while current is not None:
            path.append(current)
            current = current.parent
        return path
    
    def get_ancestors(self) -> List["TreeNode"]:
        """
        Obtiene todos los ancestros del nodo.
        
        Returns:
            List[TreeNode]: Lista de ancestros (sin incluir este nodo)
        """
        return self.get_path_to_root()[1:]
    
    def get_siblings(self) -> List["TreeNode"]:
        """
        Obtiene los hermanos del nodo.
        
        Returns:
            List[TreeNode]: Lista de hermanos
        """
        if self.parent is None:
            return []
        return [child for child in self.parent.children if child is not self]
    
    def get_descendants(self) -> List["TreeNode"]:
        """
        Obtiene todos los descendientes del nodo.
        
        Returns:
            List[TreeNode]: Lista de todos los descendientes
        """
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants
    
    def find_by_id(self, node_id: str) -> Optional["TreeNode"]:
        """
        Busca un nodo por ID en el subárbol.
        
        Args:
            node_id: ID del nodo a buscar
            
        Returns:
            TreeNode o None si no se encuentra
        """
        if self.id == node_id:
            return self
        for child in self.children:
            result = child.find_by_id(node_id)
            if result is not None:
                return result
        return None
    
    def find_by_value(self, value: Any) -> List["TreeNode"]:
        """
        Busca nodos por valor en el subárbol.
        
        Args:
            value: Valor a buscar
            
        Returns:
            List[TreeNode]: Lista de nodos con ese valor
        """
        matches = []
        if self.value == value:
            matches.append(self)
        for child in self.children:
            matches.extend(child.find_by_value(value))
        return matches
    
    def traverse_preorder(self) -> List["TreeNode"]:
        """
        Recorre el árbol en preorden (raíz, hijos).
        
        Returns:
            List[TreeNode]: Nodos en preorden
        """
        nodes = [self]
        for child in self.children:
            nodes.extend(child.traverse_preorder())
        return nodes
    
    def traverse_postorder(self) -> List["TreeNode"]:
        """
        Recorre el árbol en postorden (hijos, raíz).
        
        Returns:
            List[TreeNode]: Nodos en postorden
        """
        nodes = []
        for child in self.children:
            nodes.extend(child.traverse_postorder())
        nodes.append(self)
        return nodes
    
    def traverse_levelorder(self) -> List["TreeNode"]:
        """
        Recorre el árbol por niveles (BFS).
        
        Returns:
            List[TreeNode]: Nodos por niveles
        """
        nodes = []
        queue = deque([self])
        while queue:
            node = queue.popleft()
            nodes.append(node)
            queue.extend(node.children)
        return nodes
    
    def get_nodes_at_level(self, level: int) -> List["TreeNode"]:
        """
        Obtiene todos los nodos en un nivel específico.
        
        Args:
            level: Nivel a obtener (0 = raíz)
            
        Returns:
            List[TreeNode]: Nodos en ese nivel
        """
        if self.depth == level:
            return [self]
        nodes = []
        for child in self.children:
            nodes.extend(child.get_nodes_at_level(level))
        return nodes
    
    def map(self, func: Callable[["TreeNode"], Any]) -> List[Any]:
        """
        Aplica una función a todos los nodos del subárbol.
        
        Args:
            func: Función a aplicar
            
        Returns:
            List[Any]: Resultados de aplicar la función
        """
        return [func(node) for node in self.traverse_preorder()]
    
    def filter(self, predicate: Callable[["TreeNode"], bool]) -> List["TreeNode"]:
        """
        Filtra nodos según un predicado.
        
        Args:
            predicate: Función que retorna True para nodos a incluir
            
        Returns:
            List[TreeNode]: Nodos que cumplen el predicado
        """
        return [node for node in self.traverse_preorder() if predicate(node)]
    
    def copy(self, deep: bool = True) -> "TreeNode":
        """
        Crea una copia del nodo.
        
        Args:
            deep: Si es True, copia recursivamente los hijos
            
        Returns:
            TreeNode: Copia del nodo
        """
        new_node = TreeNode(
            id=self.id,
            label=self.label,
            node_type=self.node_type,
            value=self.value,
            depth=self.depth,
            metadata=self.metadata.copy()
        )
        if deep:
            for child in self.children:
                new_child = child.copy(deep=True)
                new_node.add_child(new_child)
        return new_node
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte el nodo y sus hijos a diccionario.
        
        Returns:
            Dict[str, Any]: Representación como diccionario
        """
        return {
            "id": self.id,
            "label": self.label,
            "type": self.node_type.value,
            "value": self.value,
            "depth": self.depth,
            "metadata": self.metadata,
            "children": [child.to_dict() for child in self.children]
        }
    
    def __repr__(self) -> str:
        """Representación del nodo"""
        return f"TreeNode(id='{self.id}', label='{self.label}', children={len(self.children)})"
    
    def __str__(self) -> str:
        """Representación en cadena"""
        return self.label

T = TypeVar('T', bound=TreeNode)

class TreeBuilder(Generic[T]):
    """
    Constructor de árboles genéricos.
    
    Proporciona métodos para construir árboles de manera fluida
    y realizar operaciones sobre ellos.
    
    Uso:
        builder = TreeBuilder()
        root = builder.create_node("root", "Raíz")
        child = builder.add_child(root, "child1", "Hijo 1")
        tree = builder.build()
    """
    
    def __init__(self, node_class: type = TreeNode):
        """
        Inicializa el constructor.
        
        Args:
            node_class: Clase de nodo a usar (por defecto TreeNode)
        """
        self.node_class = node_class
        self.root: Optional[T] = None
        self.nodes: Dict[str, T] = {}
        self._node_counter = 0
        
        logger.debug(f"TreeBuilder inicializado (node_class={node_class.__name__})")
    
    def create_node(
        self,
        node_id: Optional[str] = None,
        label: str = "",
        node_type: NodeType = NodeType.INTERNAL,
        value: Any = None,
        **kwargs
    ) -> T:
        """
        Crea un nuevo nodo.
        
        Args:
            node_id: ID del nodo (auto-generado si no se proporciona)
            label: Etiqueta del nodo
            node_type: Tipo de nodo
            value: Valor del nodo
            **kwargs: Argumentos adicionales para la clase de nodo
            
        Returns:
            T: Nuevo nodo creado
        """
        if node_id is None:
            self._node_counter += 1
            node_id = f"node_{self._node_counter}"
        
        node = self.node_class(
            id=node_id,
            label=label or node_id,
            node_type=node_type,
            value=value,
            **kwargs
        )
        
        self.nodes[node_id] = node
        logger.debug(f"Nodo creado: {node_id}")
        
        return node
    
    def create_root(
        self,
        node_id: Optional[str] = None,
        label: str = "root",
        value: Any = None,
        **kwargs
    ) -> T:
        """
        Crea el nodo raíz del árbol.
        
        Args:
            node_id: ID del nodo raíz
            label: Etiqueta del nodo raíz
            value: Valor del nodo raíz
            **kwargs: Argumentos adicionales
            
        Returns:
            T: Nodo raíz creado
        """
        self.root = self.create_node(
            node_id=node_id or "root",
            label=label,
            node_type=NodeType.ROOT,
            value=value,
            depth=0,
            **kwargs
        )
        logger.debug(f"Raíz creada: {self.root.id}")
        return self.root
    
    def add_child(
        self,
        parent: T,
        node_id: Optional[str] = None,
        label: str = "",
        value: Any = None,
        **kwargs
    ) -> T:
        """
        Agrega un hijo a un nodo padre.
        
        Args:
            parent: Nodo padre
            node_id: ID del nuevo nodo
            label: Etiqueta del nuevo nodo
            value: Valor del nuevo nodo
            **kwargs: Argumentos adicionales
            
        Returns:
            T: Nuevo nodo hijo creado
        """
        child = self.create_node(
            node_id=node_id,
            label=label,
            value=value,
            **kwargs
        )
        parent.add_child(child)
        
        return child
    
    def add_children(
        self,
        parent: T,
        children_data: List[Dict[str, Any]]
    ) -> List[T]:
        """
        Agrega múltiples hijos a un nodo padre.
        
        Args:
            parent: Nodo padre
            children_data: Lista de diccionarios con datos de cada hijo
            
        Returns:
            List[T]: Lista de nodos hijos creados
        """
        children = []
        for data in children_data:
            child = self.add_child(parent, **data)
            children.append(child)
        return children
    
    def get_node(self, node_id: str) -> Optional[T]:
        """
        Obtiene un nodo por ID.
        
        Args:
            node_id: ID del nodo
            
        Returns:
            T o None si no existe
        """
        return self.nodes.get(node_id)
    
    def remove_node(self, node_id: str) -> bool:
        """
        Elimina un nodo del árbol.
        
        Args:
            node_id: ID del nodo a eliminar
            
        Returns:
            bool: True si se eliminó, False si no existía
        """
        node = self.nodes.get(node_id)
        if node is None:
            return False
        
        if node.parent:
            node.parent.remove_child(node)
        
        # Eliminar también todos los descendientes
        for descendant in node.get_descendants():
            del self.nodes[descendant.id]
        
        del self.nodes[node_id]
        
        if self.root and self.root.id == node_id:
            self.root = None
        
        logger.debug(f"Nodo eliminado: {node_id}")
        return True
    
    def move_node(self, node_id: str, new_parent_id: str) -> bool:
        """
        Mueve un nodo a un nuevo padre.
        
        Args:
            node_id: ID del nodo a mover
            new_parent_id: ID del nuevo padre
            
        Returns:
            bool: True si se movió, False si hubo error
        """
        node = self.nodes.get(node_id)
        new_parent = self.nodes.get(new_parent_id)
        
        if node is None or new_parent is None:
            return False
        
        # No permitir mover a un descendiente
        if new_parent in node.get_descendants():
            return False
        
        if node.parent:
            node.parent.remove_child(node)
        
        new_parent.add_child(node)
        
        # Actualizar profundidades
        self._update_depths(node)
        
        logger.debug(f"Nodo {node_id} movido a {new_parent_id}")
        return True
    
    def _update_depths(self, node: T) -> None:
        """Actualiza las profundidades del subárbol"""
        if node.parent:
            node.depth = node.parent.depth + 1
        for child in node.children:
            self._update_depths(child)
    
    def build(self) -> Optional[T]:
        """
        Retorna el árbol construido.
        
        Returns:
            T: Nodo raíz del árbol o None si no hay raíz
        """
        return self.root
    
    def build_from_dict(self, data: Dict[str, Any]) -> T:
        """
        Construye un árbol desde un diccionario.
        
        Args:
            data: Diccionario con estructura del árbol
            
        Returns:
            T: Raíz del árbol construido
        """
        def create_node_from_dict(node_data: Dict[str, Any], depth: int = 0) -> T:
            node = self.node_class(
                id=node_data.get("id", f"node_{self._node_counter}"),
                label=node_data.get("label", ""),
                node_type=NodeType(node_data.get("type", "internal")),
                value=node_data.get("value"),
                depth=depth,
                metadata=node_data.get("metadata", {})
            )
            self._node_counter += 1
            self.nodes[node.id] = node
            
            for child_data in node_data.get("children", []):
                child = create_node_from_dict(child_data, depth + 1)
                node.add_child(child)
            
            return node
        
        self.root = create_node_from_dict(data)
        logger.debug(f"Árbol construido desde dict con {len(self.nodes)} nodos")
        return self.root
    
    def build_from_nested_list(
        self,
        data: List[Any],
        label_func: Callable[[Any], str] = str
    ) -> T:
        """
        Construye un árbol desde una lista anidada.
        
        Args:
            data: Lista anidada [valor, [hijos...]]
            label_func: Función para generar etiquetas
            
        Returns:
            T: Raíz del árbol construido
        """
        def create_node_from_list(item: Any, depth: int = 0) -> T:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                value = item[0]
                children_data = item[1] if len(item) > 1 else []
            else:
                value = item
                children_data = []
            
            node = self.create_node(
                label=label_func(value),
                value=value,
                depth=depth
            )
            
            if isinstance(children_data, (list, tuple)):
                for child_item in children_data:
                    child = create_node_from_list(child_item, depth + 1)
                    node.add_child(child)
            
            return node
        
        self.root = create_node_from_list(data)
        self.root.node_type = NodeType.ROOT
        
        logger.debug(f"Árbol construido desde lista con {len(self.nodes)} nodos")
        return self.root
    
    def clear(self) -> None:
        """Limpia el constructor para reutilizarlo"""
        self.root = None
        self.nodes.clear()
        self._node_counter = 0
        logger.debug("TreeBuilder limpiado")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del árbol.
        
        Returns:
            Dict[str, Any]: Estadísticas del árbol
        """
        if self.root is None:
            return {
                "total_nodes": 0,
                "height": 0,
                "leaves": 0,
                "max_depth": 0
            }
        
        return {
            "total_nodes": self.root.size(),
            "height": self.root.height(),
            "leaves": self.root.count_leaves(),
            "max_depth": self.root.max_depth(),
            "node_types": self._count_node_types()
        }
    
    def _count_node_types(self) -> Dict[str, int]:
        """Cuenta nodos por tipo"""
        type_counts = {}
        for node in self.nodes.values():
            type_name = node.node_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        return type_counts
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte el árbol a diccionario.
        
        Returns:
            Dict[str, Any]: Representación del árbol
        """
        if self.root is None:
            return {}
        return self.root.to_dict()
    
    def pretty_print(self, node: Optional[T] = None, prefix: str = "", is_last: bool = True) -> str:
        """
        Genera una representación visual del árbol.
        
        Args:
            node: Nodo desde donde empezar (por defecto la raíz)
            prefix: Prefijo para la línea actual
            is_last: Si es el último hijo
            
        Returns:
            str: Representación visual del árbol
        """
        if node is None:
            node = self.root
        
        if node is None:
            return ""
        
        lines = []
        connector = "└── " if is_last else "├── "
        lines.append(f"{prefix}{connector if prefix else ''}{node.label}")
        
        child_prefix = prefix + ("    " if is_last else "│   ")
        for i, child in enumerate(node.children):
            is_last_child = (i == len(node.children) - 1)
            lines.append(self.pretty_print(child, child_prefix, is_last_child))
        
        return "\n".join(lines)

def build_tree(
    data: Any,
    node_class: type = TreeNode,
    label_func: Callable[[Any], str] = str
) -> TreeNode:
    """
    Función helper para construir un árbol rápidamente.
    
    Args:
        data: Datos para construir el árbol (dict o lista anidada)
        node_class: Clase de nodo a usar
        label_func: Función para generar etiquetas
        
    Returns:
        TreeNode: Raíz del árbol construido
        
    Example:
        # Desde diccionario
        tree = build_tree({
            "id": "root",
            "label": "Root",
            "children": [
                {"id": "a", "label": "A"},
                {"id": "b", "label": "B", "children": [
                    {"id": "c", "label": "C"}
                ]}
            ]
        })
        
        # Desde lista anidada
        tree = build_tree(["Root", [
            ["A", []],
            ["B", [["C", []]]]
        ]])
    """
    builder = TreeBuilder(node_class=node_class)
    
    if isinstance(data, dict):
        return builder.build_from_dict(data)
    elif isinstance(data, (list, tuple)):
        return builder.build_from_nested_list(data, label_func)
    else:
        # Crear nodo simple
        return builder.create_root(label=label_func(data), value=data)