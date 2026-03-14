"""
Pattern Mapper - Conversión centralizada de schemas de patrones

Problema que resuelve:
    La conversión de ScoredPattern (core) → ScoredPattern (schema Pydantic)
    estaba triplicada en analysis_orchestrator.py y duplicada en patterns.py
    (endpoint). Cualquier cambio en la estructura de PatternMatch requería
    modificar 5+ lugares distintos.

Solución:
    Un único lugar donde vive la lógica de conversión. Todos los callers
    usan PatternMapper.to_schema() y PatternMapper.result_to_schema().

Callers que se simplifican:
    - app/services/analysis_orchestrator.py  → _detect_patterns()
    - app/api/v1/endpoints/patterns.py       → detect_patterns()

No duplica:
    - Lógica de detección (PatternDetector)
    - Lógica de scoring (PatternScorer)
    Solo la capa de traducción entre tipos internos y DTOs de API.
"""

from __future__ import annotations

from typing import List, Optional

from app.schemas import (
    ConfidenceLevelEnum,
    PatternDetectionResult,
    PatternIndicator,
    PatternMatch,
    PatternStatistics,
    ScoredPattern,
)

class PatternMapper:
    """
    Convierte objetos del core de patrones a schemas Pydantic de la API.

    Todos los métodos son estáticos — no necesita estado.
    """

    @staticmethod
    def indicator_to_schema(ind) -> PatternIndicator:
        """
        Convierte un PatternIndicator interno a schema Pydantic.

        Usa getattr con defaults seguros para tolerar versiones del
        core donde algunos campos pueden no existir.
        """
        return PatternIndicator(
            name=ind.name,
            description=ind.description,
            found=ind.found,
            weight=ind.weight,
            evidence=getattr(ind, "evidence", None) or "",
            location=getattr(ind, "location", None) or "",
        )

    @staticmethod
    def match_to_schema(pattern) -> PatternMatch:
        """
        Convierte un PatternMatch interno a schema Pydantic.

        Args:
            pattern: PatternMatch del core (app.core.patterns.base_pattern)

        Returns:
            PatternMatch schema (app.schemas.pattern)
        """
        return PatternMatch(
            pattern_type=pattern.pattern_type,
            pattern_name=pattern.pattern_name,
            confidence=pattern.confidence,
            confidence_level=ConfidenceLevelEnum(pattern.confidence_level.value),
            indicators_found=[
                PatternMapper.indicator_to_schema(i)
                for i in pattern.indicators_found
            ],
            indicators_missing=[
                PatternMapper.indicator_to_schema(i)
                for i in pattern.indicators_missing
            ],
            reasoning=pattern.reasoning,
            typical_complexity=getattr(pattern, "typical_complexity", None),
            metadata=getattr(pattern, "metadata", None) or {},
        )

    @staticmethod
    def scored_to_schema(sp) -> ScoredPattern:
        """
        Convierte un ScoredPattern interno a schema Pydantic.

        Args:
            sp: ScoredPattern del core (app.core.patterns.pattern_scorer)

        Returns:
            ScoredPattern schema (app.schemas.pattern)
        """
        confidence = sp.pattern.confidence

        return ScoredPattern(
            pattern=PatternMapper.match_to_schema(sp.pattern),
            raw_score=getattr(sp, "raw_score", confidence),
            adjusted_score=getattr(sp, "adjusted_score", sp.final_score),
            final_score=getattr(sp, "final_score", confidence),
            confidence_bonus=getattr(sp, "confidence_bonus", 0.0),
            missing_penalty=getattr(sp, "missing_penalty", 0.0),
            conflict_penalty=getattr(sp, "conflict_penalty", 0.0),
            conflicts=getattr(sp, "conflicts", None) or [],
            rank=getattr(sp, "rank", None),
        )

    @staticmethod
    def result_to_schema(result) -> PatternDetectionResult:
        """
        Convierte un PatternDetectionResult del core a schema Pydantic completo.

        Este es el método principal que usan los callers. Reemplaza los
        bloques de conversión en analysis_orchestrator.py y patterns.py.

        Args:
            result: PatternDetectionResult del core
                    (app.core.patterns.pattern_detector)

        Returns:
            PatternDetectionResult schema (app.schemas.analysis_result)
        """
        if not hasattr(result, "all_patterns"):
            # Resultado malformado — retornar vacío seguro
            return PatternDetectionResult(
                patterns_found=[],
                scored_patterns=[],
                primary_pattern=None,
                confident_patterns=[],
                summary="Error en detección de patrones",
                pattern_count=0,
                metadata={},
            )

        # Convertir todos los scored patterns
        scored_patterns: List[ScoredPattern] = [
            PatternMapper.scored_to_schema(sp) for sp in result.all_patterns
        ]

        # Los PatternMatch se extraen de los scored para patterns_found
        patterns_found: List[PatternMatch] = [sp.pattern for sp in scored_patterns]

        # Patrón primario
        primary_pattern: Optional[ScoredPattern] = (
            PatternMapper.scored_to_schema(result.primary_pattern)
            if result.primary_pattern
            else None
        )

        # Patrones confiables
        confident_patterns: List[ScoredPattern] = [
            PatternMapper.scored_to_schema(sp) for sp in result.confident_patterns
        ]

        # Estadísticas
        high_conf_count = sum(1 for p in patterns_found if p.confidence >= 0.7)
        statistics = PatternStatistics(
            total_patterns_detected=len(patterns_found),
            high_confidence_patterns=high_conf_count,
            medium_confidence_patterns=sum(
                1 for p in patterns_found
                if p.confidence_level == ConfidenceLevelEnum.MEDIUM
            ),
            low_confidence_patterns=sum(
                1 for p in patterns_found
                if p.confidence_level == ConfidenceLevelEnum.LOW
            ),
            pattern_types_found=[p.pattern_type for p in patterns_found],
            most_confident_pattern=(
                result.primary_pattern_name if result.primary_pattern else None
            ),
            average_confidence=(
                sum(p.confidence for p in patterns_found) / len(patterns_found)
                if patterns_found
                else 0.0
            ),
        )

        return PatternDetectionResult(
            patterns_found=patterns_found,
            scored_patterns=scored_patterns,
            primary_pattern=primary_pattern,
            confident_patterns=confident_patterns,
            summary=result.summary,
            pattern_count=len(patterns_found),
            high_confidence_count=high_conf_count,
            statistics=statistics,
            metadata=getattr(result, "metadata", {}),
        )