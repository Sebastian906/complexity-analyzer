"""
StructureStep

Ejecuta StructureIdentifier y convierte el resultado usando
StructureTransformer.
"""

from __future__ import annotations

from app.core.data_structures import StructureIdentifier
from app.schemas.analysis_request import CompleteAnalysisRequest
from app.services.pipeline.context import PipelineContext
from app.services.transformers import StructureTransformer
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class StructureStep:
    """Paso de detección de estructuras de datos."""

    name = "structures"

    def __init__(
        self,
        identifier: StructureIdentifier = None,
        request: CompleteAnalysisRequest = None,
    ) -> None:
        self._identifier = identifier or StructureIdentifier()
        self._request = request

    def should_run(self, ctx: PipelineContext) -> bool:
        req = self._request or ctx.request
        return req.analyze_structures and ctx.parse_succeeded

    async def execute(self, ctx: PipelineContext) -> PipelineContext:
        req = self._request or ctx.request

        try:
            core_result = self._identifier.identify(
                ctx.ast,
                min_confidence=req.structure_options.min_confidence,
            )
            ctx.structures = StructureTransformer.to_schema(core_result)

            primary = (
                ctx.structures.primary_structure.structure_name
                if ctx.structures.primary_structure
                else "ninguna"
            )
            logger.debug(
                f"StructureStep: {ctx.algorithm_name} — "
                f"estructura principal: {primary}"
            )

        except Exception as exc:
            logger.warning(f"StructureStep: error — {exc}")
            ctx.warnings.append(f"Detección de estructuras fallida: {exc}")

        return ctx