"""
API Endpoints - Análisis de Complejidad

Endpoints REST para analizar algoritmos y obtener su complejidad.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, status
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
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()

@router.post(
    "/analyze",
    response_model=CompleteAnalysisResult,
    status_code=status.HTTP_200_OK,
    summary="Analizar Complejidad Completa",
    description="Analiza completamente un algoritmo incluyendo ecuaciones de recurrencia"
)
async def analyze_complexity(request: ComplexityAnalysisRequest):
    """
    Analiza la complejidad completa de un algoritmo.
    
    Incluye:
    - Complejidad temporal (O, Ω, Θ)
    - Complejidad espacial (S(n))
    - Ecuaciones de recurrencia T(n) y S(n)
    - Cotas ajustadas (Theta)
    - Análisis línea por línea
    """
    try:
        logger.info("Recibida solicitud de análisis completo")

        # 1. Parsear el código
        parser = PseudocodeParser()
        ast = parser.parse(request.code)

        logger.info(f"Código parseado: {ast.algorithm.name}")

        # 2. Analizar con el motor principal
        engine = AnalyzerEngine()
        result = engine.analyze(
            ast,
            analyze_line_by_line=request.options.analyze_line_by_line,
            analyze_space=request.options.analyze_spatial,
            analyze_recurrence=request.options.analyze_recurrence,
            analyze_tight_bounds=request.options.calculate_tight_bounds
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
            line_by_line = LineByLineAnalysis(
                lines=[
                    LineExecution(
                        line_number=line.line_number,
                        code=line.code,
                        execution_count=line.execution_count,
                        statement_type=line.statement_type,
                        complexity_contribution=line.complexity_contribution,
                        explanation=line.explanation,
                        location=None,
                    )
                    for line in result.line_by_line.lines
                ],
                dominant_complexity=result.big_o,
                total_lines=len(result.line_by_line.lines),
                summary=f"Análisis línea por línea de {ast.algorithm.name}",
            )

        # 9. Construir metadata
        from app.schemas.common import AnalysisMetadata, TimingMetadata
        from datetime import datetime
        
        metadata = AnalysisMetadata(
            timing=TimingMetadata(
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
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
            timestamp=datetime.utcnow(),
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
    "/solve-recurrence",
    summary="Resolver Ecuación de Recurrencia",
    description="Resuelve una ecuación de recurrencia específica"
)
async def solve_recurrence_equation(
    equation: str,
    base_case: Optional[str] = None,
    method: Optional[str] = None
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
    try:
        from app.core.analyzer.recurrence import solve_recurrence, SolutionMethod
        
        # Convertir método si se especificó
        preferred_method = None
        if method:
            try:
                preferred_method = SolutionMethod(method)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Método inválido: {method}"
                )

        # Resolver
        result = solve_recurrence(equation, base_case, preferred_method)

        # Construir RecurrenceSolution
        solution = RecurrenceSolution(
            complexity=result.complexity,
            complexity_class=_get_complexity_class(result.complexity),
            method_used=result.method_used,
            steps=result.steps,
            verification=result.explanation,
        )

        return {
            "success": True,
            "equation": equation,
            "base_case": base_case,
            "solution": solution.dict(),
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