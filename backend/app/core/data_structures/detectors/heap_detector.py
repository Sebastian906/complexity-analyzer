"""
Heap Detector - Detector de Montículos (Heaps)

Detecta el uso de montículos en el algoritmo mediante análisis estático
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

class HeapDetector(BaseStructureDetector):
    """
    Detector de Montículos (Heaps).
    
    Identifica heaps mediante:
    - Operaciones insert/extractMin/extractMax
    - Operaciones heapify/buildHeap
    - Acceso al elemento mínimo/máximo en O(1)
    - Variables con nombres típicos (heap, montículo)
    - Uso en algoritmos de ordenamiento (heapsort)
    """

    def __init__(self):
        super().__init__()
        self.structure_type = StructureType.HEAP
        self.structure_name = "Montículo (Heap)"
        self.description = "Árbol binario completo con propiedad de orden"

        # Palabras clave relacionadas con heaps
        self.heap_keywords = {
            "heap", "montículo", "priority", "prioridad",
            "heapify", "buildheap", "extractmin", "extractmax",
            "min", "max", "parent", "padre"
        }

        # Indicadores de heaps
        self.indicators = [
            StructureIndicator(
                name="Operación insert",
                description="Inserción con heapify up",
                weight=3.0
            ),
            StructureIndicator(
                name="Operación extract (min/max)",
                description="Extracción del elemento prioritario",
                weight=3.0
            ),
            StructureIndicator(
                name="Operación heapify",
                description="Función heapify detectada",
                weight=2.5
            ),
            StructureIndicator(
                name="Variable con nombre heap",
                description="Variable nombrada heap, montículo o priority",
                weight=2.0
            ),
            StructureIndicator(
                name="Acceso a padre/hijos",
                description="Cálculos parent, left, right típicos de heap",
                weight=2.0
            ),
            StructureIndicator(
                name="Uso en heapsort",
                description="Patrón de heapsort detectado",
                weight=1.5
            ),
        ]

        # Complejidades de operaciones
        self.operation_complexities = [
            OperationComplexity(
                operation="insert (insertar)",
                best_case="O(1)",
                average_case="O(log n)",
                worst_case="O(log n)",
                space="O(1)"
            ),
            OperationComplexity(
                operation="extractMin/extractMax (extraer)",
                best_case="O(log n)",
                average_case="O(log n)",
                worst_case="O(log n)",
                space="O(1)"
            ),
            OperationComplexity(
                operation="getMin/getMax (ver mínimo/máximo)",
                best_case="O(1)",
                average_case="O(1)",
                worst_case="O(1)",
                space="O(1)"
            ),
            OperationComplexity(
                operation="heapify",
                best_case="O(log n)",
                average_case="O(log n)",
                worst_case="O(log n)",
                space="O(1)"
            ),
            OperationComplexity(
                operation="buildHeap",
                best_case="O(n)",
                average_case="O(n)",
                worst_case="O(n)",
                space="O(1)"
            ),
        ]

    def detect(self, ast: ProgramNode) -> Optional[StructureMatch]:
        """
        Detecta heaps en el AST.

        Args:
            ast: Nodo raíz del programa

        Returns:
            StructureMatch si se detecta heap, None si no
        """
        algorithm = ast.algorithm
        if not algorithm:
            return None

        # Recolectar evidencia
        heap_vars: PySet[str] = set()
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

        # 1. Buscar operaciones insert
        insert_ops = self._find_operations(
            algorithm.body,
            ["insert", "insertar", "add"]
        )
        # Filtrar solo si parece heap context
        heap_insert = [op for op in insert_ops if self._is_heap_context(op)]
        if heap_insert:
            indicators[0].found = True
            indicators[0].evidence = f"{len(heap_insert)} inserciones"
            operations.extend(f"insert heap" for _ in heap_insert[:3])
            evidence.append(f"Operaciones insert: {len(heap_insert)}")
        
        # 2. Buscar operaciones extract
        extract_ops = self._find_operations(
            algorithm.body,
            ["extract", "extraer", "extractmin", "extractmax", "deletemin", "deletemax"]
        )
        if extract_ops:
            indicators[1].found = True
            indicators[1].evidence = f"{len(extract_ops)} extracciones"
            operations.extend(f"extract de heap" for _ in extract_ops[:3])
            evidence.append(f"Operaciones extract: {len(extract_ops)}")

        # 3. Buscar operaciones heapify
        heapify_ops = self._find_operations(
            algorithm.body,
            ["heapify", "buildheap", "makeheap"]
        )
        if heapify_ops:
            indicators[2].found = True
            indicators[2].evidence = f"{len(heapify_ops)} llamadas heapify"
            operations.extend("heapify" for _ in heapify_ops[:3])
            evidence.append(f"Operaciones heapify: {len(heapify_ops)}")

        # 4. Buscar variables con nombres heap
        named_vars = self._find_heap_named_variables(algorithm)
        if named_vars:
            indicators[3].found = True
            indicators[3].evidence = f"Variables: {', '.join(named_vars)}"
            heap_vars.update(named_vars)
            evidence.append(f"Variables heap: {', '.join(named_vars)}")

        # 5. Buscar cálculos de padre/hijos
        has_parent_child = self._has_parent_child_calculations(algorithm.body)
        if has_parent_child:
            indicators[4].found = True
            indicators[4].evidence = "Cálculos parent/left/right"
            evidence.append("Operaciones típicas de heap binario")

        # 6. Detectar patrón heapsort
        is_heapsort = self._is_heapsort_pattern(algorithm)
        if is_heapsort:
            indicators[5].found = True
            indicators[5].evidence = "Patrón heapsort detectado"
            evidence.append("Algoritmo heapsort identificado")

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
            "total_variables": len(heap_vars),
            "insert_count": len(heap_insert) if heap_insert else 0,
            "extract_count": len(extract_ops),
            "has_heapify": len(heapify_ops) > 0,
            "is_heapsort": is_heapsort,
            "likely_type": "min_heap" if "min" in str(algorithm.body).lower() else "max_heap"
        }

        return StructureMatch(
            structure_type=self.structure_type,
            structure_name=self.structure_name,
            confidence=confidence,
            variables=list(heap_vars) if heap_vars else ["heap"],
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
                    operations.append({
                        "operation": func_name,
                        "node": n
                    })

            if hasattr(n, 'statements'):
                for stmt in n.statements:
                    visit(stmt)

        visit(node)
        return operations

    def _is_heap_context(self, operation: dict) -> bool:
        """Verifica si una operación está en contexto de heap"""
        # Simplificado: asume que si hay heapify cerca, es heap
        return True

    def _find_heap_named_variables(self, algorithm: AlgorithmNode) -> List[str]:
        """Encuentra variables con nombres relacionados a heap"""
        named_vars = []

        for param in algorithm.parameters:
            param_name = param.name if hasattr(param, 'name') else str(param)
            param_lower = param_name.lower()

            if any(keyword in param_lower for keyword in self.heap_keywords):
                named_vars.append(param_name)

        return named_vars

    def _has_parent_child_calculations(self, node: ASTNode) -> bool:
        """Detecta cálculos típicos de heap: parent = i/2, left = 2*i"""
        # Simplificado: buscar divisiones y multiplicaciones por 2
        code_str = str(node).lower()
        has_div_2 = "/2" in code_str or "div 2" in code_str
        has_mult_2 = "*2" in code_str or "2*" in code_str

        return has_div_2 or has_mult_2

    def _is_heapsort_pattern(self, algorithm: AlgorithmNode) -> bool:
        """Detecta si es algoritmo heapsort"""
        algo_name = algorithm.name.lower()
        return "heapsort" in algo_name or "heap_sort" in algo_name