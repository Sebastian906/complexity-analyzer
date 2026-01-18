"""
API Endpoints - Visualización

Endpoints REST para generar visualizaciones de algoritmos.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, status
from app.schemas import (
    # Visualization Request Schemas
    VisualizationRequest,
    VisualizationOptions,
    VisualizationType as SchemaVisualizationType,
    
    # Visualization Result Schemas
    VisualizationResult,
    
    # Common
    BaseResponse,
)

from app.core.parser import PseudocodeParser
from app.core.visualization import (
    generate_recursion_tree,
    generate_execution_flow,
    generate_graph,
    render_diagram,
    RenderFormat as VizRenderFormat,
    LayoutType
)
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()

@router.post(
    "/recursion-tree",
    response_model=VisualizationResult,
    status_code=status.HTTP_200_OK,
    summary="Generar Árbol de Recursión",
    description="Genera y renderiza un árbol de recursión para un algoritmo recursivo"
)
async def generate_recursion_tree_endpoint(request: VisualizationRequest):
    """
    Genera árbol de recursión para un algoritmo recursivo.
    
    Muestra:
    - Llamadas recursivas
    - Trabajo por nivel
    - Tipo de recursión detectado
    - Complejidad total
    """
    try:
        logger.info("Generando árbol de recursión")
        
        # Parsear código
        parser = PseudocodeParser()
        ast = parser.parse(request.code)
        
        logger.info(f"Código parseado: {ast.algorithm.name}")
        
        # Extraer opciones
        max_depth = request.options.max_depth if request.options else 10
        start_value = request.options.start_value if request.options else None
        viz_format = request.options.format if request.options else "svg"
        
        # Generar árbol de recursión
        from app.core.visualization import RecursionTreeGenerator
        
        generator = RecursionTreeGenerator(max_depth=max_depth)
        tree_result = generator.generate(ast, start_value=start_value)
        
        logger.info(
            f"Árbol generado: {tree_result.total_calls} llamadas, "
            f"prof. {tree_result.max_depth}"
        )
        
        # Renderizar
        render_format = VizRenderFormat(viz_format)
        render_result = render_diagram(tree_result, format=render_format)
        
        # Construir respuesta usando VisualizationResult del schema
        content = render_result.content
        if isinstance(content, bytes):
            content = content.decode('utf-8')
        
        return VisualizationResult(
            type="recursion_tree",
            format=viz_format,
            content=content,
            file_path=None,
            statistics={
                "recursion_type": tree_result.recursion_type.value,
                "total_calls": tree_result.total_calls,
                "max_depth": tree_result.max_depth,
                "base_cases": tree_result.base_cases,
                "total_work": tree_result.total_work,
                "work_per_level": tree_result.work_per_level,
            },
            metadata={
                "algorithm_name": ast.algorithm.name,
            },
        )
    
    except Exception as e:
        logger.error(f"Error generando árbol de recursión: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "RecursionTreeError",
                "message": str(e)
            }
        )

@router.post(
    "/execution-flow",
    response_model=VisualizationResult,
    status_code=status.HTTP_200_OK,
    summary="Generar Flujo de Ejecución",
    description="Genera un diagrama de flujo que muestra la ejecución paso a paso"
)
async def generate_execution_flow_endpoint(request: VisualizationRequest):
    """
    Genera diagrama de flujo de ejecución.
    
    Muestra:
    - Nodos de proceso, decisión, loops
    - Flujo de control
    - Caminos de ejecución
    """
    try:
        logger.info("Generando flujo de ejecución")
        
        # Parsear código
        parser = PseudocodeParser()
        ast = parser.parse(request.code)
        
        # Generar flujo
        flow_result = generate_execution_flow(ast)
        
        logger.info(
            f"Flujo generado: {flow_result.statistics['total_nodes']} nodos, "
            f"{flow_result.statistics['total_edges']} aristas"
        )
        
        # Renderizar
        viz_format = request.options.format if request.options else "svg"
        render_format = VizRenderFormat(viz_format)
        render_result = render_diagram(flow_result, format=render_format)
        
        content = render_result.content
        if isinstance(content, bytes):
            content = content.decode('utf-8')
        
        return VisualizationResult(
            type="execution_flow",
            format=viz_format,
            content=content,
            file_path=None,
            statistics=flow_result.statistics,
            metadata={
                "algorithm_name": ast.algorithm.name,
            },
        )
    
    except Exception as e:
        logger.error(f"Error generando flujo de ejecución: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "ExecutionFlowError",
                "message": str(e)
            }
        )

@router.post(
    "/graph",
    response_model=VisualizationResult,
    status_code=status.HTTP_200_OK,
    summary="Generar Grafo de Estructura",
    description="Genera representación gráfica de una estructura de datos"
)
async def generate_graph_endpoint(
    structure_type: str,
    values: Optional[list] = None,
    num_nodes: Optional[int] = None,
    edges_list: Optional[list] = None,
    directed: Optional[bool] = True,
    layout: Optional[str] = "hierarchical",
    render_format: Optional[str] = "svg"
):
    """
    Genera grafo de estructura de datos.
    
    Soporta:
    - Árboles binarios
    - Grafos dirigidos/no dirigidos
    - Listas enlazadas
    """
    try:
        logger.info(f"Generando grafo: {structure_type}")
        
        # Preparar kwargs
        kwargs = {}
        if values:
            kwargs["values"] = values
        if num_nodes:
            kwargs["num_nodes"] = num_nodes
        if edges_list:
            kwargs["edges_list"] = [tuple(edge) for edge in edges_list]
        if directed is not None:
            kwargs["directed"] = directed
        
        # Layout
        try:
            layout_type = LayoutType(layout)
        except ValueError:
            layout_type = LayoutType.HIERARCHICAL
        
        # Generar grafo
        graph_result = generate_graph(
            structure_type=structure_type,
            layout=layout_type,
            **kwargs
        )
        
        logger.info(
            f"Grafo generado: {graph_result.statistics['num_nodes']} nodos, "
            f"{graph_result.statistics['num_edges']} aristas"
        )
        
        # Renderizar
        viz_format = VizRenderFormat(render_format)
        render_result = render_diagram(graph_result, format=viz_format)
        
        content = render_result.content
        if isinstance(content, bytes):
            content = content.decode('utf-8')
        
        return VisualizationResult(
            type="data_structure",
            format=render_format,
            content=content,
            file_path=None,
            statistics=graph_result.statistics,
            metadata={
                "structure_type": structure_type,
                "layout": layout,
            },
        )
    
    except Exception as e:
        logger.error(f"Error generando grafo: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "GraphGenerationError",
                "message": str(e)
            }
        )

@router.get(
    "/formats",
    status_code=status.HTTP_200_OK,
    summary="Listar Formatos de Renderizado",
    description="Retorna los formatos de renderizado disponibles"
)
async def get_render_formats():
    """
    Lista formatos de renderizado soportados.
    
    Returns:
        Lista de formatos disponibles con descripción
    """
    formats = [
        {
            "format": "svg",
            "name": "SVG",
            "description": "Scalable Vector Graphics",
            "mime_type": "image/svg+xml",
            "scalable": True,
            "recommended_for": ["web", "print"]
        },
        {
            "format": "png",
            "name": "PNG",
            "description": "Portable Network Graphics",
            "mime_type": "image/png",
            "scalable": False,
            "recommended_for": ["presentations", "documents"]
        },
        {
            "format": "pdf",
            "name": "PDF",
            "description": "Portable Document Format",
            "mime_type": "application/pdf",
            "scalable": True,
            "recommended_for": ["reports", "print"]
        },
        {
            "format": "dot",
            "name": "DOT",
            "description": "Graphviz DOT Language",
            "mime_type": "text/vnd.graphviz",
            "scalable": True,
            "recommended_for": ["processing", "editing"]
        },
        {
            "format": "mermaid",
            "name": "Mermaid",
            "description": "Mermaid Diagram",
            "mime_type": "text/plain",
            "scalable": True,
            "recommended_for": ["markdown", "documentation"]
        },
        {
            "format": "json",
            "name": "JSON",
            "description": "JavaScript Object Notation",
            "mime_type": "application/json",
            "scalable": True,
            "recommended_for": ["data", "api"]
        }
    ]

    return {
        "success": True,
        "formats": formats,
        "total": len(formats)
    }

@router.get(
    "/layouts",
    status_code=status.HTTP_200_OK,
    summary="Listar Tipos de Layout",
    description="Retorna los tipos de layout disponibles para grafos"
)
async def get_layout_types():
    """
    Lista tipos de layout soportados.
    
    Returns:
        Lista de layouts disponibles
    """
    layouts = [
        {
            "type": "hierarchical",
            "name": "Hierarchical",
            "description": "Layout jerárquico (árboles)",
            "best_for": ["trees", "dags"]
        },
        {
            "type": "circular",
            "name": "Circular",
            "description": "Nodos en círculo",
            "best_for": ["cycles", "small_graphs"]
        },
        {
            "type": "spring",
            "name": "Spring",
            "description": "Basado en fuerzas físicas",
            "best_for": ["general", "undirected"]
        },
        {
            "type": "shell",
            "name": "Shell",
            "description": "Capas concéntricas",
            "best_for": ["hierarchical", "layered"]
        },
        {
            "type": "spectral",
            "name": "Spectral",
            "description": "Basado en eigenvalores",
            "best_for": ["analysis", "clustering"]
        },
        {
            "type": "kamada_kawai",
            "name": "Kamada-Kawai",
            "description": "Optimización de distancias",
            "best_for": ["aesthetics", "small_graphs"]
        }
    ]

    return {
        "success": True,
        "layouts": layouts,
        "total": len(layouts)
    }