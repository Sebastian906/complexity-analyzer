"""
Semantic Analyzer - Análisis Semántico del AST

Valida reglas semánticas como:
- Variables usadas antes de ser declaradas
- Tipos incompatibles
- Índices de arrays válidos
- Llamadas a funciones existentes

"""

from typing import Dict, Set, List, Optional
from dataclasses import dataclass, field

from app.core.parser.ast_nodes import (
    ASTNode, ProgramNode, AlgorithmNode, BlockNode,
    AssignmentNode, ForLoopNode, WhileLoopNode, RepeatLoopNode,
    IfStatementNode, CallStatementNode, ReturnStatementNode,
    VariableNode, LValueNode, ArrayAccessNode, BinaryOpNode,
    UnaryOpNode, FunctionCallNode, ParameterNode
)
from app.core.exceptions import SemanticErrorException
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class VariableInfo:
    """Información sobre una variable"""
    name: str
    is_array: bool = False
    is_parameter: bool = False
    dimensions: List[Optional[int]] = field(default_factory=list)
    first_use_line: Optional[int] = None


@dataclass
class FunctionInfo:
    """Información sobre una función/algoritmo"""
    name: str
    parameters: List[ParameterNode] = field(default_factory=list)
    is_recursive: bool = False


class SemanticAnalyzer:
    """
    Analizador semántico del AST.
    
    Realiza validaciones semánticas sobre el código parseado.
    """
    
    def __init__(self):
        self.logger = setup_logger(__name__)
        
        # Tabla de símbolos: {variable_name: VariableInfo}
        self.symbol_table: Dict[str, VariableInfo] = {}
        
        # Variables declaradas (usadas)
        self.declared_vars: Set[str] = set()
        
        # Funciones disponibles
        self.functions: Dict[str, FunctionInfo] = {}
        
        # Nombre del algoritmo actual
        self.current_algorithm: Optional[str] = None
        
        # Errores encontrados
        self.errors: List[str] = []
        
        # Warnings encontrados
        self.warnings: List[str] = []
    
    def analyze(self, ast: ProgramNode) -> bool:
        """
        Analiza semánticamente el AST completo.
        
        Args:
            ast: AST a analizar
        
        Returns:
            bool: True si no hay errores, False si hay errores
        
        Raises:
            SemanticErrorException: Si hay errores semánticos
        """
        self.logger.info("Iniciando análisis semántico")
        
        try:
            # Registrar clases si existen
            for class_def in ast.classes:
                self._register_class(class_def)
            
            # Analizar el algoritmo principal
            if ast.algorithm:
                self._analyze_algorithm(ast.algorithm)
            
            # Verificar si hay errores
            if self.errors:
                error_msg = "\n".join(self.errors)
                self.logger.error(f"Errores semánticos encontrados:\n{error_msg}")
                raise SemanticErrorException(
                    message="Errores semánticos en el código",
                    context=error_msg
                )
            
            # Log warnings si existen
            if self.warnings:
                warning_msg = "\n".join(self.warnings)
                self.logger.warning(f"Warnings semánticos:\n{warning_msg}")
            
            self.logger.info("Análisis semántico completado exitosamente")
            return True
        
        except SemanticErrorException:
            raise
        except Exception as e:
            self.logger.error(f"Error inesperado en análisis semántico: {e}")
            raise SemanticErrorException(
                message="Error inesperado durante análisis semántico",
                context=str(e)
            )
    
    def _register_class(self, class_def):
        """Registra una clase en la tabla de símbolos"""
        # Por ahora, solo log
        self.logger.debug(f"Clase registrada: {class_def.name}")
    
    def _analyze_algorithm(self, algorithm: AlgorithmNode):
        """Analiza un algoritmo"""
        self.current_algorithm = algorithm.name
        self.logger.debug(f"Analizando algoritmo: {algorithm.name}")
        
        # Registrar función
        func_info = FunctionInfo(
            name=algorithm.name,
            parameters=algorithm.parameters
        )
        self.functions[algorithm.name] = func_info
        
        # Registrar parámetros como variables declaradas
        for param in algorithm.parameters:
            var_info = VariableInfo(
                name=param.name,
                is_parameter=True,
                is_array=(param.param_type == "array"),
                dimensions=param.array_dimensions if param.param_type == "array" else []
            )
            self.symbol_table[param.name] = var_info
            self.declared_vars.add(param.name)
        
        # Analizar el cuerpo
        if algorithm.body:
            self._analyze_block(algorithm.body)
    
    def _analyze_block(self, block: BlockNode):
        """Analiza un bloque de código"""
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
            self._analyze_call_statement(statement)
        
        elif isinstance(statement, ReturnStatementNode):
            self._analyze_return_statement(statement)
    
    def _analyze_assignment(self, assignment: AssignmentNode):
        """Analiza una asignación"""
        # Registrar la variable del lado izquierdo
        target_name = assignment.target.name
        
        if target_name not in self.symbol_table:
            # Primera vez que se usa esta variable
            var_info = VariableInfo(
                name=target_name,
                is_array=(assignment.target.access_type == "array"),
                first_use_line=assignment.line
            )
            self.symbol_table[target_name] = var_info
        
        # Marcar como declarada
        self.declared_vars.add(target_name)
        
        # Analizar la expresión del lado derecho
        self._analyze_expression(assignment.value)
    
    def _analyze_for_loop(self, for_loop: ForLoopNode):
        """Analiza un ciclo FOR"""
        # Registrar la variable del loop
        loop_var = for_loop.variable
        
        if loop_var not in self.symbol_table:
            var_info = VariableInfo(
                name=loop_var,
                is_parameter=False,
                first_use_line=for_loop.line
            )
            self.symbol_table[loop_var] = var_info
        
        self.declared_vars.add(loop_var)
        
        # Analizar start y end
        self._analyze_expression(for_loop.start)
        self._analyze_expression(for_loop.end)
        
        # Analizar el cuerpo
        self._analyze_block(for_loop.body)
    
    def _analyze_while_loop(self, while_loop: WhileLoopNode):
        """Analiza un ciclo WHILE"""
        # Analizar la condición
        self._analyze_expression(while_loop.condition)
        
        # Analizar el cuerpo
        self._analyze_block(while_loop.body)
    
    def _analyze_repeat_loop(self, repeat_loop: RepeatLoopNode):
        """Analiza un ciclo REPEAT"""
        # Analizar el cuerpo
        for statement in repeat_loop.body:
            self._analyze_statement(statement)
        
        # Analizar la condición
        self._analyze_expression(repeat_loop.condition)
    
    def _analyze_if_statement(self, if_stmt: IfStatementNode):
        """Analiza un IF statement"""
        # Analizar la condición
        self._analyze_expression(if_stmt.condition)
        
        # Analizar then block
        self._analyze_block(if_stmt.then_block)
        
        # Analizar else block si existe
        if if_stmt.else_block:
            self._analyze_block(if_stmt.else_block)
    
    def _analyze_call_statement(self, call: CallStatementNode):
        """Analiza una llamada a función"""
        func_name = call.function_name
        
        # Verificar si la función existe o es recursiva
        if func_name not in self.functions and func_name != self.current_algorithm:
            self.warnings.append(
                f"Llamada a función '{func_name}' que no está definida"
            )
        
        # Si es recursiva, marcar
        if func_name == self.current_algorithm:
            self.functions[func_name].is_recursive = True
        
        # Analizar argumentos
        for arg in call.arguments:
            self._analyze_expression(arg)
    
    def _analyze_return_statement(self, return_stmt: ReturnStatementNode):
        """Analiza un RETURN statement"""
        if return_stmt.value:
            self._analyze_expression(return_stmt.value)
    
    def _analyze_expression(self, expr):
        """Analiza una expresión"""
        if isinstance(expr, VariableNode):
            self._check_variable_used(expr.name)
        
        elif isinstance(expr, BinaryOpNode):
            self._analyze_expression(expr.left)
            self._analyze_expression(expr.right)
        
        elif isinstance(expr, UnaryOpNode):
            self._analyze_expression(expr.operand)
        
        elif isinstance(expr, ArrayAccessNode):
            self._check_variable_used(expr.array_name)
            for index in expr.indices:
                self._analyze_expression(index)
        
        elif isinstance(expr, FunctionCallNode):
            # Verificar si es una llamada recursiva
            if expr.function_name == self.current_algorithm:
                if self.current_algorithm in self.functions:
                    self.functions[self.current_algorithm].is_recursive = True
            
            # Analizar argumentos
            for arg in expr.arguments:
                self._analyze_expression(arg)
        
        elif isinstance(expr, LValueNode):
            self._check_variable_used(expr.name)
            for index in expr.indices:
                self._analyze_expression(index)
        
        # Literales y otros nodos no necesitan análisis
    
    def _check_variable_used(self, var_name: str):
        """Verifica si una variable ha sido declarada antes de usarse"""
        if var_name not in self.declared_vars:
            self.errors.append(
                f"Variable '{var_name}' usada sin declarar (validación semántica)"
            )
    
    def get_symbol_table(self) -> Dict[str, VariableInfo]:
        """Retorna la tabla de símbolos"""
        return self.symbol_table
    
    def is_recursive(self, algorithm_name: str) -> bool:
        """Verifica si un algoritmo es recursivo"""
        if algorithm_name in self.functions:
            return self.functions[algorithm_name].is_recursive
        return False