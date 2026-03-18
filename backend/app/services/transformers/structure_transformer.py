"""
Structure Transformer

Convierte StructureDetectionResult del core al schema Pydantic correspondiente.
Extraído de analysis_orchestrator.py donde vivía el método _detect_structures().

La lógica de detección sigue en StructureIdentifier (core).
Este módulo solo traduce tipos.
"""

from __future__ import annotations

from typing import Optional

from app.core.data_structures.structure_identifier import (
    StructureDetectionResult as CoreStructureDetectionResult,
)
from app.schemas.analysis_result import StructureDetectionResult, StructureMatch
from app.schemas.common import ConfidenceLevelEnum


class StructureTransformer:
    """
    Convierte resultados del StructureIdentifier a schemas Pydantic.

    Todos los métodos son estáticos — no necesita estado.
    """

    @staticmethod
    def to_schema(
        result: CoreStructureDetectionResult,
    ) -> StructureDetectionResult:
        """
        Convierte un StructureDetectionResult del core al schema de la API.

        Reemplaza el bloque de conversión en _detect_structures()
        dentro de analysis_orchestrator.py.

        Args:
            result: StructureDetectionResult del core (dataclass)

        Returns:
            StructureDetectionResult schema (Pydantic)
        """
        structures_found = [
            StructureTransformer._match_to_schema(s)
            for s in result.structures_found
        ]

        primary_structure: Optional[StructureMatch] = None
        if result.primary_structure:
            primary_structure = StructureTransformer._match_to_schema(
                result.primary_structure
            )

        return StructureDetectionResult(
            structures_found=structures_found,
            primary_structure=primary_structure,
            primary_usage=None,
            summary=result.summary,
        )

    @staticmethod
    def _match_to_schema(match) -> StructureMatch:
        """
        Convierte un StructureMatch del core al schema Pydantic.

        El campo confidence_level del core es un enum interno. Lo
        convertimos a ConfidenceLevelEnum del schema usando su .value
        para no acoplar los dos enums directamente.
        """
        confidence_level_value = getattr(match, "confidence_level", None)
        if confidence_level_value is None:
            confidence_level = ConfidenceLevelEnum.LOW
        elif isinstance(confidence_level_value, ConfidenceLevelEnum):
            confidence_level = confidence_level_value
        else:
            try:
                confidence_level = ConfidenceLevelEnum(confidence_level_value.value)
            except (AttributeError, ValueError):
                confidence_level = ConfidenceLevelEnum.LOW

        # structure_type puede ser un enum o un string dependiendo de la versión
        structure_type_raw = match.structure_type
        structure_type = (
            structure_type_raw.value
            if hasattr(structure_type_raw, "value")
            else str(structure_type_raw)
        )

        return StructureMatch(
            structure_type=structure_type,
            structure_name=match.structure_name,
            confidence=match.confidence,
            confidence_level=confidence_level,
            variables=list(getattr(match, "variables", []) or []),
            operations=list(getattr(match, "operations", []) or []),
            reasoning=getattr(match, "reasoning", ""),
        )