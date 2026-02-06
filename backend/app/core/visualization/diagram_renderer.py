"""
Diagram Renderer - Renderizador de Diagramas

Renderiza árboles, grafos y diagramas en múltiples formatos
(SVG, PNG, DOT, Mermaid, etc.).
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional, Union
from enum import Enum
from pathlib import Path
import json

try:
    import graphviz
    GRAPHVIZ_AVAILABLE = True
except ImportError:
    GRAPHVIZ_AVAILABLE = False
    graphviz = None

from app.core.visualization.tree_builder import TreeNode
from app.core.visualization.recursion_tree_generator import RecursionTreeResult
from app.core.visualization.execution_flow_generator import ExecutionFlowResult
from app.core.visualization.graph_generator import GraphResult
from app.core.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class RenderFormat(str, Enum):
    """Formatos de renderizado soportados"""
    SVG = "svg"
    PNG = "png"
    PDF = "pdf"
    DOT = "dot"
    MERMAID = "mermaid"
    JSON = "json"
    HTML = "html"


@dataclass
class RenderOptions:
    """
    Opciones de renderizado.
    
    Attributes:
        format: Formato de salida
        engine: Motor de Graphviz (dot, neato, etc.)
        node_shape: Forma de nodos
        node_color: Color de nodos
        edge_color: Color de aristas
        font_name: Fuente tipográfica
        font_size: Tamaño de fuente
        dpi: DPI para imágenes
        rankdir: Dirección del grafo (TB, LR, etc.)
    """
    format: RenderFormat = RenderFormat.SVG
    engine: str = "dot"
    node_shape: str = "box"
    node_color: str = "#e3f2fd"
    edge_color: str = "#666666"
    font_name: str = "Arial"
    font_size: int = 12
    dpi: int = 300
    rankdir: str = "TB"  # TB (top-bottom), LR (left-right)


@dataclass
class RenderResult:
    """
    Resultado del renderizado.
    
    Attributes:
        content: Contenido renderizado (string o bytes)
        format: Formato del contenido
        file_path: Ruta del archivo guardado (opcional)
        metadata: Metadatos adicionales
    """
    content: Union[str, bytes]
    format: RenderFormat
    file_path: Optional[Path] = None
    metadata: Dict[str, Any] = None


class DiagramRenderer:
    """
    Renderizador unificado de diagramas.
    
    Soporta múltiples tipos de entrada (árboles, grafos, flujos)
    y múltiples formatos de salida (SVG, PNG, DOT, Mermaid).
    """
    
    def __init__(self, options: Optional[RenderOptions] = None):
        """
        Inicializa el renderizador.
        
        Args:
            options: Opciones de renderizado
        """
        self.options = options or RenderOptions()
        logger.debug(f"DiagramRenderer inicializado (formato={self.options.format.value})")
    
    def render_tree(
        self,
        tree: Union[TreeNode, RecursionTreeResult],
        output_path: Optional[Path] = None
    ) -> RenderResult:
        """
        Renderiza un árbol.
        
        Args:
            tree: Árbol a renderizar
            output_path: Ruta de salida (opcional)
            
        Returns:
            RenderResult: Resultado del renderizado
        """
        logger.info("Renderizando árbol")
        
        # Extraer TreeNode si es RecursionTreeResult
        if isinstance(tree, RecursionTreeResult):
            root = tree.root
        else:
            root = tree
        
        if self.options.format == RenderFormat.DOT:
            return self._render_tree_dot(root, output_path)
        
        elif self.options.format == RenderFormat.MERMAID:
            return self._render_tree_mermaid(root, output_path)
        
        elif self.options.format == RenderFormat.JSON:
            return self._render_tree_json(root, output_path)
        
        elif self.options.format in [RenderFormat.SVG, RenderFormat.PNG, RenderFormat.PDF]:
            return self._render_tree_graphviz(root, output_path)
        
        else:
            raise ValueError(f"Formato no soportado: {self.options.format}")
    
    def render_graph(
        self,
        graph: GraphResult,
        output_path: Optional[Path] = None
    ) -> RenderResult:
        """
        Renderiza un grafo.
        
        Args:
            graph: Grafo a renderizar
            output_path: Ruta de salida (opcional)
            
        Returns:
            RenderResult: Resultado del renderizado
        """
        logger.info("Renderizando grafo")
        
        if self.options.format == RenderFormat.DOT:
            return self._render_graph_dot(graph, output_path)
        
        elif self.options.format == RenderFormat.MERMAID:
            return self._render_graph_mermaid(graph, output_path)
        
        elif self.options.format == RenderFormat.JSON:
            return self._render_graph_json(graph, output_path)
        
        elif self.options.format in [RenderFormat.SVG, RenderFormat.PNG, RenderFormat.PDF]:
            return self._render_graph_graphviz(graph, output_path)
        
        else:
            raise ValueError(f"Formato no soportado: {self.options.format}")
    
    def render_flow(
        self,
        flow: ExecutionFlowResult,
        output_path: Optional[Path] = None
    ) -> RenderResult:
        """
        Renderiza un flujo de ejecución.
        
        Args:
            flow: Flujo a renderizar
            output_path: Ruta de salida (opcional)
            
        Returns:
            RenderResult: Resultado del renderizado
        """
        logger.info("Renderizando flujo de ejecución")
        
        if self.options.format == RenderFormat.DOT:
            return self._render_flow_dot(flow, output_path)
        
        elif self.options.format == RenderFormat.MERMAID:
            return self._render_flow_mermaid(flow, output_path)
        
        elif self.options.format == RenderFormat.JSON:
            return self._render_flow_json(flow, output_path)
        
        elif self.options.format in [RenderFormat.SVG, RenderFormat.PNG, RenderFormat.PDF]:
            return self._render_flow_graphviz(flow, output_path)
        
        else:
            raise ValueError(f"Formato no soportado: {self.options.format}")
    
    # Métodos de renderizado para árboles
    
    def _render_tree_dot(self, root: TreeNode, output_path: Optional[Path]) -> RenderResult:
        """Renderiza árbol en formato DOT"""
        dot_lines = ["digraph Tree {"]
        dot_lines.append(f'    rankdir="{self.options.rankdir}";')
        dot_lines.append('    node [shape=box, style=filled, fillcolor="#e3f2fd"];')
        
        def add_node(node: TreeNode):
            label = node.label.replace('"', '\\"')
            dot_lines.append(f'    "{node.id}" [label="{label}"];')
            
            for child in node.children:
                dot_lines.append(f'    "{node.id}" -> "{child.id}";')
                add_node(child)
        
        add_node(root)
        dot_lines.append("}")
        
        content = "\n".join(dot_lines)
        
        if output_path:
            output_path.write_text(content)
        
        return RenderResult(
            content=content,
            format=RenderFormat.DOT,
            file_path=output_path
        )
    
    def _render_tree_mermaid(self, root: TreeNode, output_path: Optional[Path]) -> RenderResult:
        """Renderiza árbol en formato Mermaid"""
        mermaid_lines = ["graph TD"]
        
        def add_node(node: TreeNode):
            label = node.label.replace('"', "'")
            mermaid_lines.append(f'    {node.id}["{label}"]')
            
            for child in node.children:
                mermaid_lines.append(f'    {node.id} --> {child.id}')
                add_node(child)
        
        add_node(root)
        
        content = "\n".join(mermaid_lines)
        
        if output_path:
            output_path.write_text(content)
        
        return RenderResult(
            content=content,
            format=RenderFormat.MERMAID,
            file_path=output_path
        )
    
    def _render_tree_json(self, root: TreeNode, output_path: Optional[Path]) -> RenderResult:
        """Renderiza árbol en formato JSON"""
        content = json.dumps(root.to_dict(), indent=2)
        
        if output_path:
            output_path.write_text(content)
        
        return RenderResult(
            content=content,
            format=RenderFormat.JSON,
            file_path=output_path
        )
    
    def _render_tree_graphviz(self, root: TreeNode, output_path: Optional[Path]) -> RenderResult:
        """Renderiza árbol usando Graphviz"""
        if not GRAPHVIZ_AVAILABLE:
            raise ImportError("Graphviz no está disponible. Instalar: pip install graphviz")
        
        # Crear grafo
        dot = graphviz.Digraph(
            engine=self.options.engine,
            format=self.options.format.value
        )
        
        dot.attr(rankdir=self.options.rankdir)
        dot.attr('node', shape=self.options.node_shape, style='filled', fillcolor=self.options.node_color)
        
        def add_node(node: TreeNode):
            dot.node(node.id, node.label)
            for child in node.children:
                dot.edge(node.id, child.id)
                add_node(child)
        
        add_node(root)
        
        # Renderizar
        if output_path:
            dot.render(str(output_path.with_suffix('')), cleanup=True)
            content = output_path.read_bytes()
        else:
            content = dot.pipe()
        
        return RenderResult(
            content=content,
            format=self.options.format,
            file_path=output_path
        )
    
    # Métodos de renderizado para grafos
    
    def _render_graph_dot(self, graph: GraphResult, output_path: Optional[Path]) -> RenderResult:
        """Renderiza grafo en formato DOT"""
        graph_type = "digraph" if graph.graph_type.value in ["directed", "tree", "dag"] else "graph"
        connector = "->" if graph_type == "digraph" else "--"
        
        dot_lines = [f"{graph_type} G {{"]
        dot_lines.append(f'    rankdir="{self.options.rankdir}";')
        
        # Nodos
        for node in graph.nodes:
            label = node.label.replace('"', '\\"')
            dot_lines.append(f'    "{node.id}" [label="{label}"];')
        
        # Aristas
        for edge in graph.edges:
            if edge.label:
                label_attr = f' [label="{edge.label}"]'
            else:
                label_attr = ""
            dot_lines.append(f'    "{edge.source}" {connector} "{edge.target}"{label_attr};')
        
        dot_lines.append("}")
        
        content = "\n".join(dot_lines)
        
        if output_path:
            output_path.write_text(content)
        
        return RenderResult(
            content=content,
            format=RenderFormat.DOT,
            file_path=output_path
        )
    
    def _render_graph_mermaid(self, graph: GraphResult, output_path: Optional[Path]) -> RenderResult:
        """Renderiza grafo en formato Mermaid"""
        connector = "-->" if graph.graph_type.value in ["directed", "tree", "dag"] else "---"
        
        mermaid_lines = ["graph TD"]
        
        # Nodos
        for node in graph.nodes:
            label = node.label.replace('"', "'")
            mermaid_lines.append(f'    {node.id}["{label}"]')
        
        # Aristas
        for edge in graph.edges:
            if edge.label:
                mermaid_lines.append(f'    {edge.source} {connector}|{edge.label}| {edge.target}')
            else:
                mermaid_lines.append(f'    {edge.source} {connector} {edge.target}')
        
        content = "\n".join(mermaid_lines)
        
        if output_path:
            output_path.write_text(content)
        
        return RenderResult(
            content=content,
            format=RenderFormat.MERMAID,
            file_path=output_path
        )
    
    def _render_graph_json(self, graph: GraphResult, output_path: Optional[Path]) -> RenderResult:
        """Renderiza grafo en formato JSON"""
        content = json.dumps(graph.to_dict(), indent=2)
        
        if output_path:
            output_path.write_text(content)
        
        return RenderResult(
            content=content,
            format=RenderFormat.JSON,
            file_path=output_path
        )
    
    def _render_graph_graphviz(self, graph: GraphResult, output_path: Optional[Path]) -> RenderResult:
        """Renderiza grafo usando Graphviz"""
        if not GRAPHVIZ_AVAILABLE:
            # Fallback a formato DOT textual si graphviz no está instalado
            logger.warning("Graphviz no está disponible, usando fallback a DOT textual")
            return self._render_graph_dot(graph, output_path)
        
        try:
            # Crear grafo
            if graph.graph_type.value in ["directed", "tree", "dag"]:
                dot = graphviz.Digraph(engine=self.options.engine, format=self.options.format.value)
            else:
                dot = graphviz.Graph(engine=self.options.engine, format=self.options.format.value)
            
            # Nodos
            for node in graph.nodes:
                dot.node(node.id, node.label)
            
            # Aristas
            for edge in graph.edges:
                dot.edge(edge.source, edge.target, label=edge.label or "")
            
            # Renderizar
            if output_path:
                dot.render(str(output_path.with_suffix('')), cleanup=True)
                content = output_path.read_bytes()
            else:
                content = dot.pipe()
            
            return RenderResult(
                content=content,
                format=self.options.format,
                file_path=output_path
            )
        except Exception as e:
            logger.error(f"Error en graphviz, usando fallback a DOT: {e}")
            return self._render_graph_dot(graph, output_path)
    
    # Métodos de renderizado para flujos
    
    def _render_flow_dot(self, flow: ExecutionFlowResult, output_path: Optional[Path]) -> RenderResult:
        """Renderiza flujo en formato DOT"""
        dot_lines = ["digraph Flow {"]
        dot_lines.append('    rankdir="TB";')
        
        # Nodos con formas según tipo
        shape_map = {
            "start": "ellipse",
            "end": "ellipse",
            "decision": "diamond",
            "process": "box"
        }
        
        for node in flow.nodes:
            shape = shape_map.get(node.node_type.value, "box")
            label = node.label.replace('"', '\\"')
            dot_lines.append(f'    "{node.id}" [label="{label}", shape="{shape}"];')
        
        # Aristas
        for edge in flow.edges:
            label_attr = f' [label="{edge.label}"]' if edge.label else ""
            dot_lines.append(f'    "{edge.source}" -> "{edge.target}"{label_attr};')
        
        dot_lines.append("}")
        
        content = "\n".join(dot_lines)
        
        if output_path:
            output_path.write_text(content)
        
        return RenderResult(
            content=content,
            format=RenderFormat.DOT,
            file_path=output_path
        )
    
    def _render_flow_mermaid(self, flow: ExecutionFlowResult, output_path: Optional[Path]) -> RenderResult:
        """Renderiza flujo en formato Mermaid"""
        mermaid_lines = ["flowchart TD"]
        
        # Nodos
        for node in flow.nodes:
            label = node.label.replace('"', "'")
            
            if node.node_type.value in ["start", "end"]:
                mermaid_lines.append(f'    {node.id}(("{label}"))')
            elif node.node_type.value == "decision":
                mermaid_lines.append(f'    {node.id}{{{{{label}}}}}')
            else:
                mermaid_lines.append(f'    {node.id}["{label}"]')
        
        # Aristas
        for edge in flow.edges:
            if edge.label:
                mermaid_lines.append(f'    {edge.source} -->|{edge.label}| {edge.target}')
            else:
                mermaid_lines.append(f'    {edge.source} --> {edge.target}')
        
        content = "\n".join(mermaid_lines)
        
        if output_path:
            output_path.write_text(content)
        
        return RenderResult(
            content=content,
            format=RenderFormat.MERMAID,
            file_path=output_path
        )
    
    def _render_flow_json(self, flow: ExecutionFlowResult, output_path: Optional[Path]) -> RenderResult:
        """Renderiza flujo en formato JSON"""
        content = json.dumps(flow.to_dict(), indent=2)
        
        if output_path:
            output_path.write_text(content)
        
        return RenderResult(
            content=content,
            format=RenderFormat.JSON,
            file_path=output_path
        )
    
    def _render_flow_graphviz(self, flow: ExecutionFlowResult, output_path: Optional[Path]) -> RenderResult:
        """Renderiza flujo usando Graphviz"""
        if not GRAPHVIZ_AVAILABLE:
            raise ImportError("Graphviz no está disponible")
        
        dot = graphviz.Digraph(engine=self.options.engine, format=self.options.format.value)
        dot.attr(rankdir="TB")
        
        # Nodos
        shape_map = {
            "start": "ellipse",
            "end": "ellipse",
            "decision": "diamond",
            "process": "box"
        }
        
        for node in flow.nodes:
            shape = shape_map.get(node.node_type.value, "box")
            dot.node(node.id, node.label, shape=shape)
        
        # Aristas
        for edge in flow.edges:
            dot.edge(edge.source, edge.target, label=edge.label or "")
        
        # Renderizar
        if output_path:
            dot.render(str(output_path.with_suffix('')), cleanup=True)
            content = output_path.read_bytes()
        else:
            content = dot.pipe()
        
        return RenderResult(
            content=content,
            format=self.options.format,
            file_path=output_path
        )


def render_diagram(
    diagram: Union[TreeNode, RecursionTreeResult, GraphResult, ExecutionFlowResult],
    format: RenderFormat = RenderFormat.SVG,
    output_path: Optional[Path] = None,
    **options
) -> RenderResult:
    """
    Helper para renderizar diagramas.
    
    Args:
        diagram: Diagrama a renderizar
        format: Formato de salida
        output_path: Ruta de salida
        **options: Opciones adicionales
        
    Returns:
        RenderResult: Resultado del renderizado
    """
    render_options = RenderOptions(format=format, **options)
    renderer = DiagramRenderer(render_options)
    
    if isinstance(diagram, (TreeNode, RecursionTreeResult)):
        return renderer.render_tree(diagram, output_path)
    elif isinstance(diagram, GraphResult):
        return renderer.render_graph(diagram, output_path)
    elif isinstance(diagram, ExecutionFlowResult):
        return renderer.render_flow(diagram, output_path)
    else:
        raise TypeError(f"Tipo de diagrama no soportado: {type(diagram)}")