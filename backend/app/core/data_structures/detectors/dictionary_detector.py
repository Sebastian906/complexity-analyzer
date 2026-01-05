"""
Dictionary Detector - Detector de Diccionarios/Mapas

Detecta el uso de diccionarios/maps en el algoritmo mediante análisis estático
del AST.
"""

from typing import Optional, List, Set

from app.core.parser.ast_nodes import (
    ASTNode, ProgramNode, AlgorithmNode,
    ForLoopNode, ParameterNode
)
from app.core.data_structures.base_structure import (
    BaseStructureDetector,
    StructureType,
    StructureMatch,
    StructureIndicator,
    OperationComplexity
)

class DictionaryDetector(BaseStructureDetector):
    """Detector de Diccionarios/Maps"""

    def __init__(self):
        super().__init__()
        self.structure_type = StructureType.DICTIONARY
        self.structure_name = "Diccionario/Map"
        self.description = "Estructura clave-valor"

        self.keywords = {"dict", "map", "diccionario", "mapa", "hash"}

        self.indicators = [
            StructureIndicator("Acceso por clave", "map[key]", 3.0),
            StructureIndicator("Operación put/set", "Insertar clave-valor", 2.5),
            StructureIndicator("Operación get", "Obtener por clave", 2.5),
            StructureIndicator("Variable dict/map", "Nombre típico", 2.0),
            StructureIndicator("Búsqueda de clave", "contains/hasKey", 1.5),
        ]

        self.operation_complexities = [
            OperationComplexity("Inserción", "O(1)", "O(1)", "O(n)", "O(1)"),
            OperationComplexity("Búsqueda", "O(1)", "O(1)", "O(n)", "O(1)"),
            OperationComplexity("Eliminación", "O(1)", "O(1)", "O(n)", "O(1)"),
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

        # Buscar variables dict/map
        named_vars = [p.name if hasattr(p, 'name') else str(p) 
                     for p in algorithm.parameters
                     if any(k in str(p).lower() for k in self.keywords)]

        if named_vars:
            indicators[3].found = True
            vars_found.update(named_vars)
            evidence.append(f"Variables dict: {', '.join(named_vars)}")
            indicators[0].found = True  # Asumimos acceso por clave
            confidence = 0.6
        else:
            confidence = 0.2

        if confidence < 0.3:
            return None

        found, missing = self._split_indicators(indicators)

        return StructureMatch(
            structure_type=self.structure_type,
            structure_name=self.structure_name,
            confidence=confidence,
            variables=list(vars_found) if vars_found else ["dict"],
            indicators_found=found,
            indicators_missing=missing,
            operations=operations,
            operation_complexities=self.operation_complexities,
            reasoning="Diccionario detectado por nombres de variables",
            properties={},
            code_evidence=evidence
        )