"""
Execution Flow Generator - Generador de Flujo de Ejecución

Genera diagramas de flujo que muestran el camino de ejecución
paso a paso de un algoritmo.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from enum import Enum

from app.core.parser.ast_nodes import (
    ASTNode,
    ProgramNode,
    AlgorithmNode,
    BlockNode,
    ForLoopNode,
    WhileLoopNode,
    IfStatementNode,
    AssignmentNode,
    CallStatementNode,
    ReturnStatementNode
)
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class FlowNodeType(str, Enum):
    """Tipos de nodos de flujo"""
    START = "start"
    END = "end"
    PROCESS = "process"
    DECISION = "decision"
    LOOP_START = "loop_start"
    LOOP_END = "loop_end"
    CALL = "call"
    RETURN = "return"
    INPUT = "input"
    OUTPUT = "output"

@dataclass
class FlowNode:
    """
    Nodo de flujo de ejecución.
    
    Attributes:
        id: Identificador único
        label: Etiqueta visible
        node_type: Tipo de nodo
        code: Código asociado
        metadata: Metadatos adicionales
    """
    id: str
    label: str
    node_type: FlowNodeType
    code: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario"""
        return {
            "id": self.id,
            "label": self.label,
            "type": self.node_type.value,
            "code": self.code,
            "metadata": self.metadata
        }

@dataclass
class FlowEdge:
    """
    Arista de flujo de ejecución.

    Attributes:
        source: ID del nodo origen
        target: ID del nodo destino
        label: Etiqueta de la arista (condición)
        edge_type: Tipo de arista
    """
    source: str
    target: str
    label: Optional[str] = None
    edge_type: str = "default"

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario"""
        return {
            "source": self.source,
            "target": self.target,
            "label": self.label,
            "type": self.edge_type
        }

@dataclass
class ExecutionFlowResult:
    """
    Resultado de generación de flujo.

    Attributes:
        nodes: Lista de nodos
        edges: Lista de aristas
        start_node: ID del nodo inicial
        end_nodes: IDs de nodos finales
        statistics: Estadísticas del flujo
    """
    nodes: List[FlowNode]
    edges: List[FlowEdge]
    start_node: str
    end_nodes: List[str]
    statistics: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario"""
        return {
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": [edge.to_dict() for edge in self.edges],
            "start_node": self.start_node,
            "end_nodes": self.end_nodes,
            "statistics": self.statistics
        }

