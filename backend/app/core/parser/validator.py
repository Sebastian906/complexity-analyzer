"""
Validator - Validador de AST

Valida restricciones estructurales del AST:
- Profundidad máxima de anidación
- Número máximo de nodos
- Estructuras válidas
- Límites del sistema

"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

from app.core.parser.ast_nodes import (
    ASTNode, ProgramNode, AlgorithmNode, BlockNode,
    ForLoopNode, WhileLoopNode, RepeatLoopNode, IfStatementNode
)
from app.core.exceptions import ValidationException
from app.core.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

@dataclass
class ValidationResult:
    """Resultado de la validación"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    statistics: Dict[str, Any] = field(default_factory=dict)

    def __bool__(self):
        return self.is_valid

class ASTValidator:
    """
    Validador de AST.

    Verifica restricciones estructurales y límites del sistema.
    """

    def __init__(self, max_depth: int = 20, max_nodes: int = 10000):
        """
        Args:
            max_depth: Profundidad máxima de anidación
            max_nodes: Número máximo de nodos en el AST
        """
        self.max_depth = max_depth
        self.max_nodes = max_nodes

        self.logger = setup_logger(__name__)

        # Contadores
        self.current_depth = 0
        self.max_depth_found = 0
        self.total_nodes = 0

        # Errores y warnings
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate(self, ast: ProgramNode) -> ValidationResult:
        """
        Valida el AST completo.

        Args:
            ast: AST a validar

        Returns:
            ValidationResult: Resultado de la validación
        """
        self.logger.info("Iniciando validación de AST")

        # Reset contadores
        self.current_depth = 0
        self.max_depth_found = 0
        self.total_nodes = 0
        self.errors.clear()
        self.warnings.clear()

        try:
            # Validar estructura básica
            if not ast.algorithm:
                self.errors.append("El programa debe contener al menos un algoritmo")
                return self._create_result()

            # Validar el algoritmo
            self._validate_algorithm(ast.algorithm)

            # Verificar número total de nodos
            if self.total_nodes > self.max_nodes:
                self.errors.append(
                    f"El AST excede el número máximo de nodos permitido: "
                    f"{self.total_nodes} > {self.max_nodes}"
                )

            # Verificar profundidad
            if self.max_depth_found > self.max_depth:
                self.errors.append(
                    f"El AST excede la profundidad máxima de anidación: "
                    f"{self.max_depth_found} > {self.max_depth}"
                )

            # Log resultados
            self.logger.info(
                f"Validación completada: "
                f"nodos={self.total_nodes}, "
                f"profundidad={self.max_depth_found}, "
                f"errores={len(self.errors)}, "
                f"warnings={len(self.warnings)}"
            )

            return self._create_result()

        except Exception as e:
            self.logger.error(f"Error durante validación: {e}")
            self.errors.append(f"Error inesperado durante validación: {str(e)}")
            return self._create_result()

    def _validate_algorithm(self, algorithm: AlgorithmNode):
        """Valida un algoritmo"""
        self.total_nodes += 1

        # Validar nombre
        if not algorithm.name or not algorithm.name.strip():
            self.errors.append("El algoritmo debe tener un nombre")

        # Validar que tenga cuerpo
        if not algorithm.body:
            self.errors.append(f"El algoritmo '{algorithm.name}' no tiene cuerpo")
            return

        # Validar el cuerpo
        self._validate_block(algorithm.body)

    def _validate_block(self, block: BlockNode):
        """Valida un bloque de código"""
        self.total_nodes += 1
        self.current_depth += 1

        # Actualizar profundidad máxima
        if self.current_depth > self.max_depth_found:
            self.max_depth_found = self.current_depth

        # Validar cada statement
        for statement in block.statements:
            self._validate_statement(statement)

        self.current_depth -= 1

    def _validate_statement(self, statement: ASTNode):
        """Valida un statement"""
        self.total_nodes += 1

        if isinstance(statement, ForLoopNode):
            self._validate_for_loop(statement)

        elif isinstance(statement, WhileLoopNode):
            self._validate_while_loop(statement)

        elif isinstance(statement, RepeatLoopNode):
            self._validate_repeat_loop(statement)

        elif isinstance(statement, IfStatementNode):
            self._validate_if_statement(statement)

        elif isinstance(statement, BlockNode):
            self._validate_block(statement)

    def _validate_for_loop(self, for_loop: ForLoopNode):
        """Valida un FOR loop"""
        # Validar que tenga variable
        if not for_loop.variable:
            self.errors.append("FOR loop debe tener una variable de iteración")

        # Validar que tenga start y end
        if not for_loop.start or not for_loop.end:
            self.errors.append("FOR loop debe tener valores de inicio y fin")

        # Validar el cuerpo
        if for_loop.body:
            if len(for_loop.body.statements) == 0:
                self.warnings.append("FOR loop tiene cuerpo vacío")
            self._validate_block(for_loop.body)
        else:
            self.warnings.append("FOR loop tiene cuerpo vacío")

    def _validate_while_loop(self, while_loop: WhileLoopNode):
        """Valida un WHILE loop"""
        # Validar que tenga condición
        if not while_loop.condition:
            self.errors.append("WHILE loop debe tener una condición")

        # Validar el cuerpo
        if while_loop.body:
            if len(while_loop.body.statements) == 0:
                self.warnings.append("WHILE loop tiene cuerpo vacío")
            self._validate_block(while_loop.body)
        else:
            self.warnings.append("WHILE loop tiene cuerpo vacío")

    def _validate_repeat_loop(self, repeat_loop: RepeatLoopNode):
        """Valida un REPEAT loop"""
        # Validar que tenga condición
        if not repeat_loop.condition:
            self.errors.append("REPEAT loop debe tener una condición")

        # Validar el cuerpo
        if not repeat_loop.body:
            self.warnings.append("REPEAT loop tiene cuerpo vacío")

    def _validate_if_statement(self, if_stmt: IfStatementNode):
        """Valida un IF statement"""
        # Validar que tenga condición
        if not if_stmt.condition:
            self.errors.append("IF statement debe tener una condición")

        # Validar then block
        if if_stmt.then_block:
            if len(if_stmt.then_block.statements) == 0:
                self.warnings.append("IF statement tiene bloque THEN vacío")
            self._validate_block(if_stmt.then_block)
        else:
            self.warnings.append("IF statement tiene bloque THEN vacío")

        # Validar else block si existe
        if if_stmt.else_block:
            if len(if_stmt.else_block.statements) == 0:
                self.warnings.append("IF statement tiene bloque ELSE vacío")
            self._validate_block(if_stmt.else_block)

    def _create_result(self) -> ValidationResult:
        """Crea el resultado de la validación"""
        return ValidationResult(
            is_valid=(len(self.errors) == 0),
            errors=self.errors.copy(),
            warnings=self.warnings.copy(),
            statistics={
                "total_nodes": self.total_nodes,
                "max_depth": self.max_depth_found,
                "errors_count": len(self.errors),
                "warnings_count": len(self.warnings)
            }
        )

    def get_stats(self) -> dict:
        """Retorna estadísticas de la validación"""
        return {
            "total_nodes": self.total_nodes,
            "max_depth": self.max_depth_found,
            "errors": len(self.errors),
            "warnings": len(self.warnings)
        }