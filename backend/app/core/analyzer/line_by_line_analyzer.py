"""
Analizador Línea por Línea

Analiza cada línea del algoritmo y cuenta cuántas veces se ejecuta
en función del tamaño de entrada n.
"""

from typing import Dict, List
from dataclasses import dataclass, field

from app.core.parser.ast_nodes import *
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

@dataclass
class LineExecution:
    """Información de ejecución de una línea"""
    line_number: int
    code: str = ""  # Código fuente de la línea
    statement_type: str = ""
    execution_count: str = ""  # Expresión: "1", "n", "n^2", etc.
    explanation: str = ""

@dataclass
class LineByLineResult:
    """Resultado del análisis línea por línea"""
    lines: List[LineExecution] = field(default_factory=list)
    total_operations: str = "0"
    
    def to_dict(self) -> dict:
        return {
            "lines": [
                {
                    "line": line.line_number,
                    "code": line.code,
                    "type": line.statement_type,
                    "executions": line.execution_count,
                    "explanation": line.explanation
                }
                for line in self.lines
            ],
            "total_operations": self.total_operations
        }

class LineByLineAnalyzer:
    """
    Analizador línea por línea.
    
    Determina cuántas veces se ejecuta cada línea del código.
    """
    
    def __init__(self):
        self.logger = setup_logger(__name__)
        
        # Resultado del análisis
        self.result = LineByLineResult()
        
        # Contexto actual (para loops anidados)
        self.context_multiplier = "1"
        self.context_stack: List[str] = []
        
        # Líneas del código fuente original
        self._source_lines: List[str] = []
    
    def analyze(self, ast: ProgramNode, source_code: str = "") -> LineByLineResult:
        """Analiza el algoritmo línea por línea
        
        Args:
            ast: AST del algoritmo
            source_code: Código fuente original para extraer texto de cada línea
        """
        self.logger.info(f"Analizando línea por línea: {ast.algorithm.name}")
        
        # Reset
        self.result = LineByLineResult()
        self.context_stack = []
        self.context_multiplier = "1"
        self._source_lines = source_code.split('\n') if source_code else []
        
        # Analizar el algoritmo
        if ast.algorithm:
            self._analyze_algorithm(ast.algorithm)
        
        return self.result
    
    def _analyze_algorithm(self, algorithm: AlgorithmNode):
        """Analiza un algoritmo"""
        # La declaración del algoritmo se ejecuta 1 vez
        alg_line = algorithm.line or 1
        self._add_line(
            line_number=alg_line,
            statement_type="algorithm_declaration",
            execution_count="1",
            explanation=f"Declaración del algoritmo {algorithm.name}"
        )
        
        # Analizar el cuerpo
        if algorithm.body:
            self._analyze_block(algorithm.body)
    
    def _analyze_block(self, block: BlockNode):
        """Analiza un bloque"""
        for statement in block.statements:
            self._analyze_statement(statement)
    
    def _analyze_statement(self, statement: ASTNode):
        """Analiza un statement"""
        if isinstance(statement, AssignmentNode):
            self._analyze_assignment(statement)
        
        elif isinstance(statement, ForLoopNode):
            self._analyze_for_loop(statement)
        
        elif isinstance(statement, WhileLoopNode):
            self._analyze_while_loop(statement)
        
        elif isinstance(statement, RepeatLoopNode):
            self._analyze_repeat_loop(statement)
        
        elif isinstance(statement, IfStatementNode):
            self._analyze_if_statement(statement)
        
        elif isinstance(statement, CallStatementNode):
            self._analyze_call(statement)
        
        elif isinstance(statement, ReturnStatementNode):
            self._analyze_return(statement)
    
    def _analyze_assignment(self, assignment: AssignmentNode):
        """Analiza una asignación"""
        self._add_line(
            line_number=assignment.line or 0,
            statement_type="assignment",
            execution_count=self.context_multiplier,
            explanation=f"Asignación a {assignment.target.name}"
        )
    
    def _analyze_for_loop(self, for_loop: ForLoopNode):
        """Analiza un FOR loop"""
        # La inicialización del loop se ejecuta 1 vez en el contexto actual
        self._add_line(
            line_number=for_loop.line or 0,
            statement_type="for_init",
            execution_count=self.context_multiplier,
            explanation=f"Inicialización FOR (variable {for_loop.variable})"
        )
        
        # Determinar número de iteraciones
        iterations = self._calculate_iterations(for_loop.start, for_loop.end)
        
        # Guardar contexto anterior
        self.context_stack.append(self.context_multiplier)
        
        # Actualizar contexto (multiplicar por iteraciones)
        self.context_multiplier = self._multiply(self.context_multiplier, iterations)
        
        # Analizar el cuerpo
        self._analyze_block(for_loop.body)
        
        # Restaurar contexto
        self.context_multiplier = self.context_stack.pop()
    
    def _calculate_iterations(self, start, end) -> str:
        """Calcula número de iteraciones"""
        if isinstance(start, LiteralNode) and isinstance(end, LiteralNode):
            return str(end.value - start.value + 1)
        return "n"
    
    def _analyze_while_loop(self, while_loop: WhileLoopNode):
        """Analiza un WHILE loop"""
        self._add_line(
            line_number=while_loop.line or 0,
            statement_type="while_condition",
            execution_count=self.context_multiplier,
            explanation="Evaluación de condición WHILE"
        )
        
        # Asumir n iteraciones
        self.context_stack.append(self.context_multiplier)
        self.context_multiplier = self._multiply(self.context_multiplier, "n")
        
        self._analyze_block(while_loop.body)
        
        self.context_multiplier = self.context_stack.pop()
    
    def _analyze_repeat_loop(self, repeat_loop: RepeatLoopNode):
        """Analiza un REPEAT loop"""
        # Asumir n iteraciones
        self.context_stack.append(self.context_multiplier)
        self.context_multiplier = self._multiply(self.context_multiplier, "n")
        
        for statement in repeat_loop.body:
            self._analyze_statement(statement)
        
        # La condición se evalúa al final
        self._add_line(
            line_number=repeat_loop.line or 0,
            statement_type="repeat_condition",
            execution_count=self.context_multiplier,
            explanation="Evaluación de condición REPEAT"
        )
        
        self.context_multiplier = self.context_stack.pop()
    
    def _analyze_if_statement(self, if_stmt: IfStatementNode):
        """Analiza un IF statement"""
        # La evaluación de la condición se ejecuta siempre
        self._add_line(
            line_number=if_stmt.line or 0,
            statement_type="if_condition",
            execution_count=self.context_multiplier,
            explanation="Evaluación de condición IF"
        )
        
        # Analizar then block (se ejecuta condicionalmente)
        self._analyze_block(if_stmt.then_block)
        
        # Analizar else block si existe
        if if_stmt.else_block:
            self._analyze_block(if_stmt.else_block)
    
    def _analyze_call(self, call: CallStatementNode):
        """Analiza una llamada a función"""
        self._add_line(
            line_number=call.line or 0,
            statement_type="function_call",
            execution_count=self.context_multiplier,
            explanation=f"Llamada a {call.function_name}"
        )
    
    def _analyze_return(self, return_stmt: ReturnStatementNode):
        """Analiza un RETURN"""
        self._add_line(
            line_number=return_stmt.line or 0,
            statement_type="return",
            execution_count=self.context_multiplier,
            explanation="Retorno de función"
        )
    
    def _add_line(self, line_number: int, statement_type: str, 
                  execution_count: str, explanation: str):
        """Agrega una línea al resultado"""
        # Obtener código fuente de la línea
        code_text = ""
        if self._source_lines and 0 < line_number <= len(self._source_lines):
            code_text = self._source_lines[line_number - 1].strip()
        
        line = LineExecution(
            line_number=line_number,
            code=code_text or f"Línea {line_number}",
            statement_type=statement_type,
            execution_count=execution_count,
            explanation=explanation
        )
        self.result.lines.append(line)
    
    def _multiply(self, a: str, b: str) -> str:
        """Multiplica dos expresiones de complejidad"""
        if a == "1":
            return b
        if b == "1":
            return a
        
        # Casos especiales
        if a == "n" and b == "n":
            return "n^2"
        
        return f"{a} * {b}"