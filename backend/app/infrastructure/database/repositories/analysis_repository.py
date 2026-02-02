"""
Analysis Repository - MongoDB

Repositorio para gestionar resultados de análisis de algoritmos en MongoDB.
Proporciona operaciones CRUD y queries especializadas para análisis.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from beanie import PydanticObjectId

from app.infrastructure.database.repositories.base_repository import BaseRepository
from app.infrastructure.database.models.mongo import AnalysisResult, Algorithm
from app.utils.logger import get_logger

logger = get_logger(__name__)

class AnalysisRepository(BaseRepository[AnalysisResult]):
    """
    Repositorio para resultados de análisis (MongoDB).
    
    Gestiona operaciones CRUD y queries especializadas para
    resultados de análisis de complejidad algorítmica.
    """
    
    async def create(self, entity: AnalysisResult) -> AnalysisResult:
        """
        Crear un nuevo resultado de análisis.
        
        Args:
            entity: AnalysisResult a crear
        
        Returns:
            AnalysisResult: Entidad creada con ID
        
        Example:
            >>> repo = AnalysisRepository()
            >>> analysis = AnalysisResult(
            ...     algorithm=algorithm_link,
            ...     big_o="O(n log n)",
            ...     omega="Ω(n log n)",
            ...     theta="Θ(n log n)"
            ... )
            >>> created = await repo.create(analysis)
        """
        try:
            await entity.insert()
            # El algoritmo puede ser un Link o un Document directamente
            algo_id = getattr(entity.algorithm, 'ref', entity.algorithm).id if hasattr(entity.algorithm, 'ref') or hasattr(entity.algorithm, 'id') else "unknown"
            logger.info(f"Análisis creado: {entity.id} para algoritmo {algo_id}")
            return entity
        except Exception as e:
            logger.error(f"Error creando análisis: {e}")
            raise
    
    async def get_by_id(self, id: str) -> Optional[AnalysisResult]:
        """
        Obtener análisis por ID.
        
        Args:
            id: ID del análisis
        
        Returns:
            AnalysisResult o None si no existe
        """
        try:
            return await AnalysisResult.get(id)
        except Exception as e:
            logger.error(f"Error obteniendo análisis {id}: {e}")
            return None
    
    async def update(self, id: str, data: Dict[str, Any]) -> Optional[AnalysisResult]:
        """
        Actualizar un análisis.
        
        Args:
            id: ID del análisis
            data: Datos a actualizar
        
        Returns:
            AnalysisResult actualizado o None
        """
        try:
            analysis = await self.get_by_id(id)
            if not analysis:
                return None
            
            await analysis.set(data)
            logger.info(f"Análisis {id} actualizado")
            return analysis
        except Exception as e:
            logger.error(f"Error actualizando análisis {id}: {e}")
            raise
    
    async def delete(self, id: str) -> bool:
        """
        Eliminar un análisis.
        
        Args:
            id: ID del análisis
        
        Returns:
            bool: True si se eliminó
        """
        try:
            analysis = await self.get_by_id(id)
            if not analysis:
                return False
            
            await analysis.delete()
            logger.info(f"Análisis {id} eliminado")
            return True
        except Exception as e:
            logger.error(f"Error eliminando análisis {id}: {e}")
            return False
    
    async def list(self, skip: int = 0, limit: int = 100) -> List[AnalysisResult]:
        """
        Listar análisis con paginación.
        
        Args:
            skip: Número de registros a saltar
            limit: Número máximo de registros
        
        Returns:
            List[AnalysisResult]: Lista de análisis
        """
        try:
            return await AnalysisResult.find_all().skip(skip).limit(limit).to_list()
        except Exception as e:
            logger.error(f"Error listando análisis: {e}")
            return []
    
    # QUERIES ESPECIALIZADAS
    async def get_by_algorithm_id(
        self,
        algorithm_id: str
    ) -> List[AnalysisResult]:
        """
        Obtener todos los análisis de un algoritmo.
        
        Args:
            algorithm_id: ID del algoritmo
        
        Returns:
            List[AnalysisResult]: Análisis del algoritmo
        """
        try:
            # Convertir a ObjectId
            algo_id = PydanticObjectId(algorithm_id)
            
            # Usar sintaxis de MongoDB para campos Link: algorithm.$id
            return await AnalysisResult.find(
                {"algorithm.$id": algo_id}
            ).to_list()
        except Exception as e:
            logger.error(f"Error obteniendo análisis de algoritmo {algorithm_id}: {e}")
            return []
    
    async def get_latest_by_algorithm(
        self,
        algorithm_id: str
    ) -> Optional[AnalysisResult]:
        """
        Obtener el análisis más reciente de un algoritmo.
        
        Args:
            algorithm_id: ID del algoritmo
        
        Returns:
            AnalysisResult o None
        """
        try:
            algo_id = PydanticObjectId(algorithm_id)
            
            # Usar sintaxis de MongoDB para campos Link: algorithm.$id
            return await AnalysisResult.find(
                {"algorithm.$id": algo_id}
            ).sort(-AnalysisResult.created_at).first_or_none()
        except Exception as e:
            logger.error(f"Error obteniendo último análisis: {e}")
            return None
    
    async def search_by_complexity(
        self,
        big_o: Optional[str] = None,
        omega: Optional[str] = None,
        theta: Optional[str] = None
    ) -> List[AnalysisResult]:
        """
        Buscar análisis por complejidad.
        
        Args:
            big_o: Complejidad O a buscar
            omega: Complejidad Ω a buscar
            theta: Complejidad Θ a buscar
        
        Returns:
            List[AnalysisResult]: Análisis que coinciden
        
        Example:
            >>> results = await repo.search_by_complexity(big_o="O(n)")
        """
        try:
            query = {}
            
            if big_o:
                query["big_o"] = big_o
            if omega:
                query["omega"] = omega
            if theta:
                query["theta"] = theta
            
            if not query:
                return []
            
            return await AnalysisResult.find(query).to_list()
        except Exception as e:
            logger.error(f"Error buscando por complejidad: {e}")
            return []
    
    async def get_recent_analyses(
        self,
        hours: int = 24,
        limit: int = 50
    ) -> List[AnalysisResult]:
        """
        Obtener análisis recientes.
        
        Args:
            hours: Horas hacia atrás
            limit: Número máximo de resultados
        
        Returns:
            List[AnalysisResult]: Análisis recientes
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            return await AnalysisResult.find(
                AnalysisResult.created_at >= cutoff_time
            ).sort(-AnalysisResult.created_at).limit(limit).to_list()
        except Exception as e:
            logger.error(f"Error obteniendo análisis recientes: {e}")
            return []
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Obtener estadísticas de análisis.
        
        Returns:
            Dict con estadísticas:
                - total: Total de análisis
                - by_complexity: Conteo por complejidad
                - avg_analysis_time: Tiempo promedio
        """
        try:
            # Total de análisis
            total = await AnalysisResult.count()
            
            # Análisis por complejidad Big O
            pipeline = [
                {
                    "$group": {
                        "_id": "$big_o",
                        "count": {"$sum": 1}
                    }
                },
                {"$sort": {"count": -1}}
            ]
            
            complexity_stats = await AnalysisResult.aggregate(pipeline).to_list()
            
            # Tiempo promedio de análisis
            avg_time_pipeline = [
                {
                    "$group": {
                        "_id": None,
                        "avg_time": {"$avg": "$analysis_time"}
                    }
                }
            ]
            
            avg_result = await AnalysisResult.aggregate(avg_time_pipeline).to_list()
            avg_time = avg_result[0]["avg_time"] if avg_result else 0
            
            return {
                "total": total,
                "by_complexity": {
                    stat["_id"]: stat["count"]
                    for stat in complexity_stats
                },
                "avg_analysis_time": round(avg_time, 4)
            }
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {
                "total": 0,
                "by_complexity": {},
                "avg_analysis_time": 0
            }
    
    async def delete_old_analyses(
        self,
        days: int = 90
    ) -> int:
        """
        Eliminar análisis antiguos (housekeeping).
        
        Args:
            days: Días de antigüedad
        
        Returns:
            int: Número de análisis eliminados
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            result = await AnalysisResult.find(
                AnalysisResult.created_at < cutoff_date
            ).delete()
            
            deleted_count = result.deleted_count if result else 0
            logger.info(f"Eliminados {deleted_count} análisis antiguos (>{days} días)")
            
            return deleted_count
        except Exception as e:
            logger.error(f"Error eliminando análisis antiguos: {e}")
            return 0
    
    async def get_analysis_with_algorithm(
        self,
        analysis_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Obtener análisis con información del algoritmo.
        
        Args:
            analysis_id: ID del análisis
        
        Returns:
            Dict con análisis y algoritmo, o None
        """
        try:
            analysis = await self.get_by_id(analysis_id)
            if not analysis:
                return None
            
            # Fetch del algoritmo relacionado
            await analysis.fetch_link(AnalysisResult.algorithm)
            
            return {
                "analysis": analysis.dict(),
                "algorithm": analysis.algorithm.dict() if analysis.algorithm else None
            }
        except Exception as e:
            logger.error(f"Error obteniendo análisis con algoritmo: {e}")
            return None
    
    async def count_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> int:
        """
        Contar análisis en un rango de fechas.
        
        Args:
            start_date: Fecha inicio
            end_date: Fecha fin
        
        Returns:
            int: Número de análisis
        """
        try:
            return await AnalysisResult.find(
                AnalysisResult.created_at >= start_date,
                AnalysisResult.created_at <= end_date
            ).count()
        except Exception as e:
            logger.error(f"Error contando análisis por rango: {e}")
            return 0