"""
Analizador de Complejidad Espacial

Analiza el uso de memoria de un algoritmo:
- Variables locales
- Estructuras de datos (arrays, objetos)
- Espacio de pila de recursión
- Espacio auxiliar
"""

from typing import Dict, List, Set
from dataclasses import dataclass, field

from app.core.parser.ast_nodes import *
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class SpaceUsage:
    """Uso de espacio en un punto del algoritmo"""
    variables: Set[str] = field(default_factory=set)
    arrays: Dict[str, List[str]] = field(default_factory=dict)  # {name: [dimensions]}
    objects: Set[str] = field(default_factory=set)
    recursion_depth: str = "1"  # Expresión de profundidad
    
    def total_space(self) -> str:
        """Calcula el espacio total usado"""
        # Variables simples: O(1) cada una
        var_space = len(self.variables)
        
        # Arrays: suma de sus dimensiones
        array_space = []
        for array_name, dimensions in self.arrays.items():
            if dimensions:
                # Multiplicar dimensiones
                dim_str = " * ".join(str(d) for d in dimensions if d)
                array_space.append(dim_str)
        
        # Objetos: O(1) cada uno
        obj_space = len(self.objects)
        
        # Espacio de recursión
        rec_space = self.recursion_depth
        
        # Combinar
        spaces = []
        
        if var_space > 0:
            spaces.append(str(var_space))
        
        if array_space:
            spaces.extend(array_space)
        
        if obj_space > 0:
            spaces.append(str(obj_space))
        
        if rec_space != "1":
            spaces.append(rec_space)
        
        if not spaces:
            return "1"
        
        # Tomar el dominante
        return self._get_dominant_space(spaces)
    
    def _get_dominant_space(self, spaces: List[str]) -> str:
        """Obtiene el término dominante"""
        # Orden de complejidades espaciales
        order = {
            "1": 0,
            "log n": 1,
            "n": 2,
            "n * n": 3,
            "n^2": 3,
        }
        
        max_order = 0
        dominant = "1"
        
        for space in spaces:
            space_order = order.get(space, 999)
            if space_order > max_order:
                max_order = space_order
                dominant = space
        
        return dominant


@dataclass
class SpaceAnalysisResult:
    """Resultado del análisis espacial"""
    algorithm_name: str
    space_complexity: str  # S(n) = ...
    auxiliary_space: str   # Espacio adicional (sin contar entrada)
    input_space: str       # Espacio de entrada
    recursion_space: str   # Espacio de pila de recursión
    explanation: str = ""
    breakdown: Dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "algorithm_name": self.algorithm_name,
            "space_complexity": self.space_complexity,
            "auxiliary_space": self.auxiliary_space,
            "input_space": self.input_space,
            "recursion_space": self.recursion_space,
            "explanation": self.explanation,
            "breakdown": self.breakdown,
        }


