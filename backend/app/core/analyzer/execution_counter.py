"""
Contador de ejecuciones por línea

Cuenta el número de ejecuciones que cada línea de código realiza 
durante la ejecución del algoritmo, expresándolo en función de n.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from app.core.parser.ast_nodes import (
    ASTNode, ProgramNode, AlgorithmNode, BlockNode,
    ForLoopNode, WhileLoopNode, RepeatLoopNode, IfStatementNode,
    AssignmentNode, ReturnStatementNode, CallStatementNode,
    LiteralNode, VariableNode, BinaryOpNode, UnaryOpNode
)


@dataclass
class LineExecution:
    """Información de ejecución para una línea."""
    line: int
    code: str
    count: str  # "1", "n", "n²", etc.
    level: int = 0
    notes: str = ""


class ExecutionCounter:
    """Cuenta ejecuciones por línea del código."""
    
    def __init__(self):
        self._reset()
    
    def _reset(self):
        self.executions: Dict[int, LineExecution] = {}
        self.multipliers: List[str] = []
        self.max_n_count: int = 0  # Track máxima profundidad de n
        self.max_log_count: int = 0  # Track máxima profundidad de log n
        self.level: int = 0
        self.func_name: Optional[str] = None
        self.lines: List[str] = []
    
    def count(self, ast: ProgramNode, source: str = "") -> Dict[str, Any]:
        """Cuenta ejecuciones de cada línea."""
        self._reset()
        self.lines = source.split('\n') if source else []
        
        self._visit(ast)
        
        return {
            "lines": [e.__dict__ for e in sorted(self.executions.values(), key=lambda x: x.line)],
            "total": self._get_count(),
            "dominant": self._get_dominant()
        }
    
    def _get_code(self, line: int) -> str:
        """Obtiene código de una línea."""
        return self.lines[line - 1].strip() if 0 < line <= len(self.lines) else ""
    
    def _get_count(self) -> str:
        """Calcula conteo actual basado en loops anidados."""
        if not self.multipliers:
            return "1"
        
        n_count = self.multipliers.count("n")
        log_count = self.multipliers.count("log n")
        
        if n_count == 0 and log_count == 0:
            return "1"
        if n_count == 1 and log_count == 0:
            return "n"
        if n_count == 2 and log_count == 0:
            return "n²"
        if n_count == 3 and log_count == 0:
            return "n³"
        if n_count == 1 and log_count == 1:
            return "n·log n"
        if n_count == 0 and log_count == 1:
            return "log n"
        if n_count > 3:
            return f"n^{n_count}"
        
        return "n"
    
    def _get_dominant(self) -> str:
        """Obtiene la complejidad dominante basada en multiplicadores."""
        # Primero intentar desde max counts trackeados
        if self.max_n_count >= 3:
            return "O(n³)"
        if self.max_n_count == 2:
            return "O(n²)"
        if self.max_n_count == 1 and self.max_log_count >= 1:
            return "O(n log n)"
        if self.max_n_count == 1:
            return "O(n)"
        if self.max_log_count >= 1:
            return "O(log n)"
        
        # Fallback a self.executions
        counts = [e.count for e in self.executions.values()]
        
        if any("n³" in c for c in counts):
            return "O(n³)"
        if any("n²" in c for c in counts):
            return "O(n²)"
        if any("n·log" in c for c in counts):
            return "O(n log n)"
        if any(c == "n" for c in counts):
            return "O(n)"
        if any("log" in c for c in counts):
            return "O(log n)"
        return "O(1)"
    
    def _update_max_counts(self):
        """Actualiza los contadores máximos de n y log n."""
        n_count = self.multipliers.count("n")
        log_count = self.multipliers.count("log n")
        
        if n_count > self.max_n_count:
            self.max_n_count = n_count
        if log_count > self.max_log_count:
            self.max_log_count = log_count
    
    def _add(self, line: int, notes: str = ""):
        """Agrega ejecución para una línea."""
        if line > 0:
            self.executions[line] = LineExecution(
                line=line,
                code=self._get_code(line),
                count=self._get_count(),
                level=self.level,
                notes=notes
            )
    
    def _visit(self, node):
        """Visita un nodo del AST."""
        if node is None:
            return
        
        if isinstance(node, ProgramNode):
            for cls in node.classes:
                self._visit(cls)
            if node.algorithm:
                self._visit(node.algorithm)
                
        elif isinstance(node, AlgorithmNode):
            self.func_name = node.name
            line = getattr(node, 'line', 0)
            if line:
                self._add(line, "algoritmo")
            if node.body:
                self._visit(node.body)
                
        elif isinstance(node, BlockNode):
            for stmt in node.statements:
                self._visit(stmt)
                
        elif isinstance(node, ForLoopNode):
            line = getattr(node, 'line', 0)
            mult = self._get_for_multiplier(node)
            
            # Agregar multiplier ANTES de registrar líneas
            self.multipliers.append(mult)
            self.level += 1
            
            # Actualizar contadores máximos
            self._update_max_counts()
            
            if line:
                self._add(line, f"for: {mult} iteraciones")
            
            if node.body:
                self._visit(node.body)
            
            self.multipliers.pop()
            self.level -= 1
            
        elif isinstance(node, WhileLoopNode):
            line = getattr(node, 'line', 0)
            mult = self._get_while_multiplier(node)
            
            # Agregar multiplier ANTES de registrar líneas
            self.multipliers.append(mult)
            self.level += 1
            
            # Actualizar contadores máximos
            self._update_max_counts()
            
            if line:
                self._add(line, f"while: {mult} iteraciones")
            
            if node.body:
                self._visit(node.body)
            
            self.multipliers.pop()
            self.level -= 1
            
        elif isinstance(node, IfStatementNode):
            line = getattr(node, 'line', 0)
            if line:
                self._add(line, "condición")
            if node.true_block:
                self._visit(node.true_block)
            if node.false_block:
                self._visit(node.false_block)
                
        elif isinstance(node, AssignmentNode):
            line = getattr(node, 'line', 0)
            if line:
                self._add(line, "asignación")
                
        elif isinstance(node, ReturnStatementNode):
            line = getattr(node, 'line', 0)
            if line:
                self._add(line, "return")
                
        elif isinstance(node, CallStatementNode):
            line = getattr(node, 'line', 0)
            if line:
                note = f"llamada: {node.function_name}"
                if self.func_name and node.function_name == self.func_name:
                    note += " (recursiva)"
                self._add(line, note)
                
        elif isinstance(node, RepeatLoopNode):
            line = getattr(node, 'line', 0)
            if line:
                self._add(line, "repeat")
            self.multipliers.append("n")
            self.level += 1
            if node.body:
                self._visit(node.body)
            self.multipliers.pop()
            self.level -= 1
    
    def _get_for_multiplier(self, node: ForLoopNode) -> str:
        """Determina multiplicador de un for."""
        end = self._extract_value(node.end)
        start = self._extract_value(node.start)
        
        if end == "n" and start in (0, 1, "0", "1"):
            return "n"
        if isinstance(start, str) or isinstance(end, str):
            return "n"
        return "n"
    
    def _get_while_multiplier(self, node: WhileLoopNode) -> str:
        """Determina multiplicador de un while."""
        # Detectar patrón de división (log n)
        if node.body and isinstance(node.body, BlockNode):
            for stmt in node.body.statements:
                if isinstance(stmt, AssignmentNode) and isinstance(stmt.value, BinaryOpNode):
                    if stmt.value.operator == '/':
                        return "log n"
        return "n"
    
    def _extract_value(self, expr) -> Any:
        """Extrae valor de una expresión."""
        if expr is None:
            return 0
        if isinstance(expr, LiteralNode):
            return expr.value
        if isinstance(expr, VariableNode):
            return expr.name
        if isinstance(expr, BinaryOpNode):
            left = self._extract_value(expr.left)
            if left == "n":
                return "n"
            right = self._extract_value(expr.right)
            if right == "n":
                return "n"
        return "n"


def count_executions(ast: ProgramNode, source: str = "") -> Dict[str, Any]:
    """Función de conveniencia para contar ejecuciones."""
    return ExecutionCounter().count(ast, source)