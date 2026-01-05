"""
Linked List Detector - Detector de Listas Enlazadas

Detecta el uso de listas enlazadas en el algoritmo mediante análisis estático
del AST.
"""

from typing import Optional, List, Set

from app.core.parser.ast_nodes import (
    ASTNode, ProgramNode, AlgorithmNode, 
    ForLoopNode, ParameterNode, ObjectAccessNode
)
from app.core.data_structures.base_structure import (
    BaseStructureDetector,
    StructureType,
    StructureMatch,
    StructureIndicator,
    OperationComplexity
)

class LinkedListDetector(BaseStructureDetector):
    """Detector de Listas Enlazadas"""

    def __init__(self):
        super().__init__()
        self.structure_type = StructureType.LINKED_LIST
        self.structure_name = "Lista Enlazada"
        self.description = "Estructura con nodos y punteros next/prev"

        self.keywords = {
            "node", "nodo", "next", "siguiente", "prev", 
            "anterior", "head", "cabeza", "tail", "cola"
        }

        self.indicators = [
            StructureIndicator("Acceso a .next", "Navegación por next", 3.0),
            StructureIndicator("Clase Node", "Definición de nodo", 2.5),
            StructureIndicator("Travesía secuencial", "while node != null", 2.0),
            StructureIndicator("Variable node/nodo", "Nombres típicos", 1.5),
            StructureIndicator("Inserción con enlaces", "Manipulación next", 1.5),
        ]

        self.operation_complexities = [
            OperationComplexity("Inserción inicio", "O(1)", "O(1)", "O(1)", "O(1)"),
            OperationComplexity("Inserción final", "O(1)", "O(n)", "O(n)", "O(1)"),
            OperationComplexity("Búsqueda", "O(1)", "O(n)", "O(n)", "O(1)"),
            OperationComplexity("Eliminación", "O(1)", "O(n)", "O(n)", "O(1)"),
        ]

    def detect(self, ast: ProgramNode) -> Optional[StructureMatch]:
        algorithm = ast.algorithm
        if not algorithm:
            return None

        vars_found = set()
        operations = []
        evidence = []
        indicators = [StructureIndicator(name=i.name, description=i.description, weight=i.weight) 
                     for i in self.indicators]

        # Buscar accesos .next
        next_accesses = self._find_next_accesses(algorithm.body)
        if next_accesses:
            indicators[0].found = True
            evidence.append(f"Accesos a .next: {len(next_accesses)}")
            operations.extend(next_accesses[:3])

        # Buscar clases Node
        if self._has_node_class(ast):
            indicators[1].found = True
            evidence.append("Clase Node definida")

        # Buscar travesía secuencial
        if self._has_traversal(algorithm.body):
            indicators[2].found = True
            evidence.append("Patrón de travesía detectado")

        # Variables con nombres node
        named_vars = self._find_node_vars(algorithm)
        if named_vars:
            indicators[3].found = True
            vars_found.update(named_vars)
            evidence.append(f"Variables node: {', '.join(named_vars)}")

        confidence = self._calculate_confidence(indicators)
        if confidence < 0.3:
            return None

        found, missing = self._split_indicators(indicators)

        return StructureMatch(
            structure_type=self.structure_type,
            structure_name=self.structure_name,
            confidence=confidence,
            variables=list(vars_found) if vars_found else ["node"],
            indicators_found=found,
            indicators_missing=missing,
            operations=operations,
            operation_complexities=self.operation_complexities,
            reasoning=self._build_reasoning(found, missing),
            properties={"next_accesses": len(next_accesses)},
            code_evidence=evidence
        )

    def _find_next_accesses(self, node):
        accesses = []
        def visit(n):
            # Check for ObjectAccessNode with field_name "next"
            if isinstance(n, ObjectAccessNode):
                if 'next' in n.field_name.lower():
                    accesses.append(f"{n.object_name}.next")
            # Also check any node with field_name attribute
            elif hasattr(n, 'field_name') and 'next' in str(n.field_name).lower():
                accesses.append("node.next")
            # Recursively visit all child nodes
            for attr in ['statements', 'then_block', 'else_block', 'body', 'value', 'expression', 'target']:
                if hasattr(n, attr):
                    child = getattr(n, attr)
                    if isinstance(child, list):
                        for item in child:
                            visit(item)
                    elif child is not None:
                        visit(child)
        visit(node)
        return accesses

    def _has_node_class(self, ast):
        if hasattr(ast, 'classes'):
            return any('node' in c.name.lower() for c in ast.classes)
        return False

    def _has_traversal(self, node):
        # Buscar while con condición node != null
        def visit(n):
            if hasattr(n, '__class__') and 'While' in n.__class__.__name__:
                return True
            if hasattr(n, 'statements'):
                return any(visit(s) for s in n.statements)
            return False
        return visit(node)

    def _find_node_vars(self, algo):
        vars = []
        for p in algo.parameters:
            name = p.name if hasattr(p, 'name') else str(p)
            if any(k in name.lower() for k in self.keywords):
                vars.append(name)
        return vars