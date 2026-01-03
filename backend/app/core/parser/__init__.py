"""
Parser Module

Módulo de parsing de pseudocódigo a Abstract Syntax Tree (AST).

Exports principales:
    - PseudocodeParser: Parser principal
    - parse_pseudocode: Helper function para parsing rápido
    - AST nodes: Todos los nodos del AST
    - ASTBuilder: Constructor de AST desde parse tree
    - SemanticAnalyzer: Analizador semántico del AST
    - ASTValidator: Validador de AST

Example:
    >>> from app.core.parser import parse_pseudocode
    >>> ast = parse_pseudocode(code)
    >>> print(ast.algorithm.name)
"""

from app.core.parser.ast_builder import ASTBuilder, build_ast_from_tree
from app.core.parser.ast_nodes import (
    AlgorithmNode,
    ArrayAccessNode,
    AssignmentNode,
    ASTNode,
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
    RepeatLoopNode,
    ReturnStatementNode,
    UnaryOpNode,
    VariableNode,
    WhileLoopNode,
)
from app.core.parser.pseudocode_parser import (
    PseudocodeParser,
    parse_pseudocode,
)
from app.core.parser.semantic_analyzer import SemanticAnalyzer, VariableInfo, FunctionInfo
from app.core.parser.validator import ASTValidator, ValidationResult

__all__ = [
    # Parser principal
    "PseudocodeParser",
    "parse_pseudocode",

    # AST Builder
    "ASTBuilder",
    "build_ast_from_tree",

    # Nodos AST
    "ASTNode",
    "ProgramNode",
    "ClassDefinitionNode",
    "AlgorithmNode",
    "ParameterNode",
    "BlockNode",
    "AssignmentNode",
    "LValueNode",
    "ForLoopNode",
    "WhileLoopNode",
    "RepeatLoopNode",
    "IfStatementNode",
    "CallStatementNode",
    "ReturnStatementNode",
    "BinaryOpNode",
    "UnaryOpNode",
    "LiteralNode",
    "VariableNode",
    "ArrayAccessNode",
    "ObjectAccessNode",
    "FunctionCallNode",
    
    # Análisis semántico
    "SemanticAnalyzer",
    "VariableInfo",
    "FunctionInfo",
    
    # Validación
    "ASTValidator",
    "ValidationResult",
]