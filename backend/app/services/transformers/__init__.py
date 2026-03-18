"""
Transformers — Capa de conversión entre objetos del core y schemas de la API.

Cada transformer tiene una sola responsabilidad: convertir un tipo interno
(dataclass del core) al schema Pydantic correspondiente para la API.

Transformers disponibles:
    - ComplexityTransformer : core.AnalysisResult  → schemas de complejidad
    - StructureTransformer  : core.StructureDetectionResult → schemas de estructuras
    - PatternMapper         : core.PatternDetectionResult  → schemas de patrones
                             (ya existía en mappers/, se re-exporta aquí para
                              tener un único punto de importación)

Uso desde el orchestrator:
    from app.services.transformers import (
        ComplexityTransformer,
        StructureTransformer,
        PatternMapper,
    )

    complexity_schema = ComplexityTransformer.to_schema(analysis_result)
    structures_schema = StructureTransformer.to_schema(structure_result)
    patterns_schema   = PatternMapper.result_to_schema(pattern_result)
"""

from app.services.transformers.complexity_transformer import ComplexityTransformer
from app.services.transformers.structure_transformer import StructureTransformer
from app.services.mappers.pattern_mapper import PatternMapper

__all__ = [
    "ComplexityTransformer",
    "StructureTransformer",
    "PatternMapper",
]