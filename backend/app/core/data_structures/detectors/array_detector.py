"""
Array Detector - Detector de Arrays y Listas

Detecta el uso de arrays/listas en el algoritmo mediante análisis estático
del AST.
"""

from typing import Optional, List, Set

from app.core.parser.ast_nodes import (
    ASTNode, ProgramNode, AlgorithmNode, ForLoopNode,
    AssignmentNode, ArrayAccessNode, ParameterNode, LValueNode
)
from app.core.data_structures.base_structure import (
    BaseStructureDetector,
    StructureType,
    StructureMatch,
    StructureIndicator,
    OperationComplexity
)

class ArrayDetector(BaseStructureDetector):
    """
    Detector de Arrays/Listas.

    Identifica arrays mediante:
    - Declaraciones de parámetros con notación []
    - Accesos indexados A[i]
    - Iteraciones sobre rangos
    - Operaciones típicas de arrays
    """

    def __init__(self):
        super().__init__()
        self.structure_type = StructureType.ARRAY
        self.structure_name = "Array/Lista"
        self.description = "Estructura secuencial con acceso por índice"

        # Indicadores de arrays
        self.indicators = [
            StructureIndicator(
                name="Parámetro con corchetes",
                description="Parámetro declarado como A[n] o A[]",
                weight=3.0
            ),
            StructureIndicator(
                name="Acceso indexado",
                description="Operaciones como A[i] o A[j]",
                weight=2.5
            ),
            StructureIndicator(
                name="Iteración secuencial",
                description="For loop sobre índices del array",
                weight=2.0
            ),
            StructureIndicator(
                name="Múltiples accesos",
                description="Accesos repetidos en diferentes contextos",
                weight=1.5
            ),
            StructureIndicator(
                name="Asignación a índice",
                description="Modificación de elementos via A[i] ← valor",
                weight=1.5
            ),
        ]

        # Complejidades de operaciones
        self.operation_complexities = [
            OperationComplexity(
                operation="Acceso por índice",
                best_case="O(1)",
                average_case="O(1)",
                worst_case="O(1)",
                space="O(1)"
            ),
            OperationComplexity(
                operation="Búsqueda",
                best_case="O(1)",
                average_case="O(n)",
                worst_case="O(n)",
                space="O(1)"
            ),
            OperationComplexity(
                operation="Inserción al final",
                best_case="O(1)",
                average_case="O(1)",
                worst_case="O(n)",  # Si necesita redimensionar
                space="O(1)"
            ),
            OperationComplexity(
                operation="Inserción en medio",
                best_case="O(n)",
                average_case="O(n)",
                worst_case="O(n)",
                space="O(1)"
            ),
        ]

    def detect(self, ast: ProgramNode) -> Optional[StructureMatch]:
        """
        Detecta arrays en el AST.

        Args:
            ast: Nodo raíz del programa

        Returns:
            StructureMatch si se detecta array, None si no
        """
        # Obtener algoritmo principal
        algorithm = ast.algorithm
        if not algorithm:
            return None

        # Recolectar evidencia
        array_vars: Set[str] = set()
        operations: List[str] = []
        evidence: List[str] = []

        # Clonar indicadores para evaluación
        indicators = [
            StructureIndicator(
                name=ind.name,
                description=ind.description,
                weight=ind.weight
            )
            for ind in self.indicators
        ]

        # 1. Buscar parámetros array
        array_params = self._find_array_parameters(algorithm)
        if array_params:
            indicators[0].found = True
            indicators[0].evidence = f"Parámetros: {', '.join(array_params)}"
            array_vars.update(array_params)
            evidence.append(f"Parámetros array: {', '.join(array_params)}")

        # 2. Buscar accesos indexados
        accesses = self._find_array_accesses(algorithm.body)
        if accesses:
            indicators[1].found = True
            indicators[1].evidence = f"{len(accesses)} accesos encontrados"
            array_vars.update(acc["var"] for acc in accesses)
            operations.extend(f"Acceso: {acc['var']}[{acc['index']}]" for acc in accesses[:5])
            evidence.append(f"Accesos indexados en {len(accesses)} ubicaciones")

        # 3. Buscar iteraciones secuenciales
        sequential_loops = self._find_sequential_iterations(algorithm.body, array_vars)
        if sequential_loops:
            indicators[2].found = True
            indicators[2].evidence = f"{len(sequential_loops)} loops encontrados"
            operations.extend(f"Iteración sobre {loop}" for loop in sequential_loops[:3])
            evidence.append(f"Iteraciones secuenciales: {len(sequential_loops)}")

        # 4. Verificar múltiples accesos
        if len(accesses) > 3:
            indicators[3].found = True
            indicators[3].evidence = f"{len(accesses)} accesos diferentes"

        # 5. Buscar asignaciones a índices
        assignments = self._find_index_assignments(algorithm.body)
        if assignments:
            indicators[4].found = True
            indicators[4].evidence = f"{len(assignments)} asignaciones"
            operations.extend(f"Asignación: {asig}" for asig in assignments[:3])
            evidence.append(f"Asignaciones a índices: {len(assignments)}")

        # Calcular confianza
        confidence = self._calculate_confidence(indicators)

        # Si no hay confianza mínima, no retornar match
        if confidence < 0.2:
            return None

        # Separar indicadores
        found, missing = self._split_indicators(indicators)

        # Construir razonamiento
        reasoning = self._build_reasoning(found, missing)

        # Propiedades específicas
        properties = {
            "total_variables": len(array_vars),
            "total_accesses": len(accesses),
            "has_sequential_iteration": len(sequential_loops) > 0,
            "has_modifications": len(assignments) > 0,
            "likely_sorted": self._check_if_sorted_context(algorithm.body),
        }

        return StructureMatch(
            structure_type=self.structure_type,
            structure_name=self.structure_name,
            confidence=confidence,
            variables=list(array_vars),
            indicators_found=found,
            indicators_missing=missing,
            operations=operations,
            operation_complexities=self.operation_complexities,
            reasoning=reasoning,
            properties=properties,
            code_evidence=evidence
        )

    def _find_array_parameters(self, algorithm: AlgorithmNode) -> List[str]:
        """Encuentra parámetros declarados como arrays"""
        array_params = []

        for param in algorithm.parameters:
            if isinstance(param, ParameterNode):
                # Parámetros array tienen param_type == "array" en el parser
                if hasattr(param, 'param_type') and param.param_type == "array":
                    array_params.append(param.name)
            elif isinstance(param, str):
                # Si es string simple, revisar sintaxis A[]
                if '[' in param:
                    var_name = param.split('[')[0].strip()
                    array_params.append(var_name)

        return array_params

    def _find_array_accesses(self, node: ASTNode) -> List[dict]:
        """Encuentra todos los accesos indexados en el AST"""
        accesses = []

        def visit(n: ASTNode):
            if isinstance(n, ArrayAccessNode):
                # ArrayAccessNode tiene array_name e indices (lista)
                accesses.append({
                    "var": n.array_name,
                    "index": str(n.indices[0]) if n.indices else "?",
                    "node": n
                })
            
            # También detectar LValueNode con access_type == "array"
            if isinstance(n, LValueNode) and n.access_type == "array":
                accesses.append({
                    "var": n.name,
                    "index": str(n.indices[0]) if n.indices else "?",
                    "node": n
                })

            # Recorrer hijos
            if hasattr(n, 'body') and n.body:
                if isinstance(n.body, list):
                    for child in n.body:
                        visit(child)
                else:
                    visit(n.body)

            if hasattr(n, 'statements'):
                for stmt in n.statements:
                    visit(stmt)
            
            # También revisar expresiones dentro de asignaciones
            if hasattr(n, 'value'):
                visit(n.value)
            if hasattr(n, 'target'):
                visit(n.target)
            if hasattr(n, 'condition'):
                visit(n.condition)
            if hasattr(n, 'left'):
                visit(n.left)
            if hasattr(n, 'right'):
                visit(n.right)

            if hasattr(n, 'then_block'):
                visit(n.then_block)
            if hasattr(n, 'else_block') and n.else_block:
                visit(n.else_block)

        visit(node)
        return accesses

    def _find_sequential_iterations(
        self,
        node: ASTNode,
        array_vars: Set[str]
    ) -> List[str]:
        """Encuentra loops que iteran sobre arrays"""
        sequential = []

        def visit(n: ASTNode):
            if isinstance(n, ForLoopNode):
                # Verificar si itera sobre rango típico de array
                # for i ← 1 to n, for i ← 0 to length(A)-1, etc.
                if hasattr(n, 'variable'):
                    loop_var = n.variable
                    # Si usa length() o accede array_vars, es secuencial
                    # ForLoopNode tiene 'end' no 'to_expr'
                    end_expr = getattr(n, 'end', None)
                    if end_expr and any(var in str(end_expr) for var in array_vars):
                        sequential.append(f"{loop_var} sobre array")
                    # También verificar si hay accesos a array dentro del body
                    elif array_vars:
                        sequential.append(f"{loop_var} iteración")

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
        return sequential

    def _find_index_assignments(self, node: ASTNode) -> List[str]:
        """Encuentra asignaciones a índices de array"""
        assignments = []

        def visit(n: ASTNode):
            if isinstance(n, AssignmentNode):
                # Verificar si target es array access
                # AssignmentNode usa 'target' no 'lvalue'
                target = n.target
                if isinstance(target, ArrayAccessNode):
                    # ArrayAccessNode tiene array_name
                    var_name = target.array_name
                    assignments.append(f"{var_name}[...]")
                elif isinstance(target, LValueNode) and target.access_type == "array":
                    # LValueNode con access_type "array"
                    assignments.append(f"{target.name}[...]")

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
        return assignments

    def _check_if_sorted_context(self, node: ASTNode) -> bool:
        """
        Verifica si hay evidencia de que el array está ordenado.
        
        Busca comparaciones entre elementos consecutivos o menciones
        de 'sorted' en nombres.
        """
        # Implementación simplificada
        # En una versión completa, buscaríamos:
        # - Comparaciones A[i] < A[i+1]
        # - Variables con nombres como 'sorted', 'ordenado'
        # - Algoritmos de ordenamiento conocidos

        return False  # Por ahora retornamos False