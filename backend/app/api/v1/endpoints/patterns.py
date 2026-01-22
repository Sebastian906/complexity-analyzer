"""
API Endpoints - Detección de Patrones

Endpoints REST para detectar patrones algorítmicos en pseudocódigo.
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, status
from app.schemas import (
    PatternDetectionRequest,
    PatternDetectionResult,
    PatternMatch,
    ScoredPattern,
    PatternIndicator,
    PatternStatistics,
    PatternType,
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
        logger.info(f"Detección completada: {result.pattern_count} patrones encontrados")

        # 3. Convertir correctamente a schemas Pydantic
        def convert_scored_pattern(scored_pattern) -> tuple[PatternMatch, ScoredPattern]:
            """
            Convierte un ScoredPattern interno a los schemas Pydantic.
            
            IMPORTANTE: El ScoredPattern interno puede tener diferentes atributos
            que el schema Pydantic. Usamos getattr con defaults seguros.
            """
            pattern = scored_pattern.pattern
            
            # Crear PatternMatch desde el pattern interno
            pattern_match = PatternMatch(
                pattern_type=pattern.pattern_type,
                pattern_name=pattern.pattern_name,
                confidence=pattern.confidence,
                confidence_level=ConfidenceLevelEnum(pattern.confidence_level.value),
                indicators_found=[
                    PatternIndicator(
                        name=ind.name,
                        description=ind.description,
                        found=ind.found,
                        weight=ind.weight,
                        evidence=getattr(ind, 'evidence', None) or "",
                        location=getattr(ind, 'location', None) or "",
                    )
                    for ind in pattern.indicators_found
                ],
                indicators_missing=[
                    PatternIndicator(
                        name=ind.name,
                        description=ind.description,
                        found=ind.found,
                        weight=ind.weight,
                        evidence=getattr(ind, 'evidence', None) or "",
                        location=getattr(ind, 'location', None) or "",
                    )
                    for ind in pattern.indicators_missing
                ],
                reasoning=pattern.reasoning,
                typical_complexity=getattr(pattern, 'typical_complexity', None),
                metadata=getattr(pattern, 'metadata', None) or {},
            )
            
            # El ScoredPattern interno puede no tener todos estos atributos
            # Usar getattr con defaults basados en confidence
            confidence = pattern.confidence
            
            scored = ScoredPattern(
                pattern=pattern_match,
                raw_score=getattr(scored_pattern, 'raw_score', confidence),
                adjusted_score=getattr(scored_pattern, 'adjusted_score', confidence),
                final_score=getattr(scored_pattern, 'final_score', confidence),
                confidence_bonus=getattr(scored_pattern, 'confidence_bonus', 0.0),
                missing_penalty=getattr(scored_pattern, 'missing_penalty', 0.0),
                conflict_penalty=getattr(scored_pattern, 'conflict_penalty', 0.0),
                conflicts=getattr(scored_pattern, 'conflicts', None) or [],
                rank=getattr(scored_pattern, 'rank', None),
            )
            
            return pattern_match, scored
        
        # 4. Convertir todos los patrones
        patterns_found = []
        scored_patterns = []
        
        for sp in result.all_patterns:
            pattern_match, scored_pattern = convert_scored_pattern(sp)
            patterns_found.append(pattern_match)
            scored_patterns.append(scored_pattern)
        
        # 5. Patrón primario
        primary_pattern = None
        if result.primary_pattern:
            _, primary_pattern = convert_scored_pattern(result.primary_pattern)
        
        # 6. Patrones confiables
        confident_patterns = []
        for sp in result.confident_patterns:
            _, scored = convert_scored_pattern(sp)
            confident_patterns.append(scored)
        
        # 7. Estadísticas
        statistics = PatternStatistics(
            total_patterns_detected=result.pattern_count,
            high_confidence_patterns=result.high_confidence_count,
            medium_confidence_patterns=len([
                p for p in patterns_found 
                if p.confidence_level == ConfidenceLevelEnum.MEDIUM
            ]),
            low_confidence_patterns=len([
                p for p in patterns_found 
                if p.confidence_level == ConfidenceLevelEnum.LOW
            ]),
            pattern_types_found=[p.pattern_type for p in patterns_found],
            most_confident_pattern=result.primary_pattern_name if result.primary_pattern else None,
            average_confidence=(
                sum(p.confidence for p in patterns_found) / len(patterns_found) 
                if patterns_found else 0.0
            ),
        )
        
        # 8. IMPORTANTE: Retornar usando model_validate para manejar propiedades computadas
        return PatternDetectionResult(
            patterns_found=patterns_found,
            scored_patterns=scored_patterns,
            primary_pattern=primary_pattern,
            primary_pattern_name=result.primary_pattern_name,
            confident_patterns=confident_patterns,
            pattern_count=result.pattern_count,
            high_confidence_count=result.high_confidence_count,
            summary=result.summary,
            statistics=statistics,
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
                    evidence=ind.evidence or "",
                    location=ind.location or "",
                )
                for ind in match.indicators_found
            ],
            indicators_missing=[
                PatternIndicator(
                    name=ind.name,
                    description=ind.description,
                    found=ind.found,
                    weight=ind.weight,
                    evidence=ind.evidence or "",
                    location=ind.location or "",
                )
                for ind in match.indicators_missing
            ],
            reasoning=match.reasoning,
            typical_complexity=match.typical_complexity,
            metadata=match.metadata or {},
        )

        return {
            "success": True,
            "message": f"Patrón {match.pattern_name} detectado con confianza {match.confidence:.2%}",
            "pattern_detected": True,
            "pattern_info": pattern_match.model_dump(),
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
            "message": "Patrones disponibles",
            "timestamp": None,
            "data": patterns_info,
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