"""
Visualization Module - Módulo de Visualización

Proporciona generación de visualizaciones gráficas para algoritmos,
árboles de recursión, grafos y diagramas de flujo.

Capacidades:
- Árboles de recursión
- Grafos de estructuras de datos
- Diagramas de flujo de ejecución
- Renderizado en múltiples formatos (SVG, PNG, DOT, Mermaid)
- Exportación batch con múltiples modos de procesamiento
- Optimización para grafos grandes
- Métricas y monitoring con alertas

Exports principales:
    - RecursionTreeGenerator: Generador de árboles de recursión
    - GraphGenerator: Generador de grafos
    - ExecutionFlowGenerator: Generador de flujos de ejecución
    - DiagramRenderer: Renderizador unificado
    - TreeBuilder: Constructor de árboles genéricos
    - BatchExporter: Exportación masiva de visualizaciones
    - VisualizationOptimizer: Optimizador para grafos grandes
    - MetricsCollector: Recolector de métricas y alertas
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

from app.core.visualization.batch_exporter import (
    BatchExporter,
    BatchExportConfig,
    ExportTask,
    ExportResult,
    ExportFormat,
    ProcessingMode
)

from app.core.visualization.optimizer import (
    VisualizationOptimizer,
    OptimizationConfig,
    OptimizationLevel,
    GraphMetrics
)

from app.core.visualization.metrics_collector import (
    MetricsCollector,
    MetricsContext,
    ExportMetrics,
    BatchMetrics,
    Alert,
    AlertThresholds,
    AlertSeverity,
    MetricType,
    track_export
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
    
    # Batch Export
    "BatchExporter",
    "BatchExportConfig",
    "ExportTask",
    "ExportResult",
    "ExportFormat",
    "ProcessingMode",
    
    # Optimization
    "VisualizationOptimizer",
    "OptimizationConfig",
    "OptimizationLevel",
    "GraphMetrics",
    
    # Metrics & Monitoring
    "MetricsCollector",
    "MetricsContext",
    "ExportMetrics",
    "BatchMetrics",
    "Alert",
    "AlertThresholds",
    "AlertSeverity",
    "MetricType",
    "track_export",
]