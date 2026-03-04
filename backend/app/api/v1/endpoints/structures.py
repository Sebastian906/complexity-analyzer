"""
API Endpoints - Detección de Estructuras de Datos

Endpoints REST para detectar estructuras de datos en algoritmos.
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, status, Body
from pydantic import BaseModel, Field
from app.schemas import (
    # Structure Request Schemas
    StructureDetectionRequest,
    StructureDetectionOptions,
    
    # Structure Result Schemas
    StructureDetectionResult,
    StructureMatch,
    StructureUsage,
    
    # Common
    BaseResponse,
    ConfidenceLevelEnum,
)

from app.core.parser import PseudocodeParser
from app.core.data_structures import (
    StructureIdentifier,
    StructureType,
    UsageAnalyzer
)
from app.utils.logger import setup_logger
from app.services.cache_service import CacheKey, generate_cache_key, get_cache_service
from app.core.config import settings

logger = setup_logger(__name__)

router = APIRouter()

# Schema para detección de estructura específica
class DetectSpecificStructureInput(BaseModel):
    """Schema para recibir código y tipo de estructura en el body JSON"""
    code: str = Field(
        ...,
        min_length=1,
        description=(
            "Código del algoritmo a analizar (multilínea). "
            "En JSON, los saltos de línea se representan con \\n. "
            "Ejemplo: \"algorithm test(n)\\nbegin\\n    x ← 1\\nend\""
        )
    )
    structure_type: str = Field(..., description="Tipo de estructura a detectar")
    analyze_usage: bool = Field(True, description="Analizar uso de la estructura")
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": "algorithm bubbleSort(A[n])\nbegin\n    for i ← 1 to n-1 do\n    begin\n        for j ← 1 to n-i do\n        begin\n            if A[j] > A[j+1] then\n            begin\n                temp ← A[j]\n                A[j] ← A[j+1]\n                A[j+1] ← temp\n            end\n        end\n    end\nend",
                "structure_type": "array",
                "analyze_usage": True
            }
        }

@router.post(
    "/detect",
    response_model=StructureDetectionResult,
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
        # Cache: verificar caché
        _cache = get_cache_service()
        _cache_key = generate_cache_key(
            CacheKey.STRUCTURE,
            request.code,
            min_confidence=request.options.min_confidence,
            analyze_usage=request.options.analyze_usage,
        )
        _cached = await _cache.get(_cache_key)
        if _cached is not None:
            logger.info("Cache HIT para detección de estructuras")
            return _cached

        logger.info("Recibida solicitud de detección de estructuras")

        # 1. Parsear el código
        parser = PseudocodeParser()
        ast = parser.parse(request.code)

        logger.info(f"Código parseado: {ast.algorithm.name}")

        # 2. Detectar estructuras
        identifier = StructureIdentifier()
        result = identifier.identify(ast, request.options.min_confidence)

        logger.info(
            f"Detección completada: {result.structure_count} estructura(s)"
        )

        # 3. Convertir a schemas Pydantic
        
        # Convertir structures_found
        structures_found = [
            StructureMatch(
                structure_type=s.structure_type.value,
                structure_name=s.structure_name,
                confidence=s.confidence,
                confidence_level=ConfidenceLevelEnum(s.confidence_level.value),
                variables=s.variables,
                operations=s.operations,
                reasoning=s.reasoning,
            )
            for s in result.structures_found
        ]
        
        # Estructura primaria
        primary_structure = None
        if result.primary_structure:
            s = result.primary_structure
            primary_structure = StructureMatch(
                structure_type=s.structure_type.value,
                structure_name=s.structure_name,
                confidence=s.confidence,
                confidence_level=ConfidenceLevelEnum(s.confidence_level.value),
                variables=s.variables,
                operations=s.operations,
                reasoning=s.reasoning,
            )
        
        # 4. Analizar uso (opcional)
        primary_usage = None
        if request.options.analyze_usage and result.primary_structure:
            try:
                usage_analyzer = UsageAnalyzer()
                usage = usage_analyzer.analyze(ast, result.primary_structure)

                primary_usage = StructureUsage(
                    operation_frequencies=[
                        {
                            "operation": op.operation,
                            "count": op.count,
                            "complexity": op.complexity,
                            "examples": op.examples,
                        }
                        for op in usage.operation_frequencies
                    ],
                    most_frequent_operation=usage.most_frequent_operation,
                    access_pattern=usage.access_pattern,
                    complexity_impact={},  # Mapear si está disponible
                    total_operations=usage.total_operations,
                    unique_operations=usage.unique_operations,
                    recommendations=usage.recommendations,
                )
            except Exception as e:
                logger.warning(f"Error analizando uso: {e}")

        _result = StructureDetectionResult(
            structures_found=structures_found,
            primary_structure=primary_structure,
            primary_usage=primary_usage,
            summary=result.summary,
        )

        # Cache: almacenar resultado
        await _cache.set(_cache_key, _result, ttl=settings.CACHE_TTL_ANALYSIS)

        return _result

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
    response_model=BaseResponse,
    status_code=status.HTTP_200_OK,
    summary="Detectar Estructura Específica",
    description="Detecta una estructura de datos específica"
)
async def detect_specific_structure(
    body: DetectSpecificStructureInput = Body(..., description="Código y tipo de estructura en JSON")
):
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
        code = body.code
        structure_type = body.structure_type
        analyze_usage = body.analyze_usage
        logger.info(f"Detección específica: {structure_type}")

        # Validar tipo
        try:
            structure_enum = StructureType(structure_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tipo de estructura inválido: {structure_type}"
            )

        # Parsear código
        parser = PseudocodeParser()
        ast = parser.parse(code)

        # Detectar específico
        identifier = StructureIdentifier()
        match = identifier.identify_specific(ast, structure_enum)

        if not match:
            return BaseResponse(
                success=True,
                message=f"Estructura {structure_type} no detectada",
                timestamp=None,
            )

        # Convertir a StructureMatch
        structure_match = StructureMatch(
            structure_type=match.structure_type.value,
            structure_name=match.structure_name,
            confidence=match.confidence,
            confidence_level=ConfidenceLevelEnum(match.confidence_level.value),
            variables=match.variables,
            operations=match.operations,
            reasoning=match.reasoning,
        )

        # Analizar uso
        usage_info = None
        if analyze_usage:
            try:
                usage_analyzer = UsageAnalyzer()
                usage = usage_analyzer.analyze(ast, match)

                usage_info = StructureUsage(
                    operation_frequencies=[
                        {
                            "operation": op.operation,
                            "count": op.count,
                            "complexity": op.complexity,
                            "examples": op.examples,
                        }
                        for op in usage.operation_frequencies
                    ],
                    most_frequent_operation=usage.most_frequent_operation,
                    access_pattern=usage.access_pattern,
                    complexity_impact={},
                    total_operations=usage.total_operations,
                    unique_operations=usage.unique_operations,
                    recommendations=usage.recommendations,
                )
            except Exception as e:
                logger.warning(f"Error analizando uso: {e}")

        return {
            "success": True,
            "message": f"Estructura {match.structure_name} detectada con confianza {match.confidence:.2%}",
            "structure_detected": True,
            "structure_info": structure_match.model_dump(),
            "usage_info": usage_info.model_dump() if usage_info else None,
        }

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

        return {
            "success": True,
            "message": "Estructuras disponibles",
            "timestamp": None,
            "data": structures,
            "total": len(structures)
        }

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