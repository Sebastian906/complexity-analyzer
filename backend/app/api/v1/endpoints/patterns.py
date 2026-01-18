"""
API Endpoints - Detección de Patrones

Endpoints REST para detectar patrones algorítmicos en pseudocódigo.
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, status
from app.schemas import (
    # Pattern Request Schemas
    PatternDetectionRequest,
    PatternDetectionOptions,
    
    # Pattern Result Schemas
    PatternDetectionResult,
    PatternMatch,
    ScoredPattern,
    PatternIndicator,
    PatternStatistics,
    PatternComparison,
    PatternRecommendation,
    
    # Pattern Enums
    PatternType,
    
    # Common
    BaseResponse,
    ConfidenceLevelEnum,
)

from app.core.parser import PseudocodeParser
from app.core.patterns import PatternDetector
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()

@router.post(
    "/detect",
    response_model=PatternDetectionResult,
    status_code=status.HTTP_200_OK,
    summary="Detectar Patrones Algorítmicos",
    description="Detecta todos los patrones algorítmicos presentes en el código"
)
async def detect_patterns(request: PatternDetectionRequest):
    """
    Detecta patrones algorítmicos en pseudocódigo.

    Patrones detectables:
    - Fuerza Bruta
    - Recursión
    - Divide y Vencerás
    - Programación Dinámica
    - Greedy (Voraz)
    - Backtracking
    - Branch and Bound
    - Ordenamiento
    - Búsqueda
    - Algoritmos Cuánticos
    - Algoritmos Bio-inspirados
    - Algoritmos de Aproximación
    """
    try:
        logger.info("Recibida solicitud de detección de patrones")

        # 1. Parsear el código
        parser = PseudocodeParser()
        ast = parser.parse(request.code)

        logger.info(f"Código parseado: {ast.algorithm.name}")

        # 2. Detectar patrones
        detector = PatternDetector()
        result = detector.detect(ast, request.options.min_confidence)

        logger.info(
            f"Detección completada: {result.pattern_count} patrones encontrados"
        )

        # 3. Convertir resultado a schema Pydantic
        
        # Convertir patterns_found
        patterns_found = [
            PatternMatch(
                pattern_type=p.pattern.pattern_type,
                pattern_name=p.pattern.pattern_name,
                confidence=p.pattern.confidence,
                confidence_level=ConfidenceLevelEnum(p.pattern.confidence_level.value),
                indicators_found=[
                    PatternIndicator(
                        name=ind.name,
                        description=ind.description,
                        found=ind.found,
                        weight=ind.weight,
                        evidence=ind.evidence,
                        location=ind.location,
                    )
                    for ind in p.pattern.indicators_found
                ],
                indicators_missing=[
                    PatternIndicator(
                        name=ind.name,
                        description=ind.description,
                        found=ind.found,
                        weight=ind.weight,
                        evidence=ind.evidence,
                        location=ind.location,
                    )
                    for ind in p.pattern.indicators_missing
                ],
                reasoning=p.pattern.reasoning,
                typical_complexity=p.pattern.typical_complexity,
                metadata=p.pattern.metadata,
            )
            for p in result.patterns_found
        ]
        
        # Convertir scored_patterns
        scored_patterns = [
            ScoredPattern(
                pattern=PatternMatch(
                    pattern_type=sp.pattern.pattern_type,
                    pattern_name=sp.pattern.pattern_name,
                    confidence=sp.pattern.confidence,
                    confidence_level=ConfidenceLevelEnum(sp.pattern.confidence_level.value),
                    indicators_found=[
                        PatternIndicator(
                            name=ind.name,
                            description=ind.description,
                            found=ind.found,
                            weight=ind.weight,
                            evidence=ind.evidence,
                            location=ind.location,
                        )
                        for ind in sp.pattern.indicators_found
                    ],
                    indicators_missing=[
                        PatternIndicator(
                            name=ind.name,
                            description=ind.description,
                            found=ind.found,
                            weight=ind.weight,
                            evidence=ind.evidence,
                            location=ind.location,
                        )
                        for ind in sp.pattern.indicators_missing
                    ],
                    reasoning=sp.pattern.reasoning,
                    typical_complexity=sp.pattern.typical_complexity,
                    metadata=sp.pattern.metadata,
                ),
                raw_score=sp.raw_score,
                adjusted_score=sp.adjusted_score,
                final_score=sp.final_score,
                confidence_bonus=sp.confidence_bonus,
                missing_penalty=sp.missing_penalty,
                conflict_penalty=sp.conflict_penalty,
                conflicts=sp.conflicts,
                rank=sp.rank,
            )
            for sp in result.scored_patterns
        ]
        
        # Patrón primario
        primary_pattern = None
        if result.primary_pattern:
            sp = result.primary_pattern
            primary_pattern = ScoredPattern(
                pattern=PatternMatch(
                    pattern_type=sp.pattern.pattern_type,
                    pattern_name=sp.pattern.pattern_name,
                    confidence=sp.pattern.confidence,
                    confidence_level=ConfidenceLevelEnum(sp.pattern.confidence_level.value),
                    indicators_found=[
                        PatternIndicator(
                            name=ind.name,
                            description=ind.description,
                            found=ind.found,
                            weight=ind.weight,
                            evidence=ind.evidence,
                            location=ind.location,
                        )
                        for ind in sp.pattern.indicators_found
                    ],
                    indicators_missing=[
                        PatternIndicator(
                            name=ind.name,
                            description=ind.description,
                            found=ind.found,
                            weight=ind.weight,
                            evidence=ind.evidence,
                            location=ind.location,
                        )
                        for ind in sp.pattern.indicators_missing
                    ],
                    reasoning=sp.pattern.reasoning,
                    typical_complexity=sp.pattern.typical_complexity,
                    metadata=sp.pattern.metadata,
                ),
                raw_score=sp.raw_score,
                adjusted_score=sp.adjusted_score,
                final_score=sp.final_score,
                confidence_bonus=sp.confidence_bonus,
                missing_penalty=sp.missing_penalty,
                conflict_penalty=sp.conflict_penalty,
                conflicts=sp.conflicts,
                rank=sp.rank,
            )
        
        # Patrones confiables
        confident_patterns = [
            ScoredPattern(
                pattern=PatternMatch(
                    pattern_type=sp.pattern.pattern_type,
                    pattern_name=sp.pattern.pattern_name,
                    confidence=sp.pattern.confidence,
                    confidence_level=ConfidenceLevelEnum(sp.pattern.confidence_level.value),
                    indicators_found=[
                        PatternIndicator(
                            name=ind.name,
                            description=ind.description,
                            found=ind.found,
                            weight=ind.weight,
                            evidence=ind.evidence,
                            location=ind.location,
                        )
                        for ind in sp.pattern.indicators_found
                    ],
                    indicators_missing=[
                        PatternIndicator(
                            name=ind.name,
                            description=ind.description,
                            found=ind.found,
                            weight=ind.weight,
                            evidence=ind.evidence,
                            location=ind.location,
                        )
                        for ind in sp.pattern.indicators_missing
                    ],
                    reasoning=sp.pattern.reasoning,
                    typical_complexity=sp.pattern.typical_complexity,
                    metadata=sp.pattern.metadata,
                ),
                raw_score=sp.raw_score,
                adjusted_score=sp.adjusted_score,
                final_score=sp.final_score,
                confidence_bonus=sp.confidence_bonus,
                missing_penalty=sp.missing_penalty,
                conflict_penalty=sp.conflict_penalty,
                conflicts=sp.conflicts,
                rank=sp.rank,
            )
            for sp in result.confident_patterns
        ]

        return PatternDetectionResult(
            patterns_found=patterns_found,
            scored_patterns=scored_patterns,
            primary_pattern=primary_pattern,
            confident_patterns=confident_patterns,
            summary=result.summary,
            pattern_count=result.pattern_count,
            metadata=result.metadata,
        )

    except Exception as e:
        logger.error(f"Error en detección de patrones: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "PatternDetectionError",
                "message": str(e)
            }
        )

@router.post(
    "/detect-specific",
    response_model=BaseResponse,
    status_code=status.HTTP_200_OK,
    summary="Detectar Patrón Específico",
    description="Detecta un patrón algorítmico específico"
)
async def detect_specific_pattern(
    code: str,
    pattern_type: str
):
    """
    Detecta un patrón específico en el algoritmo.

    Tipos de patrones disponibles:
    - brute_force
    - recursive
    - divide_and_conquer
    - dynamic_programming
    - greedy
    - backtracking
    - branch_and_bound
    - sorting
    - searching
    - quantum
    - bio_inspired
    - approximation
    """
    try:
        logger.info(f"Detección específica solicitada: {pattern_type}")

        # Validar pattern_type
        try:
            pattern_enum = PatternType(pattern_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tipo de patrón inválido: {pattern_type}"
            )

        # Parsear código
        parser = PseudocodeParser()
        ast = parser.parse(code)

        # Detectar patrón específico
        detector = PatternDetector()
        match = detector.detect_specific(ast, pattern_enum)

        if not match:
            return BaseResponse(
                success=True,
                message=f"Patrón {pattern_type} no detectado",
                timestamp=None,
            )

        # Convertir a PatternMatch
        pattern_match = PatternMatch(
            pattern_type=match.pattern_type,
            pattern_name=match.pattern_name,
            confidence=match.confidence,
            confidence_level=ConfidenceLevelEnum(match.confidence_level.value),
            indicators_found=[
                PatternIndicator(
                    name=ind.name,
                    description=ind.description,
                    found=ind.found,
                    weight=ind.weight,
                    evidence=ind.evidence,
                    location=ind.location,
                )
                for ind in match.indicators_found
            ],
            indicators_missing=[
                PatternIndicator(
                    name=ind.name,
                    description=ind.description,
                    found=ind.found,
                    weight=ind.weight,
                    evidence=ind.evidence,
                    location=ind.location,
                )
                for ind in match.indicators_missing
            ],
            reasoning=match.reasoning,
            typical_complexity=match.typical_complexity,
            metadata=match.metadata,
        )

        return {
            "success": True,
            "message": f"Patrón {match.pattern_name} detectado con confianza {match.confidence:.2%}",
            "pattern_detected": True,
            "pattern_info": pattern_match.dict(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en detección específica: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "SpecificPatternDetectionError",
                "message": str(e)
            }
        )

@router.get(
    "/available",
    status_code=status.HTTP_200_OK,
    summary="Obtener Patrones Disponibles",
    description="Lista todos los patrones que pueden ser detectados"
)
async def get_available_patterns():
    """
    Retorna lista de todos los patrones algorítmicos detectables.

    Incluye nombre, tipo y descripción de cada patrón.
    """
    try:
        detector = PatternDetector()

        patterns_info = []
        for det in detector.detectors:
            patterns_info.append({
                "type": det.pattern_type.value,
                "name": det.pattern_name,
                "description": det.description,
                "typical_complexity": det.typical_complexity
            })

        return {
            "success": True,
            "patterns": patterns_info,
            "total": len(patterns_info)
        }

    except Exception as e:
        logger.error(f"Error obteniendo patrones disponibles: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "AvailablePatternsError",
                "message": str(e)
            }
        )

@router.get(
    "/types",
    status_code=status.HTTP_200_OK,
    summary="Obtener Tipos de Patrones",
    description="Lista todos los tipos de patrones como enum"
)
async def get_pattern_types():
    """
    Retorna todos los tipos de patrones disponibles.
    
    Útil para saber qué valores usar en detect-specific.
    """
    try:
        return {
            "success": True,
            "pattern_types": [pt.value for pt in PatternType],
            "total": len(PatternType)
        }

    except Exception as e:
        logger.error(f"Error obteniendo tipos de patrones: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )