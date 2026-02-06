"""
API Endpoints - Análisis de Complejidad

Endpoints REST para analizar algoritmos y obtener su complejidad.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, status, Query, Body
from pydantic import BaseModel, Field
from app.schemas import (
    # Analysis Request Schemas
    ComplexityAnalysisRequest,
    ComplexityAnalysisOptions,
    RecurrenceMethod,
    
    # Analysis Result Schemas
    CompleteAnalysisResult,
    LineByLineAnalysis,
    LineExecution,
    
    # Complexity Schemas
    ComplexityAnalysis,
    SpaceComplexityAnalysis,
    RecurrenceEquation,
    RecurrenceSolution,
    TightBoundResult,
    ComplexityClass,
    SolutionMethod,
    
    # Algorithm Schemas
    AlgorithmInfo,
    
    # Common
    BaseResponse,
)

from app.core.parser import PseudocodeParser
from app.core.analyzer.analyzer_engine import AnalyzerEngine
from app.core.config import settings
from app.utils.logger import setup_logger

from app.profiling import get_performance_monitor

logger = setup_logger(__name__)

router = APIRouter()

# Schema para recibir código en el body
class CodeInput(BaseModel):
    """Schema para recibir código en el body JSON"""
    code: str = Field(..., description="Código del algoritmo a analizar (puede ser multilínea)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": "algorithm example(n)\nbegin\n    for i ← 1 to n do\n    begin\n        print(i)\n    end\nend"
            }
        }

# Mapeo de métodos de inglés a español para solve-recurrence
METHOD_MAPPING = {
    "iteration": "iteracion",
    "recursion_tree": "arbol_recursion",
    "master_theorem": "teorema_maestro",
    "substitution": "sustitucion_inteligente",
    "characteristic": "ecuacion_caracteristica",
    # También aceptar los valores en español directamente
    "iteracion": "iteracion",
    "arbol_recursion": "arbol_recursion",
    "teorema_maestro": "teorema_maestro",
    "sustitucion_inteligente": "sustitucion_inteligente",
    "ecuacion_caracteristica": "ecuacion_caracteristica",
}

# Obtener monitor global
_profiling_enabled = settings.APP_ENV in ["development", "staging"]
if _profiling_enabled:
    _monitor = get_performance_monitor()
else:
    _monitor = None

@router.post(
    "/analyze-complete",
    response_model=CompleteAnalysisResult,
    status_code=status.HTTP_200_OK,
    summary="Analizar Complejidad Completa",
    description="Analiza completamente un algoritmo incluyendo ecuaciones de recurrencia"
)
async def analyze_complexity_complete(request: ComplexityAnalysisRequest):
    """
    Analiza la complejidad completa de un algoritmo.
    
    Incluye:
    - Complejidad temporal (O, Ω, Θ)
    - Complejidad espacial (S(n))
    - Ecuaciones de recurrencia T(n) y S(n)
    - Cotas ajustadas (Theta)
    - Análisis línea por línea
    """
    # PROFILING: Endpoint completo
    if _profiling_enabled and _monitor:
        with _monitor.monitor("endpoint_analyze_complete", module="api"):
            return await _analyze_complexity_complete_impl(request)
    else:
        return await _analyze_complexity_complete_impl(request)

async def _analyze_complexity_complete_impl(request: ComplexityAnalysisRequest):
    """Implementación interna del endpoint."""
    try:
        logger.info("Recibida solicitud de análisis completo")

        # 1. Parsear el código
        # PROFILING: Parsing
        if _profiling_enabled and _monitor:
            with _monitor.monitor("parse_algorithm", module="parser"):
                parser = PseudocodeParser()
                ast = parser.parse(request.code)
        else:
            parser = PseudocodeParser()
            ast = parser.parse(request.code)
        
        logger.info(f"Código parseado: {ast.algorithm.name}")

        # 2. Analizar con el motor principal
        # PROFILING: Análisis 
        if _profiling_enabled and _monitor:
            with _monitor.monitor("analyze_algorithm", module="analyzer"):
                engine = AnalyzerEngine()
                result = engine.analyze(
                    ast,
                    analyze_line_by_line=request.options.analyze_line_by_line if request.options else True,
                    analyze_space=request.options.analyze_spatial if request.options else True,
                    analyze_recurrence=request.options.analyze_recurrence if request.options else True,
                    analyze_tight_bounds=request.options.calculate_tight_bounds if request.options else True
                )
        else:
            engine = AnalyzerEngine()
            result = engine.analyze(
                ast,
                analyze_line_by_line=request.options.analyze_line_by_line if request.options else True,
                analyze_space=request.options.analyze_spatial if request.options else True,
                analyze_recurrence=request.options.analyze_recurrence if request.options else True,
                analyze_tight_bounds=request.options.calculate_tight_bounds if request.options else True
            )

        # 3. Construir AlgorithmInfo
        algorithm_info = AlgorithmInfo(
            name=ast.algorithm.name,
            parameters=[],  # Extraer si es necesario
            has_recursion=result.is_recursive,
            has_loops=True,  # Detectar del AST
            max_nesting_depth=result.max_nesting_depth,
            total_lines=len(request.code.splitlines()),
            total_statements=0,  # Contar del AST
        )

        # 4. Construir ComplexityAnalysis
        complexity = ComplexityAnalysis(
            big_o=result.big_o,
            omega=result.omega,
            theta=result.theta,
            big_o_class=_get_complexity_class(result.big_o),
            omega_class=_get_complexity_class(result.omega),
            theta_class=_get_complexity_class(result.theta) if result.theta else None,
            explanation=f"Complejidad temporal del algoritmo {ast.algorithm.name}",
            reasoning=[
                "Análisis basado en estructura del código",
                f"Complejidad dominante: {result.big_o}"
            ],
            has_tight_bound=result.theta is not None,
        )

        # 5. Construir SpaceComplexityAnalysis
        space_complexity = None
        if result.space_analysis:
            space_complexity = SpaceComplexityAnalysis(
                total=result.space_analysis.space_complexity,
                input_space=result.space_analysis.input_space,
                auxiliary_space=result.space_analysis.auxiliary_space,
                recursion_space=result.space_analysis.recursion_space,
                explanation=f"Espacio total: {result.space_analysis.space_complexity}",
                breakdown={
                    "input": result.space_analysis.input_space,
                    "auxiliary": result.space_analysis.auxiliary_space,
                    "recursion": result.space_analysis.recursion_space,
                }
            )

        # 6. Construir RecurrenceEquation temporal
        recurrence_temporal = None
        if result.temporal_recurrence and result.temporal_recurrence.recurrence_equation:
            eq = result.temporal_recurrence.recurrence_equation
            sol = result.temporal_recurrence.solution
            
            recurrence_temporal = RecurrenceEquation(
                equation=eq.equation,
                base_case=eq.base_case,
                recursion_pattern=eq.recursion_pattern,
                a=None,  # Extraer si está disponible
                b=None,
                f_n=None,
                explanation=f"Ecuación de recurrencia para {ast.algorithm.name}",
            )

        # 7. Construir TightBoundResult
        tight_bounds = None
        if result.tight_bounds:
            tight_bounds = TightBoundResult(
                has_tight_bound=result.tight_bounds.has_tight_bound,
                theta=result.tight_bounds.theta,
                little_o=result.tight_bounds.little_o,
                little_omega=result.tight_bounds.little_omega,
                explanation=result.tight_bounds.explanation,
                conditions=[],
            )

        # 8. Construir LineByLineAnalysis
        line_by_line = None
        if result.line_by_line:
            # Filtrar líneas con line_number válido (>= 1)
            valid_lines = [line for line in result.line_by_line.lines if line.line_number >= 1]
            line_by_line = LineByLineAnalysis(
                lines=[
                    LineExecution(
                        line_number=line.line_number,
                        code=getattr(line, 'code', f"Línea {line.line_number}"),
                        execution_count=line.execution_count,
                        statement_type=line.statement_type,
                        complexity_contribution=getattr(line, 'complexity_contribution', line.execution_count),
                        explanation=line.explanation,
                        location=None,
                    )
                    for line in valid_lines
                ],
                dominant_complexity=result.big_o,
                total_lines=len(valid_lines),
                summary=f"Análisis línea por línea de {ast.algorithm.name}",
            )

        # 9. Construir metadata
        from app.schemas.common import AnalysisMetadata, TimingMetadata
        from datetime import datetime, timezone
        
        metadata = AnalysisMetadata(
            timing=TimingMetadata(
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
                duration_ms=result.analysis_time * 1000 if hasattr(result, 'analysis_time') else 0,
            ),
            resources=None,
            version="1.0.0",
            environment="production",
        )

        # 10. Generar resumen
        summary = f"""
