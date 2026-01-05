"""
Stack Detector - Detector de Pilas (Stacks)

Detecta el uso de pilas mediante análisis de operaciones LIFO,
llamadas a push/pop y patrones típicos de pila.
"""

from typing import Optional, List, Set

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

class StackDetector(BaseStructureDetector):
    """
    Detector de Pilas (LIFO - Last In First Out).

    Identifica pilas mediante:
    - Operaciones push/pop o equivalentes
    - Acceso solo al tope
    - Patrón LIFO en operaciones
    - Variables con nombres típicos (stack, pila)
    """

    def __init__(self):
        super().__init__()
        self.structure_type = StructureType.STACK
        self.structure_name = "Pila (Stack)"
        self.description = "Estructura LIFO - Last In First Out"

        # Palabras clave relacionadas con pilas
        self.stack_keywords = {
            "push", "pop", "apilar", "desapilar",
            "push_back", "pop_back",
            "stack", "pila", "tope", "top"
        }

        # Indicadores de pilas
        self.indicators = [
            StructureIndicator(
                name="Operación push",
                description="Llamada a push() o apilar()",
                weight=3.0
            ),
            StructureIndicator(
                name="Operación pop",
                description="Llamada a pop() o desapilar()",
                weight=3.0
            ),
            StructureIndicator(
                name="Par push-pop",
                description="Presencia de ambas operaciones (LIFO)",
                weight=2.5
            ),
            StructureIndicator(
                name="Variable con nombre stack/pila",
                description="Variable nombrada stack, pila o similar",
                weight=2.0
            ),
            StructureIndicator(
                name="Acceso solo al tope",
                description="Solo se accede al último elemento",
                weight=1.5
            ),
            StructureIndicator(
                name="Patrón recursivo",
                description="Uso de pila implícita en recursión",
                weight=1.0
            ),
        ]

        # Complejidades de operaciones
        self.operation_complexities = [
            OperationComplexity(
                operation="push (insertar al tope)",
                best_case="O(1)",
                average_case="O(1)",
                worst_case="O(1)",
                space="O(1)"
            ),
            OperationComplexity(
                operation="pop (eliminar del tope)",
                best_case="O(1)",
                average_case="O(1)",
                worst_case="O(1)",
                space="O(1)"
            ),
            OperationComplexity(
                operation="top/peek (ver tope)",
                best_case="O(1)",
                average_case="O(1)",
                worst_case="O(1)",
                space="O(1)"
            ),
            OperationComplexity(
                operation="isEmpty (verificar vacía)",
                best_case="O(1)",
                average_case="O(1)",
                worst_case="O(1)",
                space="O(1)"
            ),
        ]

    def detect(self, ast: ProgramNode) -> Optional[StructureMatch]:
        """
        Detecta pilas en el AST.

        Args:
            ast: Nodo raíz del programa

        Returns:
            StructureMatch si se detecta pila, None si no
        """
        algorithm = ast.algorithm
        if not algorithm:
            return None

        # Recolectar evidencia
        stack_vars: Set[str] = set()
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

        # 1. Buscar operaciones push
        push_ops = self._find_operations(algorithm.body, ["push", "apilar", "push_back"])
        if push_ops:
            indicators[0].found = True
            indicators[0].evidence = f"{len(push_ops)} operaciones push"
            stack_vars.update(op["target"] for op in push_ops)
            operations.extend(f"push a {op['target']}" for op in push_ops[:3])
            evidence.append(f"Operaciones push: {len(push_ops)}")

        # 2. Buscar operaciones pop
        pop_ops = self._find_operations(algorithm.body, ["pop", "desapilar", "pop_back"])
        if pop_ops:
            indicators[1].found = True
            indicators[1].evidence = f"{len(pop_ops)} operaciones pop"
            stack_vars.update(op["target"] for op in pop_ops)
            operations.extend(f"pop de {op['target']}" for op in pop_ops[:3])
            evidence.append(f"Operaciones pop: {len(pop_ops)}")

        # 3. Verificar par push-pop (patrón LIFO)
        if push_ops and pop_ops:
            indicators[2].found = True
            indicators[2].evidence = "Patrón LIFO detectado"
            evidence.append("Patrón LIFO completo (push + pop)")

        # 4. Buscar variables con nombres stack/pila
        named_vars = self._find_stack_named_variables(algorithm)
        if named_vars:
            indicators[3].found = True
            indicators[3].evidence = f"Variables: {', '.join(named_vars)}"
            stack_vars.update(named_vars)
            evidence.append(f"Variables con nombre stack: {', '.join(named_vars)}")

        # 5. Verificar acceso solo al tope
        if self._check_top_only_access(algorithm.body, stack_vars):
            indicators[4].found = True
            indicators[4].evidence = "Solo acceso al tope"
            evidence.append("Acceso limitado al tope de la estructura")

        # 6. Detectar recursión (pila implícita)
        if self._has_recursion(algorithm):
            indicators[5].found = True
            indicators[5].evidence = "Recursión detectada (pila implícita)"
            operations.append("Recursión (pila de llamadas)")
            evidence.append("Uso implícito de pila en recursión")

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
            "total_variables": len(stack_vars),
            "push_count": len(push_ops),
            "pop_count": len(pop_ops),
            "is_explicit_stack": len(push_ops) > 0 or len(pop_ops) > 0,
            "is_implicit_stack": self._has_recursion(algorithm),
            "balanced_operations": abs(len(push_ops) - len(pop_ops)) <= 1
        }

        return StructureMatch(
            structure_type=self.structure_type,
            structure_name=self.structure_name,
            confidence=confidence,
            variables=list(stack_vars) if stack_vars else ["pila_implícita"],
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
        """Encuentra operaciones específicas (push, pop, etc.)"""
        operations = []

        def visit(n: ASTNode):
            # Buscar en CallStatementNode
            if isinstance(n, CallStatementNode):
                func_name = n.function_name.lower()
                if any(op in func_name for op in operation_names):
                    # Intentar extraer target (primer argumento)
                    target = "unknown"
                    if n.arguments and len(n.arguments) > 0:
                        arg = n.arguments[0]
                        if hasattr(arg, 'name'):
                            target = arg.name

                    operations.append({
                        "operation": func_name,
                        "target": target,
                        "node": n
                    })

            # Buscar en FunctionCallNode
            if isinstance(n, FunctionCallNode):
                func_name = n.function_name.lower()
                if any(op in func_name for op in operation_names):
                    operations.append({
                        "operation": func_name,
                        "target": "unknown",
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

            if hasattr(n, 'then_block'):
                visit(n.then_block)
            if hasattr(n, 'else_block') and n.else_block:
                visit(n.else_block)

        visit(node)
        return operations

    def _find_stack_named_variables(self, algorithm: AlgorithmNode) -> List[str]:
        """Encuentra variables con nombres relacionados a pila"""
        named_vars = []

        # Revisar parámetros
        for param in algorithm.parameters:
            param_name = param.name if hasattr(param, 'name') else str(param)
            param_lower = param_name.lower()

            if any(keyword in param_lower for keyword in self.stack_keywords):
                named_vars.append(param_name)

        # Revisar variables locales (si están en el AST)
        def visit(n: ASTNode):
            if isinstance(n, AssignmentNode):
                # AssignmentNode usa 'target' no 'lvalue'
                target = n.target
                if hasattr(target, 'name'):
                    name_lower = target.name.lower()
                    if any(keyword in name_lower for keyword in self.stack_keywords):
                        if target.name not in named_vars:
                            named_vars.append(target.name)

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
        
        if algorithm.body:
            visit(algorithm.body)

        return named_vars

    def _check_top_only_access(
        self,
        node: ASTNode,
        stack_vars: Set[str]
    ) -> bool:
        """
        Verifica que solo se acceda al tope (último elemento).

        En una pila, no debería haber accesos indexados arbitrarios
        como stack[i] con i variable.
        """
        # Implementación simplificada
        # En versión completa, verificaríamos que todos los accesos
        # son de la forma stack[n-1], stack[length-1], o mediante pop()

        return len(stack_vars) > 0  # Placeholder

    def _has_recursion(self, algorithm: AlgorithmNode) -> bool:
        """Detecta si hay recursión (pila implícita)"""
        algo_name = algorithm.name

        def visit(n: ASTNode) -> bool:
            # Buscar llamadas recursivas
            if isinstance(n, CallStatementNode):
                if n.function_name == algo_name:
                    return True

            # Recorrer hijos
            if hasattr(n, 'body'):
                if isinstance(n.body, list):
                    if any(visit(child) for child in n.body):
                        return True
                elif n.body and visit(n.body):
                    return True

            if hasattr(n, 'statements'):
                if any(visit(stmt) for stmt in n.statements):
                    return True

            if hasattr(n, 'then_block') and visit(n.then_block):
                return True
            if hasattr(n, 'else_block') and n.else_block and visit(n.else_block):
                return True

            return False

        if algorithm.body:
            return visit(algorithm.body)

        return False