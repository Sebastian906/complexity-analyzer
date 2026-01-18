"""
Validation Schemas - DTOs para Validación de Código

Schemas Pydantic para validación de algoritmos y código.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.schemas.common import BaseResponse, SourceLocation
from app.schemas.algorithm import LanguageType

# Enums
class ValidationLevel(str, Enum):
    """Niveles de validación"""
    SYNTAX = "syntax"              # Solo sintaxis
    SEMANTIC = "semantic"          # Sintaxis + semántica
    STRUCTURAL = "structural"      # + límites estructurales
    COMPLETE = "complete"          # + best practices

class IssueSeverity(str, Enum):
    """Severidad de problemas"""
    ERROR = "error"                # Error crítico
    WARNING = "warning"            # Advertencia
    INFO = "info"                  # Información
    HINT = "hint"                  # Sugerencia

class IssueCategory(str, Enum):
    """Categorías de problemas"""
    SYNTAX = "syntax"
    SEMANTIC = "semantic"
    STRUCTURAL = "structural"
    STYLE = "style"
    PERFORMANCE = "performance"
    COMPLEXITY = "complexity"
    BEST_PRACTICE = "best_practice"

# Validation Issue
class ValidationIssue(BaseModel):
    """Problema encontrado en validación"""
    severity: IssueSeverity = Field(..., description="Severidad del problema")
    category: IssueCategory = Field(..., description="Categoría del problema")
    
    message: str = Field(..., description="Mensaje del problema")
    description: Optional[str] = Field(None, description="Descripción detallada")
    
    location: Optional[SourceLocation] = Field(None, description="Ubicación en el código")
    code_snippet: Optional[str] = Field(None, description="Fragmento de código afectado")
    
    rule: Optional[str] = Field(None, description="Regla violada")
    suggestion: Optional[str] = Field(None, description="Sugerencia de corrección")
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata adicional"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "severity": "error",
                "category": "syntax",
                "message": "Expected 'end' but found end of file",
                "description": "El bloque 'begin' no tiene su correspondiente 'end'",
                "location": {"line": 5, "column": 1},
                "code_snippet": "begin\n  x ← 1\n",
                "rule": "MISSING_END",
                "suggestion": "Agregue 'end' al final del bloque"
            }
        }

# Validation Request
class ValidationRequest(BaseModel):
    """Request para validación de código"""
    code: str = Field(..., min_length=1, description="Código a validar")
    language: LanguageType = Field(
        LanguageType.PSEUDOCODE,
        description="Lenguaje del código"
    )
    level: ValidationLevel = Field(
        ValidationLevel.COMPLETE,
        description="Nivel de validación"
    )
    
    # Opciones
    max_line_length: int = Field(
        100,
        ge=50,
        le=200,
        description="Longitud máxima de línea"
    )
    max_nesting_depth: int = Field(
        10,
        ge=3,
        le=20,
        description="Profundidad máxima de anidación"
    )
    max_nodes: int = Field(
        10000,
        ge=100,
        le=100000,
        description="Número máximo de nodos en AST"
    )
    
    # Opciones de estilo
    check_naming_conventions: bool = Field(
        True,
        description="Verificar convenciones de nombres"
    )
    check_complexity: bool = Field(
        True,
        description="Verificar complejidad ciclomática"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": "algorithm test(n)\nbegin\n  for i ← 1 to n do\n    x ← x + 1\nend",
                "language": "pseudocode",
                "level": "complete",
                "max_line_length": 100,
                "max_nesting_depth": 10,
                "check_naming_conventions": True
            }
        }

# Validation Result
class ValidationResult(BaseResponse):
    """Resultado de validación"""
    is_valid: bool = Field(..., description="Si el código es válido")
    
    # Issues
    errors: List[ValidationIssue] = Field(
        default_factory=list,
        description="Errores encontrados"
    )
    warnings: List[ValidationIssue] = Field(
        default_factory=list,
        description="Advertencias encontradas"
    )
    info: List[ValidationIssue] = Field(
        default_factory=list,
        description="Información adicional"
    )
    hints: List[ValidationIssue] = Field(
        default_factory=list,
        description="Sugerencias de mejora"
    )
    
    # Contadores
    error_count: int = Field(0, ge=0, description="Total de errores")
    warning_count: int = Field(0, ge=0, description="Total de advertencias")
    info_count: int = Field(0, ge=0, description="Total de info")
    hint_count: int = Field(0, ge=0, description="Total de hints")
    
    # Estadísticas
    lines_analyzed: int = Field(0, ge=0, description="Líneas analizadas")
    statements_analyzed: int = Field(0, ge=0, description="Statements analizados")
    
    # Resumen
    summary: str = Field(..., description="Resumen de la validación")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Validación completada",
                "is_valid": False,
                "errors": [
                    {
                        "severity": "error",
                        "category": "syntax",
                        "message": "Missing 'end'",
                        "location": {"line": 5, "column": 1}
                    }
                ],
                "warnings": [
                    {
                        "severity": "warning",
                        "category": "style",
                        "message": "Variable name 'x' is too short",
                        "suggestion": "Use descriptive names"
                    }
                ],
                "error_count": 1,
                "warning_count": 1,
                "info_count": 0,
                "hint_count": 0,
                "lines_analyzed": 5,
                "statements_analyzed": 3,
                "summary": "Se encontraron 1 errores y 1 advertencias"
            }
        }

# Syntax Validation
class SyntaxValidationResult(BaseModel):
    """Resultado de validación sintáctica"""
    is_valid: bool = Field(..., description="Si la sintaxis es válida")
    errors: List[ValidationIssue] = Field(
        default_factory=list,
        description="Errores de sintaxis"
    )
    parse_tree_available: bool = Field(
        False,
        description="Si se pudo generar el parse tree"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "is_valid": True,
                "errors": [],
                "parse_tree_available": True
            }
        }

# Semantic Validation
class SemanticValidationResult(BaseModel):
    """Resultado de validación semántica"""
    is_valid: bool = Field(..., description="Si la semántica es válida")
    
    # Variables
    undeclared_variables: List[str] = Field(
        default_factory=list,
        description="Variables usadas pero no declaradas"
    )
    unused_variables: List[str] = Field(
        default_factory=list,
        description="Variables declaradas pero no usadas"
    )
    
    # Funciones
    undefined_functions: List[str] = Field(
        default_factory=list,
        description="Funciones llamadas pero no definidas"
    )
    
    # Arrays
    invalid_array_accesses: List[str] = Field(
        default_factory=list,
        description="Accesos inválidos a arrays"
    )
    
    # Tipos
    type_mismatches: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Inconsistencias de tipos"
    )
    
    errors: List[ValidationIssue] = Field(
        default_factory=list,
        description="Errores semánticos"
    )
    warnings: List[ValidationIssue] = Field(
        default_factory=list,
        description="Advertencias semánticas"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "is_valid": False,
                "undeclared_variables": ["temp"],
                "unused_variables": [],
                "undefined_functions": ["process"],
                "invalid_array_accesses": [],
                "type_mismatches": [],
                "errors": [
                    {
                        "severity": "error",
                        "category": "semantic",
                        "message": "Variable 'temp' used but not declared"
                    }
                ]
            }
        }

# Structural Validation
class StructuralValidationResult(BaseModel):
    """Resultado de validación estructural"""
    is_valid: bool = Field(..., description="Si la estructura es válida")
    
    # Límites
    exceeds_max_depth: bool = Field(False, description="Excede profundidad máxima")
    max_depth_found: int = Field(0, ge=0, description="Profundidad máxima encontrada")
    max_depth_allowed: int = Field(0, ge=0, description="Profundidad máxima permitida")
    
    exceeds_max_nodes: bool = Field(False, description="Excede número máximo de nodos")
    nodes_found: int = Field(0, ge=0, description="Nodos encontrados")
    max_nodes_allowed: int = Field(0, ge=0, description="Nodos máximos permitidos")
    
    # Complejidad ciclomática
    cyclomatic_complexity: int = Field(0, ge=0, description="Complejidad ciclomática")
    complexity_threshold: int = Field(10, description="Umbral de complejidad")
    complexity_high: bool = Field(False, description="Si la complejidad es alta")
    
    errors: List[ValidationIssue] = Field(default_factory=list)
    warnings: List[ValidationIssue] = Field(default_factory=list)
    
    class Config:
        json_schema_extra = {
            "example": {
                "is_valid": True,
                "exceeds_max_depth": False,
                "max_depth_found": 3,
                "max_depth_allowed": 10,
                "exceeds_max_nodes": False,
                "nodes_found": 45,
                "max_nodes_allowed": 10000,
                "cyclomatic_complexity": 5,
                "complexity_threshold": 10,
                "complexity_high": False
            }
        }

# Best Practices Validation
class BestPracticeCheck(BaseModel):
    """Check de best practice"""
    rule: str = Field(..., description="Nombre de la regla")
    description: str = Field(..., description="Descripción de la regla")
    passed: bool = Field(..., description="Si pasó el check")
    severity: IssueSeverity = Field(..., description="Severidad si no pasa")
    suggestion: Optional[str] = Field(None, description="Sugerencia de mejora")
    
    class Config:
        json_schema_extra = {
            "example": {
                "rule": "descriptive_names",
                "description": "Los nombres de variables deben ser descriptivos",
                "passed": False,
                "severity": "warning",
                "suggestion": "Evitar nombres de una letra como 'x', usar 'count', 'total', etc."
            }
        }

class BestPracticesValidationResult(BaseModel):
    """Resultado de validación de best practices"""
    checks: List[BestPracticeCheck] = Field(..., description="Checks realizados")
    passed_count: int = Field(0, ge=0, description="Checks pasados")
    failed_count: int = Field(0, ge=0, description="Checks fallidos")
    score: float = Field(0.0, ge=0.0, le=1.0, description="Score de calidad (0-1)")
    
    recommendations: List[str] = Field(
        default_factory=list,
        description="Recomendaciones generales"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "checks": [
                    {
                        "rule": "descriptive_names",
                        "passed": False,
                        "severity": "warning"
                    }
                ],
                "passed_count": 7,
                "failed_count": 3,
                "score": 0.7,
                "recommendations": [
                    "Usar nombres de variables más descriptivos",
                    "Agregar comentarios a la lógica compleja"
                ]
            }
        }

# Complete Validation Result
class CompleteValidationResult(ValidationResult):
    """Resultado de validación completa (todos los niveles)"""
    syntax: SyntaxValidationResult = Field(..., description="Validación sintáctica")
    semantic: Optional[SemanticValidationResult] = Field(
        None,
        description="Validación semántica"
    )
    structural: Optional[StructuralValidationResult] = Field(
        None,
        description="Validación estructural"
    )
    best_practices: Optional[BestPracticesValidationResult] = Field(
        None,
        description="Validación de best practices"
    )
    
    overall_score: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Score general de calidad"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "is_valid": True,
                "error_count": 0,
                "warning_count": 2,
                "syntax": {"is_valid": True},
                "semantic": {"is_valid": True},
                "structural": {"is_valid": True},
                "best_practices": {"score": 0.8},
                "overall_score": 0.85,
                "summary": "Código válido con 2 advertencias menores"
            }
        }