Algoritmo: {ast.algorithm.name}
Complejidad Temporal: {result.big_o}
Complejidad Espacial: {space_complexity.total if space_complexity else 'N/A'}
Recursivo: {'Sí' if result.is_recursive else 'No'}
        """.strip()

        # 11. Construir resultado completo
        return CompleteAnalysisResult(
            success=True,
            message="Análisis completado exitosamente",
            timestamp=datetime.now(timezone.utc),
            algorithm_name=ast.algorithm.name,
            algorithm_info=algorithm_info,
            complexity=complexity,
            space_complexity=space_complexity,
            recurrence_temporal=recurrence_temporal,
            recurrence_spatial=None,
            line_by_line=line_by_line,
            patterns=None,
            structures=None,
            visualizations=[],
            metadata=metadata,
            summary=summary,
            recommendations=[
                "Considerar optimizaciones si la complejidad es alta",
                "Verificar uso de memoria para grandes entradas",
            ],
        )

    except Exception as e:
        logger.error(f"Error en análisis: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "AnalysisError",
                "message": str(e)
            }
        )

@router.post(
    "/quick",
    summary="Análisis Rápido",
    description="Análisis simplificado sin detalles completos"
)
async def analyze_quick(code: str = Query(..., description="Código a analizar")):
    """Análisis rápido de complejidad"""
    # PROFILING: Quick analysis
    if _profiling_enabled and _monitor:
        with _monitor.monitor("endpoint_quick_analysis", module="api"):
            return await _analyze_quick_impl(code)
    else:
        return await _analyze_quick_impl(code)
    
async def _analyze_quick_impl(code: str):
    """Implementación interna de quick analysis."""
    try:
        logger.info("Recibida solicitud de análisis rápido")
        
        parser = PseudocodeParser()
        ast = parser.parse(code)
        
        from app.core.analyzer.complexity import BigOAnalyzer
        analyzer = BigOAnalyzer()
        big_o = analyzer.analyze(ast)
        
        return {
            "success": True,
            "big_o": big_o,
            "algorithm_name": ast.algorithm.name,
            "message": "Análisis rápido completado"
        }
    except Exception as e:
        logger.error(f"Error en análisis rápido: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post(
    "/line-by-line",
    summary="Análisis Línea por Línea",
    description="""
