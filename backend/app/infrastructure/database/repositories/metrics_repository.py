"""
Metrics Repository - PostgreSQL

Repositorio para gestionar métricas y estadísticas del sistema en PostgreSQL.
Permite almacenar y consultar métricas de performance, uso y análisis.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.repositories.base_repository import BaseRepository
from app.utils.logger import get_logger

logger = get_logger(__name__)

# DATA CLASSES PARA MÉTRICAS
@dataclass
class MetricData:
    """Estructura de datos para una métrica"""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str]
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AggregatedMetric:
    """Métrica agregada"""
    name: str
    count: int
    min_value: float
    max_value: float
    avg_value: float
    sum_value: float
    period_start: datetime
    period_end: datetime

# METRICS REPOSITORY
class MetricsRepository:
    """
    Repositorio para métricas y estadísticas del sistema.
    
    Note:
        Este repositorio asume que tienes una tabla 'metrics' en PostgreSQL.
        La estructura de la tabla puede variar según tus necesidades.
        
    Estructura sugerida:
        - id: UUID
        - name: String (nombre de la métrica)
        - value: Float (valor numérico)
        - timestamp: DateTime
        - tags: JSON (etiquetas clave-valor)
        - metadata: JSON (datos adicionales)
    """
    
    def __init__(self, session: AsyncSession):
        """
        Inicializar repositorio.
        
        Args:
            session: Sesión de SQLAlchemy
        """
        self.session = session
    
    async def record_metric(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Registrar una métrica.
        
        Args:
            name: Nombre de la métrica
            value: Valor numérico
            tags: Tags para categorización
            metadata: Metadatos adicionales
            timestamp: Timestamp (default: ahora)
        
        Returns:
            bool: True si se registró exitosamente
        
        Example:
            >>> await repo.record_metric(
            ...     name="analysis_duration",
            ...     value=1.234,
            ...     tags={"algorithm": "quicksort", "complexity": "O(n log n)"}
            ... )
        """
        try:
            # TODO: Implementar insert a tabla de métricas
            # Por ahora, solo logging
            logger.info(
                f"Métrica registrada: {name}={value}",
                extra={"tags": tags, "metadata": metadata}
            )
            return True
        except Exception as e:
            logger.error(f"Error registrando métrica: {e}")
            return False
    
    async def get_metric_history(
        self,
        name: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[MetricData]:
        """
        Obtener historial de una métrica.
        
        Args:
            name: Nombre de la métrica
            start_time: Tiempo de inicio (opcional)
            end_time: Tiempo de fin (opcional)
            limit: Máximo de registros
        
        Returns:
            List[MetricData]: Historial de la métrica
        """
        try:
            # TODO: Implementar query a tabla de métricas
            logger.debug(f"Obteniendo historial de métrica: {name}")
            return []
        except Exception as e:
            logger.error(f"Error obteniendo historial: {e}")
            return []
    
    async def get_aggregated_metrics(
        self,
        name: str,
        period: str = "hour",  # 'minute', 'hour', 'day', 'week'
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[AggregatedMetric]:
        """
        Obtener métricas agregadas por período.
        
        Args:
            name: Nombre de la métrica
            period: Período de agregación
            start_time: Tiempo de inicio
            end_time: Tiempo de fin
        
        Returns:
            List[AggregatedMetric]: Métricas agregadas
        """
        try:
            # TODO: Implementar agregación temporal
            logger.debug(f"Agregando métricas: {name} por {period}")
            return []
        except Exception as e:
            logger.error(f"Error agregando métricas: {e}")
            return []
    
    async def get_metric_stats(
        self,
        name: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, float]:
        """
        Obtener estadísticas de una métrica.
        
        Args:
            name: Nombre de la métrica
            start_time: Tiempo de inicio
            end_time: Tiempo de fin
        
        Returns:
            Dict con estadísticas: min, max, avg, count, sum
        """
        try:
            # TODO: Implementar cálculo de estadísticas
            return {
                "min": 0.0,
                "max": 0.0,
                "avg": 0.0,
                "count": 0,
                "sum": 0.0
            }
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {}
    
    async def delete_old_metrics(
        self,
        days: int = 90
    ) -> int:
        """
        Eliminar métricas antiguas (housekeeping).
        
        Args:
            days: Días de antigüedad
        
        Returns:
            int: Número de métricas eliminadas
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # TODO: Implementar delete de métricas antiguas
            logger.info(f"Eliminando métricas más antiguas que {cutoff_date}")
            return 0
        except Exception as e:
            logger.error(f"Error eliminando métricas antiguas: {e}")
            return 0
    
    # MÉTRICAS ESPECÍFICAS DEL SISTEMA
    async def record_analysis_metric(
        self,
        algorithm_id: str,
        duration_seconds: float,
        complexity: str,
        success: bool = True
    ) -> bool:
        """
        Registrar métrica de análisis de algoritmo.
        
        Args:
            algorithm_id: ID del algoritmo
            duration_seconds: Duración del análisis
            complexity: Complejidad detectada
            success: Si fue exitoso
        
        Returns:
            bool: True si se registró
        """
        return await self.record_metric(
            name="analysis_duration",
            value=duration_seconds,
            tags={
                "algorithm_id": algorithm_id,
                "complexity": complexity,
                "success": str(success)
            }
        )
    
    async def record_api_request_metric(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        duration_ms: int,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Registrar métrica de request API.
        
        Args:
            endpoint: Endpoint llamado
            method: Método HTTP
            status_code: Código de respuesta
            duration_ms: Duración en milisegundos
            user_id: ID del usuario (opcional)
        
        Returns:
            bool: True si se registró
        """
        tags = {
            "endpoint": endpoint,
            "method": method,
            "status_code": str(status_code)
        }
        
        if user_id:
            tags["user_id"] = user_id
        
        return await self.record_metric(
            name="api_request_duration",
            value=float(duration_ms),
            tags=tags
        )

    async def record_llm_metric(
        self,
        provider: str,
        model: str,
        tokens_used: int,
        duration_seconds: float,
        success: bool = True
    ) -> bool:
        """
        Registrar métrica de llamada a LLM.
        
        Args:
            provider: Proveedor (claude, gemini)
            model: Modelo usado
            tokens_used: Tokens consumidos
            duration_seconds: Duración
            success: Si fue exitosa
        
        Returns:
            bool: True si se registró
        """
        # Registrar duración
        await self.record_metric(
            name="llm_call_duration",
            value=duration_seconds,
            tags={
                "provider": provider,
                "model": model,
                "success": str(success)
            }
        )

        # Registrar tokens
        return await self.record_metric(
            name="llm_tokens_used",
            value=float(tokens_used),
            tags={
                "provider": provider,
                "model": model
            }
        )

    async def record_cache_metric(
        self,
        operation: str,
        hit: bool,
        duration_ms: float
    ) -> bool:
        """
        Registrar métrica de caché.
        
        Args:
            operation: Tipo de operación (get, set, delete)
            hit: Si fue cache hit (solo para get)
            duration_ms: Duración
        
        Returns:
            bool: True si se registró
        """
        return await self.record_metric(
            name="cache_operation_duration",
            value=duration_ms,
            tags={
                "operation": operation,
                "hit": str(hit) if operation == "get" else "N/A"
            }
        )

    async def get_system_health_metrics(self) -> Dict[str, Any]:
        """
        Obtener métricas de salud del sistema.
        
        Returns:
            Dict con métricas clave del sistema
        """
        try:
            now = datetime.utcnow()
            last_hour = now - timedelta(hours=1)

            # TODO: Implementar cálculo real de métricas
            return {
                "timestamp": now.isoformat(),
                "period": "last_hour",
                "metrics": {
                    "total_analyses": 0,
                    "avg_analysis_duration": 0.0,
                    "total_api_requests": 0,
                    "avg_api_response_time": 0.0,
                    "cache_hit_rate": 0.0,
                    "llm_calls": 0,
                    "avg_llm_tokens": 0.0
                }
            }
        except Exception as e:
            logger.error(f"Error obteniendo métricas de salud: {e}")
            return {}
    
    async def get_usage_statistics(
        self,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Obtener estadísticas de uso del sistema.
        
        Args:
            days: Días hacia atrás
        
        Returns:
            Dict con estadísticas de uso
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            # TODO: Implementar cálculo de estadísticas
            return {
                "period_days": days,
                "start_date": start_date.isoformat(),
                "statistics": {
                    "total_users": 0,
                    "active_users": 0,
                    "total_analyses": 0,
                    "total_algorithms": 0,
                    "api_calls": 0,
                    "llm_tokens_consumed": 0
                }
            }
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de uso: {e}")
            return {}