class ExecutionFlowGenerator:
    """
    Generador de flujo de ejecución.
    
    Analiza un AST y genera un grafo de flujo que representa
    la ejecución paso a paso del algoritmo.
    """

    def __init__(self):
        """Inicializa el generador"""
        self.nodes: List[FlowNode] = []
        self.edges: List[FlowEdge] = []
        self.node_counter = 0
        self.current_node: Optional[str] = None

        logger.debug("ExecutionFlowGenerator inicializado")

    def generate(self, ast: ProgramNode) -> ExecutionFlowResult:
        """
        Genera flujo de ejecución desde AST.

        Args:
            ast: AST del algoritmo

        Returns:
            ExecutionFlowResult: Resultado de la generación
        """
        logger.info("Generando flujo de ejecución")

        if not ast.algorithm:
            raise ValueError("AST no contiene algoritmo")

        # Reset estado
        self.nodes = []
        self.edges = []
        self.node_counter = 0

        # Crear nodo START
        start_node = self._create_node(
            label=f"START: {ast.algorithm.name}",
            node_type=FlowNodeType.START,
            code=f"algorithm {ast.algorithm.name}"
        )
        self.current_node = start_node.id

        # Procesar cuerpo del algoritmo
        if ast.algorithm.body:
            self._process_block(ast.algorithm.body)

        # Crear nodo END
        end_node = self._create_node(
            label="END",
            node_type=FlowNodeType.END
        )

        # Conectar último nodo con END
        if self.current_node:
            self._add_edge(self.current_node, end_node.id)

        # Calcular estadísticas
        statistics = self._calculate_statistics()

        result = ExecutionFlowResult(
            nodes=self.nodes,
            edges=self.edges,
            start_node=start_node.id,
            end_nodes=[end_node.id],
            statistics=statistics
        )

        logger.info(f"Flujo generado: {len(self.nodes)} nodos, {len(self.edges)} aristas")

        return result

    def _create_node(
        self,
        label: str,
        node_type: FlowNodeType,
        code: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> FlowNode:
        """Crea un nuevo nodo de flujo"""
        self.node_counter += 1
        node = FlowNode(
            id=f"node_{self.node_counter}",
            label=label,
            node_type=node_type,
            code=code,
            metadata=metadata or {}
        )
        self.nodes.append(node)
        return node

    def _add_edge(
        self,
        source: str,
        target: str,
        label: Optional[str] = None,
        edge_type: str = "default"
    ) -> None:
        """Agrega una arista de flujo"""
        edge = FlowEdge(
            source=source,
            target=target,
            label=label,
            edge_type=edge_type
        )
        self.edges.append(edge)

    def _process_block(self, block: BlockNode) -> None:
        """Procesa un bloque de código"""
        for statement in block.statements:
            self._process_statement(statement)

    def _process_statement(self, statement: ASTNode) -> None:
        """Procesa un statement"""
        if isinstance(statement, AssignmentNode):
            self._process_assignment(statement)

        elif isinstance(statement, ForLoopNode):
            self._process_for_loop(statement)

        elif isinstance(statement, WhileLoopNode):
            self._process_while_loop(statement)

        elif isinstance(statement, IfStatementNode):
            self._process_if_statement(statement)

        elif isinstance(statement, CallStatementNode):
            self._process_call(statement)

        elif isinstance(statement, ReturnStatementNode):
            self._process_return(statement)

    def _process_assignment(self, node: AssignmentNode) -> None:
        """Procesa asignación"""
        process_node = self._create_node(
            label=f"{node.target} ← ...",
            node_type=FlowNodeType.PROCESS,
            code=str(node)
        )

        if self.current_node:
            self._add_edge(self.current_node, process_node.id)

        self.current_node = process_node.id

    def _process_for_loop(self, node: ForLoopNode) -> None:
        """Procesa ciclo FOR"""
        # Nodo inicio de loop
        loop_start = self._create_node(
            label=f"FOR {node.variable} ← ... TO ...",
            node_type=FlowNodeType.LOOP_START,
            code=f"for {node.variable} ← {node.start} to {node.end}"
        )

        if self.current_node:
            self._add_edge(self.current_node, loop_start.id)

        # Nodo condición
        condition_node = self._create_node(
            label=f"{node.variable} <= ?",
            node_type=FlowNodeType.DECISION,
            code=f"condition: {node.variable} <= end"
        )

        self._add_edge(loop_start.id, condition_node.id)

        # Procesar cuerpo
        prev_current = self.current_node
        self.current_node = condition_node.id

        if node.body:
            self._process_block(node.body)

        # Loop back
        if self.current_node:
            self._add_edge(
                self.current_node,
                condition_node.id,
                label="continue",
                edge_type="loop_back"
            )

        # Nodo salida de loop
        loop_end = self._create_node(
            label="END FOR",
            node_type=FlowNodeType.LOOP_END
        )

        self._add_edge(
            condition_node.id,
            loop_end.id,
            label="false",
            edge_type="exit"
        )

        self.current_node = loop_end.id

    def _process_while_loop(self, node: WhileLoopNode) -> None:
        """Procesa ciclo WHILE"""
        # Nodo condición
        condition_node = self._create_node(
            label="WHILE condition",
            node_type=FlowNodeType.DECISION,
            code=f"while ({node.condition})"
        )

        if self.current_node:
            self._add_edge(self.current_node, condition_node.id)

        # Procesar cuerpo
        prev_current = self.current_node
        self.current_node = condition_node.id

        if node.body:
            self._process_block(node.body)

        # Loop back
        if self.current_node:
            self._add_edge(
                self.current_node,
                condition_node.id,
                label="continue",
                edge_type="loop_back"
            )

        # Nodo salida
        exit_node = self._create_node(
            label="END WHILE",
            node_type=FlowNodeType.LOOP_END
        )

        self._add_edge(
            condition_node.id,
            exit_node.id,
            label="false",
            edge_type="exit"
        )

        self.current_node = exit_node.id

    def _process_if_statement(self, node: IfStatementNode) -> None:
        """Procesa condicional IF"""
        # Nodo decisión
        decision_node = self._create_node(
            label="IF condition",
            node_type=FlowNodeType.DECISION,
            code=f"if ({node.condition})"
        )

        if self.current_node:
            self._add_edge(self.current_node, decision_node.id)

        # Procesar rama THEN
        self.current_node = decision_node.id
        if node.then_block:
            self._process_block(node.then_block)
        then_exit = self.current_node

        # Procesar rama ELSE
        else_exit = decision_node.id
        if node.else_block:
            self.current_node = decision_node.id
            self._add_edge(
                decision_node.id,
                decision_node.id,  # Placeholder
                label="false",
                edge_type="branch"
            )
            self._process_block(node.else_block)
            else_exit = self.current_node

        # Nodo convergencia
        merge_node = self._create_node(
            label="END IF",
            node_type=FlowNodeType.PROCESS
        )

        if then_exit:
            self._add_edge(then_exit, merge_node.id)
        if else_exit and else_exit != decision_node.id:
            self._add_edge(else_exit, merge_node.id)

        self.current_node = merge_node.id

    def _process_call(self, node: CallStatementNode) -> None:
        """Procesa llamada a función"""
        call_node = self._create_node(
            label=f"CALL {node.function_name}",
            node_type=FlowNodeType.CALL,
            code=f"call {node.function_name}(...)"
        )

        if self.current_node:
            self._add_edge(self.current_node, call_node.id)

        self.current_node = call_node.id

    def _process_return(self, node: ReturnStatementNode) -> None:
        """Procesa return"""
        return_node = self._create_node(
            label="RETURN",
            node_type=FlowNodeType.RETURN,
            code="return ..."
        )

        if self.current_node:
            self._add_edge(self.current_node, return_node.id)

        self.current_node = return_node.id

    def _calculate_statistics(self) -> Dict[str, Any]:
        """Calcula estadísticas del flujo"""
        node_types = {}
        for node in self.nodes:
            node_type = node.node_type.value
            node_types[node_type] = node_types.get(node_type, 0) + 1

        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "node_types": node_types,
            "has_loops": any(node.node_type == FlowNodeType.LOOP_START for node in self.nodes),
            "has_decisions": any(node.node_type == FlowNodeType.DECISION for node in self.nodes),
            "has_calls": any(node.node_type == FlowNodeType.CALL for node in self.nodes)
        }

def generate_execution_flow(ast: ProgramNode) -> ExecutionFlowResult:
    """
    Helper para generar flujo de ejecución.

    Args:
        ast: AST del algoritmo
        
    Returns:
        ExecutionFlowResult: Resultado de la generación
    """
    generator = ExecutionFlowGenerator()
    return generator.generate(ast)