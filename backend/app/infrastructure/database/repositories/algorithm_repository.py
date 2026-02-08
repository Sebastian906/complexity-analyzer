from typing import Optional, List, Dict, Any
from datetime import datetime
import traceback

from app.infrastructure.database.repositories.base_repository import BaseRepository
from app.infrastructure.database.models.mongo import Algorithm
from app.utils.logger import get_logger

logger = get_logger(__name__)

class AlgorithmRepository(BaseRepository[Algorithm]):
    """Repositorio para Algoritmos (MongoDB)"""

    async def create(self, entity: Algorithm) -> Algorithm:
        """Crear algoritmo"""
        try:
            await entity.insert()
            logger.info(f"Algoritmo creado: {entity.id}")
            return entity
        except Exception as e:
            # Log detallado para debugging
            logger.error(f"Error creando algoritmo: {type(e).__name__}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    async def get_by_id(self, id: str) -> Optional[Algorithm]:
        """Obtener algoritmo por ID"""
        try:
            return await Algorithm.get(id)
        except Exception:
            return None

    async def get_by_name(self, name: str) -> Optional[Algorithm]:
        """Obtener algoritmo por nombre"""
        return await Algorithm.find_one(Algorithm.name == name)

    async def update(self, id: str, data: Dict[str, Any]) -> Optional[Algorithm]:
        """Actualizar algoritmo"""
        algorithm = await self.get_by_id(id)
        if not algorithm:
            return None

        data["updated_at"] = datetime.utcnow()
        await algorithm.set(data)
        return algorithm

    async def delete(self, id: str) -> bool:
        """Eliminar algoritmo"""
        algorithm = await self.get_by_id(id)
        if not algorithm:
            return False

        await algorithm.delete()
        return True

    async def list(self, skip: int = 0, limit: int = 100) -> List[Algorithm]:
        """Listar algoritmos"""
        return await Algorithm.find_all().skip(skip).limit(limit).to_list()

    async def search_by_category(self, category: str) -> List[Algorithm]:
        """Buscar por categoría"""
        return await Algorithm.find(Algorithm.category == category).to_list()

    async def search_by_tags(self, tags: List[str]) -> List[Algorithm]:
        """Buscar por tags"""
        return await Algorithm.find({"tags": {"$in": tags}}).to_list()
    
    async def find(
        self,
        filter_dict: dict,
        skip: int = 0,
        limit: int = 100
    ) -> List[Algorithm]:
        """
        Busca algoritmos con filtros y paginación.
        
        Args:
            filter_dict: Filtros MongoDB
            skip: Número de documentos a saltar
            limit: Número máximo de documentos a retornar
            
        Returns:
            Lista de modelos Algorithm
        """
        try:
            query = Algorithm.find(filter_dict)
            query = query.skip(skip).limit(limit)
            results = await query.to_list()
            return results
        except Exception as e:
            logger.error(f"Error en find: {e}")
            return []
    
    async def count(self, filter_dict: dict) -> int:
        """
        Cuenta documentos que coinciden con el filtro.
        
        Args:
            filter_dict: Filtros MongoDB
            
        Returns:
            Número de documentos
        """
        try:
            count = await Algorithm.find(filter_dict).count()
            return count
        except Exception as e:
            logger.error(f"Error en count: {e}")
            return 0