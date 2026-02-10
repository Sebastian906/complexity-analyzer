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
# Almacenamiento en memoria para métricas (fallback cuando no hay tabla)
_metrics_store: list = []
_MAX_METRICS_IN_MEMORY = 10000  # Límite para evitar memoria excesiva

class MetricsRepository:
    """
    Repositorio para métricas y estadísticas del sistema.
    
    Note:
        Este repositorio usa almacenamiento en memoria como fallback.
        Para producción, se recomienda usar una tabla 'metrics' en PostgreSQL.
        
    Estructura sugerida para tabla PostgreSQL:
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
        global _metrics_store
        try:
            # Crear objeto de métrica
            metric = MetricData(
                name=name,
                value=value,
                timestamp=timestamp or datetime.utcnow(),
                tags=tags or {},
                metadata=metadata
            )
            
            # Almacenar en memoria
            _metrics_store.append(metric)
            
            # Limitar tamaño del store para evitar memoria excesiva
            if len(_metrics_store) > _MAX_METRICS_IN_MEMORY:
                # Eliminar las métricas más antiguas (primeros 1000)
                _metrics_store = _metrics_store[-(_MAX_METRICS_IN_MEMORY - 1000):]
            
            logger.debug(
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
        global _metrics_store
        try:
            # Filtrar métricas por nombre
            result = [m for m in _metrics_store if m.name == name]
            
            # Filtrar por tiempo
            if start_time:
                result = [m for m in result if m.timestamp >= start_time]
            if end_time:
                result = [m for m in result if m.timestamp <= end_time]
            
            # Ordenar por timestamp descendente y limitar
            result = sorted(result, key=lambda x: x.timestamp, reverse=True)[:limit]
            
            logger.debug(f"Historial de '{name}': {len(result)} registros")
            return result
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
        global _metrics_store
        try:
            from collections import defaultdict
            
            # Obtener historial base
            history = await self.get_metric_history(name, start_time, end_time, limit=10000)
            
            if not history:
                return []
            
            # Definir función de agrupación según período
            def get_period_key(ts: datetime) -> tuple:
                if period == "minute":
                    return (ts.year, ts.month, ts.day, ts.hour, ts.minute)
                elif period == "hour":
                    return (ts.year, ts.month, ts.day, ts.hour)
                elif period == "day":
                    return (ts.year, ts.month, ts.day)
                elif period == "week":
                    return (ts.year, ts.isocalendar()[1])  # año, semana
                else:
                    return (ts.year, ts.month, ts.day, ts.hour)
            
            # Agrupar métricas por período
            grouped: Dict[tuple, list] = defaultdict(list)
            for metric in history:
                key = get_period_key(metric.timestamp)
                grouped[key].append(metric)
            
            # Calcular agregados
            aggregated = []
            for key, metrics in grouped.items():
                values = [m.value for m in metrics]
                timestamps = [m.timestamp for m in metrics]
                
                aggregated.append(AggregatedMetric(
                    name=name,
                    count=len(values),
                    min_value=min(values),
                    max_value=max(values),
                    avg_value=sum(values) / len(values),
                    sum_value=sum(values),
                    period_start=min(timestamps),
                    period_end=max(timestamps)
                ))
            
            # Ordenar por período
            aggregated.sort(key=lambda x: x.period_start, reverse=True)
            
            logger.debug(f"Agregado '{name}' por {period}: {len(aggregated)} períodos")
            return aggregated
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
            # Obtener historial de métricas
            history = await self.get_metric_history(name, start_time, end_time, limit=10000)
            
            if not history:
                return {
                    "min": 0.0,
                    "max": 0.0,
                    "avg": 0.0,
                    "count": 0,
                    "sum": 0.0
                }
            
            values = [m.value for m in history]
            
            return {
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "count": len(values),
                "sum": sum(values)
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
        global _metrics_store
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Contar métricas a eliminar
            initial_count = len(_metrics_store)
            
            # Filtrar métricas manteniendo las recientes
            _metrics_store = [m for m in _metrics_store if m.timestamp >= cutoff_date]
            
            deleted_count = initial_count - len(_metrics_store)
            
            logger.info(f"Eliminadas {deleted_count} métricas más antiguas que {cutoff_date}")
            return deleted_count
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

            # Calcular métricas de análisis
            analysis_stats = await self.get_metric_stats("analysis_duration", last_hour)
            api_stats = await self.get_metric_stats("api_request_duration", last_hour)
            llm_stats = await self.get_metric_stats("llm_tokens", last_hour)
            llm_call_stats = await self.get_metric_stats("llm_request", last_hour)
            
            # Calcular cache hit rate
            cache_hits = await self.get_metric_history("cache_hit", last_hour)
            cache_misses = await self.get_metric_history("cache_miss", last_hour)
            total_cache_ops = len(cache_hits) + len(cache_misses)
            cache_hit_rate = len(cache_hits) / total_cache_ops if total_cache_ops > 0 else 0.0
            
            return {
                "timestamp": now.isoformat(),
                "period": "last_hour",
                "metrics": {
                    "total_analyses": analysis_stats.get("count", 0),
                    "avg_analysis_duration": analysis_stats.get("avg", 0.0),
                    "total_api_requests": api_stats.get("count", 0),
                    "avg_api_response_time": api_stats.get("avg", 0.0),
                    "cache_hit_rate": cache_hit_rate,
                    "llm_calls": llm_call_stats.get("count", 0),
                    "avg_llm_tokens": llm_stats.get("avg", 0.0)
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

            # Obtener métricas del período
            analysis_history = await self.get_metric_history("analysis_duration", start_date)
            api_history = await self.get_metric_history("api_request_duration", start_date)
            llm_stats = await self.get_metric_stats("llm_tokens", start_date)
            
            # Extraer usuarios únicos de las métricas
            users = set()
            algorithms = set()
            for metric in _metrics_store:
                if metric.timestamp >= start_date:
                    if metric.tags.get("user_id"):
                        users.add(metric.tags["user_id"])
                    if metric.tags.get("algorithm_id"):
                        algorithms.add(metric.tags["algorithm_id"])
            
            return {
                "period_days": days,
                "start_date": start_date.isoformat(),
                "statistics": {
                    "total_users": len(users),
                    "active_users": len(users),
                    "total_analyses": len(analysis_history),
                    "total_algorithms": len(algorithms),
                    "api_calls": len(api_history),
                    "llm_tokens_consumed": int(llm_stats.get("sum", 0))
                }
            }
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de uso: {e}")
            return {}