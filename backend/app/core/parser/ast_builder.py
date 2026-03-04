"""
AST Builder - Transformer de Parse Tree a AST

Convierte el parse tree de Lark en nuestro Abstract Syntax Tree personalizado.
Implementa el patrón Visitor para procesar cada tipo de nodo.
"""

from typing import Any, List, Optional, Union

from lark import Transformer, Token, Tree

from app.core.exceptions import ASTBuildException
from app.core.parser.ast_nodes import (
    AlgorithmNode,
    ArrayAccessNode,
    AssignmentNode,
    BinaryOpNode,
    BlockNode,
    CallStatementNode,
    ClassDefinitionNode,
    ForLoopNode,
    FunctionCallNode,
    IfStatementNode,
    LiteralNode,
    LValueNode,
    ObjectAccessNode,
    ParameterNode,
    ProgramNode,
    RangeNode,
    RepeatLoopNode,
    ReturnStatementNode,
    UnaryOpNode,
    VariableNode,
    WhileLoopNode,
)
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class ASTBuilder(Transformer):
    """
    Transformer que convierte parse tree de Lark en AST.

    Cada método corresponde a una regla de la gramática y retorna
    el nodo AST apropiado.

    Example:
        >>> from lark import Lark
        >>> parser = Lark(grammar, start='start')
        >>> tree = parser.parse(code)
        >>> builder = ASTBuilder()
        >>> ast = builder.transform(tree)
    """

    def __init__(self):
        """Inicializa el builder"""
        super().__init__()
        logger.debug("ASTBuilder inicializado")

    # Programa principal

    def start(self, items: List[Any]) -> ProgramNode:
        """Regla start: programa completo"""
        logger.debug("Construyendo nodo Program")
        return items[0]  # Retorna el ProgramNode

    def program(self, items: List[Any]) -> ProgramNode:
        """Regla program: class_definition* algorithm"""
        classes = []
        algorithm = None

        for item in items:
            if isinstance(item, ClassDefinitionNode):
                classes.append(item)
            elif isinstance(item, AlgorithmNode):
                algorithm = item

        logger.debug(f"Program: {len(classes)} classes, algorithm={algorithm.name if algorithm else None}")

        return ProgramNode(
            classes=classes,
            algorithm=algorithm
        )

    # Definición de clases

    def class_definition(self, items: List[Any]) -> ClassDefinitionNode:
        """Regla class_definition: CLASS_NAME "{" attribute_list "}" """
        class_name = str(items[0])
        attributes = items[1] if len(items) > 1 else []

        logger.debug(f"Class definition: {class_name} with {len(attributes)} attributes")

        return ClassDefinitionNode(
            name=class_name,
            attributes=attributes
        )

    def attribute_list(self, items: List[Token]) -> List[str]:
        """Regla attribute_list: IDENTIFIER+ """
        return [str(token) for token in items]

    # Algoritmo

    def algorithm(self, items: List[Any]) -> AlgorithmNode:
        """Regla algorithm: ALGORITHM_KW IDENTIFIER "(" parameter_list? ")" block"""
        # items[0] es ALGORITHM_KW, items[1] es IDENTIFIER (nombre del algoritmo)
        alg_token = items[0]  # ALGORITHM_KW token con info de línea
        name = str(items[1])
        parameters = []
        body = None

        for item in items[2:]:
            if isinstance(item, list):  # parameter_list
                parameters = item
            elif isinstance(item, BlockNode):
                body = item

        logger.debug(f"Algorithm: {name} with {len(parameters)} parameters")

        return AlgorithmNode(
            name=name,
            parameters=parameters,
            body=body,
            line=getattr(alg_token, 'line', None),
            column=getattr(alg_token, 'column', None)
        )

    def parameter_list(self, items: List[ParameterNode]) -> List[ParameterNode]:
        """Regla parameter_list: parameter ("," parameter)*"""
        return items

    def parameter(self, items: List[Any]) -> ParameterNode:
        """Regla parameter: array_parameter | object_parameter | IDENTIFIER"""
        item = items[0]
        # Si ya es un ParameterNode (de array_parameter u object_parameter), retornarlo
        if isinstance(item, ParameterNode):
            return item
        # Si es un IDENTIFIER (Token), crear un ParameterNode simple
        return ParameterNode(
            name=str(item),
            param_type="simple"
        )

    def array_parameter(self, items: List[Any]) -> ParameterNode:
        """Regla array_parameter: IDENTIFIER "[" (NUMBER | IDENTIFIER)? "]" ..."""
        name = str(items[0])
        dimensions = []

        for item in items[1:]:
            if isinstance(item, Token):
                if item.type == 'NUMBER':
                    dimensions.append(int(item))
                elif item.type == 'IDENTIFIER':
                    dimensions.append(str(item))  # Variable como dimensión
                # Ignorar corchetes y otros tokens
            elif isinstance(item, LiteralNode):
                # NUMBER ya procesado como LiteralNode
                dimensions.append(item.value)
            elif isinstance(item, str):
                # IDENTIFIER ya procesado
                dimensions.append(item)
            elif isinstance(item, int):
                dimensions.append(item)

        # Si no hay dimensiones, agregar None
        if not dimensions:
            dimensions.append(None)

        return ParameterNode(
            name=name,
            param_type="array",
            array_dimensions=dimensions
        )

    def object_parameter(self, items: List[Token]) -> ParameterNode:
        """Regla object_parameter: CLASS_NAME IDENTIFIER"""
        class_name = str(items[0])
        name = str(items[1])

        return ParameterNode(
            name=name,
            param_type="object",
            class_name=class_name
        )

    # Bloques y statements

    def block(self, items: List[Any]) -> BlockNode:
        """Regla block: BEGIN statement_list END"""
        # items = [BEGIN, statement_list, END]
        statements = items[1] if len(items) > 1 and isinstance(items[1], list) else []

        return BlockNode(statements=statements)

    def statement_list(self, items: List[Any]) -> List[Any]:
        """Regla statement_list: (statement)*"""
        # Filtrar None y items vacíos
        return [item for item in items if item is not None]

    def statement(self, items: List[Any]) -> Optional[Any]:
        """Regla statement: varios tipos de statements"""
        if items:
            return items[0]
        return None

    # Asignación

    def assignment(self, items: List[Any]) -> AssignmentNode:
        """Regla assignment: lvalue ASSIGN expression
        
        items[0] = lvalue (target)
        items[1] = ASSIGN token
        items[2] = expression (value)
        """
        target = items[0]
        assign_token = items[1]  # ASSIGN token con info de línea
        value = items[2]

        return AssignmentNode(
            target=target,
            value=value,
            line=getattr(assign_token, 'line', None),
            column=getattr(assign_token, 'column', None)
        )

    def lvalue(self, items: List[Any]) -> LValueNode:
        """Regla lvalue: variable, array access, o object field"""
        name = str(items[0])

        # Variable simple
        if len(items) == 1:
            return LValueNode(
                name=name,
                access_type="variable"
            )

        # Object field access: IDENTIFIER "." IDENTIFIER
        # El segundo elemento será un string (nombre del campo) porque IDENTIFIER() retorna str
        # Para array access, el segundo elemento será una expresión (nodo AST)
        if len(items) == 2 and isinstance(items[1], str):
            return LValueNode(
                name=name,
                access_type="object_field",
                field_name=items[1]
            )

        # Array access: los índices son expresiones (nodos AST), no strings
        indices = [item for item in items[1:] if not isinstance(item, str)]

        return LValueNode(
            name=name,
            access_type="array",
            indices=indices
        )

    # Ciclos

    def for_loop(self, items: List[Any]) -> ForLoopNode:
        """Regla for_loop: FOR IDENTIFIER ASSIGN expression TO expression DO block
        
        items[0] = FOR token
        items[1] = IDENTIFIER (variable)
        items[2] = ASSIGN token
        items[3] = expression (start)
        items[4] = TO token
        items[5] = expression (end)
        items[6] = DO token
        items[7] = block (body)
        """
        variable = str(items[1])
        start = items[3]
        end = items[5]
        body = items[7]

        logger.debug(f"ForLoop: {variable} from {start} to {end}")

        for_token = items[0]  # FOR token con info de línea
        return ForLoopNode(
            variable=variable,
            start=start,
            end=end,
            body=body,
            line=getattr(for_token, 'line', None),
            column=getattr(for_token, 'column', None)
        )

    def while_loop(self, items: List[Any]) -> WhileLoopNode:
        """Regla while_loop: WHILE "(" condition ")" DO block
        
        items[0] = WHILE token
        items[1] = condition
        items[2] = DO token
        items[3] = block (body)
        """
        while_token = items[0]  # WHILE token con info de línea
        condition = items[1]
        body = items[3]

        return WhileLoopNode(
            condition=condition,
            body=body,
            line=getattr(while_token, 'line', None),
            column=getattr(while_token, 'column', None)
        )

    def repeat_loop(self, items: List[Any]) -> RepeatLoopNode:
        """Regla repeat_loop: REPEAT statement_list UNTIL "(" condition ")"
        
        items[0] = REPEAT token
        items[1] = statement_list
        items[2] = UNTIL token
        items[3] = condition
        """
        repeat_token = items[0]  # REPEAT token con info de línea
        statements = items[1] if isinstance(items[1], list) else []
        condition = items[3]

        return RepeatLoopNode(
            body=statements,
            condition=condition,
            line=getattr(repeat_token, 'line', None),
            column=getattr(repeat_token, 'column', None)
        )

    # Condicional

    def if_statement(self, items: List[Any]) -> IfStatementNode:
        """Regla if_statement: IF "(" condition ")" THEN block (ELSE block)?
        
        items[0] = IF token
        items[1] = condition
        items[2] = THEN token
        items[3] = block (then_block)
        items[4] = ELSE token (opcional)
        items[5] = block (else_block) (opcional)
        """
        if_token = items[0]  # IF token con info de línea
        condition = items[1]
        then_block = items[3]
        else_block = items[5] if len(items) > 5 else None
        
        return IfStatementNode(
            condition=condition,
            then_block=then_block,
            else_block=else_block,
            line=getattr(if_token, 'line', None),
            column=getattr(if_token, 'column', None)
        )

    # Llamadas y Retorno

    def call_statement(self, items: List[Any]) -> CallStatementNode:
        """Regla call_statement: CALL IDENTIFIER "(" argument_list? ")"
        
        items[0] = CALL token
        items[1] = IDENTIFIER (function_name)
        items[2] = argument_list (opcional)
        """
        call_token = items[0]  # CALL token con info de línea
        function_name = str(items[1])
        arguments = items[2] if len(items) > 2 else []
        
        return CallStatementNode(
            function_name=function_name,
            arguments=arguments,
            line=getattr(call_token, 'line', None),
            column=getattr(call_token, 'column', None)
        )

    def argument_list(self, items: List[Any]) -> List[Any]:
        """Regla argument_list: argument ("," argument)*"""
        return items

    def argument(self, items: List[Any]) -> Any:
        """Regla argument: expression o array slice"""
        return items[0]

    def return_statement(self, items: List[Any]) -> ReturnStatementNode:
        """Regla return_statement: RETURN expression?"""
        # items[0] es el token RETURN, items[1] (si existe) es la expresión
        return_token = items[0]  # RETURN token con info de línea
        value = items[1] if len(items) > 1 else None
        return ReturnStatementNode(
            value=value,
            line=getattr(return_token, 'line', None),
            column=getattr(return_token, 'column', None)
        )

    # Expresiones - Lógicas

    def logical_or(self, items: List[Any]) -> Any:
        """Regla logical_or: logical_and (OR logical_and)*"""
        if len(items) == 1:
            return items[0]

        result = items[0]
        for i in range(1, len(items)):
            result = BinaryOpNode(
                operator="or",
                left=result,
                right=items[i]
            )
        return result

    def logical_and(self, items: List[Any]) -> Any:
        """Regla logical_and: logical_not (AND logical_not)*"""
        if len(items) == 1:
            return items[0]

        result = items[0]
        for i in range(1, len(items)):
            result = BinaryOpNode(
                operator="and",
                left=result,
                right=items[i]
            )
        return result

    def logical_not(self, items: List[Any]) -> Any:
        """Regla logical_not: NOT? comparison"""
        if len(items) == 1:
            return items[0]

        return UnaryOpNode(
            operator="not",
            operand=items[0]
        )

    # Expresiones - Comparación

    def comparison(self, items: List[Any]) -> Any:
        """Regla comparison: arithmetic (compare_op arithmetic)?"""
        if len(items) == 1:
            return items[0]

        left = items[0]
        operator = items[1]
        right = items[2]

        return BinaryOpNode(operator=operator, left=left, right=right)

    def compare_op(self, items: List[Token]) -> str:
        """Regla compare_op: operadores de comparación"""
        op = str(items[0])

        # Normalizar operadores
        if op in ['≤', '<=']:
            return '<='
        elif op in ['≥', '>=']:
            return '>='
        elif op in ['≠', '!=']:
            return '!='
        elif op == '=':
            return '=='  # En pseudocódigo = es comparación

        return op

    # Expresiones - Aritméticas

    def arithmetic(self, items: List[Any]) -> Any:
        """Regla arithmetic: arithmetic ("+" | "-") term"""
        # items = [left, operator, right]
        if len(items) == 1:
            return items[0]
        
        left = items[0]
        operator = str(items[1])
        right = items[2]
        return BinaryOpNode(operator=operator, left=left, right=right)

    def term(self, items: List[Any]) -> Any:
        """Regla term: term ("*" | "/" | MOD | DIV) factor"""
        # items = [left, operator, right]
        if len(items) == 1:
            return items[0]

        left = items[0]
        operator = str(items[1])
        right = items[2]
        return BinaryOpNode(operator=operator, left=left, right=right)

    def factor(self, items: List[Any]) -> Any:
        """Regla factor: ("+"|"-")? power"""
        if len(items) == 1:
            return items[0]

        # Operador unario
        operator = items[0]
        operand = items[1]

        if operator == '+':
            return operand  # +x es simplemente x

        return UnaryOpNode(operator='-', operand=operand)

    def power(self, items: List[Any]) -> Any:
        """Regla power: atom ("^" factor)?"""
        if len(items) == 1:
            return items[0]

        return BinaryOpNode(
            operator="^",
            left=items[0],
            right=items[1]
        )

    # Expresiones - Átomos

    def atom(self, items: List[Any]) -> Any:
        """Regla atom: varios tipos de valores atómicos"""
        return items[0]

    def function_call(self, items: List[Any]) -> FunctionCallNode:
        """Regla function_call: IDENTIFIER "(" (expression ("," expression)*)? ")" """
        function_name = str(items[0])
        arguments = items[1:] if len(items) > 1 else []

        return FunctionCallNode(
            function_name=function_name,
            arguments=arguments
        )

    # Literales y variables

    def NUMBER(self, token: Token) -> LiteralNode:
        """Terminal NUMBER"""
        value = float(token) if '.' in str(token) or 'e' in str(token).lower() else int(token)
        return LiteralNode(value=value, literal_type="number")

    def STRING(self, token: Token) -> LiteralNode:
        """Terminal STRING"""
        # Remover comillas
        value = str(token)[1:-1]
        return LiteralNode(value=value, literal_type="string")

    def BOOLEAN(self, token: Token) -> LiteralNode:
        """Terminal BOOLEAN"""
        value_str = str(token).upper()
        value = value_str in ['T', 'TRUE', 'VERDADERO']
        return LiteralNode(value=value, literal_type="boolean")

    def IDENTIFIER(self, token: Token) -> Union[VariableNode, str]:
        """
        Terminal IDENTIFIER

        En algunos contextos retorna str (nombres de funciones, variables en for),
        en otros retorna VariableNode (expresiones)
        """
        # El contexto determina si necesitamos un nodo o solo el string
        # Por defecto retornamos el string, el método padre decidirá
        return str(token)

    def CLASS_NAME(self, token: Token) -> str:
        """Terminal CLASS_NAME"""
        return str(token)

    # Accesos a arrays y objetos

    def expression(self, items: List[Any]) -> Any:
        """Regla expression: delega a logical_or"""
        return items[0]

    def condition(self, items: List[Any]) -> Any:
        """Regla condition: delega a logical_or"""
        return items[0]

    def range_notation(self, items: List[Any]) -> 'RangeNode':
        """
        Regla range_notation: expression ".." expression

        Procesa notaciones de rango como 1..n en parámetros de arrays.

        Args:
            items: [start_expression, end_expression]

        Returns:
            RangeNode: Nodo representando el rango
        """
        from app.core.parser.ast_nodes import RangeNode

        start = items[0]
        end = items[1]

        # Convertir tokens a valores si es necesario
        if isinstance(start, Token):
            start = int(start) if start.type == 'NUMBER' else str(start)
        if isinstance(end, Token):
            end = int(end) if end.type == 'NUMBER' else str(end)

        logger.debug(f"Range notation: {start}..{end}")

        return RangeNode(start=start, end=end)

    def array_bounds(self, items: List[Any]) -> Any:
        """
        Regla array_bounds: range_notation | expression

        Procesa los límites de un array, que pueden ser un rango o una expresión.

        Args:
            items: [RangeNode o expression]

        Returns:
            El contenido (RangeNode, expresión, o None)
        """
        if not items:
            return None

        return items[0]

    def array_parameter(self, items: List[Any]) -> ParameterNode:
        """
        Regla array_parameter: IDENTIFIER "[" array_bounds? "]" ...["]"]*

        SOBRESCRIBE el método existente para manejar range_notation.

        Args:
            items: [name, bounds?, ...]

        Returns:
            ParameterNode con información del array
        """
        from app.core.parser.ast_nodes import RangeNode

        name = str(items[0])
        dimensions = []

        # Procesar bounds y dimensiones adicionales
        for item in items[1:]:
            if item is None:
                # Bound vacío: []
                dimensions.append(None)
            elif isinstance(item, RangeNode):
                # Rango: [1..n]
                # Guardar como string para compatibilidad
                dimensions.append(f"{item.start}..{item.end}")
            elif isinstance(item, Token):
                # Token directo
                if item.type == 'NUMBER':
                    dimensions.append(int(item))
                elif item.type == 'IDENTIFIER':
                    dimensions.append(str(item))
            elif isinstance(item, LiteralNode):
                # Ya procesado como LiteralNode
                dimensions.append(item.value)
            elif isinstance(item, (str, int)):
                # Ya convertido
                dimensions.append(item)
            # Ignorar otros tipos (corchetes, etc.)

        # Si no hay dimensiones explícitas, agregar una dimensión sin tamaño
        if not dimensions:
            dimensions.append(None)

        logger.debug(f"Array parameter: {name} with dimensions: {dimensions}")

        return ParameterNode(
            name=name,
            param_type="array",
            array_dimensions=dimensions
        )

    # Manejo de Errores
    def __default__(self, data: str, children: List[Any], meta) -> Any:
        """
        Handler por defecto para reglas no implementadas.
        
        Lanza excepción con información detallada para debugging.
        """
        logger.error(f"Regla no implementada: {data}")
        logger.error(f"Children: {children}")
        logger.error(f"Meta: {meta}")
        
        raise ASTBuildException(
            message=f"Regla de gramática no implementada: {data}",
            node_type=data
        )

# Funciones Helper

def build_ast_from_tree(parse_tree: Tree) -> ProgramNode:
    """
    Helper function para construir AST desde parse tree.

    Args:
        parse_tree: Parse tree de Lark

    Returns:
        ProgramNode: AST construido

    Example:
        >>> tree = parser.parse(code)
        >>> ast = build_ast_from_tree(tree)
    """
    builder = ASTBuilder()
    return builder.transform(parse_tree)