from typing import Generic, TypeVar, Optional, List, Dict, Any
from abc import ABC, abstractmethod

T = TypeVar('T')

class BaseRepository(ABC, Generic[T]):
    """Repositorio base abstracto"""

    @abstractmethod
    async def create(self, entity: T) -> T:
        """Crear entidad"""
        pass

    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[T]:
        """Obtener por ID"""
        pass

    @abstractmethod
    async def update(self, id: str, data: Dict[str, Any]) -> Optional[T]:
        """Actualizar entidad"""
        pass

    @abstractmethod
    async def delete(self, id: str) -> bool:
        """Eliminar entidad"""
        pass

    @abstractmethod
    async def list(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Listar entidades"""
        pass