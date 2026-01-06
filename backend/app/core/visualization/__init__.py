"""
Visualization Module - Módulo de Visualización

Proporciona generación de visualizaciones gráficas para algoritmos,
árboles de recursión, grafos y diagramas de flujo.

Capacidades:
- Árboles de recursión
- Grafos de estructuras de datos
- Diagramas de flujo de ejecución
- Renderizado en múltiples formatos (SVG, PNG, DOT, Mermaid)

Exports principales:
    - RecursionTreeGenerator: Generador de árboles de recursión
    - GraphGenerator: Generador de grafos
    - ExecutionFlowGenerator: Generador de flujos de ejecución
    - DiagramRenderer: Renderizador unificado
    - TreeBuilder: Constructor de árboles genéricos
"""

from app.core.visualization.tree_builder import (
    TreeBuilder,
    TreeNode,
    NodeType,
    build_tree
)

from app.core.visualization.recursion_tree_generator import (
    RecursionTreeGenerator,
    RecursionTreeNode,
    RecursionTreeResult,
    RecursionType,
    generate_recursion_tree
)

from app.core.visualization.execution_flow_generator import (
    ExecutionFlowGenerator,
    FlowNode,
    FlowEdge,
    FlowNodeType,
    ExecutionFlowResult,
    generate_execution_flow
)

from app.core.visualization.graph_generator import (
    GraphGenerator,
    GraphNode,
    GraphEdge,
    GraphResult,
    GraphType,
    LayoutType,
    generate_graph
)

from app.core.visualization.diagram_renderer import (
    DiagramRenderer,
    RenderFormat,
    RenderOptions,
    RenderResult,
    render_diagram
)

__all__ = [
    # Tree Builder
    "TreeBuilder",
    "TreeNode",
    "NodeType",
    "build_tree",
    
    # Recursion Trees
    "RecursionTreeGenerator",
    "RecursionTreeNode",
    "RecursionTreeResult",
    "RecursionType",
    "generate_recursion_tree",
    
    # Execution Flow
    "ExecutionFlowGenerator",
    "FlowNode",
    "FlowEdge",
    "FlowNodeType",
    "ExecutionFlowResult",
    "generate_execution_flow",
    
    # Graphs
    "GraphGenerator",
    "GraphNode",
    "GraphEdge",
    "GraphResult",
    "GraphType",
    "LayoutType",
    "generate_graph",
    
    # Rendering
    "DiagramRenderer",
    "RenderFormat",
    "RenderOptions",
    "RenderResult",
    "render_diagram",
]