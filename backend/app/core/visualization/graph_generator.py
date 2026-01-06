"""
Graph Generator - Generador de Grafos

Genera representaciones gráficas de estructuras de datos como
grafos, árboles, listas enlazadas, etc.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
from enum import Enum

import networkx as nx

from app.core.data_structures import StructureType, StructureMatch
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class GraphType(str, Enum):
    """Tipos de grafos"""
    DIRECTED = "directed"
    UNDIRECTED = "undirected"
    TREE = "tree"
    DAG = "dag"  # Directed Acyclic Graph
    WEIGHTED = "weighted"
    BIPARTITE = "bipartite"


class LayoutType(str, Enum):
    """Tipos de layout para grafos"""
    HIERARCHICAL = "hierarchical"
    CIRCULAR = "circular"
    SPRING = "spring"
    SHELL = "shell"
    SPECTRAL = "spectral"
    KAMADA_KAWAI = "kamada_kawai"


@dataclass
class GraphNode:
    """
    Nodo de grafo.
    
    Attributes:
        id: Identificador único
        label: Etiqueta visible
        value: Valor del nodo
        position: Posición (x, y) opcional
        metadata: Metadatos adicionales
    """
    id: str
    label: str
    value: Any = None
    position: Optional[Tuple[float, float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario"""
        return {
            "id": self.id,
            "label": self.label,
            "value": self.value,
            "position": self.position,
            "metadata": self.metadata
        }


@dataclass
class GraphEdge:
    """
    Arista de grafo.
    
    Attributes:
        source: ID del nodo origen
        target: ID del nodo destino
        weight: Peso de la arista
        label: Etiqueta de la arista
        metadata: Metadatos adicionales
    """
    source: str
    target: str
    weight: Optional[float] = None
    label: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario"""
        return {
            "source": self.source,
            "target": self.target,
            "weight": self.weight,
            "label": self.label,
            "metadata": self.metadata
        }


@dataclass
class GraphResult:
    """
    Resultado de generación de grafo.
    
    Attributes:
        nodes: Lista de nodos
        edges: Lista de aristas
        graph_type: Tipo de grafo
        layout: Tipo de layout usado
        statistics: Estadísticas del grafo
        networkx_graph: Grafo NetworkX (opcional)
    """
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    graph_type: GraphType
    layout: LayoutType
    statistics: Dict[str, Any]
    networkx_graph: Optional[nx.Graph] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario"""
        return {
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": [edge.to_dict() for edge in self.edges],
            "graph_type": self.graph_type.value,
            "layout": self.layout.value,
            "statistics": self.statistics
        }


