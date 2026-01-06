"""
API Endpoints - Visualización

Endpoints REST para generar visualizaciones de algoritmos.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from enum import Enum

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

# Enums para API

class RenderFormat(str, Enum):
    """Formatos de renderizado"""
    SVG = "svg"
    PNG = "png"
    PDF = "pdf"
    DOT = "dot"
    MERMAID = "mermaid"
    JSON = "json"

class VisualizationType(str, Enum):
    """Tipos de visualización"""
    RECURSION_TREE = "recursion_tree"
    EXECUTION_FLOW = "execution_flow"
    DATA_STRUCTURE = "data_structure"

# Schemas

class RecursionTreeRequest(BaseModel):
    """Request para árbol de recursión"""
    code: str = Field(..., description="Código del algoritmo en pseudocódigo")
    start_value: Optional[int] = Field(8, description="Valor inicial para la recursión")
    max_depth: Optional[int] = Field(10, description="Profundidad máxima del árbol")
    render_format: RenderFormat = Field(RenderFormat.JSON, description="Formato de renderizado")

class ExecutionFlowRequest(BaseModel):
    """Request para flujo de ejecución"""
    code: str = Field(..., description="Código del algoritmo en pseudocódigo")
    render_format: RenderFormat = Field(RenderFormat.JSON, description="Formato de renderizado")

class GraphGenerationRequest(BaseModel):
    """Request para generación de grafo"""
    structure_type: str = Field(..., description="Tipo de estructura (tree, graph, linked_list)")
    values: Optional[list] = Field(None, description="Valores para la estructura")
    num_nodes: Optional[int] = Field(None, description="Número de nodos (para grafos)")
    edges_list: Optional[list] = Field(None, description="Lista de aristas")
    directed: Optional[bool] = Field(True, description="Si el grafo es dirigido")
    layout: Optional[str] = Field("hierarchical", description="Tipo de layout")
    render_format: RenderFormat = Field(RenderFormat.JSON, description="Formato de renderizado")

class VisualizationResponse(BaseModel):
    """Response genérico de visualización"""
    success: bool
    visualization_type: str
    render_format: str
    content: str
    statistics: dict
    message: str

# Endpoints

@router.post(
    "/recursion-tree",
    response_model=VisualizationResponse,
    status_code=status.HTTP_200_OK,
    summary="Generar Árbol de Recursión",
    description="Genera y renderiza un árbol de recursión para un algoritmo recursivo"
)
async def generate_recursion_tree_endpoint(request: RecursionTreeRequest):
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
        
        # Generar árbol de recursión
        from app.core.visualization import RecursionTreeGenerator
        
        generator = RecursionTreeGenerator(max_depth=request.max_depth)
        tree_result = generator.generate(ast, start_value=request.start_value)
        
        logger.info(
            f"Árbol generado: {tree_result.total_calls} llamadas, "
            f"prof. {tree_result.max_depth}"
        )
        
        # Renderizar
        viz_format = VizRenderFormat(request.render_format.value)
        render_result = render_diagram(tree_result, format=viz_format)
        
        # Construir respuesta
        return VisualizationResponse(
            success=True,
            visualization_type="recursion_tree",
            render_format=request.render_format.value,
            content=render_result.content if isinstance(render_result.content, str) else render_result.content.decode('utf-8'),
            statistics={
                "recursion_type": tree_result.recursion_type.value,
                "total_calls": tree_result.total_calls,
                "max_depth": tree_result.max_depth,
                "base_cases": tree_result.base_cases,
                "total_work": tree_result.total_work,
                "work_per_level": tree_result.work_per_level
            },
            message="Árbol de recursión generado exitosamente"
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
    response_model=VisualizationResponse,
    status_code=status.HTTP_200_OK,
    summary="Generar Flujo de Ejecución",
    description="Genera un diagrama de flujo que muestra la ejecución paso a paso"
)
async def generate_execution_flow_endpoint(request: ExecutionFlowRequest):
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
        viz_format = VizRenderFormat(request.render_format.value)
        render_result = render_diagram(flow_result, format=viz_format)
        
        return VisualizationResponse(
            success=True,
            visualization_type="execution_flow",
            render_format=request.render_format.value,
            content=render_result.content if isinstance(render_result.content, str) else render_result.content.decode('utf-8'),
            statistics=flow_result.statistics,
            message="Flujo de ejecución generado exitosamente"
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
    response_model=VisualizationResponse,
    status_code=status.HTTP_200_OK,
    summary="Generar Grafo de Estructura",
    description="Genera representación gráfica de una estructura de datos"
)
async def generate_graph_endpoint(request: GraphGenerationRequest):
    """
    Genera grafo de estructura de datos.
    
    Soporta:
    - Árboles binarios
    - Grafos dirigidos/no dirigidos
    - Listas enlazadas
    """
    try:
        logger.info(f"Generando grafo: {request.structure_type}")
        
        # Preparar kwargs
        kwargs = {}
        if request.values:
            kwargs["values"] = request.values
        if request.num_nodes:
            kwargs["num_nodes"] = request.num_nodes
        if request.edges_list:
            kwargs["edges_list"] = [tuple(edge) for edge in request.edges_list]
        if request.directed is not None:
            kwargs["directed"] = request.directed
        
        # Layout
        try:
            layout = LayoutType(request.layout)
        except ValueError:
            layout = LayoutType.HIERARCHICAL
        
        # Generar grafo
        graph_result = generate_graph(
            structure_type=request.structure_type,
            layout=layout,
            **kwargs
        )
        
        logger.info(
            f"Grafo generado: {graph_result.statistics['num_nodes']} nodos, "
            f"{graph_result.statistics['num_edges']} aristas"
        )
        
        # Renderizar
        viz_format = VizRenderFormat(request.render_format.value)
        render_result = render_diagram(graph_result, format=viz_format)
        
        return VisualizationResponse(
            success=True,
            visualization_type="data_structure",
            render_format=request.render_format.value,
            content=render_result.content if isinstance(render_result.content, str) else render_result.content.decode('utf-8'),
            statistics=graph_result.statistics,
            message=f"Grafo de {request.structure_type} generado exitosamente"
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