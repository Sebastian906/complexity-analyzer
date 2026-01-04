"""
API Endpoints - Análisis de Complejidad

Endpoints REST para analizar algoritmos y obtener su complejidad.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.core.parser import PseudocodeParser
from app.core.analyzer.analyzer_engine import AnalyzerEngine
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()

class AnalysisRequest(BaseModel):
    """Request para análisis de complejidad"""
    code: str = Field(..., description="Código del algoritmo en pseudocódigo")
    analyze_temporal: bool = Field(True, description="Analizar complejidad temporal")
    analyze_spatial: bool = Field(True, description="Analizar complejidad espacial")
    analyze_line_by_line: bool = Field(True, description="Análisis línea por línea")
    analyze_recurrence: bool = Field(True, description="Construir ecuaciones de recurrencia")
    analyze_tight_bounds: bool = Field(True, description="Verificar cotas ajustadas")

class RecurrenceInfo(BaseModel):
    """Información de ecuación de recurrencia"""
    equation: Optional[str] = None

class RecurrenceSolveRequest(BaseModel):
    """Request para resolver ecuación de recurrencia"""
    equation: str = Field(..., description="Ecuación (ej: T(n) = 2T(n/2) + n)")
    base_case: Optional[str] = Field(None, description="Caso base (ej: T(1) = 1)")
    method: Optional[str] = Field(None, description="Método preferido")
    base_case: Optional[str] = None
    pattern: Optional[str] = None
    method_used: Optional[str] = None
    solution_complexity: Optional[str] = None
    solution_steps: Optional[list] = None
    alternative_methods: Optional[list] = None

class ComplexityInfo(BaseModel):
    """Información de complejidad"""
    big_o: str
    omega: str
    theta: Optional[str]

class SpaceInfo(BaseModel):
    """Información de complejidad espacial"""
    total: str
    input_space: str
    auxiliary_space: str
    recursion_space: str
    breakdown: Optional[dict] = None

class TightBoundsInfo(BaseModel):
    """Información de cotas ajustadas"""
    has_tight_bound: bool
    theta: Optional[str] = None
    explanation: str
    little_o: Optional[str] = None
    little_omega: Optional[str] = None

class LineInfo(BaseModel):
    """Información de una línea"""
    line: int
    type: str
    executions: str
    explanation: str

class AnalysisResponse(BaseModel):
    """Response del análisis completo"""
    success: bool
    algorithm_name: str

    # Complejidad temporal
    temporal_complexity: ComplexityInfo

    # Complejidad espacial
    spatial_complexity: Optional[SpaceInfo] = None

    # Ecuaciones de recurrencia
    temporal_recurrence: Optional[RecurrenceInfo] = None
    spatial_recurrence: Optional[RecurrenceInfo] = None

    # Cotas ajustadas
    tight_bounds: Optional[TightBoundsInfo] = None

    # Análisis línea por línea
    line_by_line: Optional[list[LineInfo]] = None

    # Metadata
    metadata: dict

    # Resumen legible
    summary: Optional[str] = None

    message: str

@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analizar Complejidad Completa",
    description="Analiza completamente un algoritmo incluyendo ecuaciones de recurrencia"
)
async def analyze_complexity(request: AnalysisRequest):
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
            analyze_line_by_line=request.analyze_line_by_line,
            analyze_space=request.analyze_spatial,
            analyze_recurrence=request.analyze_recurrence,
            analyze_tight_bounds=request.analyze_tight_bounds
        )

        # 3. Construir respuesta estructurada

        # Complejidad temporal
        temporal_complexity = ComplexityInfo(
            big_o=result.big_o,
            omega=result.omega,
            theta=result.theta
        )

        # Complejidad espacial
        spatial_complexity = None
        if result.space_analysis:
            spatial_complexity = SpaceInfo(
                total=result.space_analysis.space_complexity,
                input_space=result.space_analysis.input_space,
                auxiliary_space=result.space_analysis.auxiliary_space,
                recursion_space=result.space_analysis.recursion_space,
                breakdown=result.space_analysis.breakdown
            )

        # Ecuación de recurrencia temporal
        temporal_recurrence = None
        if result.temporal_recurrence and result.temporal_recurrence.recurrence_equation:
            eq = result.temporal_recurrence.recurrence_equation
            sol = result.temporal_recurrence.solution
            
            temporal_recurrence = RecurrenceInfo(
                equation=eq.equation,
                base_case=eq.base_case,
                pattern=eq.recursion_pattern,
                method_used=sol.method_used.value if sol else None,
                solution_complexity=sol.complexity if sol else None,
                solution_steps=sol.steps if sol else None,
                alternative_methods=[m.value for m in sol.alternative_methods] if sol else None
            )
        
        # Ecuación de recurrencia espacial
        spatial_recurrence = None
        if result.spatial_recurrence and result.spatial_recurrence.recurrence_equation:
            eq = result.spatial_recurrence.recurrence_equation
            sol = result.spatial_recurrence.solution
            
            spatial_recurrence = RecurrenceInfo(
                equation=eq.equation,
                base_case=eq.base_case,
                pattern=eq.recursion_pattern,
                method_used=sol.method_used.value if sol else None,
                solution_complexity=sol.complexity if sol else None,
                solution_steps=sol.steps if sol else None,
                alternative_methods=[m.value for m in sol.alternative_methods] if sol else None
            )

        # Cotas ajustadas
        tight_bounds = None
        if result.tight_bounds:
            tight_bounds = TightBoundsInfo(
                has_tight_bound=result.tight_bounds.has_tight_bound,
                theta=result.tight_bounds.theta,
                explanation=result.tight_bounds.explanation,
                little_o=result.tight_bounds.little_o,
                little_omega=result.tight_bounds.little_omega
            )

        # Análisis línea por línea
        line_by_line_list = None
        if result.line_by_line:
            line_by_line_list = [
                LineInfo(
                    line=line.line_number,
                    type=line.statement_type,
                    executions=line.execution_count,
                    explanation=line.explanation
                )
                for line in result.line_by_line.lines
            ]

        # Metadata
        metadata = {
            "is_recursive": result.is_recursive,
            "max_nesting_depth": result.max_nesting_depth,
            "analysis_time": result.analysis_time,
            "complexity_class": _get_complexity_class(result.big_o),
            "space_optimal": _is_space_optimal(spatial_complexity.auxiliary_space if spatial_complexity else "1")
        }

        # Generar resumen legible
        summary = engine.get_complexity_summary(result)

        return AnalysisResponse(
            success=True,
            algorithm_name=result.algorithm_name,
            temporal_complexity=temporal_complexity,
            spatial_complexity=spatial_complexity,
            temporal_recurrence=temporal_recurrence,
            spatial_recurrence=spatial_recurrence,
            tight_bounds=tight_bounds,
            line_by_line=line_by_line_list,
            metadata=metadata,
            summary=summary,
            message="Análisis completado exitosamente"
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
async def solve_recurrence_equation(request: RecurrenceSolveRequest):
    """
    Resuelve una ecuación de recurrencia específica.
    
    Métodos disponibles:
    - iteracion
    - arbol_recursion
    - teorema_maestro
    - sustitucion_inteligente
    - ecuacion_caracteristica
    """
    try:
        from app.core.analyzer.recurrence import solve_recurrence, SolutionMethod
        
        # Convertir método si se especificó
        preferred_method = None
        if request.method:
            try:
                preferred_method = SolutionMethod(request.method)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Método inválido: {request.method}"
                )

        # Resolver
        result = solve_recurrence(request.equation, request.base_case, preferred_method)

        return {
            "success": True,
            "equation": request.equation,
            "base_case": request.base_case,
            "form_detected": result.form_detected.name,
            "method_used": result.method_used.value,
            "complexity": result.complexity,
            "steps": result.steps,
            "alternative_methods": [m.value for m in result.alternative_methods],
            "explanation": result.explanation
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

# Funciones auxiliares

def _get_complexity_class(big_o: str) -> str:
    """Obtiene la clase de complejidad"""
    clean = big_o.replace("O(", "").replace(")", "")

    classes = {
        "1": "Constante",
        "log n": "Logarítmica",
        "n": "Lineal",
        "n log n": "Linealítmica",
        "n²": "Cuadrática",
        "n^2": "Cuadrática",
        "2^n": "Exponencial",
        "n!": "Factorial"
    }

    return classes.get(clean, "Polinomial")

def _is_space_optimal(auxiliary_space: str) -> bool:
    """Verifica si el espacio auxiliar es óptimo"""
    clean = auxiliary_space.replace("O(", "").replace(")", "")
    return clean in ["1", "log n"]