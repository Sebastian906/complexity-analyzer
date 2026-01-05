"""
Set Detector - Detector de Conjuntos (Sets)

Detecta el uso de conjuntos en el algoritmo mediante análisis estático
del AST.
"""

from typing import Optional, List, Set as PySet

from app.core.parser.ast_nodes import (
    ASTNode, ProgramNode, AlgorithmNode,
    CallStatementNode, FunctionCallNode, AssignmentNode
)
from app.core.data_structures.base_structure import (
    BaseStructureDetector,
    StructureType,
    StructureMatch,
    StructureIndicator,
    OperationComplexity
)

class SetDetector(BaseStructureDetector):
    """
    Detector de Conjuntos (Sets).

    Identifica sets mediante:
    - Operaciones add/remove/contains
    - Verificaciones de membresía (in, not in)
    - Operaciones de conjuntos (union, intersección)
    - Variables con nombres típicos (set, conjunto)
    """

    def __init__(self):
        super().__init__()
        self.structure_type = StructureType.SET
        self.structure_name = "Conjunto (Set)"
        self.description = "Colección no ordenada sin duplicados"

        # Palabras clave relacionadas con sets
        self.set_keywords = {
            "set", "conjunto", "add", "agregar",
            "remove", "eliminar", "contains", "contiene",
            "union", "intersect", "intersección",
            "difference", "diferencia", "subset"
        }

        # Indicadores de sets
        self.indicators = [
            StructureIndicator(
                name="Operación add/insert",
                description="Llamada a add() o agregar()",
                weight=3.0
            ),
            StructureIndicator(
                name="Operación contains",
                description="Verificación de membresía (in, contains)",
                weight=2.5
            ),
            StructureIndicator(
                name="Operación remove",
                description="Eliminación de elementos",
                weight=2.0
            ),
            StructureIndicator(
                name="Variable con nombre set/conjunto",
                description="Variable nombrada set, conjunto o similar",
                weight=2.5
            ),
            StructureIndicator(
                name="Operaciones de conjuntos",
                description="Union, intersección, diferencia",
                weight=2.0
            ),
            StructureIndicator(
                name="Sin acceso indexado",
                description="No hay accesos por índice (no ordenado)",
                weight=1.5
            ),
        ]

        # Complejidades de operaciones
        self.operation_complexities = [
            OperationComplexity(
                operation="add/insert (agregar)",
                best_case="O(1)",
                average_case="O(1)",
                worst_case="O(1)",
                space="O(1)"
            ),
            OperationComplexity(
                operation="remove (eliminar)",
                best_case="O(1)",
                average_case="O(1)",
                worst_case="O(1)",
                space="O(1)"
            ),
            OperationComplexity(
                operation="contains (membresía)",
                best_case="O(1)",
                average_case="O(1)",
                worst_case="O(1)",
                space="O(1)"
            ),
            OperationComplexity(
                operation="union (unión)",
                best_case="O(n+m)",
                average_case="O(n+m)",
                worst_case="O(n+m)",
                space="O(n+m)"
            ),
            OperationComplexity(
                operation="intersection (intersección)",
                best_case="O(min(n,m))",
                average_case="O(min(n,m))",
                worst_case="O(min(n,m))",
                space="O(min(n,m))"
            ),
        ]

    def detect(self, ast: ProgramNode) -> Optional[StructureMatch]:
        """
        Detecta sets en el AST.

        Args:
            ast: Nodo raíz del programa

        Returns:
            StructureMatch si se detecta set, None si no
        """
        algorithm = ast.algorithm
        if not algorithm:
            return None

        # Recolectar evidencia
        set_vars: PySet[str] = set()
        operations: List[str] = []
        evidence: List[str] = []

        # Clonar indicadores
        indicators = [
            StructureIndicator(
                name=ind.name,
                description=ind.description,
                weight=ind.weight
            )
            for ind in self.indicators
        ]

        # 1. Buscar operaciones add/insert
        add_ops = self._find_operations(
            algorithm.body,
            ["add", "agregar", "insert"]
        )
        if add_ops:
            indicators[0].found = True
            indicators[0].evidence = f"{len(add_ops)} operaciones add"
            set_vars.update(op["target"] for op in add_ops)
            operations.extend(f"add a {op['target']}" for op in add_ops[:3])
            evidence.append(f"Operaciones add: {len(add_ops)}")

        # 2. Buscar operaciones contains/in
        contains_ops = self._find_operations(
            algorithm.body,
            ["contains", "contiene", "in"]
        )
        if contains_ops:
            indicators[1].found = True
            indicators[1].evidence = f"{len(contains_ops)} verificaciones"
            set_vars.update(op["target"] for op in contains_ops)
            operations.extend(f"contains en {op['target']}" for op in contains_ops[:3])
            evidence.append(f"Verificaciones de membresía: {len(contains_ops)}")

        # 3. Buscar operaciones remove
        remove_ops = self._find_operations(
            algorithm.body,
            ["remove", "eliminar", "delete"]
        )
        if remove_ops:
            indicators[2].found = True
            indicators[2].evidence = f"{len(remove_ops)} eliminaciones"
            set_vars.update(op["target"] for op in remove_ops)
            operations.extend(f"remove de {op['target']}" for op in remove_ops[:3])
            evidence.append(f"Operaciones remove: {len(remove_ops)}")

        # 4. Buscar variables con nombres set/conjunto
        named_vars = self._find_set_named_variables(algorithm)
        if named_vars:
            indicators[3].found = True
            indicators[3].evidence = f"Variables: {', '.join(named_vars)}"
            set_vars.update(named_vars)
            evidence.append(f"Variables con nombre set: {', '.join(named_vars)}")

        # 5. Buscar operaciones de conjuntos
        set_ops = self._find_operations(
            algorithm.body,
            ["union", "intersect", "difference", "subset"]
        )
        if set_ops:
            indicators[4].found = True
            indicators[4].evidence = f"{len(set_ops)} operaciones de conjuntos"
            operations.extend(f"{op['operation']}" for op in set_ops[:3])
            evidence.append(f"Operaciones de conjuntos: {len(set_ops)}")

        # 6. Verificar sin acceso indexado (no es definitivo)
        has_no_index = not self._has_indexed_access(algorithm.body, set_vars)
        if has_no_index and set_vars:
            indicators[5].found = True
            indicators[5].evidence = "No hay accesos indexados"
            evidence.append("Sin acceso por índice (colección no ordenada)")

        # Calcular confianza
        confidence = self._calculate_confidence(indicators)

        # Umbral mínimo
        if confidence < 0.25:
            return None

        # Separar indicadores
        found, missing = self._split_indicators(indicators)

        # Razonamiento
        reasoning = self._build_reasoning(found, missing)

        # Propiedades
        properties = {
            "total_variables": len(set_vars),
            "add_count": len(add_ops),
            "contains_count": len(contains_ops),
            "remove_count": len(remove_ops),
            "has_set_operations": len(set_ops) > 0,
            "likely_no_duplicates": True,  # Sets no permiten duplicados
        }

        return StructureMatch(
            structure_type=self.structure_type,
            structure_name=self.structure_name,
            confidence=confidence,
            variables=list(set_vars) if set_vars else ["conjunto"],
            indicators_found=found,
            indicators_missing=missing,
            operations=operations,
            operation_complexities=self.operation_complexities,
            reasoning=reasoning,
            properties=properties,
            code_evidence=evidence
        )

    def _find_operations(
        self,
        node: ASTNode,
        operation_names: List[str]
    ) -> List[dict]:
        """Encuentra operaciones específicas"""
        operations = []

        def visit(n: ASTNode):
            if isinstance(n, CallStatementNode):
                func_name = n.function_name.lower()
                if any(op in func_name for op in operation_names):
                    target = "set"
                    if n.arguments and len(n.arguments) > 0:
                        arg = n.arguments[0]
                        if hasattr(arg, 'name'):
                            target = arg.name

                    operations.append({
                        "operation": func_name,
                        "target": target,
                        "node": n
                    })

            if isinstance(n, FunctionCallNode):
                func_name = n.function_name.lower()
                if any(op in func_name for op in operation_names):
                    operations.append({
                        "operation": func_name,
                        "target": "set",
                        "node": n
                    })

            # Recorrer hijos
            if hasattr(n, 'body'):
                if isinstance(n.body, list):
                    for child in n.body:
                        visit(child)
                elif n.body:
                    visit(n.body)

            if hasattr(n, 'statements'):
                for stmt in n.statements:
                    visit(stmt)

        visit(node)
        return operations

    def _find_set_named_variables(self, algorithm: AlgorithmNode) -> List[str]:
        """Encuentra variables con nombres relacionados a set"""
        named_vars = []

        # Revisar parámetros
        for param in algorithm.parameters:
            param_name = param.name if hasattr(param, 'name') else str(param)
            param_lower = param_name.lower()

            if any(keyword in param_lower for keyword in self.set_keywords):
                named_vars.append(param_name)

        return named_vars

    def _has_indexed_access(
        self,
        node: ASTNode,
        set_vars: PySet[str]
    ) -> bool:
        """Verifica si hay accesos indexados a las variables set"""
        from app.core.parser.ast_nodes import ArrayAccessNode

        def visit(n: ASTNode) -> bool:
            if isinstance(n, ArrayAccessNode):
                if hasattr(n.array, 'name') and n.array.name in set_vars:
                    return True

            if hasattr(n, 'body'):
                if isinstance(n.body, list):
                    if any(visit(child) for child in n.body):
                        return True
                elif n.body and visit(n.body):
                    return True

            if hasattr(n, 'statements'):
                if any(visit(stmt) for stmt in n.statements):
                    return True

            return False

        return visit(node)