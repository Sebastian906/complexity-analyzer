"""
SummarizeStep

Genera el resumen ejecutivo y las recomendaciones delegando
en Summarizer. Siempre corre si el parse fue exitoso.
"""

from __future__ import annotations

from app.services.pipeline.context import PipelineContext
from app.services.summarizer import Summarizer
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class SummarizeStep:
    """Paso de generación de resumen y recomendaciones."""

    name = "summarize"

    def should_run(self, ctx: PipelineContext) -> bool:
        return ctx.parse_succeeded

    async def execute(self, ctx: PipelineContext) -> PipelineContext:
        try:
            ctx.summary = Summarizer.generate_summary(
                algorithm_name=ctx.algorithm_name,
                complexity=ctx.complexity,
                space_complexity=ctx.space_complexity,
                patterns=ctx.patterns,
                structures=ctx.structures,
            )
            ctx.recommendations = Summarizer.generate_recommendations(
                complexity=ctx.complexity,
                patterns=ctx.patterns,
            )
            logger.debug(f"SummarizeStep: resumen generado para '{ctx.algorithm_name}'")

        except Exception as exc:
            logger.warning(f"SummarizeStep: error — {exc}")
            ctx.warnings.append(f"Generación de resumen fallida: {exc}")
            ctx.summary = f"Algoritmo: {ctx.algorithm_name}"
            ctx.recommendations = []

        return ctx