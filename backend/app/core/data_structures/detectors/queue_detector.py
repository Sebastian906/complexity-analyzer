"""
Queue Detector - Detector de Colas (FIFO - First In First Out)

Detecta el uso de colas en el algoritmo mediante análisis estático
del AST.
"""

from typing import Optional, List, Set
from app.core.parser.ast_nodes import (
    ASTNode, ProgramNode, AlgorithmNode,
    CallStatementNode, FunctionCallNode
)
from app.core.data_structures.base_structure import (
    BaseStructureDetector, StructureType, StructureMatch,
    StructureIndicator, OperationComplexity
)

class QueueDetector(BaseStructureDetector):
    """Detector de Colas (FIFO - First In First Out)"""

    def __init__(self):
        super().__init__()
        self.structure_type = StructureType.QUEUE
        self.structure_name = "Cola (Queue)"
        self.description = "Estructura FIFO - First In First Out"
        
        self.queue_keywords = {
            "enqueue", "dequeue", "encolar", "desencolar",
            "queue", "cola", "front", "rear", "frente"
        }

        self.indicators = [
            StructureIndicator("Operación enqueue", "Llamada a enqueue()", 0.6),
            StructureIndicator("Operación dequeue", "Llamada a dequeue()", 0.6),
            StructureIndicator("Par enqueue-dequeue", "Patrón FIFO", 0.5),
            StructureIndicator("Variable queue/cola", "Nombre típico", 0.4),
            StructureIndicator("Acceso frente y final", "Front y rear", 0.3),
        ]

        self.operation_complexities = [
            OperationComplexity("enqueue", "O(1)", "O(1)", "O(1)", "O(1)"),
            OperationComplexity("dequeue", "O(1)", "O(1)", "O(1)", "O(1)"),
            OperationComplexity("front/peek", "O(1)", "O(1)", "O(1)", "O(1)"),
        ]

    def detect(self, ast: ProgramNode) -> Optional[StructureMatch]:
        algorithm = ast.algorithm
        if not algorithm:
            return None

        queue_vars = set()
        operations = []
        evidence = []
        indicators = [StructureIndicator(name=i.name, description=i.description, weight=i.weight) 
                     for i in self.indicators]

        # Buscar enqueue
        enqueue_ops = self._find_ops(algorithm.body, ["enqueue", "encolar"])
        if enqueue_ops:
            indicators[0].found = True
            queue_vars.update(op["target"] for op in enqueue_ops)
            operations.extend(f"enqueue a {op['target']}" for op in enqueue_ops[:3])
            evidence.append(f"Operaciones enqueue: {len(enqueue_ops)}")

        # Buscar dequeue
        dequeue_ops = self._find_ops(algorithm.body, ["dequeue", "desencolar"])
        if dequeue_ops:
            indicators[1].found = True
            queue_vars.update(op["target"] for op in dequeue_ops)
            operations.extend(f"dequeue de {op['target']}" for op in dequeue_ops[:3])
            evidence.append(f"Operaciones dequeue: {len(dequeue_ops)}")

        # Par enqueue-dequeue
        if enqueue_ops and dequeue_ops:
            indicators[2].found = True
            evidence.append("Patrón FIFO completo")

        # Variables con nombre queue
        named_vars = self._find_named_vars(algorithm)
        if named_vars:
            indicators[3].found = True
            queue_vars.update(named_vars)
            evidence.append(f"Variables queue: {', '.join(named_vars)}")
        
        confidence = self._calculate_confidence(indicators)
        if confidence < 0.25:
            return None

        found, missing = self._split_indicators(indicators)

        return StructureMatch(
            structure_type=self.structure_type,
            structure_name=self.structure_name,
            confidence=confidence,
            variables=list(queue_vars) if queue_vars else ["cola"],
            indicators_found=found,
            indicators_missing=missing,
            operations=operations,
            operation_complexities=self.operation_complexities,
            reasoning=self._build_reasoning(found, missing),
            properties={
                "total_variables": len(queue_vars),
                "enqueue_count": len(enqueue_ops),
                "dequeue_count": len(dequeue_ops),
            },
            code_evidence=evidence
        )

    def _find_ops(self, node, ops):
        results = []
        def visit(n):
            # Check CallStatementNode (call enqueue(...))
            if isinstance(n, CallStatementNode):
                if any(op in n.function_name.lower() for op in ops):
                    results.append({"operation": n.function_name, "target": "queue"})
            # Check FunctionCallNode (x := dequeue(...))
            if isinstance(n, FunctionCallNode):
                if any(op in n.function_name.lower() for op in ops):
                    results.append({"operation": n.function_name, "target": "queue"})
            # Recursively visit all attributes
            for attr in ['statements', 'then_block', 'else_block', 'body', 'value', 'expression']:
                if hasattr(n, attr):
                    child = getattr(n, attr)
                    if isinstance(child, list):
                        for item in child:
                            visit(item)
                    elif child is not None:
                        visit(child)
        visit(node)
        return results

    def _find_named_vars(self, algo):
        vars = []
        for p in algo.parameters:
            name = p.name if hasattr(p, 'name') else str(p)
            if any(k in name.lower() for k in self.queue_keywords):
                vars.append(name)
        return vars