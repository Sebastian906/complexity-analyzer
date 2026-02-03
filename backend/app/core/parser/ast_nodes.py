"""
Definición de Nodos del Abstract Syntax Tree (AST)

Define todas las clases de nodos que representan la estructura del algoritmo.
Usando dataclasses para código limpio y type hints para seguridad de tipos.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, List, Optional, Union

from app.core.constants import ASTNodeType

# Clase Base para Nodos AST
@dataclass(kw_only=True)
class ASTNode(ABC):
    """
    Clase base abstracta para todos los nodos del AST.

    Attributes:
        node_type: Tipo de nodo (del enum ASTNodeType).
        line: Número de línea en el código fuente.
        column: Columna en el código fuente.
    
    Nota: Se usa kw_only=True para evitar conflictos de herencia con
    argumentos sin valor por defecto después de argumentos con default.
    """
    node_type: ASTNodeType = field(default=ASTNodeType.PROGRAM)
    line: Optional[int] = None
    column: Optional[int] = None

    @abstractmethod
    def __repr__(self) -> str:
        """Representación string del nodo"""
        pass

    @abstractmethod
    def to_dict(self) -> dict:
        """Convierte el nodo a diccionario para la serialización"""
        pass

# Nodo de Programa
@dataclass
class ProgramNode(ASTNode):
    """Nodo raíz del programa"""
    classes: List['ClassDefinitionNode'] = field(default_factory=list)
    algorithm: Optional['AlgorithmNode'] = None

    def __post_init__(self):
        self.node_type = ASTNodeType.PROGRAM

    def __repr__(self):
        return f"Program(classes={len(self.classes)}, algorithm={self.algorithm.name if self.algorithm else None})"

    def to_dict(self) -> dict:
        return {
            "type": self.node_type.value,
            "classes": [c.to_dict() for c in self.classes],
            "algorithm": self.algorithm.to_dict() if self.algorithm else None
        }

# Definición de Clases
@dataclass
class ClassDefinitionNode(ASTNode):
    """Definición de una clase/estructura de datos"""
    name: str
    attributes: List[str] = field(default_factory=list)

    def __post_init__(self):
        self.node_type = ASTNodeType.CLASS_DEFINITION

    def __repr__(self):
        return f"ClassDefinition({self.name}, attrs={self.attributes})"

    def to_dict(self) -> dict:
        return {
            "type": self.node_type.value,
            "name": self.name,
            "attributes": self.attributes
        }

# Algoritmo
@dataclass
class AlgorithmNode(ASTNode):
    """Definición del algoritmo principal"""
    name: str
    parameters: List['ParameterNode'] = field(default_factory=list)
    body: Optional['BlockNode'] = None

    def __post_init__(self):
        self.node_type = ASTNodeType.ALGORITHM

    def __repr__(self) -> str:
        return f"Algorithm({self.name}, params={len(self.parameters)})"

    def to_dict(self) -> dict:
        return {
            "type": self.node_type.value,
            "name": self.name,
            "parameters": [p.to_dict() for p in self.parameters],
            "body": self.body.to_dict() if self.body else None
        }

@dataclass
class ParameterNode(ASTNode):
    """Parámetro de un algoritmo"""
    name: str
    param_type: str # "simple", "array", "object"
    array_dimensions: List[Optional[Union[int, 'RangeNode']]] = field(default_factory=list)
    class_name: Optional[str] = None

    def __post_init__(self):
        self.node_type = ASTNodeType.PROGRAM # No hay un tipo específico para parámetros

    def __repr__(self):
        if self.param_type == "array":
            dims = "".join(f"[{d if d else ''}]" for d in self.array_dimensions)
            return f"Param({self.name}{dims})"
        elif self.param_type == "object":
            return f"Param({self.class_name} {self.name})"
        return f"Param({self.name})"

    def to_dict(self) -> dict:
        return {
            "type": "parameter",
            "name": self.name,
            "param_type": self.param_type,
            "array_dimensions": [d.to_dict() if isinstance(d, RangeNode) else d for d in self.array_dimensions],
            "class_name": self.class_name
        }

# Bloque de Código
@dataclass
class BlockNode(ASTNode):
    """Bloque de código (begin...end)"""
    statements: List[ASTNode] = field(default_factory=list)

    def __post_init__(self):
        self.node_type = ASTNodeType.BLOCK

    def __repr__(self) -> str:
        return f"Block({len(self.statements)} statements)"

    def to_dict(self) -> dict:
        return {
            "type": self.node_type.value,
            "statements": [s.to_dict() for s in self.statements]
        }

# Asignación
@dataclass
class AssignmentNode(ASTNode):
    """Asignación: variable ← expresión"""
    target: 'LValueNode'
    value: 'ExpressionNode'

    def __post_init__(self):
        self.node_type = ASTNodeType.ASSIGNMENT

    def __repr__(self) -> str:
        return f"Assignment({self.target} ← {self.value})"

    def to_dict(self) -> dict:
        return {
            "type": self.node_type.value,
            "target": self.target.to_dict(),
            "value": self.value.to_dict()
        }

@dataclass
class LValueNode(ASTNode):
    """L-Value: lado izquierdo de asignación"""
    name: str
    access_type: str  # "variable", "array", "object_field"
    indices: List['ExpressionNode'] = field(default_factory=list)
    field_name: Optional[str] = None

    def __post_init__(self):
        self.node_type = ASTNodeType.VARIABLE

    def __repr__(self) -> str:
        if self.access_type == "array":
            idx_str = "".join(f"[{i}]" for i in self.indices)
            return f"{self.name}{idx_str}"
        elif self.access_type == "object_field":
            return f"{self.name}.{self.field_name}"
        return self.name

    def to_dict(self) -> dict:
        return {
            "type": "lvalue",
            "name": self.name,
            "access_type": self.access_type,
            "indices": [i.to_dict() for i in self.indices],
            "field_name": self.field_name
        }

# Ciclos
@dataclass
class ForLoopNode(ASTNode):
    """Ciclo FOR: for variable ← start to end do ... end"""
    variable: str
    start: 'ExpressionNode'
    end: 'ExpressionNode'
    body: BlockNode

    def __post_init__(self):
        self.node_type = ASTNodeType.FOR_LOOP

    def __repr__(self) -> str:
        return f"ForLoop({self.variable}: {self.start} to {self.end})"

    def to_dict(self) -> dict:
        return {
            "type": self.node_type.value,
            "variable": self.variable,
            "start": self.start.to_dict(),
            "end": self.end.to_dict(),
            "body": self.body.to_dict()
        }

@dataclass
class WhileLoopNode(ASTNode):
    """Ciclo WHILE: while (condition) do ... end"""
    condition: 'ExpressionNode'
    body: BlockNode

    def __post_init__(self):
        self.node_type = ASTNodeType.WHILE_LOOP

    def __repr__(self) -> str:
        return f"WhileLoop({self.condition})"

    def to_dict(self) -> dict:
        return {
            "type": self.node_type.value,
            "condition": self.condition.to_dict(),
            "body": self.body.to_dict()
        }

@dataclass
class RepeatLoopNode(ASTNode):
    """Ciclo REPEAT: repeat ... until (condition)"""
    body: List[ASTNode]  # Lista de statements, no BlockNode
    condition: 'ExpressionNode'

    def __post_init__(self):
        self.node_type = ASTNodeType.REPEAT_LOOP

    def __repr__(self) -> str:
        return f"RepeatLoop(until {self.condition})"

    def to_dict(self) -> dict:
        return {
            "type": self.node_type.value,
            "body": [s.to_dict() for s in self.body],
            "condition": self.condition.to_dict()
        }

# Condicional
@dataclass
class IfStatementNode(ASTNode):
    """Condicional IF: if (condition) then ... else ... end"""
    condition: 'ExpressionNode'
    then_block: BlockNode
    else_block: Optional[BlockNode] = None

    def __post_init__(self):
        self.node_type = ASTNodeType.IF_STATEMENT

    def __repr__(self) -> str:
        return f"IfStatement({self.condition})"

    def to_dict(self) -> dict:
        return {
            "type": self.node_type.value,
            "condition": self.condition.to_dict(),
            "then_block": self.then_block.to_dict(),
            "else_block": self.else_block.to_dict() if self.else_block else None
        }

# Llamadas
@dataclass
class CallStatementNode(ASTNode):
    """Llamada a subrutina: call function(args)"""
    function_name: str
    arguments: List['ExpressionNode'] = field(default_factory=list)

    def __post_init__(self):
        self.node_type = ASTNodeType.CALL

    def __repr__(self) -> str:
        return f"Call({self.function_name}, {len(self.arguments)} args)"

    def to_dict(self) -> dict:
        return {
            "type": self.node_type.value,
            "function_name": self.function_name,
            "arguments": [a.to_dict() for a in self.arguments]
        }

@dataclass
class ReturnStatementNode(ASTNode):
    """Retorno de función: return expression"""
    value: Optional['ExpressionNode'] = None

    def __post_init__(self):
        self.node_type = ASTNodeType.RETURN

    def __repr__(self) -> str:
        return f"Return({self.value if self.value else 'void'})"

    def to_dict(self) -> dict:
        return {
            "type": self.node_type.value,
            "value": self.value.to_dict() if self.value else None
        }

# Expresiones
@dataclass
class ExpressionNode(ASTNode):
    """Clase base para expresiones"""
    pass

@dataclass
class BinaryOpNode(ExpressionNode):
    """Operación binaria: left op right"""
    operator: str
    left: ExpressionNode
    right: ExpressionNode
    
    def __post_init__(self):
        self.node_type = ASTNodeType.BINARY_OP
    
    def __repr__(self) -> str:
        return f"({self.left} {self.operator} {self.right})"
    
    def to_dict(self) -> dict:
        return {
            "type": self.node_type.value,
            "operator": self.operator,
            "left": self.left.to_dict(),
            "right": self.right.to_dict()
        }

@dataclass
class UnaryOpNode(ExpressionNode):
    """Operación unaria: op operand"""
    operator: str
    operand: ExpressionNode
    
    def __post_init__(self):
        self.node_type = ASTNodeType.UNARY_OP
    
    def __repr__(self) -> str:
        return f"({self.operator}{self.operand})"
    
    def to_dict(self) -> dict:
        return {
            "type": self.node_type.value,
            "operator": self.operator,
            "operand": self.operand.to_dict()
        }

@dataclass
class LiteralNode(ExpressionNode):
    """Literal: número, string, booleano"""
    value: Union[int, float, str, bool]
    literal_type: str  # "number", "string", "boolean"
    
    def __post_init__(self):
        self.node_type = ASTNodeType.LITERAL
    
    def __repr__(self) -> str:
        return f"{self.value}"
    
    def to_dict(self) -> dict:
        return {
            "type": self.node_type.value,
            "value": self.value,
            "literal_type": self.literal_type
        }

@dataclass
class VariableNode(ExpressionNode):
    """Variable simple"""
    name: str
    
    def __post_init__(self):
        self.node_type = ASTNodeType.VARIABLE
    
    def __repr__(self) -> str:
        return self.name
    
    def to_dict(self) -> dict:
        return {
            "type": self.node_type.value,
            "name": self.name
        }

@dataclass
class ArrayAccessNode(ExpressionNode):
    """Acceso a array: A[i] o A[i][j]"""
    array_name: str
    indices: List[ExpressionNode]
    
    def __post_init__(self):
        self.node_type = ASTNodeType.ARRAY_ACCESS
    
    def __repr__(self) -> str:
        idx_str = "".join(f"[{i}]" for i in self.indices)
        return f"{self.array_name}{idx_str}"
    
    def to_dict(self) -> dict:
        return {
            "type": self.node_type.value,
            "array_name": self.array_name,
            "indices": [i.to_dict() for i in self.indices]
        }

@dataclass
class ObjectAccessNode(ExpressionNode):
    """Acceso a campo de objeto: obj.field"""
    object_name: str
    field_name: str
    
    def __post_init__(self):
        self.node_type = ASTNodeType.OBJECT_ACCESS
    
    def __repr__(self) -> str:
        return f"{self.object_name}.{self.field_name}"
    
    def to_dict(self) -> dict:
        return {
            "type": self.node_type.value,
            "object_name": self.object_name,
            "field_name": self.field_name
        }

@dataclass
class FunctionCallNode(ExpressionNode):
    """Llamada a función en expresión: func(args)"""
    function_name: str
    arguments: List[ExpressionNode] = field(default_factory=list)
    
    def __post_init__(self):
        self.node_type = ASTNodeType.CALL
    
    def __repr__(self) -> str:
        return f"{self.function_name}({len(self.arguments)} args)"
    
    def to_dict(self) -> dict:
        return {
            "type": "function_call",
            "function_name": self.function_name,
            "arguments": [a.to_dict() for a in self.arguments]
        }

@dataclass
class RangeNode(ExpressionNode):
    """
    Representa un rango: 1..n
    
    Usado en parámetros de arrays como A[1..n]
    """
    start: Union[int, str, ExpressionNode]
    end: Union[int, str, ExpressionNode]
    
    def __post_init__(self):
        self.node_type = ASTNodeType.LITERAL  # Reutilizamos tipo existente
    
    def __repr__(self) -> str:
        return f"{self.start}..{self.end}"
    
    def to_dict(self) -> dict:
        return {
            "type": "range",
            "start": str(self.start),
            "end": str(self.end)
        }