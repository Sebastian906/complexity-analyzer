"""
API Endpoints - Detección de Estructuras de Datos

Endpoints REST para detectar estructuras de datos en algoritmos.
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.core.parser import PseudocodeParser
from app.core.data_structures import (
    StructureIdentifier,
    StructureType,
    UsageAnalyzer
)
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()

# SCHEMAS - DTOs
class StructureDetectionRequest(BaseModel):
    """Request para detección de estructuras"""
    code: str = Field(..., description="Código del algoritmo en pseudocódigo")
    min_confidence: float = Field(
        0.3,
        ge=0.0,
        le=1.0,
        description="Umbral mínimo de confianza (0.0 - 1.0)"
    )
    analyze_usage: bool = Field(
        True,
        description="Analizar uso de estructuras detectadas"
    )

class OperationComplexityInfo(BaseModel):
    """Información de complejidad de operación"""
    operation: str
    best_case: str
    average_case: str
    worst_case: str
    space: str

class StructureIndicatorInfo(BaseModel):
    """Información de un indicador"""
    name: str
    description: str
    found: bool
    weight: float
    evidence: Optional[str] = None

class StructureInfo(BaseModel):
    """Información de una estructura detectada"""
    structure_type: str
    structure_name: str
    confidence: float
    confidence_level: str
    variables: List[str]

    # Indicadores
    indicators_found: List[StructureIndicatorInfo]
    indicators_missing: List[StructureIndicatorInfo]

    # Operaciones y complejidades
    operations: List[str]
    operation_complexities: List[OperationComplexityInfo]

    # Explicación
    reasoning: str
    properties: dict
    code_evidence: List[str]

class OperationFrequencyInfo(BaseModel):
    """Frecuencia de operación"""
    operation: str
    count: int
    complexity: str
    examples: List[str]

class StructureUsageInfo(BaseModel):
    """Información de uso de estructura"""
    operation_frequencies: List[OperationFrequencyInfo]
    most_frequent_operation: Optional[str]
    access_pattern: str
    complexity_impact: dict
    total_operations: int
    unique_operations: int
    recommendations: List[str]

class StructureDetectionResponse(BaseModel):
    """Response de la detección de estructuras"""
    success: bool
    algorithm_name: str

    # Estructura principal
    primary_structure: Optional[StructureInfo]

    # Uso de estructura principal
    primary_usage: Optional[StructureUsageInfo] = None

    # Todas las estructuras detectadas
    all_structures: List[StructureInfo]

    # Resumen
    summary: str

    # Metadata
    metadata: dict

    message: str

class SpecificStructureRequest(BaseModel):
    """Request para detectar estructura específica"""
    code: str = Field(..., description="Código del algoritmo")
    structure_type: str = Field(
        ...,
        description="Tipo de estructura (array, stack, queue, etc.)"
    )

class SpecificStructureResponse(BaseModel):
    """Response de detección específica"""
    success: bool
    structure_detected: bool
    structure_info: Optional[StructureInfo]
    usage_info: Optional[StructureUsageInfo] = None
    message: str

class AvailableStructuresResponse(BaseModel):
    """Response de estructuras disponibles"""
    success: bool
    structures: List[dict]
    total: int

# ENDPOINTS
@router.post(
    "/detect",
    response_model=StructureDetectionResponse,
    status_code=status.HTTP_200_OK,
    summary="Detectar Estructuras de Datos",
    description="Detecta todas las estructuras de datos presentes en el código"
)
async def detect_structures(request: StructureDetectionRequest):
    """
    Detecta estructuras de datos en pseudocódigo.

    Estructuras detectables:
    - Arrays/Listas
    - Pilas (Stacks)
    - Colas (Queues)
    - Listas Enlazadas
    - Diccionarios/Maps
    - Árboles
    - Grafos
    - Tablas Hash
    """
    try:
        logger.info("Recibida solicitud de detección de estructuras")

        # 1. Parsear el código
        parser = PseudocodeParser()
        ast = parser.parse(request.code)

        logger.info(f"Código parseado: {ast.algorithm.name}")

        # 2. Detectar estructuras
        identifier = StructureIdentifier()
        result = identifier.identify(ast, request.min_confidence)

        logger.info(
            f"Detección completada: {result.structure_count} estructura(s)"
        )

        # 3. Convertir a DTOs

        def _indicator_to_dto(ind) -> StructureIndicatorInfo:
            return StructureIndicatorInfo(
                name=ind.name,
                description=ind.description,
                found=ind.found,
                weight=ind.weight,
                evidence=ind.evidence
            )

        def _complexity_to_dto(comp) -> OperationComplexityInfo:
            return OperationComplexityInfo(
                operation=comp.operation,
                best_case=comp.best_case,
                average_case=comp.average_case,
                worst_case=comp.worst_case,
                space=comp.space
            )

        def _structure_to_dto(struct) -> StructureInfo:
            return StructureInfo(
                structure_type=struct.structure_type.value,
                structure_name=struct.structure_name,
                confidence=struct.confidence,
                confidence_level=struct.confidence_level.value,
                variables=struct.variables,
                indicators_found=[
                    _indicator_to_dto(ind) for ind in struct.indicators_found
                ],
                indicators_missing=[
                    _indicator_to_dto(ind) for ind in struct.indicators_missing
                ],
                operations=struct.operations,
                operation_complexities=[
                    _complexity_to_dto(comp) 
                    for comp in struct.operation_complexities
                ],
                reasoning=struct.reasoning,
                properties=struct.properties,
                code_evidence=struct.code_evidence
            )

        # Convertir estructura principal
        primary_info = None
        if result.primary_structure:
            primary_info = _structure_to_dto(result.primary_structure)

        # Convertir todas las estructuras
        all_structures_info = [
            _structure_to_dto(s) for s in result.structures_found
        ]

        # 4. Analizar uso (opcional)
        primary_usage_info = None
        if request.analyze_usage and result.primary_structure:
            try:
                usage_analyzer = UsageAnalyzer()
                primary_usage = usage_analyzer.analyze(
                    ast,
                    result.primary_structure
                )

                primary_usage_info = StructureUsageInfo(
                    operation_frequencies=[
                        OperationFrequencyInfo(
                            operation=op.operation,
                            count=op.count,
                            complexity=op.complexity,
                            examples=op.examples
                        )
                        for op in primary_usage.operation_frequencies
                    ],
                    most_frequent_operation=primary_usage.most_frequent_operation,
                    access_pattern=primary_usage.access_pattern,
                    complexity_impact=primary_usage.complexity_impact,
                    total_operations=primary_usage.total_operations,
                    unique_operations=primary_usage.unique_operations,
                    recommendations=primary_usage.recommendations
                )
            except Exception as e:
                logger.warning(f"Error analizando uso: {e}")

        return StructureDetectionResponse(
            success=True,
            algorithm_name=ast.algorithm.name,
            primary_structure=primary_info,
            primary_usage=primary_usage_info,
            all_structures=all_structures_info,
            summary=result.summary,
            metadata=result.metadata,
            message="Detección de estructuras completada exitosamente"
        )

    except Exception as e:
        logger.error(f"Error en detección de estructuras: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "StructureDetectionError",
                "message": str(e)
            }
        )

@router.post(
    "/detect-specific",
    response_model=SpecificStructureResponse,
    status_code=status.HTTP_200_OK,
    summary="Detectar Estructura Específica",
    description="Detecta una estructura de datos específica"
)
async def detect_specific_structure(request: SpecificStructureRequest):
    """
    Detecta una estructura específica en el algoritmo.

    Tipos disponibles:
    - array
    - stack
    - queue
    - linked_list
    - dictionary
    - tree
    - graph
    - hash_table
    """
    try:
        logger.info(f"Detección específica: {request.structure_type}")

        # Validar tipo
        try:
            structure_type = StructureType(request.structure_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tipo de estructura inválido: {request.structure_type}"
            )

        # Parsear código
        parser = PseudocodeParser()
        ast = parser.parse(request.code)

        # Detectar específico
        identifier = StructureIdentifier()
        match = identifier.identify_specific(ast, structure_type)

        if not match:
            return SpecificStructureResponse(
                success=True,
                structure_detected=False,
                structure_info=None,
                message=f"Estructura {request.structure_type} no detectada"
            )

        # Convertir a DTO
        def _indicator_to_dto(ind):
            return StructureIndicatorInfo(
                name=ind.name,
                description=ind.description,
                found=ind.found,
                weight=ind.weight,
                evidence=ind.evidence
            )

        def _complexity_to_dto(comp):
            return OperationComplexityInfo(
                operation=comp.operation,
                best_case=comp.best_case,
                average_case=comp.average_case,
                worst_case=comp.worst_case,
                space=comp.space
            )

        structure_info = StructureInfo(
            structure_type=match.structure_type.value,
            structure_name=match.structure_name,
            confidence=match.confidence,
            confidence_level=match.confidence_level.value,
            variables=match.variables,
            indicators_found=[
                _indicator_to_dto(ind) for ind in match.indicators_found
            ],
            indicators_missing=[
                _indicator_to_dto(ind) for ind in match.indicators_missing
            ],
            operations=match.operations,
            operation_complexities=[
                _complexity_to_dto(comp) 
                for comp in match.operation_complexities
            ],
            reasoning=match.reasoning,
            properties=match.properties,
            code_evidence=match.code_evidence
        )

        # Analizar uso
        usage_info = None
        try:
            usage_analyzer = UsageAnalyzer()
            usage = usage_analyzer.analyze(ast, match)

            usage_info = StructureUsageInfo(
                operation_frequencies=[
                    OperationFrequencyInfo(
                        operation=op.operation,
                        count=op.count,
                        complexity=op.complexity,
                        examples=op.examples
                    )
                    for op in usage.operation_frequencies
                ],
                most_frequent_operation=usage.most_frequent_operation,
                access_pattern=usage.access_pattern,
                complexity_impact=usage.complexity_impact,
                total_operations=usage.total_operations,
                unique_operations=usage.unique_operations,
                recommendations=usage.recommendations
            )
        except Exception as e:
            logger.warning(f"Error analizando uso: {e}")

        return SpecificStructureResponse(
            success=True,
            structure_detected=True,
            structure_info=structure_info,
            usage_info=usage_info,
            message=f"Estructura {match.structure_name} detectada con confianza {match.confidence:.2%}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en detección específica: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "SpecificStructureDetectionError",
                "message": str(e)
            }
        )

@router.get(
    "/available",
    response_model=AvailableStructuresResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener Estructuras Disponibles",
    description="Lista todas las estructuras que pueden ser detectadas"
)
async def get_available_structures():
    """
    Retorna lista de todas las estructuras detectables.
    
    Incluye tipo, nombre y descripción de cada estructura.
    """
    try:
        identifier = StructureIdentifier()
        structures = identifier.get_available_structures()

        return AvailableStructuresResponse(
            success=True,
            structures=structures,
            total=len(structures)
        )

    except Exception as e:
        logger.error(f"Error obteniendo estructuras: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "AvailableStructuresError",
                "message": str(e)
            }
        )

@router.get(
    "/types",
    status_code=status.HTTP_200_OK,
    summary="Obtener Tipos de Estructuras",
    description="Lista todos los tipos como enum"
)
async def get_structure_types():
    """
    Retorna todos los tipos de estructuras disponibles.

    Útil para saber qué valores usar en detect-specific.
    """
    try:
        return {
            "success": True,
            "structure_types": [st.value for st in StructureType],
            "total": len(StructureType)
        }

    except Exception as e:
        logger.error(f"Error obteniendo tipos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )