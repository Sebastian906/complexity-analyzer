"""
API Endpoints - Algorithms CRUD

Endpoints REST para operaciones CRUD de algoritmos.
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, status, Depends

from app.schemas import (
    AlgorithmCreate,
    AlgorithmUpdate,
    Algorithm,
    AlgorithmResponse,
    AlgorithmListResponse,
    AlgorithmMetadata,
    AlgorithmSearchCriteria,
)
from app.services import AlgorithmService
from app.utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()

_service_instance = None

async def get_algorithm_service() -> AlgorithmService:
    """
    Dependency para obtener instancia del AlgorithmService.
    
    Inicializa la conexión a MongoDB la primera vez.
    """
    global _service_instance
    
    if _service_instance is None:
        _service_instance = AlgorithmService()
        # INICIALIZAR CONEXIÓN A MONGODB
        await _service_instance.initialize()
        logger.info("AlgorithmService inicializado con MongoDB")
    
    return _service_instance

@router.post(
    "",
    response_model=AlgorithmResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear Algoritmo",
    description="Crea y almacena un nuevo algoritmo en MongoDB"
)
async def create_algorithm(
    request: AlgorithmCreate,
    service: AlgorithmService = Depends(get_algorithm_service)
):
    """Crea un nuevo algoritmo"""
    try:
        result = await service.create(request)
        return result
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
    description="Obtiene un algoritmo por ID desde MongoDB"
)
async def get_algorithm(
    algorithm_id: str,
    service: AlgorithmService = Depends(get_algorithm_service)
):
    """Obtiene un algoritmo específico"""
    result = await service.get(algorithm_id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Algoritmo no encontrado: {algorithm_id}"
        )
    
    return result

@router.put(
    "/{algorithm_id}",
    response_model=AlgorithmResponse,
    summary="Actualizar Algoritmo",
    description="Actualiza un algoritmo existente en MongoDB"
)
async def update_algorithm(
    algorithm_id: str,
    request: AlgorithmUpdate,
    service: AlgorithmService = Depends(get_algorithm_service)
):
    """Actualiza un algoritmo"""
    result = await service.update(algorithm_id, request)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Algoritmo no encontrado: {algorithm_id}"
        )
    
    return result

@router.delete(
    "/{algorithm_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar Algoritmo",
    description="Elimina un algoritmo de MongoDB"
)
async def delete_algorithm(
    algorithm_id: str,
    service: AlgorithmService = Depends(get_algorithm_service)
):
    """Elimina un algoritmo"""
    deleted = await service.delete(algorithm_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Algoritmo no encontrado: {algorithm_id}"
        )

@router.get(
    "",
    response_model=AlgorithmListResponse,
    summary="Listar Algoritmos",
    description="Lista algoritmos desde MongoDB con filtros y paginación"
)
async def list_algorithms(
    category: Optional[str] = Query(None, description="Filtrar por categoría"),
    tags: Optional[List[str]] = Query(None, description="Filtrar por tags"),
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(10, ge=1, le=100, description="Elementos por página"),
    service: AlgorithmService = Depends(get_algorithm_service)
):
    """Lista algoritmos con filtros y paginación"""
    from app.schemas.algorithm import AlgorithmCategory
    
    # Construir criterios de búsqueda SIN limit/offset
    criteria = AlgorithmSearchCriteria(
        category=AlgorithmCategory(category) if category else None,
        tags=tags,
    )
    
    # Pasar paginación por separado al service
    return await service.search(criteria, page=page, page_size=page_size)

@router.post(
    "/search",
    response_model=AlgorithmListResponse,
    summary="Buscar Algoritmos",
    description="Busca algoritmos en MongoDB con criterios avanzados"
)
async def search_algorithms(
    criteria: AlgorithmSearchCriteria,
    service: AlgorithmService = Depends(get_algorithm_service)
):
    """Busca algoritmos con criterios avanzados"""
    return await service.search(criteria)

@router.get(
    "/statistics",
    summary="Obtener Estadísticas",
    description="Obtiene estadísticas de algoritmos almacenados en MongoDB"
)
async def get_statistics(
    service: AlgorithmService = Depends(get_algorithm_service)
):
    """Obtiene estadísticas de algoritmos"""
    return await service.get_statistics()