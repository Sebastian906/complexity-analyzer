"""
Complexity Transformer

Convierte los objetos del core de análisis a los schemas Pydantic
que expone la API. Extraído de analysis_orchestrator.py donde vivían
los métodos _build_complexity_analysis(), _build_space_complexity(),
_build_recurrence_equation() y _build_line_by_line().

"""

from __future__ import annotations

from typing import Optional

from app.core.analyzer.analyzer_engine import AnalysisResult
from app.schemas.complexity import (
    ComplexityAnalysis,
    ComplexityClass,
    RecurrenceEquation,
    RecurrenceType,
    SpaceComplexityAnalysis,
)
from app.schemas.analysis_result import LineByLineAnalysis, LineExecution

# Mapeo de notación textual → enum ComplexityClass.
# Centralizado aquí para que cualquier cambio en el enum sea un cambio en
# un solo lugar.
_NOTATION_TO_CLASS: dict[str, ComplexityClass] = {
    "1":         ComplexityClass.CONSTANT,
    "log n":     ComplexityClass.LOGARITHMIC,
    "n":         ComplexityClass.LINEAR,
    "n log n":   ComplexityClass.LINEARITHMIC,
    "n²":        ComplexityClass.QUADRATIC,
    "n^2":       ComplexityClass.QUADRATIC,
    "n³":        ComplexityClass.CUBIC,
    "n^3":       ComplexityClass.CUBIC,
    "2^n":       ComplexityClass.EXPONENTIAL,
    "n!":        ComplexityClass.FACTORIAL,
}

def _clean_notation(notation: str) -> str:
    """Elimina los prefijos de notación asintótica para obtener el término puro."""
    for prefix in ("O(", "Ω(", "Θ(", "o(", "ω("):
        notation = notation.replace(prefix, "")
    return notation.replace(")", "").strip()

def _notation_to_class(notation: str) -> Optional[ComplexityClass]:
    """Convierte una notación como 'O(n²)' al enum ComplexityClass."""
    if not notation:
        return None
    clean = _clean_notation(notation)
    return _NOTATION_TO_CLASS.get(clean, ComplexityClass.POLYNOMIAL)

