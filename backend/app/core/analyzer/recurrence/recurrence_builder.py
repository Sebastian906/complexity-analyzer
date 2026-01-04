"""
Recurrence Builder - Constructor de Ecuaciones de Recurrencia

Construye ecuaciones T(n) para complejidad temporal y S(n) para espacial
a partir del análisis del código.
"""

from typing import Optional, List, Tuple
from dataclasses import dataclass

from app.core.parser.ast_nodes import *
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class RecurrenceEquation:
    """Ecuación de recurrencia"""
    equation: str           # T(n) = ...
    base_case: str          # T(1) = ...
    recurrence_type: str    # "temporal" o "spatial"
    is_recursive: bool = False
    recursion_pattern: Optional[str] = None  # "linear", "binary", "multiple"
    work_per_call: str = "1"
    explanation: str = ""


class RecurrenceBuilder:
    """
    Constructor de ecuaciones de recurrencia.
    
    Genera ecuaciones T(n) y S(n) para algoritmos recursivos.
    """
    
    def __init__(self):
        self.logger = setup_logger(__name__)
        self.is_recursive = False
        self.recursive_calls: List[Tuple[str, List]] = []  # [(function_name, args)]
        self.work_outside_recursion = "1"
    
    def build_temporal_recurrence(
        self,
        ast: ProgramNode,
        algorithm_name: Optional[str] = None
    ) -> Optional[RecurrenceEquation]:
        """
        Construye ecuación de recurrencia temporal T(n).
        
        Args:
            ast: AST del algoritmo
            algorithm_name: Nombre del algoritmo (para detectar recursión)
        
        Returns:
            RecurrenceEquation o None si no es recursivo
        """
        if not algorithm_name:
            algorithm_name = ast.algorithm.name
        
        self.logger.info(f"Construyendo T(n) para: {algorithm_name}")
        
        # Reset
        self.is_recursive = False
        self.recursive_calls.clear()
        self.work_outside_recursion = "1"
        
        # Analizar el cuerpo
        if ast.algorithm.body:
            self._analyze_for_recursion(ast.algorithm.body, algorithm_name)
        
        if not self.is_recursive:
            return None
        
        # Determinar patrón de recursión
        pattern = self._determine_recursion_pattern()
        
        # Construir ecuación
        equation = self._build_temporal_equation(pattern)
        base_case = self._determine_base_case()
        
        return RecurrenceEquation(
            equation=equation,
            base_case=base_case,
            recurrence_type="temporal",
            is_recursive=True,
            recursion_pattern=pattern,
            work_per_call=self.work_outside_recursion,
            explanation=self._explain_temporal_equation(pattern)
        )
    
    def build_spatial_recurrence(
        self,
        ast: ProgramNode,
        algorithm_name: Optional[str] = None
    ) -> Optional[RecurrenceEquation]:
        """
        Construye ecuación de recurrencia espacial S(n).
        
        Args:
            ast: AST del algoritmo
            algorithm_name: Nombre del algoritmo
        
        Returns:
            RecurrenceEquation o None si no es recursivo
        """
        if not algorithm_name:
            algorithm_name = ast.algorithm.name
        
        self.logger.info(f"Construyendo S(n) para: {algorithm_name}")
        
        # Reset
        self.is_recursive = False
        self.recursive_calls.clear()
        
        # Analizar
        if ast.algorithm.body:
            self._analyze_for_recursion(ast.algorithm.body, algorithm_name)
        
        if not self.is_recursive:
            return None
        
        # Determinar patrón
        pattern = self._determine_recursion_pattern()
        
        # Construir ecuación espacial
        # S(n) = espacio_local + espacio_pila_recursion
        
        if pattern == "linear":
            # S(n) = S(n-1) + O(1)
            equation = "S(n) = S(n-1) + O(1)"
            base_case = "S(1) = O(1)"
        
        elif pattern == "binary":
            # S(n) = S(n/2) + O(1) - solo una rama se ejecuta a la vez
            equation = "S(n) = S(n/2) + O(1)"
            base_case = "S(1) = O(1)"
        
        else:
            # Patrón genérico
            equation = f"S(n) = S(n/k) + O(1)"
            base_case = "S(1) = O(1)"
        
        return RecurrenceEquation(
            equation=equation,
            base_case=base_case,
            recurrence_type="spatial",
            is_recursive=True,
            recursion_pattern=pattern,
            explanation=self._explain_spatial_equation(pattern)
        )
    
    # Métodos privados
    
    def _analyze_for_recursion(self, block: BlockNode, algorithm_name: str):
        """Analiza un bloque buscando llamadas recursivas"""
        for statement in block.statements:
            if isinstance(statement, CallStatementNode):
                if statement.function_name == algorithm_name:
                    self.is_recursive = True
                    self.recursive_calls.append((
                        statement.function_name,
                        statement.arguments
                    ))
            
            elif isinstance(statement, ReturnStatementNode):
                # Buscar llamadas recursivas en la expresión de retorno
                if statement.value:
                    self._analyze_expression_for_recursion(statement.value, algorithm_name)
            
            elif isinstance(statement, AssignmentNode):
                # Buscar llamadas recursivas en el lado derecho de asignaciones
                if statement.value:
                    self._analyze_expression_for_recursion(statement.value, algorithm_name)
            
            elif isinstance(statement, ForLoopNode):
                self._analyze_for_recursion(statement.body, algorithm_name)
                # Trabajo fuera de recursión
                self.work_outside_recursion = "n"
            
            elif isinstance(statement, WhileLoopNode):
                self._analyze_for_recursion(statement.body, algorithm_name)
                self.work_outside_recursion = "n"
            
            elif isinstance(statement, RepeatLoopNode):
                for stmt in statement.body:
                    if isinstance(stmt, CallStatementNode):
                        if stmt.function_name == algorithm_name:
                            self.is_recursive = True
                            self.recursive_calls.append((stmt.function_name, stmt.arguments))
            
            elif isinstance(statement, IfStatementNode):
                self._analyze_for_recursion(statement.then_block, algorithm_name)
                if statement.else_block:
                    self._analyze_for_recursion(statement.else_block, algorithm_name)
    
    def _analyze_expression_for_recursion(self, expr, algorithm_name: str):
        """Analiza una expresión buscando llamadas recursivas"""
        if isinstance(expr, FunctionCallNode):
            if expr.function_name == algorithm_name:
                self.is_recursive = True
                self.recursive_calls.append((
                    expr.function_name,
                    expr.arguments
                ))
            # También analizar los argumentos
            for arg in expr.arguments:
                self._analyze_expression_for_recursion(arg, algorithm_name)
        
        elif isinstance(expr, BinaryOpNode):
            self._analyze_expression_for_recursion(expr.left, algorithm_name)
            self._analyze_expression_for_recursion(expr.right, algorithm_name)
        
        elif isinstance(expr, UnaryOpNode):
            self._analyze_expression_for_recursion(expr.operand, algorithm_name)
    
    def _determine_recursion_pattern(self) -> str:
        """Determina el patrón de recursión"""
        num_calls = len(self.recursive_calls)
        
        if num_calls == 0:
            return "none"
        elif num_calls == 1:
            return "linear"
        elif num_calls == 2:
            return "binary"
        else:
            return "multiple"
    
    def _build_temporal_equation(self, pattern: str) -> str:
        """Construye la ecuación temporal según el patrón"""
        work = self.work_outside_recursion
        
        if pattern == "linear":
            # T(n) = T(n-1) + O(work)
            return f"T(n) = T(n-1) + O({work})"
        
        elif pattern == "binary":
            # T(n) = 2*T(n/2) + O(work)
            return f"T(n) = 2*T(n/2) + O({work})"
        
        elif pattern == "multiple":
            num_calls = len(self.recursive_calls)
            # T(n) = k*T(n/m) + O(work)
            return f"T(n) = {num_calls}*T(n/k) + O({work})"
        
        return "T(n) = O(1)"
    
    def _determine_base_case(self) -> str:
        """Determina el caso base"""
        # Por defecto, el caso base es O(1)
        return "T(1) = O(1)"
    
    def _explain_temporal_equation(self, pattern: str) -> str:
        """Genera explicación de la ecuación temporal"""
        explanations = {
            "linear": (
                "Recursión lineal: el algoritmo se llama a sí mismo una vez "
                f"con entrada reducida, haciendo O({self.work_outside_recursion}) trabajo "
                "en cada llamada."
            ),
            "binary": (
                "Recursión binaria: el algoritmo se divide en dos subproblemas "
                f"del mismo tamaño, haciendo O({self.work_outside_recursion}) trabajo "
                "para combinar resultados."
            ),
            "multiple": (
                f"Recursión múltiple: el algoritmo hace {len(self.recursive_calls)} "
                f"llamadas recursivas, con O({self.work_outside_recursion}) trabajo adicional."
            )
        }
        return explanations.get(pattern, "Patrón de recursión no determinado")
    
    def _explain_spatial_equation(self, pattern: str) -> str:
        """Genera explicación de la ecuación espacial"""
        explanations = {
            "linear": (
                "La profundidad de la pila de recursión es O(n) porque cada "
                "llamada reduce el problema en 1, con O(1) espacio local por llamada."
            ),
            "binary": (
                "La profundidad de la pila es O(log n) porque el problema se "
                "divide a la mitad en cada llamada, con O(1) espacio local."
            ),
            "multiple": (
                "La profundidad de la pila depende del factor de reducción, "
                "con O(1) espacio local por llamada."
            )
        }
        return explanations.get(pattern, "Patrón espacial no determinado")


def build_recurrence_equations(
    ast: ProgramNode,
    algorithm_name: Optional[str] = None
) -> Tuple[Optional[RecurrenceEquation], Optional[RecurrenceEquation]]:
    """
    Helper function para construir ambas ecuaciones.
    
    Args:
        ast: AST del algoritmo
        algorithm_name: Nombre del algoritmo
    
    Returns:
        Tuple[T(n), S(n)]
    """
    builder = RecurrenceBuilder()
    
    temporal = builder.build_temporal_recurrence(ast, algorithm_name)
    spatial = builder.build_spatial_recurrence(ast, algorithm_name)
    
    return temporal, spatial