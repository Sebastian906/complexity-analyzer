"""
API Endpoints - Algorithms CRUD

Endpoints REST para operaciones CRUD de algoritmos.
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, status

from app.schemas import (
    AlgorithmCreate,
    AlgorithmUpdate,
    Algorithm,
    AlgorithmResponse,
    AlgorithmListResponse,
    AlgorithmMetadata,
    BaseResponse,
)
from app.services import AlgorithmService
from app.utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()

# Instancia del servicio
algorithm_service = AlgorithmService()

@router.post(
    "",
    response_model=AlgorithmResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear Algoritmo",
    description="Crea y almacena un nuevo algoritmo"
)
async def create_algorithm(request: AlgorithmCreate):
    """Crea un nuevo algoritmo"""
    try:
        result = await algorithm_service.create(request)
        
        algorithm_obj = Algorithm(
            id=result.metadata.id,
            name=result.metadata.name,
            description=result.metadata.description,
            category=result.metadata.category,
            tags=result.metadata.tags,
            language="pseudocode",
            code=result.code,
            info=None,
            created_at=result.metadata.created_at,
            updated_at=result.metadata.updated_at,
            analyzed=False,
            analysis_count=0,
            complexity_class=None,
            big_o=None,
        )
        
        return {
            "success": True,
            "message": "Algoritmo creado exitosamente",
            "timestamp": None,
                "data": algorithm_obj.model_dump(),
            "algorithm": algorithm_obj,
        }
    except Exception as e:
        logger.error(f"Error creando algoritmo: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get(
    "/{algorithm_id}",
    response_model=AlgorithmResponse,
    summary="Obtener Algoritmo",
    description="Obtiene un algoritmo por ID"
)
async def get_algorithm(algorithm_id: str):
    """Obtiene un algoritmo específico"""
    result = await algorithm_service.get(algorithm_id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Algoritmo no encontrado: {algorithm_id}"
        )
    
    algorithm_obj = Algorithm(
        id=result.metadata.id,
        name=result.metadata.name,
        description=result.metadata.description,
        category=result.metadata.category,
        tags=result.metadata.tags,
        language="pseudocode",
        code=result.code,
        info=None,
        created_at=result.metadata.created_at,
        updated_at=result.metadata.updated_at,
        analyzed=result.metadata.analysis_count > 0,
        analysis_count=result.metadata.analysis_count,
        complexity_class=None,
        big_o=None,
    )
    
    return {
        "success": True,
        "message": "Algoritmo recuperado exitosamente",
        "timestamp": None,
        "data": algorithm_obj.model_dump(),
        "algorithm": algorithm_obj,
    }

@router.put(
    "/{algorithm_id}",
    response_model=AlgorithmResponse,
    summary="Actualizar Algoritmo"
)
async def update_algorithm(algorithm_id: str, request: AlgorithmUpdate):
    """Actualiza un algoritmo"""
    result = await algorithm_service.update(algorithm_id, request)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Algoritmo no encontrado: {algorithm_id}"
        )
    
    algorithm_obj = Algorithm(
        id=result.metadata.id,
        name=result.metadata.name,
        description=result.metadata.description,
        category=result.metadata.category,
        tags=result.metadata.tags,
        language="pseudocode",
        code=result.code,
        info=None,
        created_at=result.metadata.created_at,
        updated_at=result.metadata.updated_at,
        analyzed=result.metadata.analysis_count > 0,
        analysis_count=result.metadata.analysis_count,
        complexity_class=None,
        big_o=None,
    )
    
    return {
        "success": True,
        "message": "Algoritmo actualizado exitosamente",
        "timestamp": None,
        "data": algorithm_obj.model_dump(),
        "algorithm": algorithm_obj,
    }

@router.delete(
    "/{algorithm_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar Algoritmo"
)
async def delete_algorithm(algorithm_id: str):
    """Elimina un algoritmo"""
    deleted = await algorithm_service.delete(algorithm_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Algoritmo no encontrado: {algorithm_id}"
        )

@router.get(
    "",
    response_model=AlgorithmListResponse,
    summary="Listar Algoritmos"
)
async def list_algorithms(
    category: Optional[str] = Query(None),
    tags: Optional[List[str]] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):
    """Lista algoritmos con filtros y paginación"""
    from app.services.algorithm_service import AlgorithmSearchCriteria as InternalCriteria
    
    criteria = InternalCriteria(
        category=category,
        tags=tags,
        limit=page_size,
        offset=(page - 1) * page_size
    )
    
    results = await algorithm_service.search(criteria)
    
    metadata_list = [
        AlgorithmMetadata(
            id=r.id,
            name=r.name,
            category=r.category,
            tags=r.tags,
            complexity_class=None,
            big_o=None,
            created_at=r.created_at,
            analyzed=r.analysis_count > 0,
        )
        for r in results
    ]
    
    total = len(results)
    total_pages = (total + page_size - 1) // page_size
    
    return AlgorithmListResponse(
        success=True,
        message="Algoritmos listados exitosamente",
        timestamp=None,
        algorithms=metadata_list,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )