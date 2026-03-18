"""
ComplexityStep

Ejecuta el AnalyzerEngine y convierte el resultado usando
ComplexityTransformer. Maneja las cuatro sub-análisis opcionales:
    - Complejidad temporal (Big O, Omega, Theta)
    - Complejidad espacial S(n)
    - Análisis línea por línea
    - Ecuaciones de recurrencia T(n) y S(n)
"""

from __future__ import annotations

from app.core.analyzer import AnalyzerEngine
from app.core.exceptions import AnalyzerException
from app.schemas.analysis_request import CompleteAnalysisRequest
from app.services.pipeline.context import PipelineContext
from app.services.transformers import ComplexityTransformer
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class ComplexityStep:
    """
    Paso de análisis de complejidad.

    Delega el análisis al AnalyzerEngine y la conversión de tipos
    al ComplexityTransformer. No tiene lógica propia de análisis.
    """

    name = "complexity"

    def __init__(
        self,
        engine: AnalyzerEngine = None,
        request: CompleteAnalysisRequest = None,
    ) -> None:
        self._engine = engine or AnalyzerEngine()
        self._request = request

    def should_run(self, ctx: PipelineContext) -> bool:
        req = self._request or ctx.request
        return req.analyze_complexity and ctx.parse_succeeded

    async def execute(self, ctx: PipelineContext) -> PipelineContext:
        req = self._request or ctx.request
        opts = req.complexity_options

        try:
            core_result = self._engine.analyze(
                ctx.ast,
                analyze_line_by_line=opts.analyze_line_by_line,
                analyze_space=opts.analyze_spatial,
                analyze_recurrence=opts.analyze_recurrence,
                analyze_tight_bounds=opts.calculate_tight_bounds,
                source_code=req.code,
            )

            if core_result is None:
                ctx.errors.append("AnalyzerEngine retornó resultado nulo")
                return ctx

            # Complejidad temporal
            ctx.complexity = ComplexityTransformer.to_schema(core_result)

            # Complejidad espacial
            if opts.analyze_spatial:
                ctx.space_complexity = ComplexityTransformer.space_to_schema(
                    core_result
                )

            # Análisis línea por línea
            if opts.analyze_line_by_line and core_result.line_by_line:
                ctx.line_by_line = ComplexityTransformer.line_by_line_to_schema(
                    core_result,
                    dominant_complexity=core_result.big_o,
                )

            # Ecuaciones de recurrencia
            if opts.analyze_recurrence:
                ctx.recurrence_temporal = (
                    ComplexityTransformer.temporal_recurrence_to_schema(core_result)
                )
                ctx.recurrence_spatial = (
                    ComplexityTransformer.spatial_recurrence_to_schema(core_result)
                )

            logger.debug(
                f"ComplexityStep: {ctx.algorithm_name} — "
                f"Big O={core_result.big_o}, Omega={core_result.omega}"
            )

        except AnalyzerException as exc:
            logger.error(f"ComplexityStep: error de análisis — {exc}")
            ctx.errors.append(f"Error en análisis de complejidad: {exc}")
        except Exception as exc:
            logger.error(f"ComplexityStep: error inesperado — {exc}", exc_info=True)
            ctx.errors.append(f"Error inesperado en complejidad: {exc}")

        return ctx