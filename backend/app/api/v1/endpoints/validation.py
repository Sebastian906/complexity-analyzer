"""
API Endpoints - Validation

Endpoints para validar código pseudocódigo.
"""

from fastapi import APIRouter, HTTPException, Query, status

from app.schemas import (
    ValidationRequest,
    CompleteValidationResult,
    ValidationLevel,
)
from app.services import ValidationService
from app.utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()

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
        from datetime import datetime, timezone
        
        result = await validation_service.validate(request)
        
        # Helper: map service ValidationIssue -> schema dict
        def _map_issue(issue):
            # pydantic model
            if hasattr(issue, "model_dump"):
                item = issue.model_dump()
            # dict-like
            elif isinstance(issue, dict):
                item = issue
            # dataclass or plain object
            else:
                item = issue.__dict__ if hasattr(issue, "__dict__") else {}

            # Normalize keys
            line = item.get("line") or item.get("lineno")
            column = item.get("column") or item.get("col")

            location = None
            if line is not None or column is not None:
                location = {"line": line, "column": column}

            # Extraer valor del enum 
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

        return {
            "success": result.is_valid,
            "message": "Validación completada",
            "timestamp": datetime.now(timezone.utc),
            "is_valid": result.is_valid,
            "errors": mapped_errors,
            "warnings": mapped_warnings,
            "info": mapped_infos,
            "error_count": len(result.errors),
            "warning_count": len(result.warnings),
            "info_count": len(result.infos),
            "hint_count": 0,
            "lines_analyzed": result.metadata.get("lines_count", 0),
            "statements_analyzed": 0,
            "summary": f"Validación {'exitosa' if result.is_valid else 'fallida'}: {result.total_issues} issues",
            "syntax": syntax_obj,
            "semantic": semantic_obj,
            "structural": structural_obj,
            "best_practices": None,
            "overall_score": 1.0 if result.is_valid else 0.5,
        }
        
    except Exception as e:
        logger.error(f"Error en validación: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post(
    "/validate/quick",
    summary="Validación Rápida",
    description="Validación rápida solo sintaxis (true/false)"
)
async def quick_validate(code: str = Query(..., description="Código a validar")):
    """Validación rápida solo sintaxis"""
    try:
        is_valid = await validation_service.quick_validate(code)
        return {"is_valid": is_valid}
    except Exception as e:
        return {"is_valid": False, "error": str(e)}