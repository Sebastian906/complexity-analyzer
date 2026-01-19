"""
Tree Detector - Detector de Árboles

Detecta el uso de árboles en el algoritmo mediante análisis estático
del AST.
"""

from typing import Optional, List, Set

from app.core.parser.ast_nodes import (
    ASTNode, ProgramNode, 
    AlgorithmNode, CallStatementNode, ObjectAccessNode
)
from app.core.data_structures.base_structure import (
    BaseStructureDetector,
    StructureType,
    StructureMatch,
    StructureIndicator,
    OperationComplexity
)

class TreeDetector(BaseStructureDetector):
    """Detector de Árboles"""

    def __init__(self):
        super().__init__()
        self.structure_type = StructureType.TREE
        self.structure_name = "Árbol"
        self.description = "Estructura jerárquica con raíz y nodos hijos"

        self.keywords = {
            "tree", "arbol", "root", "raiz", "left", "right",
            "izquierdo", "derecho", "child", "hijo", "parent"
        }

        self.indicators = [
            StructureIndicator("Acceso left/right", "Navegación hijos", 0.6),
            StructureIndicator("Clase TreeNode", "Definición nodo árbol", 0.5),
            StructureIndicator("Recursión binaria", "Llamadas left y right", 0.5),
            StructureIndicator("Variable tree/root", "Nombres típicos", 0.4),
            StructureIndicator("Travesía recursiva", "DFS/BFS pattern", 0.3),
        ]

        self.operation_complexities = [
            OperationComplexity("Búsqueda", "O(log n)", "O(log n)", "O(n)", "O(h)"),
            OperationComplexity("Inserción", "O(log n)", "O(log n)", "O(n)", "O(h)"),
            OperationComplexity("Eliminación", "O(log n)", "O(log n)", "O(n)", "O(h)"),
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

        # Buscar accesos left/right
        lr_accesses = self._find_lr_accesses(algorithm.body)
        if lr_accesses:
            indicators[0].found = True
            evidence.append(f"Accesos left/right: {len(lr_accesses)}")

        # Buscar recursión binaria
        if self._has_binary_recursion(algorithm):
            indicators[2].found = True
            evidence.append("Recursión binaria detectada")

        # Variables tree
        named_vars = [p.name if hasattr(p, 'name') else str(p) 
                     for p in algorithm.parameters
                     if any(k in str(p).lower() for k in self.keywords)]

        if named_vars:
            indicators[3].found = True
            vars_found.update(named_vars)
            evidence.append(f"Variables tree: {', '.join(named_vars)}")

        confidence = self._calculate_confidence(indicators)
        if confidence < 0.3:
            return None

        found, missing = self._split_indicators(indicators)

        return StructureMatch(
            structure_type=self.structure_type,
            structure_name=self.structure_name,
            confidence=confidence,
            variables=list(vars_found) if vars_found else ["tree"],
            indicators_found=found,
            indicators_missing=missing,
            operations=operations,
            operation_complexities=self.operation_complexities,
            reasoning=self._build_reasoning(found, missing),
            properties={"lr_accesses": len(lr_accesses)},
            code_evidence=evidence
        )

    def _find_lr_accesses(self, node):
        accesses = []
        def visit(n):
            # Check ObjectAccessNode for left/right fields
            if isinstance(n, ObjectAccessNode):
                field = n.field_name.lower()
                if 'left' in field or 'right' in field:
                    accesses.append(f"{n.object_name}.{n.field_name}")
            # Also check any node with field_name attribute
            elif hasattr(n, 'field_name'):
                field = str(n.field_name).lower()
                if 'left' in field or 'right' in field:
                    accesses.append(field)
            # Recursively visit all child nodes
            for attr in ['statements', 'then_block', 'else_block', 'body', 'value', 'expression', 'arguments']:
                if hasattr(n, attr):
                    child = getattr(n, attr)
                    if isinstance(child, list):
                        for item in child:
                            visit(item)
                    elif child is not None:
                        visit(child)
        visit(node)
        return accesses

    def _has_binary_recursion(self, algo):
        # Buscar dos llamadas recursivas (left y right)
        def visit(n, calls=0):
            if isinstance(n, CallStatementNode):
                if n.function_name == algo.name:
                    calls += 1
            if hasattr(n, 'statements'):
                for s in n.statements:
                    calls = visit(s, calls)
            return calls

        return visit(algo.body) >= 2