Análisis detallado de cada línea del algoritmo.

El código puede enviarse de dos formas:
1. **Query Parameter**: `?code=...` (para código corto, URL-encoded)
2. **Request Body**: JSON con campo `code` (recomendado para código multilínea)

Ejemplo Body:
```json
{
    "code": "algorithm example(n)\\nbegin\\n    for i ← 1 to n do\\n    begin\\n        print(i)\\n    end\\nend"
}
```
"""
)
async def analyze_line_by_line(
    code: Optional[str] = Query(None, description="Código a analizar (URL-encoded)"),
    body: Optional[CodeInput] = Body(None, description="Código en JSON (recomendado para multilínea)")
):
    """
    Análisis línea por línea.
    
    Acepta código via:
    - Query parameter `code` (para compatibilidad, código URL-encoded)
    - Request body con campo `code` (recomendado para código multilínea)
    """
    # Determinar fuente del código (prioridad al body)
    source_code = None
    if body and body.code:
        source_code = body.code
    elif code:
        source_code = code
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Se requiere código. Envíe via query parameter 'code' o en el body JSON con campo 'code'"
        )
    
    # PROFILING: Line by line
    if _profiling_enabled and _monitor:
        with _monitor.monitor("endpoint_line_by_line", module="api"):
            return await _analyze_line_by_line_impl(source_code)
    else:
        return await _analyze_line_by_line_impl(source_code)

async def _analyze_line_by_line_impl(code: str):
    """Implementación interna de line by line."""
    try:
        logger.info("Recibida solicitud de análisis línea por línea")
        
        parser = PseudocodeParser()
        ast = parser.parse(code)
        
        from app.core.analyzer import LineByLineAnalyzer
        analyzer = LineByLineAnalyzer()
        result = analyzer.analyze(ast)
        
        lines_data = []
        for line in result.lines:
            # Filtrar líneas con line_number inválido
            if line.line_number < 1:
                continue
            lines_data.append({
                "line_number": line.line_number,
                "code": getattr(line, 'code', f"Línea {line.line_number}"),
                "execution_count": line.execution_count,
                "statement_type": line.statement_type,
                "complexity_contribution": getattr(line, 'complexity_contribution', line.execution_count),
                "explanation": line.explanation
            })
        
        return {
            "success": True,
            "algorithm_name": ast.algorithm.name,
            "lines": lines_data,
            "total_lines": len(lines_data),
            "message": "Análisis línea por línea completado"
        }
    except Exception as e:
        logger.error(f"Error en análisis línea por línea: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post(
    "/solve-recurrence",
    summary="Resolver Ecuación de Recurrencia",
    description="Resuelve una ecuación de recurrencia específica"
)
async def solve_recurrence_equation(
    equation: str,
    base_case: Optional[str] = None,
    method: Optional[str] = None,
    variable: Optional[str] = None
):
    """
    Resuelve una ecuación de recurrencia específica.
    
    Métodos disponibles:
    - iteration
    - recursion_tree
    - master_theorem
    - substitution
    - characteristic
    """
    # PROFILING: Solve recurrence
    if _profiling_enabled and _monitor:
        with _monitor.monitor("solve_recurrence", module="api"):
            return await _solve_recurrence_impl(equation, base_case, method)
    else:
        return await _solve_recurrence_impl(equation, base_case, method)

async def _solve_recurrence_impl(equation: str, base_case: Optional[str], method: Optional[str], variable: Optional[str] = None):
    """Implementación interna de solve recurrence."""
    try:
        # Importar el helper del solver, usando alias para evitar shadowing
        from app.core.analyzer.recurrence import solve_recurrence, SolutionMethod as SolverSolutionMethod
        
        # Convertir método si se especificó
        preferred_method = None
        if method:
            # Mapear método de inglés a español si es necesario
            mapped_method = METHOD_MAPPING.get(method.lower())
            if not mapped_method:
                valid_methods = list(set(METHOD_MAPPING.keys()))
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Método inválido: {method}. Métodos válidos: {valid_methods}"
                )
            try:
                # Construir preferred_method como el enum del solver (valores en español)
                preferred_method = SolverSolutionMethod(mapped_method)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Método inválido: {method}"
                )

        # Resolver
        result = solve_recurrence(equation, base_case, preferred_method)

        # Mapear el método devuelto (enum del solver, valores en español)
        # al enum del schema (valores en inglés) esperado por RecurrenceSolution
        SPANISH_TO_ENGLISH = {
            "iteracion": "iteration",
            "arbol_recursion": "recursion_tree",
            "teorema_maestro": "master_theorem",
            "sustitucion_inteligente": "substitution",
            "ecuacion_caracteristica": "characteristic",
        }

        schema_method = None
        try:
            if isinstance(result.method_used, SolverSolutionMethod):
                spanish_val = result.method_used.value
                eng = SPANISH_TO_ENGLISH.get(spanish_val)
                if eng:
                    # SolutionMethod del schema (importado arriba) espera valores en inglés
                    schema_method = SolutionMethod(eng)
                else:
                    # Fallback: intentar usar el nombre en minúsculas
                    schema_method = SolutionMethod(result.method_used.name.lower())
            else:
                # Si viene como string, intentar mapear directamente
                schema_method = SolutionMethod(SPANISH_TO_ENGLISH.get(str(result.method_used), str(result.method_used)))
        except Exception:
            # Si no se pudo mapear, dejar como None y continuar (pydantic hará validación)
            schema_method = None

        # Construir RecurrenceSolution usando el método mapeado
        solution = RecurrenceSolution(
            complexity=result.complexity,
            complexity_class=_get_complexity_class(result.complexity),
            method_used=schema_method,
            steps=result.steps,
            verification=result.explanation,
        )

        return {
            "success": True,
            "equation": equation,
            "variable": variable,
            "base_case": base_case,
            "solution": solution.model_dump(),
        }

    except Exception as e:
        logger.error(f"Error resolviendo ecuación: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get(
    "/methods/{equation_form}",
    summary="Obtener Métodos Aplicables",
    description="Obtiene los métodos de solución aplicables para una forma"
)
async def get_applicable_methods(equation_form: str):
    """
    Obtiene los métodos aplicables para una forma de ecuación.

    Formas: F0, F1, F2, F3, F4, F5, F6
    """
    try:
        from app.core.analyzer.recurrence import RecurrenceSolver, RecurrenceForm

        # Convertir string a enum
        try:
            form = RecurrenceForm[equation_form.upper()]
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Forma inválida: {equation_form}"
            )

        solver = RecurrenceSolver()
        applicable = solver._get_applicable_methods(form)

        return {
            "form": form.name,
            "description": form.value,
            "applicable_methods": [m.value for m in applicable],
            "recommended": solver._select_best_method(form, applicable).value if applicable else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo métodos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# FUNCIONES AUXILIARES
def _get_complexity_class(notation: str) -> Optional[ComplexityClass]:
    """Obtiene la clase de complejidad desde notación"""
    if not notation:
        return None
    
    clean = notation.replace("O(", "").replace(")", "").replace("Ω(", "").replace("Θ(", "")
    
    mapping = {
        "1": ComplexityClass.CONSTANT,
        "log n": ComplexityClass.LOGARITHMIC,
        "n": ComplexityClass.LINEAR,
        "n log n": ComplexityClass.LINEARITHMIC,
        "n²": ComplexityClass.QUADRATIC,
        "n^2": ComplexityClass.QUADRATIC,
        "n³": ComplexityClass.CUBIC,
        "n^3": ComplexityClass.CUBIC,
        "2^n": ComplexityClass.EXPONENTIAL,
        "n!": ComplexityClass.FACTORIAL,
    }
    
    return mapping.get(clean, ComplexityClass.POLYNOMIAL)