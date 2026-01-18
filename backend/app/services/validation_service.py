"""
Validation Service - Servicio de Validación

Valida código pseudocódigo y resultados de análisis usando múltiples estrategias.
Preparado para integrar LLMs en el futuro (Módulo 6).
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any

from app.core.parser import PseudocodeParser, ASTValidator, SemanticAnalyzer
from app.core.exceptions import ValidationException
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# Enums
class ValidationLevel(str, Enum):
    """Niveles de validación"""
    SYNTAX = "syntax"           # Solo sintaxis
    SEMANTIC = "semantic"       # Sintaxis + semántica
    STRUCTURAL = "structural"   # + límites estructurales
    COMPLETE = "complete"       # Todas las validaciones

class IssueSeverity(str, Enum):
    """Severidad de un issue"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

# DTOs
@dataclass
class ValidationIssue:
    """Issue encontrado en validación"""
    severity: IssueSeverity
    message: str
    line: Optional[int] = None
    column: Optional[int] = None
    rule: Optional[str] = None
    suggestion: Optional[str] = None

@dataclass
class ValidationRequest:
    """Request de validación"""
    code: str
    level: ValidationLevel = ValidationLevel.COMPLETE
    check_best_practices: bool = False

    # Límites personalizados (opcional)
    max_lines: Optional[int] = None
    max_depth: Optional[int] = None
    max_complexity: Optional[str] = None

@dataclass
class ValidationResult:
    """Resultado de validación"""
    is_valid: bool
    level: ValidationLevel

    # Issues encontrados
    errors: List[ValidationIssue] = field(default_factory=list)
    warnings: List[ValidationIssue] = field(default_factory=list)
    infos: List[ValidationIssue] = field(default_factory=list)

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def total_issues(self) -> int:
        """Total de issues"""
        return len(self.errors) + len(self.warnings) + len(self.infos)

    @property
    def has_errors(self) -> bool:
        """Tiene errores"""
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        """Tiene warnings"""
        return len(self.warnings) > 0

