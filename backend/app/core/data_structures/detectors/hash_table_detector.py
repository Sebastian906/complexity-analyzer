"""
Hash Table Detector - Detector de Tablas Hash

Detecta el uso de tablas hash en el algoritmo mediante análisis estático
del AST.
"""

from typing import Optional, List, Set

from app.core.parser.ast_nodes import (
    ASTNode, ProgramNode, AlgorithmNode, 
    CallStatementNode, FunctionCallNode
)
from app.core.data_structures.base_structure import (
    BaseStructureDetector,
    StructureType,
    StructureMatch,
    StructureIndicator,
    OperationComplexity
)

class HashTableDetector(BaseStructureDetector):
    """Detector de Tablas Hash"""

    def __init__(self):
        super().__init__()
        self.structure_type = StructureType.HASH_TABLE
        self.structure_name = "Tabla Hash"
        self.description = "Estructura con función hash y buckets"

        self.keywords = {"hash", "bucket", "collision", "colision"}

        self.indicators = [
            StructureIndicator("Función hash", "hash(key)", 3.0),
            StructureIndicator("Variable hash_table", "Nombre típico", 2.5),
            StructureIndicator("Manejo colisiones", "Chaining o probing", 2.0),
            StructureIndicator("Acceso con hash", "table[hash(key)]", 2.0),
        ]

        self.operation_complexities = [
            OperationComplexity("Inserción", "O(1)", "O(1)", "O(n)", "O(n)"),
            OperationComplexity("Búsqueda", "O(1)", "O(1)", "O(n)", "O(1)"),
            OperationComplexity("Eliminación", "O(1)", "O(1)", "O(n)", "O(1)"),
        ]

    def detect(self, ast: ProgramNode) -> Optional[StructureMatch]:
        algorithm = ast.algorithm
        if not algorithm:
            return None

        vars_found = set()
        evidence = []
        indicators = [StructureIndicator(name=i.name, description=i.description, weight=i.weight) 
                     for i in self.indicators]

        # Buscar función hash
        if self._has_hash_function(algorithm.body):
            indicators[0].found = True
            evidence.append("Función hash detectada")

        # Variables hash
        named_vars = [p.name if hasattr(p, 'name') else str(p) 
                     for p in algorithm.parameters
                     if any(k in str(p).lower() for k in self.keywords)]

        if named_vars:
            indicators[1].found = True
            vars_found.update(named_vars)
            evidence.append(f"Variables hash: {', '.join(named_vars)}")

        confidence = self._calculate_confidence(indicators)
        if confidence < 0.3:
            return None

        found, missing = self._split_indicators(indicators)

        return StructureMatch(
            structure_type=self.structure_type,
            structure_name=self.structure_name,
            confidence=confidence,
            variables=list(vars_found) if vars_found else ["hash_table"],
            indicators_found=found,
            indicators_missing=missing,
            operations=[],
            operation_complexities=self.operation_complexities,
            reasoning=self._build_reasoning(found, missing),
            properties={},
            code_evidence=evidence
        )

    def _has_hash_function(self, node):
        def visit(n):
            if isinstance(n, CallStatementNode):
                if 'hash' in n.function_name.lower():
                    return True
            if isinstance(n, FunctionCallNode):
                if 'hash' in n.function_name.lower():
                    return True
            if hasattr(n, 'statements'):
                return any(visit(s) for s in n.statements)
            return False
        return visit(node)