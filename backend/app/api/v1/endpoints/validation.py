"""
API Endpoints - Validation

Endpoints para validar código pseudocódigo.
"""

from fastapi import APIRouter, HTTPException, Query, Body, status
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from app.schemas import (
    ValidationRequest,
    CompleteValidationResult,
    ValidationLevel,
)
from app.services import ValidationService
from app.utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()

# Schema para recibir código en el body de validación rápida
class QuickValidateInput(BaseModel):
    """Schema para recibir código en el body JSON para validación rápida"""
    code: str = Field(
        ...,
        min_length=1,
        description=(
            "Código del algoritmo a validar (multilínea). "
            "En JSON, los saltos de línea se representan con \\n. "
            "Ejemplo: \"algorithm test(n)\\nbegin\\n    x ← 1\\nend\""
        )
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": "algorithm bubbleSort(A[n])\nbegin\n    for i ← 1 to n-1 do\n    begin\n        for j ← 1 to n-i do\n        begin\n            if A[j] > A[j+1] then\n            begin\n                call swap(A[j], A[j+1])\n            end\n        end\n    end\nend"
            }
        }

# Instancia del servicio
validation_service = ValidationService()

@router.post(
    "/validate",
    response_model=CompleteValidationResult,
    status_code=status.HTTP_200_OK,
    summary="Validar Código",
    description="Valida código pseudocódigo en múltiples niveles"
)
async def validate_code(request: ValidationRequest):
    """
    Valida código pseudocódigo.
    
    Niveles:
    - SYNTAX: Solo sintaxis
    - SEMANTIC: Sintaxis + semántica
    - STRUCTURAL: + límites estructurales
    - COMPLETE: Todas las validaciones + best practices
    """
    try:
        # Validación explícita de código vacío
        if not request.code or request.code.strip() == "":
            logger.warning("Intento de validar código vacío")
            return CompleteValidationResult(
                success=False,
                message="Validación fallida",
                timestamp=datetime.now(timezone.utc),
                is_valid=False,
                errors=[{
                    "severity": "error",
                    "category": "syntax",
                    "message": "El código no puede estar vacío",
                    "description": "Se debe proporcionar al menos una línea de código válido",
                    "location": None,
                    "code_snippet": None,
                    "rule": "syntax",
                    "suggestion": "Proporcione código pseudocódigo válido",
                    "metadata": {},
                }],
                warnings=[],
                info=[],
                error_count=1,
                warning_count=0,
                info_count=0,
                hint_count=0,
                lines_analyzed=0,
                statements_analyzed=0,
                summary="Error: Código vacío",
                syntax={
                    "is_valid": False,
                    "errors": [{
                        "severity": "error",
                        "category": "syntax",
                        "message": "El código no puede estar vacío",
                        "location": None,
                        "rule": "syntax",
                    }],
                    "parse_tree_available": False,
                },
                semantic=None,
                structural=None,
                best_practices=None,
                overall_score=0.0,
            )
        
        # Proceder con validación normal
        result = await validation_service.validate(request)
        
        # Helper: map service ValidationIssue -> schema dict
        def _map_issue(issue):
            """Mapea ValidationIssue a diccionario para el schema"""
            # Obtener atributos del issue (puede ser objeto o dict)
            if hasattr(issue, "model_dump"):
                item = issue.model_dump()
            elif isinstance(issue, dict):
                item = issue
            else:
                item = issue.__dict__ if hasattr(issue, "__dict__") else {}

            # Normalizar keys
            line = item.get("line") or item.get("lineno")
            column = item.get("column") or item.get("col")

            location = None
            if line is not None or column is not None:
                location = {"line": line, "column": column}

            # Extraer valor del enum severity
            severity_value = item.get("severity")
            if hasattr(severity_value, 'value'):
                # Es un enum, obtener su valor
                severity_str = severity_value.value
            elif isinstance(severity_value, str):
                # Ya es string, limpiar si tiene formato "IssueSeverity.ERROR"
                severity_str = severity_value.split('.')[-1].lower() if '.' in severity_value else severity_value.lower()
            else:
                severity_str = "error"  # Default

            # Determine category from rule if available
            rule = item.get("rule")
            if rule in ("syntax", "semantic", "structural"):
                category = rule
            else:
                category = item.get("category") or "style"

            return {
                "severity": severity_str,  # "error", "warning", "info", "hint"
                "category": category,
                "message": item.get("message", ""),
                "description": item.get("description"),
                "location": location,
                "code_snippet": item.get("code_snippet"),
                "rule": rule,
                "suggestion": item.get("suggestion"),
                "metadata": item.get("metadata", {}),
            }

        # Map all issues
        mapped_errors = [_map_issue(i) for i in result.errors]
        mapped_warnings = [_map_issue(i) for i in result.warnings]
        mapped_infos = [_map_issue(i) for i in result.infos]

        # Build syntax/semantic/structural subsections
        syntax_errors = [e for e in mapped_errors if e.get("rule") == "syntax" or e.get("category") == "syntax"]
        syntax_obj = {
            "is_valid": result.metadata.get("syntax_valid", not bool(syntax_errors)),
            "errors": syntax_errors,
            "parse_tree_available": result.metadata.get("parse_tree_available", False),
        }

        semantic_errors = [e for e in mapped_errors if e.get("rule") == "semantic" or e.get("category") == "semantic"]
        semantic_obj = None
        if semantic_errors or result.metadata.get("semantic_valid") is not None:
            semantic_obj = {
                "is_valid": result.metadata.get("semantic_valid", not bool(semantic_errors)),
                "errors": semantic_errors,
                "undeclared_variables": result.metadata.get("undeclared_variables", []),
                "unused_variables": result.metadata.get("unused_variables", []),
                "undefined_functions": result.metadata.get("undefined_functions", []),
                "invalid_array_accesses": result.metadata.get("invalid_array_accesses", []),
                "type_mismatches": result.metadata.get("type_mismatches", []),
                "warnings": mapped_warnings,
            }

        structural_errors = [e for e in mapped_errors if e.get("rule") == "structural" or e.get("category") == "structural"]
        structural_obj = None
        if structural_errors or result.metadata.get("structural_valid") is not None:
            structural_obj = {
                "is_valid": result.metadata.get("structural_valid", not bool(structural_errors)),
                "errors": structural_errors,
                "exceeds_max_depth": result.metadata.get("max_depth_found", 0) > result.metadata.get("max_depth_allowed", 0),
                "max_depth_found": result.metadata.get("max_depth_found", 0),
                "max_depth_allowed": result.metadata.get("max_depth_allowed", 0),
                "exceeds_max_nodes": result.metadata.get("total_nodes", 0) > result.metadata.get("max_nodes_allowed", 0),
                "nodes_found": result.metadata.get("total_nodes", 0),
                "max_nodes_allowed": result.metadata.get("max_nodes_allowed", 0),
                "cyclomatic_complexity": result.metadata.get("cyclomatic_complexity", 0),
                "complexity_threshold": result.metadata.get("complexity_threshold", 10),
                "complexity_high": result.metadata.get("complexity_high", False),
                "warnings": mapped_warnings,
            }

        # Construir respuesta final
        return CompleteValidationResult(
            success=result.is_valid,
            message="Validación completada",
            timestamp=datetime.now(timezone.utc),
            is_valid=result.is_valid,
            errors=mapped_errors,
            warnings=mapped_warnings,
            info=mapped_infos,
            error_count=len(result.errors),
            warning_count=len(result.warnings),
            info_count=len(result.infos),
            hint_count=0,
            lines_analyzed=result.metadata.get("lines_count", 0),
            statements_analyzed=0,
            summary=f"Validación {'exitosa' if result.is_valid else 'fallida'}: {result.total_issues} issues",
            syntax=syntax_obj,
            semantic=semantic_obj,
            structural=structural_obj,
            best_practices=None,
            overall_score=1.0 if result.is_valid else 0.5,
        )
        
    except Exception as e:
        logger.error(f"Error en validación: {e}", exc_info=True)
        # Retornar 200 con error en lugar de 400
        return CompleteValidationResult(
            success=False,
            message="Error en validación",
            timestamp=datetime.now(timezone.utc),
            is_valid=False,
            errors=[{
                "severity": "error",
                "category": "internal",
                "message": f"Error interno: {str(e)}",
                "description": None,
                "location": None,
                "code_snippet": None,
                "rule": "internal",
                "suggestion": None,
                "metadata": {},
            }],
            warnings=[],
            info=[],
            error_count=1,
            warning_count=0,
            info_count=0,
            hint_count=0,
            lines_analyzed=0,
            statements_analyzed=0,
            summary=f"Error: {str(e)}",
            syntax=None,
            semantic=None,
            structural=None,
            best_practices=None,
            overall_score=0.0,
        )

@router.post(
    "/validate/quick",
    summary="Validación Rápida",
    description="Validación rápida solo sintaxis (true/false)"
)
async def quick_validate(body: QuickValidateInput = Body(..., description="Código a validar en JSON")):
    """Validación rápida solo sintaxis - ACTUALIZADO"""
    try:
        code = body.code
        # Manejar código vacío
        if not code or code.strip() == "":
            return {"is_valid": False, "error": "Código vacío"}
        
        is_valid = await validation_service.quick_validate(code)
        return {"is_valid": is_valid}
    except Exception as e:
        return {"is_valid": False, "error": str(e)}