# Service
class ValidationService:
    """
    Servicio de validación de código.

    Proporciona validación en múltiples niveles usando
    estrategias complementarias.

    Example:
        >>> service = ValidationService()
        >>> request = ValidationRequest(
        ...     code="algorithm test(n)\\nbegin\\n  x <- 1\\nend",
        ...     level=ValidationLevel.COMPLETE
        ... )
        >>> result = await service.validate(request)
        >>> print(result.is_valid)
    """

    def __init__(
        self,
        parser: Optional[PseudocodeParser] = None,
        validator: Optional[ASTValidator] = None,
        semantic_analyzer: Optional[SemanticAnalyzer] = None,
    ):
        """
        Inicializa el servicio.

        Args:
            parser: Parser personalizado
            validator: Validador AST personalizado
            semantic_analyzer: Analizador semántico personalizado
        """
        self.parser = parser or PseudocodeParser()
        self.validator = validator or ASTValidator()
        self.semantic_analyzer = semantic_analyzer or SemanticAnalyzer()

        logger.info("ValidationService inicializado")

    async def validate(
        self,
        request: ValidationRequest
    ) -> ValidationResult:
        """
        Valida código según nivel especificado.

        Args:
            request: Configuración de validación

        Returns:
            ValidationResult: Resultado de validación
        """
        logger.info(f"Validando código - Nivel: {request.level}")

        result = ValidationResult(
            is_valid=True,
            level=request.level,
            metadata={
                "code_length": len(request.code),
                "lines_count": len(request.code.splitlines()),
            }
        )

        # Nivel 1: Sintaxis
        await self._validate_syntax(request, result)

        if not result.is_valid and request.level == ValidationLevel.SYNTAX:
            return result

        # Nivel 2: Semántica
        if request.level in [ValidationLevel.SEMANTIC, ValidationLevel.STRUCTURAL, ValidationLevel.COMPLETE]:
            await self._validate_semantic(request, result)

        if not result.is_valid and request.level == ValidationLevel.SEMANTIC:
            return result

        # Nivel 3: Estructural
        if request.level in [ValidationLevel.STRUCTURAL, ValidationLevel.COMPLETE]:
            await self._validate_structural(request, result)

        # Nivel 4: Best Practices (opcional)
        # LÍNEA PROBLEMÁTICA (línea ~164):
        # if request.check_best_practices:
        
        # REEMPLAZAR CON:
        if request.level == ValidationLevel.COMPLETE:
            await self._validate_best_practices(request, result)

        logger.info(
            f"Validación completada - Valid: {result.is_valid}, "
            f"Issues: {result.total_issues}"
        )

        return result

    async def _validate_syntax(
        self,
        request: ValidationRequest,
        result: ValidationResult
    ) -> None:
        """Valida sintaxis del código"""
        try:
            self.parser.parse(request.code, validate=False)
            result.metadata["syntax_valid"] = True

        except Exception as e:
            result.is_valid = False
            result.errors.append(
                ValidationIssue(
                    severity=IssueSeverity.ERROR,
                    message=f"Error de sintaxis: {e}",
                    rule="syntax",
                )
            )
            result.metadata["syntax_valid"] = False

    async def _validate_semantic(
        self,
        request: ValidationRequest,
        result: ValidationResult
    ) -> None:
        """Valida semántica del código"""
        try:
            ast = self.parser.parse(request.code, validate=True)

            # Análisis semántico
            is_valid = self.semantic_analyzer.analyze(ast)

            # Agregar errores semánticos
            for error in self.semantic_analyzer.errors:
                result.errors.append(
                    ValidationIssue(
                        severity=IssueSeverity.ERROR,
                        message=error,
                        rule="semantic",
                    )
                )
                result.is_valid = False

            # Agregar warnings semánticos
            for warning in self.semantic_analyzer.warnings:
                result.warnings.append(
                    ValidationIssue(
                        severity=IssueSeverity.WARNING,
                        message=warning,
                        rule="semantic",
                    )
                )

            result.metadata["semantic_valid"] = is_valid

        except Exception as e:
            logger.error(f"Error en validación semántica: {e}")
            result.warnings.append(
                ValidationIssue(
                    severity=IssueSeverity.WARNING,
                    message=f"Validación semántica incompleta: {e}",
                    rule="semantic",
                )
            )

    async def _validate_structural(
        self,
        request: ValidationRequest,
        result: ValidationResult
    ) -> None:
        """Valida restricciones estructurales"""
        try:
            ast = self.parser.parse(request.code, validate=True)

            # Validar con ASTValidator
            validation = self.validator.validate(ast)

            if not validation.is_valid:
                for error in validation.errors:
                    result.errors.append(
                        ValidationIssue(
                            severity=IssueSeverity.ERROR,
                            message=error,
                            rule="structural",
                        )
                    )
                result.is_valid = False

            result.metadata.update({
                "structural_valid": validation.is_valid,
                "max_depth_found": validation.statistics.get("max_depth", 0),
                "total_nodes": validation.statistics.get("total_nodes", 0),
            })

        except Exception as e:
            logger.error(f"Error en validación estructural: {e}")
            result.warnings.append(
                ValidationIssue(
                    severity=IssueSeverity.WARNING,
                    message=f"Validación estructural incompleta: {e}",
                    rule="structural",
                )
            )

    async def _validate_best_practices(
        self,
        request: ValidationRequest,
        result: ValidationResult
    ) -> None:
        """Valida best practices (heurísticas)"""
        lines = request.code.splitlines()

        # Heurística: líneas muy largas
        for i, line in enumerate(lines, 1):
            if len(line) > 100:
                result.warnings.append(
                    ValidationIssue(
                        severity=IssueSeverity.WARNING,
                        message="Línea muy larga (>100 caracteres)",
                        line=i,
                        rule="line_length",
                        suggestion="Dividir en múltiples líneas"
                    )
                )

        # Heurística: nombres muy cortos
        import re
        variables = re.findall(r'\b([a-z])\s*←', request.code)
        if len(set(variables)) > 3:
            result.infos.append(
                ValidationIssue(
                    severity=IssueSeverity.INFO,
                    message="Múltiples variables de una letra detectadas",
                    rule="naming",
                    suggestion="Considerar nombres más descriptivos"
                )
            )

    async def quick_validate(self, code: str) -> bool:
        """
        Validación rápida solo sintaxis.

        Args:
            code: Código a validar

        Returns:
            bool: True si es sintácticamente válido
        """
        try:
            self.parser.parse(code, validate=False)
            return True
        except:
            return False