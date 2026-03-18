"""
PatternStep

Ejecuta PatternDetector y convierte el resultado usando PatternMapper.
"""

from __future__ import annotations

from app.core.patterns import PatternDetector
from app.schemas.analysis_request import CompleteAnalysisRequest
from app.services.pipeline.context import PipelineContext
from app.services.transformers import PatternMapper
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class PatternStep:
    """Paso de detección de patrones algorítmicos."""

    name = "patterns"

    def __init__(
        self,
        detector: PatternDetector = None,
        request: CompleteAnalysisRequest = None,
    ) -> None:
        self._detector = detector or PatternDetector()
        self._request = request

    def should_run(self, ctx: PipelineContext) -> bool:
        req = self._request or ctx.request
        return req.analyze_patterns and ctx.parse_succeeded

    async def execute(self, ctx: PipelineContext) -> PipelineContext:
        req = self._request or ctx.request

        try:
            core_result = self._detector.detect(
                ctx.ast,
                min_confidence=req.pattern_options.min_confidence,
            )
            ctx.patterns = PatternMapper.result_to_schema(core_result)

            primary = ctx.patterns.primary_pattern_name or "ninguno"
            logger.debug(
                f"PatternStep: {ctx.algorithm_name} — patrón principal: {primary}"
            )

        except Exception as exc:
            logger.warning(f"PatternStep: error — {exc}")
            ctx.warnings.append(f"Detección de patrones fallida: {exc}")

        return ctx