class GraphGenerator:
    """
    Generador de grafos.
    
    Genera representaciones gráficas de estructuras de datos
    y las prepara para visualización.
    """
    
    def __init__(self):
        """Inicializa el generador"""
        logger.debug("GraphGenerator inicializado")
    
    def generate_from_structure(
        self,
        structure: StructureMatch,
        layout: LayoutType = LayoutType.HIERARCHICAL
    ) -> GraphResult:
        """
        Genera grafo desde una estructura detectada.
        
        Args:
            structure: Estructura de datos detectada
            layout: Tipo de layout a usar
            
        Returns:
            GraphResult: Resultado de la generación
        """
        logger.info(f"Generando grafo para estructura: {structure.structure_name}")
        
        if structure.structure_type == StructureType.TREE:
            return self.generate_tree(layout=layout)
        
        elif structure.structure_type == StructureType.GRAPH:
            return self.generate_graph(layout=layout)
        
        elif structure.structure_type == StructureType.LINKED_LIST:
            return self.generate_linked_list(layout=layout)
        
        else:
            # Estructura genérica
            return self.generate_generic_structure(structure, layout)
    
    def generate_tree(
        self,
        values: Optional[List[Any]] = None,
        layout: LayoutType = LayoutType.HIERARCHICAL
    ) -> GraphResult:
        """
        Genera un árbol binario.
        
        Args:
            values: Lista de valores para el árbol
            layout: Tipo de layout
            
        Returns:
            GraphResult: Resultado de la generación
        """
        if values is None:
            values = [10, 5, 15, 3, 7, 12, 20]
        
        # Crear grafo NetworkX
        G = nx.DiGraph()
        
        nodes = []
        edges = []
        
        # Construir árbol
        for i, val in enumerate(values):
            if val is not None:
                node = GraphNode(
                    id=f"node_{i}",
                    label=str(val),
                    value=val
                )
                nodes.append(node)
                G.add_node(node.id, label=node.label)
                
                # Agregar aristas a hijos
                left_idx = 2 * i + 1
                right_idx = 2 * i + 2
                
                if left_idx < len(values) and values[left_idx] is not None:
                    edge = GraphEdge(
                        source=node.id,
                        target=f"node_{left_idx}",
                        label="left"
                    )
                    edges.append(edge)
                    G.add_edge(edge.source, edge.target)
                
                if right_idx < len(values) and values[right_idx] is not None:
                    edge = GraphEdge(
                        source=node.id,
                        target=f"node_{right_idx}",
                        label="right"
                    )
                    edges.append(edge)
                    G.add_edge(edge.source, edge.target)
        
        # Aplicar layout
        positions = self._apply_layout(G, layout)
        
        # Asignar posiciones a nodos
        for node in nodes:
            if node.id in positions:
                node.position = positions[node.id]
        
        # Calcular estadísticas
        statistics = self._calculate_graph_statistics(G, GraphType.TREE)
        
        return GraphResult(
            nodes=nodes,
            edges=edges,
            graph_type=GraphType.TREE,
            layout=layout,
            statistics=statistics,
            networkx_graph=G
        )
    
    def generate_graph(
        self,
        num_nodes: int = 6,
        edges_list: Optional[List[Tuple[int, int]]] = None,
        directed: bool = True,
        layout: LayoutType = LayoutType.SPRING
    ) -> GraphResult:
        """
        Genera un grafo genérico.
        
        Args:
            num_nodes: Número de nodos
            edges_list: Lista de aristas (opcional)
            directed: Si el grafo es dirigido
            layout: Tipo de layout
            
        Returns:
            GraphResult: Resultado de la generación
        """
        # Crear grafo NetworkX
        if directed:
            G = nx.DiGraph()
            graph_type = GraphType.DIRECTED
        else:
            G = nx.Graph()
            graph_type = GraphType.UNDIRECTED
        
        nodes = []
        edges = []
        
        # Crear nodos
        for i in range(num_nodes):
            node = GraphNode(
                id=f"v{i}",
                label=f"V{i}",
                value=i
            )
            nodes.append(node)
            G.add_node(node.id, label=node.label)
        
        # Crear aristas
        if edges_list is None:
            # Grafo de ejemplo
            edges_list = [
                (0, 1), (0, 2), (1, 3), (1, 4), (2, 4), (3, 5), (4, 5)
            ]
        
        for source_idx, target_idx in edges_list:
            edge = GraphEdge(
                source=f"v{source_idx}",
                target=f"v{target_idx}"
            )
            edges.append(edge)
            G.add_edge(edge.source, edge.target)
        
        # Aplicar layout
        positions = self._apply_layout(G, layout)
        
        # Asignar posiciones
        for node in nodes:
            if node.id in positions:
                node.position = positions[node.id]
        
        # Calcular estadísticas
        statistics = self._calculate_graph_statistics(G, graph_type)
        
        return GraphResult(
            nodes=nodes,
            edges=edges,
            graph_type=graph_type,
            layout=layout,
            statistics=statistics,
            networkx_graph=G
        )
    
    def generate_linked_list(
        self,
        values: Optional[List[Any]] = None,
        layout: LayoutType = LayoutType.HIERARCHICAL
    ) -> GraphResult:
        """
        Genera una lista enlazada.
        
        Args:
            values: Lista de valores
            layout: Tipo de layout
            
        Returns:
            GraphResult: Resultado de la generación
        """
        if values is None:
            values = [1, 2, 3, 4, 5]
        
        # Crear grafo dirigido
        G = nx.DiGraph()
        
        nodes = []
        edges = []
        
        # Crear nodos
        for i, val in enumerate(values):
            node = GraphNode(
                id=f"node_{i}",
                label=str(val),
                value=val,
                metadata={"index": i}
            )
            nodes.append(node)
            G.add_node(node.id, label=node.label)
            
            # Conectar con siguiente
            if i > 0:
                edge = GraphEdge(
                    source=f"node_{i-1}",
                    target=node.id,
                    label="next"
                )
                edges.append(edge)
                G.add_edge(edge.source, edge.target)
        
        # Layout horizontal
        positions = {}
        for i, node in enumerate(nodes):
            positions[node.id] = (i * 2, 0)
            node.position = positions[node.id]
        
        # Calcular estadísticas
        statistics = self._calculate_graph_statistics(G, GraphType.DIRECTED)
        statistics["is_linear"] = True
        
        return GraphResult(
            nodes=nodes,
            edges=edges,
            graph_type=GraphType.DIRECTED,
            layout=layout,
            statistics=statistics,
            networkx_graph=G
        )
    
    def generate_generic_structure(
        self,
        structure: StructureMatch,
        layout: LayoutType = LayoutType.SPRING
    ) -> GraphResult:
        """Genera representación genérica de una estructura"""
        # Placeholder: crear grafo simple
        return self.generate_graph(num_nodes=5, layout=layout)
    
    def _apply_layout(
        self,
        G: nx.Graph,
        layout_type: LayoutType
    ) -> Dict[str, Tuple[float, float]]:
        """
        Aplica un layout al grafo.
        
        Args:
            G: Grafo NetworkX
            layout_type: Tipo de layout
            
        Returns:
            Diccionario con posiciones de nodos
        """
        if layout_type == LayoutType.HIERARCHICAL:
            return nx.spring_layout(G, k=1, iterations=50)
        
        elif layout_type == LayoutType.CIRCULAR:
            return nx.circular_layout(G)
        
        elif layout_type == LayoutType.SPRING:
            return nx.spring_layout(G)
        
        elif layout_type == LayoutType.SHELL:
            return nx.shell_layout(G)
        
        elif layout_type == LayoutType.SPECTRAL:
            return nx.spectral_layout(G)
        
        elif layout_type == LayoutType.KAMADA_KAWAI:
            return nx.kamada_kawai_layout(G)
        
        else:
            return nx.spring_layout(G)
    
    def _calculate_graph_statistics(
        self,
        G: nx.Graph,
        graph_type: GraphType
    ) -> Dict[str, Any]:
        """Calcula estadísticas del grafo"""
        stats = {
            "num_nodes": G.number_of_nodes(),
            "num_edges": G.number_of_edges(),
            "is_directed": isinstance(G, nx.DiGraph),
            "graph_type": graph_type.value
        }
        
        # Estadísticas adicionales
        if G.number_of_nodes() > 0:
            if isinstance(G, nx.DiGraph):
                stats["avg_in_degree"] = sum(dict(G.in_degree()).values()) / G.number_of_nodes()
                stats["avg_out_degree"] = sum(dict(G.out_degree()).values()) / G.number_of_nodes()
            else:
                stats["avg_degree"] = sum(dict(G.degree()).values()) / G.number_of_nodes()
            
            # Conectividad
            if isinstance(G, nx.DiGraph):
                stats["is_weakly_connected"] = nx.is_weakly_connected(G)
                stats["is_strongly_connected"] = nx.is_strongly_connected(G)
            else:
                stats["is_connected"] = nx.is_connected(G)
        
        return stats

def generate_graph(
    structure_type: str = "tree",
    layout: LayoutType = LayoutType.HIERARCHICAL,
    **kwargs
) -> GraphResult:
    """
    Helper para generar grafos.

    Args:
        structure_type: Tipo de estructura (tree, graph, linked_list)
        layout: Tipo de layout
        **kwargs: Argumentos adicionales

    Returns:
        GraphResult: Resultado de la generación
    """
    generator = GraphGenerator()

    if structure_type == "tree":
        return generator.generate_tree(layout=layout, **kwargs)
    elif structure_type == "graph":
        return generator.generate_graph(layout=layout, **kwargs)
    elif structure_type == "linked_list":
        return generator.generate_linked_list(layout=layout, **kwargs)
    else:
        raise ValueError(f"Tipo de estructura no soportado: {structure_type}")