class SpaceAnalyzer:
    """
    Analizador de complejidad espacial.
    
    Analiza el uso de memoria del algoritmo.
    """
    
    def __init__(self):
        self.logger = setup_logger(__name__)
        
        # Variables declaradas
        self.variables: Set[str] = set()
        
        # Arrays declarados: {name: dimensions}
        self.arrays: Dict[str, List[str]] = {}
        
        # Objetos declarados
        self.objects: Set[str] = set()
        
        # Profundidad de recursión
        self.is_recursive: bool = False
        self.recursion_depth: str = "1"
        
        # Parámetros del algoritmo
        self.parameters: Set[str] = set()
        self.array_parameters: Dict[str, List] = {}
    
    def analyze(self, ast: ProgramNode) -> SpaceAnalysisResult:
        """
        Analiza la complejidad espacial del algoritmo.
        
        Args:
            ast: AST del algoritmo
        
        Returns:
            SpaceAnalysisResult: Resultado del análisis
        """
        self.logger.info(f"Analizando complejidad espacial: {ast.algorithm.name}")
        
        # Reset
        self.variables.clear()
        self.arrays.clear()
        self.objects.clear()
        self.parameters.clear()
        self.array_parameters.clear()
        self.is_recursive = False
        self.recursion_depth = "1"
        
        # Analizar
        algorithm = ast.algorithm
        
        # Registrar parámetros
        for param in algorithm.parameters:
            self.parameters.add(param.name)
            
            if param.param_type == "array":
                self.array_parameters[param.name] = param.array_dimensions
        
        # Analizar el cuerpo
        if algorithm.body:
            self._analyze_block(algorithm.body, algorithm.name)
        
        # Calcular complejidad espacial
        space_usage = self._calculate_space_usage()
        
        # Espacio de entrada
        input_space = self._calculate_input_space()
        
        # Espacio auxiliar (sin contar entrada)
        auxiliary_space = space_usage
        
        # Espacio de recursión
        recursion_space = self.recursion_depth if self.is_recursive else "1"
        
        # Espacio total: S(n) = input + auxiliary + recursion
        total_space = self._combine_spaces([input_space, auxiliary_space, recursion_space])
        
        # Explicación
        explanation = self._generate_explanation(
            input_space,
            auxiliary_space,
            recursion_space,
            total_space
        )
        
        # Breakdown
        breakdown = {
            "variables": {
                "count": len(self.variables),
                "names": list(self.variables),
                "space": str(len(self.variables)) if self.variables else "0"
            },
            "arrays": {
                "count": len(self.arrays),
                "details": [
                    {
                        "name": name,
                        "dimensions": dims,
                        "space": " * ".join(str(d) for d in dims if d)
                    }
                    for name, dims in self.arrays.items()
                ]
            },
            "objects": {
                "count": len(self.objects),
                "names": list(self.objects),
                "space": str(len(self.objects)) if self.objects else "0"
            },
            "recursion": {
                "is_recursive": self.is_recursive,
                "depth": recursion_space
            }
        }
        
        return SpaceAnalysisResult(
            algorithm_name=algorithm.name,
            space_complexity=total_space,
            auxiliary_space=auxiliary_space,
            input_space=input_space,
            recursion_space=recursion_space,
            explanation=explanation,
            breakdown=breakdown
        )
    
    def _analyze_block(self, block: BlockNode, algorithm_name: str):
        """Analiza un bloque de código"""
        for statement in block.statements:
            self._analyze_statement(statement, algorithm_name)
    
    def _analyze_statement(self, statement: ASTNode, algorithm_name: str):
        """Analiza un statement"""
        if isinstance(statement, AssignmentNode):
            self._analyze_assignment(statement)
        
        elif isinstance(statement, ForLoopNode):
            self._analyze_for_loop(statement, algorithm_name)
        
        elif isinstance(statement, WhileLoopNode):
            self._analyze_while_loop(statement, algorithm_name)
        
        elif isinstance(statement, RepeatLoopNode):
            self._analyze_repeat_loop(statement, algorithm_name)
        
        elif isinstance(statement, IfStatementNode):
            self._analyze_if_statement(statement, algorithm_name)
        
        elif isinstance(statement, CallStatementNode):
            # Verificar si es llamada recursiva
            if statement.function_name == algorithm_name:
                self.is_recursive = True
                # TODO: Calcular profundidad de recursión
                self.recursion_depth = "n"  # Placeholder
    
    def _analyze_assignment(self, assignment: AssignmentNode):
        """Analiza una asignación"""
        target = assignment.target
        
        # Registrar variable
        if target.access_type == "variable":
            self.variables.add(target.name)
        
        elif target.access_type == "array":
            # Registrar array
            if target.name not in self.array_parameters:
                # Array local
                # TODO: Determinar dimensiones
                self.arrays[target.name] = ["n"]  # Placeholder
    
    def _analyze_for_loop(self, for_loop: ForLoopNode, algorithm_name: str):
        """Analiza un FOR loop"""
        # La variable del loop usa espacio O(1)
        self.variables.add(for_loop.variable)
        
        # Analizar el cuerpo
        self._analyze_block(for_loop.body, algorithm_name)
    
    def _analyze_while_loop(self, while_loop: WhileLoopNode, algorithm_name: str):
        """Analiza un WHILE loop"""
        self._analyze_block(while_loop.body, algorithm_name)
    
    def _analyze_repeat_loop(self, repeat_loop: RepeatLoopNode, algorithm_name: str):
        """Analiza un REPEAT loop"""
        for statement in repeat_loop.body:
            self._analyze_statement(statement, algorithm_name)
    
    def _analyze_if_statement(self, if_stmt: IfStatementNode, algorithm_name: str):
        """Analiza un IF statement"""
        # Analizar then block
        self._analyze_block(if_stmt.then_block, algorithm_name)
        
        # Analizar else block si existe
        if if_stmt.else_block:
            self._analyze_block(if_stmt.else_block, algorithm_name)
    
    def _calculate_space_usage(self) -> str:
        """Calcula el uso de espacio del algoritmo"""
        spaces = []
        
        # Variables: O(1) cada una
        if self.variables:
            spaces.append(str(len(self.variables)))
        
        # Arrays: O(dimensiones)
        for array_name, dimensions in self.arrays.items():
            if dimensions:
                dim_str = " * ".join(str(d) for d in dimensions if d)
                spaces.append(dim_str)
        
        # Objetos: O(1) cada uno
        if self.objects:
            spaces.append(str(len(self.objects)))
        
        if not spaces:
            return "1"
        
        # Tomar el dominante
        return self._get_dominant_space(spaces)
    
    def _calculate_input_space(self) -> str:
        """Calcula el espacio de entrada"""
        input_spaces = []
        
        # Parámetros simples: O(1)
        simple_params = len(self.parameters) - len(self.array_parameters)
        if simple_params > 0:
            input_spaces.append(str(simple_params))
        
        # Arrays de entrada
        for array_name, dimensions in self.array_parameters.items():
            if dimensions:
                dim_str = " * ".join(str(d) if d else "n" for d in dimensions)
                input_spaces.append(dim_str)
        
        if not input_spaces:
            return "1"
        
        return self._get_dominant_space(input_spaces)
    
    def _combine_spaces(self, spaces: List[str]) -> str:
        """Combina múltiples espacios"""
        # Filtrar "1"
        non_constant = [s for s in spaces if s != "1"]
        
        if not non_constant:
            return "1"
        
        # Tomar el dominante
        return self._get_dominant_space(non_constant)
    
    def _get_dominant_space(self, spaces: List[str]) -> str:
        """Obtiene el término dominante"""
        order = {
            "1": 0,
            "log n": 1,
            "n": 2,
            "n log n": 3,
            "n * n": 4,
            "n^2": 4,
            "n^3": 5,
        }
        
        max_order = 0
        dominant = "1"
        
        for space in spaces:
            space_order = order.get(space, 999)
            if space_order > max_order:
                max_order = space_order
                dominant = space
        
        return dominant
    
    def _generate_explanation(
        self,
        input_space: str,
        auxiliary_space: str,
        recursion_space: str,
        total_space: str
    ) -> str:
        """Genera explicación del análisis"""
        parts = []
        
        parts.append(f"Complejidad espacial total: S(n) = O({total_space})")
        
        if input_space != "1":
            parts.append(f"- Espacio de entrada: O({input_space})")
        
        if auxiliary_space != "1":
            parts.append(f"- Espacio auxiliar: O({auxiliary_space})")
        
        if self.is_recursive:
            parts.append(f"- Espacio de pila de recursión: O({recursion_space})")
        
        return "\n".join(parts)