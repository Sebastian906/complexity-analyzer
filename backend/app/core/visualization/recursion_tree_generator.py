"""
Recursion Tree Generator - Generador de Árboles de Recursión

Genera árboles de recursión para visualizar llamadas recursivas
y ayudar en el análisis de complejidad.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum

from app.core.parser.ast_nodes import (
    ASTNode,
    ProgramNode,
    AlgorithmNode,
    CallStatementNode,
    FunctionCallNode
)
from app.core.visualization.tree_builder import TreeBuilder, TreeNode, NodeType
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class RecursionType(str, Enum):
    """Tipos de recursión"""
    LINEAR = "linear"          # T(n) = T(n-1) + f(n)
    BINARY = "binary"          # T(n) = 2T(n/2) + f(n)
    MULTIPLE = "multiple"      # T(n) = aT(n/b) + f(n)
    NESTED = "nested"          # Recursión anidada
    MUTUAL = "mutual"          # Recursión mutua
    TAIL = "tail"              # Recursión de cola

@dataclass
class RecursionTreeNode(TreeNode):
    """
    Nodo de árbol de recursión.
    
    Extiende TreeNode con información específica de recursión.
    """
    call_args: List[Any] = field(default_factory=list)
    work_done: str = "O(1)"
    is_base_case: bool = False
    call_count: int = 1

@dataclass
class RecursionTreeResult:
    """
    Resultado de generación de árbol de recursión.
    
    Attributes:
        root: Nodo raíz del árbol
        recursion_type: Tipo de recursión detectado
        max_depth: Profundidad máxima
        total_calls: Total de llamadas
        base_cases: Número de casos base
        work_per_level: Trabajo por nivel
        total_work: Trabajo total
        statistics: Estadísticas del árbol
    """
    root: RecursionTreeNode
    recursion_type: RecursionType
    max_depth: int
    total_calls: int
    base_cases: int
    work_per_level: List[str]
    total_work: str
    statistics: Dict[str, Any]

class RecursionTreeGenerator:
    """
    Generador de árboles de recursión.

    Analiza un algoritmo recursivo y genera su árbol de llamadas
    para visualización y análisis de complejidad.
    """

    def __init__(self, max_depth: int = 10, max_nodes: int = 100):
        """
        Inicializa el generador.

        Args:
            max_depth: Profundidad máxima permitida
            max_nodes: Número máximo de nodos
        """
        self.max_depth = max_depth
        self.max_nodes = max_nodes
        self.tree_builder = TreeBuilder()
        self.node_count = 0

        logger.debug(f"RecursionTreeGenerator inicializado (max_depth={max_depth}, max_nodes={max_nodes})")

    def generate(
        self,
        ast: ProgramNode,
        start_value: Optional[int] = None
    ) -> RecursionTreeResult:
        """
        Genera árbol de recursión desde AST.

        Args:
            ast: AST del algoritmo
            start_value: Valor inicial para la primera llamada

        Returns:
            RecursionTreeResult: Resultado de la generación
        """
        logger.info("Generando árbol de recursión")

        if not ast.algorithm:
            raise ValueError("AST no contiene algoritmo")

        algorithm = ast.algorithm

        # Detectar tipo de recursión
        recursion_type = self._detect_recursion_type(algorithm)
        logger.debug(f"Tipo de recursión detectado: {recursion_type.value}")

        # Determinar valor inicial
        if start_value is None:
            start_value = self._determine_start_value(recursion_type)

        # Construir árbol
        root = self._build_recursion_tree(
            algorithm,
            start_value,
            depth=0
        )

        # Calcular estadísticas
        statistics = self._calculate_statistics(root)

        # Calcular trabajo por nivel
        work_per_level = self._calculate_work_per_level(root, recursion_type)

        # Calcular trabajo total
        total_work = self._calculate_total_work(work_per_level)

        result = RecursionTreeResult(
            root=root,
            recursion_type=recursion_type,
            max_depth=statistics["max_depth"],
            total_calls=statistics["total_calls"],
            base_cases=statistics["base_cases"],
            work_per_level=work_per_level,
            total_work=total_work,
            statistics=statistics
        )

        logger.info(f"Árbol generado: {result.total_calls} nodos, profundidad {result.max_depth}")

        return result

    def _detect_recursion_type(self, algorithm: AlgorithmNode) -> RecursionType:
        """Detecta el tipo de recursión del algoritmo"""
        recursive_calls = self._find_recursive_calls(algorithm)

        if len(recursive_calls) == 0:
            return RecursionType.LINEAR

        if len(recursive_calls) == 1:
            # Analizar el argumento de la llamada
            call = recursive_calls[0]
            if self._is_tail_recursion(call, algorithm):
                return RecursionType.TAIL
            return RecursionType.LINEAR

        if len(recursive_calls) == 2:
            return RecursionType.BINARY

        return RecursionType.MULTIPLE

    def _find_recursive_calls(self, algorithm: AlgorithmNode) -> List[ASTNode]:
        """Encuentra llamadas recursivas en el algoritmo"""
        recursive_calls = []

        def visit(node: ASTNode):
            if isinstance(node, CallStatementNode):
                if node.function_name == algorithm.name:
                    recursive_calls.append(node)
            elif isinstance(node, FunctionCallNode):
                if node.function_name == algorithm.name:
                    recursive_calls.append(node)

            # Recorrer hijos
            if hasattr(node, 'children'):
                for child in node.children:
                    if isinstance(child, ASTNode):
                        visit(child)

            # Recorrer atributos específicos
            for attr_name in ['body', 'then_block', 'else_block', 'statements']:
                attr = getattr(node, attr_name, None)
                if attr:
                    if isinstance(attr, list):
                        for item in attr:
                            if isinstance(item, ASTNode):
                                visit(item)
                    elif isinstance(attr, ASTNode):
                        visit(attr)

        if algorithm.body:
            visit(algorithm.body)

        return recursive_calls

    def _is_tail_recursion(self, call: ASTNode, algorithm: AlgorithmNode) -> bool:
        """Verifica si una llamada es recursión de cola"""
        # Simplificado: considera recursión de cola si la llamada está al final
        # En una implementación real, verificaríamos si es la última operación
        return False

    def _determine_start_value(self, recursion_type: RecursionType) -> int:
        """Determina valor inicial apropiado según tipo de recursión"""
        if recursion_type in [RecursionType.LINEAR, RecursionType.TAIL]:
            return 4  # n pequeño para recursión lineal
        else:
            return 8  # Potencia de 2 para divide y vencerás

    def _build_recursion_tree(
        self,
        algorithm: AlgorithmNode,
        n: int,
        depth: int
    ) -> RecursionTreeNode:
        """
        Construye el árbol de recursión recursivamente.

        Args:
            algorithm: Algoritmo a analizar
            n: Valor del parámetro
            depth: Profundidad actual

        Returns:
            RecursionTreeNode: Nodo raíz del subárbol
        """
        self.node_count += 1

        # Verificar límites
        if depth >= self.max_depth or self.node_count >= self.max_nodes:
            return self._create_truncated_node(n, depth)

        # Verificar caso base
        is_base_case = n <= 1

        node = RecursionTreeNode(
            id=f"call_{self.node_count}",
            label=f"{algorithm.name}({n})",
            node_type=NodeType.CALL if not is_base_case else NodeType.RETURN,
            value=n,
            call_args=[n],
            work_done="O(1)" if is_base_case else "O(n)",
            is_base_case=is_base_case,
            depth=depth
        )

        if is_base_case:
            return node

        # Generar llamadas recursivas según tipo de recursión
        recursion_type = self._detect_recursion_type(algorithm)

        if recursion_type == RecursionType.LINEAR:
            # T(n) = T(n-1) + f(n)
            child = self._build_recursion_tree(algorithm, n - 1, depth + 1)
            node.add_child(child)

        elif recursion_type == RecursionType.BINARY:
            # T(n) = 2T(n/2) + f(n)
            left = self._build_recursion_tree(algorithm, n // 2, depth + 1)
            right = self._build_recursion_tree(algorithm, n // 2, depth + 1)
            node.add_child(left)
            node.add_child(right)

        elif recursion_type == RecursionType.MULTIPLE:
            # T(n) = aT(n/b) + f(n)
            # Por defecto: 3 llamadas
            for _ in range(3):
                child = self._build_recursion_tree(algorithm, n // 2, depth + 1)
                node.add_child(child)

        return node

    def _create_truncated_node(self, n: int, depth: int) -> RecursionTreeNode:
        """Crea nodo truncado cuando se alcanzan límites"""
        self.node_count += 1
        return RecursionTreeNode(
            id=f"truncated_{self.node_count}",
            label=f"... ({n})",
            node_type=NodeType.LEAF,
            value=n,
            is_base_case=True,
            depth=depth,
            metadata={"truncated": True}
        )

    def _calculate_statistics(self, root: RecursionTreeNode) -> Dict[str, Any]:
        """Calcula estadísticas del árbol"""
        nodes = self._collect_nodes(root)

        return {
            "total_calls": len(nodes),
            "max_depth": max(node.depth for node in nodes),
            "base_cases": sum(1 for node in nodes if node.is_base_case),
            "recursive_calls": sum(1 for node in nodes if not node.is_base_case),
            "truncated": sum(1 for node in nodes if node.metadata.get("truncated", False))
        }

    def _collect_nodes(self, node: RecursionTreeNode) -> List[RecursionTreeNode]:
        """Colecta todos los nodos del árbol"""
        nodes = [node]
        for child in node.children:
            nodes.extend(self._collect_nodes(child))
        return nodes

    def _calculate_work_per_level(
        self,
        root: RecursionTreeNode,
        recursion_type: RecursionType
    ) -> List[str]:
        """Calcula trabajo por nivel del árbol"""
        max_depth = root.max_depth()
        work_per_level = []

        for level in range(max_depth + 1):
            nodes_at_level = self._get_nodes_at_level(root, level)

            if recursion_type == RecursionType.LINEAR:
                # Cada nivel tiene 1 nodo con trabajo O(n-level)
                work_per_level.append(f"O(n-{level})")

            elif recursion_type == RecursionType.BINARY:
                # Cada nivel tiene 2^level nodos con trabajo O(n/2^level)
                num_nodes = len(nodes_at_level)
                work_per_level.append(f"{num_nodes} × O(n/{2**level}) = O(n)")

            else:
                work_per_level.append(f"O(n)")

        return work_per_level

    def _get_nodes_at_level(
        self,
        node: RecursionTreeNode,
        target_level: int
    ) -> List[RecursionTreeNode]:
        """Obtiene nodos en un nivel específico"""
        if node.depth == target_level:
            return [node]

        nodes = []
        for child in node.children:
            nodes.extend(self._get_nodes_at_level(child, target_level))

        return nodes

    def _calculate_total_work(self, work_per_level: List[str]) -> str:
        """Calcula trabajo total del árbol"""
        # Simplificado: suma simbólica
        # En realidad se aplicaría análisis de sumas

        if len(work_per_level) == 0:
            return "O(1)"

        # Detectar patrón
        if all("O(n)" in w for w in work_per_level):
            return f"O(n × {len(work_per_level)}) = O(n log n)"

        return "O(n)"

def generate_recursion_tree(
    ast: ProgramNode,
    start_value: Optional[int] = None,
    max_depth: int = 10
) -> RecursionTreeResult:
    """
    Helper para generar árbol de recursión.

    Args:
        ast: AST del algoritmo
        start_value: Valor inicial
        max_depth: Profundidad máxima
        
    Returns:
        RecursionTreeResult: Resultado de la generación
    """
    generator = RecursionTreeGenerator(max_depth=max_depth)
    return generator.generate(ast, start_value)