class ComplexityTransformer:
    """
    Convierte resultados del AnalyzerEngine a schemas Pydantic.

    Todos los métodos son estáticos — no necesita estado.

    El método principal es to_schema(). Los métodos individuales
    (complexity_analysis, space_complexity, etc.) están expuestos
    por si algún caller solo necesita una parte del resultado.
    """

    @staticmethod
    def to_schema(result: AnalysisResult) -> ComplexityAnalysis:
        """
        Convierte un AnalysisResult completo al schema ComplexityAnalysis.

        Este es el método que llama el orchestrator. Reemplaza
        _build_complexity_analysis() en analysis_orchestrator.py.

        Args:
            result: AnalysisResult del AnalyzerEngine (dataclass del core)

        Returns:
            ComplexityAnalysis schema (Pydantic)
        """
        has_tight_bound = (
            result.tight_bounds is not None
            and result.tight_bounds.has_tight_bound
        )

        theta = None
        if has_tight_bound and result.tight_bounds:
            theta = result.tight_bounds.theta
        elif result.theta and result.theta not in ("None", ""):
            theta = result.theta

        return ComplexityAnalysis(
            big_o=result.big_o,
            omega=result.omega,
            theta=theta,
            big_o_class=_notation_to_class(result.big_o),
            omega_class=_notation_to_class(result.omega),
            theta_class=_notation_to_class(theta) if theta else None,
            explanation="Complejidad temporal del algoritmo",
            reasoning=[
                "Análisis basado en estructura del código",
                f"Complejidad dominante: {result.big_o}",
            ],
            has_tight_bound=has_tight_bound,
        )

    @staticmethod
    def space_to_schema(result: AnalysisResult) -> Optional[SpaceComplexityAnalysis]:
        """
        Extrae la complejidad espacial de un AnalysisResult.

        Reemplaza _build_space_complexity() en analysis_orchestrator.py.

        Returns:
            SpaceComplexityAnalysis schema, o None si no hay análisis espacial.
        """
        sa = result.space_analysis
        if not sa:
            return None

        return SpaceComplexityAnalysis(
            total=sa.space_complexity,
            input_space=sa.input_space,
            auxiliary_space=sa.auxiliary_space,
            recursion_space=getattr(sa, "recursion_space", None),
            explanation=f"Espacio total: {sa.space_complexity}",
            breakdown={
                "input":     sa.input_space,
                "auxiliary": sa.auxiliary_space,
                "recursion": getattr(sa, "recursion_space", "O(1)"),
            },
        )

    @staticmethod
    def temporal_recurrence_to_schema(
        result: AnalysisResult,
    ) -> Optional[RecurrenceEquation]:
        """
        Extrae la ecuación de recurrencia temporal.

        Reemplaza _build_recurrence_equation() en analysis_orchestrator.py.

        Returns:
            RecurrenceEquation schema, o None si el algoritmo no es recursivo
            o no se pudo construir la ecuación.
        """
        tr = result.temporal_recurrence
        if not tr or not tr.recurrence_equation:
            return None

        eq = tr.recurrence_equation
        pattern_value = getattr(eq, "recursion_pattern", None)

        # El campo recursion_pattern puede ser un string o un enum dependiendo
        # de la versión del core — normalizar siempre a RecurrenceType.
        if pattern_value is None:
            recurrence_type = RecurrenceType.LINEAR
        elif isinstance(pattern_value, RecurrenceType):
            recurrence_type = pattern_value
        else:
            try:
                recurrence_type = RecurrenceType(str(pattern_value))
            except ValueError:
                recurrence_type = RecurrenceType.LINEAR

        return RecurrenceEquation(
            equation=eq.equation,
            base_case=getattr(eq, "base_case", "T(1) = O(1)"),
            recursion_pattern=recurrence_type,
            a=getattr(eq, "a", None),
            b=getattr(eq, "b", None),
            f_n=getattr(eq, "f_n", None),
            explanation="Ecuación de recurrencia temporal T(n)",
        )

    @staticmethod
    def spatial_recurrence_to_schema(
        result: AnalysisResult,
    ) -> Optional[RecurrenceEquation]:
        """
        Extrae la ecuación de recurrencia espacial.

        Returns:
            RecurrenceEquation schema, o None si no aplica.
        """
        sr = result.spatial_recurrence
        if not sr or not sr.recurrence_equation:
            return None

        eq = sr.recurrence_equation
        pattern_value = getattr(eq, "recursion_pattern", None)

        if pattern_value is None:
            recurrence_type = RecurrenceType.LINEAR
        elif isinstance(pattern_value, RecurrenceType):
            recurrence_type = pattern_value
        else:
            try:
                recurrence_type = RecurrenceType(str(pattern_value))
            except ValueError:
                recurrence_type = RecurrenceType.LINEAR

        return RecurrenceEquation(
            equation=eq.equation,
            base_case=getattr(eq, "base_case", "S(1) = O(1)"),
            recursion_pattern=recurrence_type,
            a=getattr(eq, "a", None),
            b=getattr(eq, "b", None),
            f_n=getattr(eq, "f_n", None),
            explanation="Ecuación de recurrencia espacial S(n)",
        )

    @staticmethod
    def line_by_line_to_schema(
        result: AnalysisResult,
        dominant_complexity: str,
    ) -> Optional[LineByLineAnalysis]:
        """
        Convierte el análisis línea por línea del core al schema.

        Reemplaza _build_line_by_line() en analysis_orchestrator.py.

        Args:
            result:               AnalysisResult con line_by_line poblado.
            dominant_complexity:  Big O del análisis (se pasa por claridad,
                                  no se recalcula aquí).

        Returns:
            LineByLineAnalysis schema, o None si no hay análisis línea a línea.
        """
        lbl = result.line_by_line
        if not lbl:
            return None

        lines = [
            LineExecution(
                line_number=line.line_number,
                code=getattr(line, "code", getattr(line, "statement", "")),
                execution_count=str(line.execution_count),
                statement_type=line.statement_type,
                complexity_contribution=line.complexity_contribution,
                explanation=line.explanation,
                location=None,
            )
            for line in lbl.lines
        ]

        return LineByLineAnalysis(
            lines=lines,
            dominant_complexity=dominant_complexity,
            total_lines=len(lines),
            summary="Análisis línea por línea completado",
        )

    @staticmethod
    def notation_to_class(notation: str) -> Optional[ComplexityClass]:
        """
        Exposición pública de la función interna de mapeo.

        Útil si otros callers (endpoints, tests) necesitan convertir
        una notación a su clase sin instanciar el transformer completo.
        """
        return _notation_to_class(notation)