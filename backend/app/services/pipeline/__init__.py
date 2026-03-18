"""
Pipeline — Motor de análisis formal y extensible.

El pipeline convierte el orchestrator de coordinador implícito
a un sistema de pasos registrables y reemplazables.

Uso desde el orchestrator:
    from app.services.pipeline import AnalysisPipeline, PipelineContext
    from app.services.pipeline.steps import (
        ParseStep, ComplexityStep, PatternStep,
        StructureStep, SummarizeStep,
    )

    pipeline = AnalysisPipeline([
        ParseStep(parser),
        ComplexityStep(engine, request),
        PatternStep(detector, request),
        StructureStep(identifier, request),
        SummarizeStep(),
    ])
    ctx = await pipeline.run(PipelineContext(request=request))

Para agregar un paso nuevo sin tocar el orchestrator:
    pipeline.register_step(MyCustomStep(), position=-1)
"""

from app.services.pipeline.context import PipelineContext
from app.services.pipeline.pipeline import AnalysisPipeline
from app.services.pipeline.step import PipelineStep

__all__ = [
    "AnalysisPipeline",
    "PipelineContext",
    "PipelineStep",
]