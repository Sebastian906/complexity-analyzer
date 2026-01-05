"""
Graph Detector - Detector de Grafos

Detecta el uso de grafos en el algoritmo mediante análisis estático
del AST.
"""

from typing import Optional, List, Set

from app.core.parser.ast_nodes import (
    ASTNode, ProgramNode, 
    AlgorithmNode, CallStatementNode
)
from app.core.data_structures.base_structure import (
    BaseStructureDetector,
    StructureType,
    StructureMatch,
    StructureIndicator,
    OperationComplexity
)

class GraphDetector(BaseStructureDetector):
    """Detector de Grafos"""

    def __init__(self):
        super().__init__()
        self.structure_type = StructureType.GRAPH
        self.structure_name = "Grafo"
        self.description = "Estructura con nodos y aristas"

        self.keywords = {
            "graph", "grafo", "vertex", "vertice", "edge",
            "arista", "adj", "adjacency", "adyacencia", "neighbor"
        }

        self.indicators = [
            StructureIndicator("Lista adyacencia", "adj[] o neighbors", 3.0),
            StructureIndicator("Matriz adyacencia", "graph[i][j]", 2.5),
            StructureIndicator("Variable graph", "Nombre típico", 2.0),
            StructureIndicator("Travesía BFS/DFS", "Patrón de recorrido", 2.0),
            StructureIndicator("Visitados/Marcados", "visited[]", 1.5),
        ]

        self.operation_complexities = [
            OperationComplexity("Agregar vértice", "O(1)", "O(1)", "O(1)", "O(1)"),
            OperationComplexity("Agregar arista", "O(1)", "O(1)", "O(1)", "O(1)"),
            OperationComplexity("BFS/DFS", "O(V+E)", "O(V+E)", "O(V+E)", "O(V)"),
        ]

    def detect(self, ast: ProgramNode) -> Optional[StructureMatch]:
        algorithm = ast.algorithm
        if not algorithm:
            return None

        vars_found = set()
        evidence = []
        indicators = [StructureIndicator(name=i.name, description=i.description, weight=i.weight) 
                     for i in self.indicators]

        # Variables graph
        named_vars = [p.name if hasattr(p, 'name') else str(p) 
                     for p in algorithm.parameters
                     if any(k in str(p).lower() for k in self.keywords)]

        if named_vars:
            indicators[2].found = True
            vars_found.update(named_vars)
            evidence.append(f"Variables graph: {', '.join(named_vars)}")

        # Buscar visited[]
        if self._has_visited_array(algorithm.body):
            indicators[4].found = True
            evidence.append("Array visited detectado")

        confidence = self._calculate_confidence(indicators)
        if confidence < 0.25:
            return None

        found, missing = self._split_indicators(indicators)

        return StructureMatch(
            structure_type=self.structure_type,
            structure_name=self.structure_name,
            confidence=confidence,
            variables=list(vars_found) if vars_found else ["graph"],
            indicators_found=found,
            indicators_missing=missing,
            operations=[],
            operation_complexities=self.operation_complexities,
            reasoning=self._build_reasoning(found, missing),
            properties={},
            code_evidence=evidence
        )

    def _has_visited_array(self, node):
        def visit(n):
            # Check variable names
            if hasattr(n, 'name') and 'visit' in str(n.name).lower():
                return True
            # Check assignment targets
            if hasattr(n, 'target'):
                target_str = str(n.target).lower()
                if 'visit' in target_str:
                    return True
            # Recursively check all child nodes
            for attr in ['statements', 'then_block', 'else_block', 'body']:
                if hasattr(n, attr):
                    child = getattr(n, attr)
                    if isinstance(child, list):
                        if any(visit(s) for s in child):
                            return True
                    elif child is not None:
                        if visit(child):
                            return True
            return False
        return visit(node)