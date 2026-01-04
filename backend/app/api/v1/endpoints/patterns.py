"""
API Endpoints - Detección de Patrones

Endpoints REST para detectar patrones algorítmicos en pseudocódigo.
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.core.parser import PseudocodeParser
from app.core.patterns import PatternDetector, PatternType
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()

class PatternDetectionRequest(BaseModel):
    """Request para detección de patrones"""
    code: str = Field(..., description="Código del algoritmo en pseudocódigo")
    min_confidence: float = Field(
        0.3,
        ge=0.0,
        le=1.0,
        description="Umbral mínimo de confianza (0.0 - 1.0)"
    )
    detect_specific: Optional[str] = Field(
        None,
        description="Detectar patrón específico (opcional)"
    )

class IndicatorInfo(BaseModel):
    """Información de un indicador"""
    name: str
    description: str
    found: bool
    weight: float
    evidence: Optional[str] = None

class PatternInfo(BaseModel):
    """Información de un patrón detectado"""
    pattern_type: str
    pattern_name: str
    confidence: float
    confidence_level: str
    typical_complexity: Optional[str]
    reasoning: str
    indicators_found: List[IndicatorInfo]
    indicators_missing: List[IndicatorInfo]
    rank: int
    is_primary: bool
    final_score: float
    conflicts: List[str]

class PatternDetectionResponse(BaseModel):
    """Response de la detección de patrones"""
    success: bool
    algorithm_name: str

    # Patrón principal
    primary_pattern: Optional[PatternInfo]

    # Todos los patrones detectados
    all_patterns: List[PatternInfo]

    # Solo patrones con confianza suficiente
    confident_patterns: List[PatternInfo]

    # Resumen
    summary: str

    # Metadata
    metadata: dict

    message: str

class AvailablePatternsResponse(BaseModel):
    """Response de patrones disponibles"""
    success: bool
    patterns: List[dict]
    total: int

class SpecificPatternRequest(BaseModel):
    """Request para detectar patrón específico"""
    code: str = Field(..., description="Código del algoritmo")
    pattern_type: str = Field(..., description="Tipo de patrón (ej: 'divide_and_conquer')")

class SpecificPatternResponse(BaseModel):
    """Response de detección específica"""
    success: bool
    pattern_detected: bool
    pattern_info: Optional[PatternInfo]
    message: str


@router.post(
    "/detect",
    response_model=PatternDetectionResponse,
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
        result = detector.detect(ast, request.min_confidence)

        logger.info(
            f"Detección completada: {result.pattern_count} patrones encontrados"
        )

        # 3. Construir respuesta

        # Función helper para convertir indicador
        def _indicator_to_dict(ind) -> IndicatorInfo:
            return IndicatorInfo(
                name=ind.name,
                description=ind.description,
                found=ind.found,
                weight=ind.weight,
                evidence=ind.evidence
            )

        # Función helper para convertir patrón
        def _pattern_to_dict(scored_pattern) -> PatternInfo:
            pattern = scored_pattern.pattern
            return PatternInfo(
                pattern_type=pattern.pattern_type.value,
                pattern_name=pattern.pattern_name,
                confidence=pattern.confidence,
                confidence_level=pattern.confidence_level.value,
                typical_complexity=pattern.typical_complexity,
                reasoning=pattern.reasoning,
                indicators_found=[
                    _indicator_to_dict(ind) for ind in pattern.indicators_found
                ],
                indicators_missing=[
                    _indicator_to_dict(ind) for ind in pattern.indicators_missing
                ],
                rank=scored_pattern.rank,
                is_primary=scored_pattern.is_primary,
                final_score=scored_pattern.final_score,
                conflicts=scored_pattern.conflicts
            )

        # Convertir patrón primario
        primary_info = None
        if result.primary_pattern:
            primary_info = _pattern_to_dict(result.primary_pattern)

        # Convertir todos los patrones
        all_patterns_info = [
            _pattern_to_dict(p) for p in result.all_patterns
        ]

        # Convertir patrones confiables
        confident_info = [
            _pattern_to_dict(p) for p in result.confident_patterns
        ]

        return PatternDetectionResponse(
            success=True,
            algorithm_name=ast.algorithm.name,
            primary_pattern=primary_info,
            all_patterns=all_patterns_info,
            confident_patterns=confident_info,
            summary=result.summary,
            metadata=result.metadata,
            message="Detección de patrones completada exitosamente"
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
    response_model=SpecificPatternResponse,
    status_code=status.HTTP_200_OK,
    summary="Detectar Patrón Específico",
    description="Detecta un patrón algorítmico específico"
)
async def detect_specific_pattern(request: SpecificPatternRequest):
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
        logger.info(f"Detección específica solicitada: {request.pattern_type}")

        # Validar pattern_type
        try:
            pattern_type = PatternType(request.pattern_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tipo de patrón inválido: {request.pattern_type}"
            )

        # Parsear código
        parser = PseudocodeParser()
        ast = parser.parse(request.code)

        # Detectar patrón específico
        detector = PatternDetector()
        match = detector.detect_specific(ast, pattern_type)

        if not match:
            return SpecificPatternResponse(
                success=True,
                pattern_detected=False,
                pattern_info=None,
                message=f"Patrón {request.pattern_type} no detectado"
            )

        # Convertir a PatternInfo
        def _indicator_to_dict(ind) -> IndicatorInfo:
            return IndicatorInfo(
                name=ind.name,
                description=ind.description,
                found=ind.found,
                weight=ind.weight,
                evidence=ind.evidence
            )

        pattern_info = PatternInfo(
            pattern_type=match.pattern_type.value,
            pattern_name=match.pattern_name,
            confidence=match.confidence,
            confidence_level=match.confidence_level.value,
            typical_complexity=match.typical_complexity,
            reasoning=match.reasoning,
            indicators_found=[
                _indicator_to_dict(ind) for ind in match.indicators_found
            ],
            indicators_missing=[
                _indicator_to_dict(ind) for ind in match.indicators_missing
            ],
            rank=1,
            is_primary=True,
            final_score=match.confidence,
            conflicts=[]
        )

        return SpecificPatternResponse(
            success=True,
            pattern_detected=True,
            pattern_info=pattern_info,
            message=f"Patrón {match.pattern_name} detectado con confianza {match.confidence:.2%}"
        )

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
    response_model=AvailablePatternsResponse,
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

        return AvailablePatternsResponse(
            success=True,
            patterns=patterns_info,
            total=len(patterns_info)
        )

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