"""
Steps — Pasos concretos del pipeline de análisis.

Cada paso implementa el protocolo PipelineStep:
    - name: str
    - should_run(ctx) -> bool
    - execute(ctx) -> PipelineContext

Pasos disponibles:
    ParseStep       — parsing de código a AST
    ComplexityStep  — análisis temporal, espacial, LBL, recurrencia
    PatternStep     — detección de patrones algorítmicos
    StructureStep   — detección de estructuras de datos
    SummarizeStep   — resumen ejecutivo y recomendaciones

Paso opcional (requiere LLMRouter):
    LLMValidationStep — validación cruzada con LLM (Paso 2B)
"""

from app.services.pipeline.steps.parse_step import ParseStep
from app.services.pipeline.steps.complexity_step import ComplexityStep
from app.services.pipeline.steps.pattern_step import PatternStep
from app.services.pipeline.steps.structure_step import StructureStep
from app.services.pipeline.steps.summarize_step import SummarizeStep
from app.services.pipeline.steps.llm_validation_step import LLMValidationStep

__all__ = [
    "ParseStep",
    "ComplexityStep",
    "PatternStep",
    "StructureStep",
    "SummarizeStep",
    "LLMValidationStep",
]