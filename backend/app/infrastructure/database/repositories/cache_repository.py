"""
Cache Repository - Redis

Repositorio para operaciones de caché usando Redis.
Proporciona una interfaz de alto nivel para almacenamiento temporal.
"""

from typing import Optional, Any, List, Dict
import json
from datetime import timedelta

from app.infrastructure.cache.redis_cache import get_redis_client
from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

class CacheRepository:
    """
    Repositorio para operaciones de caché con Redis.
    
    Proporciona métodos de alto nivel para:
    - Almacenamiento y recuperación de datos
    - Gestión de TTL
    - Operaciones en lote
    - Patrones comunes de caché
    """
    
    def __init__(self):
        """Inicializar repositorio de caché"""
        self.client = get_redis_client()
    
    # OPERACIONES BÁSICAS
    async def get(self, key: str) -> Optional[Any]:
        """
        Obtener valor de caché.
        
        Args:
            key: Clave del caché
        
        Returns:
            Valor deserializado o None
        
        Example:
            >>> repo = CacheRepository()
            >>> value = await repo.get("analysis:123")
        """
        try:
            return await self.client.get(key)
        except Exception as e:
            logger.error(f"Error obteniendo de caché key={key}: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Guardar valor en caché.
        
        Args:
            key: Clave del caché
            value: Valor a guardar (será serializado a JSON)
            ttl: Time to live en segundos (opcional)
        
        Returns:
            bool: True si se guardó exitosamente
        
        Example:
            >>> await repo.set("analysis:123", {"big_o": "O(n)"}, ttl=3600)
        """
        try:
            return await self.client.set(key, value, ttl=ttl)
        except Exception as e:
            logger.error(f"Error guardando en caché key={key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Eliminar valor de caché.
        
        Args:
            key: Clave a eliminar
        
        Returns:
            bool: True si se eliminó
        """
        try:
            return await self.client.delete(key)
        except Exception as e:
            logger.error(f"Error eliminando de caché key={key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """
        Verificar si existe una clave.
        
        Args:
            key: Clave a verificar
        
        Returns:
            bool: True si existe
        """
        try:
            value = await self.get(key)
            return value is not None
        except Exception as e:
            logger.error(f"Error verificando existencia key={key}: {e}")
            return False
    
    # OPERACIONES DE ANÁLISIS
    async def cache_analysis_result(
        self,
        algorithm_id: str,
        analysis_result: Dict[str, Any]
    ) -> bool:
        """
        Cachear resultado de análisis.
        
        Args:
            algorithm_id: ID del algoritmo
            analysis_result: Resultado del análisis
        
        Returns:
            bool: True si se cacheó
        
        Example:
            >>> await repo.cache_analysis_result(
            ...     "algo123",
            ...     {"big_o": "O(n)", "omega": "Ω(1)"}
            ... )
        """
        key = self._build_analysis_key(algorithm_id)
        return await self.set(
            key,
            analysis_result,
            ttl=settings.CACHE_TTL_ANALYSIS
        )
    
    async def get_cached_analysis(
        self,
        algorithm_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Obtener análisis cacheado.
        
        Args:
            algorithm_id: ID del algoritmo
        
        Returns:
            Dict con resultado o None
        """
        key = self._build_analysis_key(algorithm_id)
        return await self.get(key)
    
    async def invalidate_analysis_cache(self, algorithm_id: str) -> bool:
        """
        Invalidar caché de análisis.
        
        Args:
            algorithm_id: ID del algoritmo
        
        Returns:
            bool: True si se invalidó
        """
        key = self._build_analysis_key(algorithm_id)
        return await self.delete(key)
    
    # OPERACIONES DE PATRONES
    async def cache_pattern_detection(
        self,
        algorithm_id: str,
        patterns: Dict[str, Any]
    ) -> bool:
        """
        Cachear detección de patrones.
        
        Args:
            algorithm_id: ID del algoritmo
            patterns: Patrones detectados
        
        Returns:
            bool: True si se cacheó
        """
        key = self._build_pattern_key(algorithm_id)
        return await self.set(
            key,
            patterns,
            ttl=settings.CACHE_TTL_PATTERN
        )
    
    async def get_cached_patterns(
        self,
        algorithm_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Obtener patrones cacheados.
        
        Args:
            algorithm_id: ID del algoritmo
        
        Returns:
            Dict con patrones o None
        """
        key = self._build_pattern_key(algorithm_id)
        return await self.get(key)
    
    # OPERACIONES DE LLM
    async def cache_llm_response(
        self,
        prompt_hash: str,
        llm_type: str,
        response: Dict[str, Any]
    ) -> bool:
        """
        Cachear respuesta de LLM.
        
        Args:
            prompt_hash: Hash del prompt
            llm_type: Tipo de LLM (claude, gemini)
            response: Respuesta del LLM
        
        Returns:
            bool: True si se cacheó
        """
        key = self._build_llm_key(prompt_hash, llm_type)
        return await self.set(
            key,
            response,
            ttl=settings.CACHE_TTL_LLM
        )
    
    async def get_cached_llm_response(
        self,
        prompt_hash: str,
        llm_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Obtener respuesta cacheada de LLM.
        
        Args:
            prompt_hash: Hash del prompt
            llm_type: Tipo de LLM
        
        Returns:
            Dict con respuesta o None
        """
        key = self._build_llm_key(prompt_hash, llm_type)
        return await self.get(key)
    
    # OPERACIONES EN LOTE
    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """
        Obtener múltiples valores.
        
        Args:
            keys: Lista de claves
        
        Returns:
            Dict con key -> value
        """
        result = {}
        for key in keys:
            value = await self.get(key)
            if value is not None:
                result[key] = value
        return result
    
    async def set_many(
        self,
        items: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> int:
        """
        Guardar múltiples valores.
        
        Args:
            items: Dict con key -> value
            ttl: TTL para todos los items
        
        Returns:
            int: Número de items guardados exitosamente
        """
        count = 0
        for key, value in items.items():
            if await self.set(key, value, ttl=ttl):
                count += 1
        return count
    
    async def delete_many(self, keys: List[str]) -> int:
        """
        Eliminar múltiples claves.
        
        Args:
            keys: Lista de claves
        
        Returns:
            int: Número de claves eliminadas
        """
        count = 0
        for key in keys:
            if await self.delete(key):
                count += 1
        return count
    
    # OPERACIONES DE PATRÓN
    async def clear_pattern(self, pattern: str) -> int:
        """
        Eliminar todas las claves que coinciden con un patrón.
        
        Args:
            pattern: Patrón (ej: "analysis:*")
        
        Returns:
            int: Número de claves eliminadas
        
        Note:
            Esta operación puede ser costosa en producción.
            Usar con precaución.
        """
        try:
            # TODO: Implementar SCAN pattern en Redis
            logger.warning(f"Clearing cache pattern: {pattern}")
            return 0
        except Exception as e:
            logger.error(f"Error clearing pattern {pattern}: {e}")
            return 0
    
    # HELPERS PARA CONSTRUCCIÓN DE KEYS
    def _build_analysis_key(self, algorithm_id: str) -> str:
        """Construir clave para análisis"""
        return f"analysis:{algorithm_id}"
    
    def _build_pattern_key(self, algorithm_id: str) -> str:
        """Construir clave para patrones"""
        return f"pattern:{algorithm_id}"
    
    def _build_llm_key(self, prompt_hash: str, llm_type: str) -> str:
        """Construir clave para respuesta LLM"""
        return f"llm:{llm_type}:{prompt_hash}"
    
    # UTILIDADES
    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas del caché.
        
        Returns:
            Dict con estadísticas (si Redis lo soporta)
        """
        try:
            # Verificar conexión
            is_connected = await self.client.ping()
            
            return {
                "connected": is_connected,
                "type": "redis",
                # TODO: Agregar más estadísticas de Redis INFO
            }
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de caché: {e}")
            return {
                "connected": False,
                "error": str(e)
            }
    
    async def flush_all(self) -> bool:
        """
        Limpiar todo el caché.
        
        WARNING: Esta operación elimina TODAS las claves.
        Usar solo en desarrollo/testing.
        
        Returns:
            bool: True si se limpió
        """
        try:
            if settings.APP_ENV == "production":
                logger.error("Intento de flush_all en producción bloqueado")
                return False
            
            # TODO: Implementar FLUSHALL en Redis
            logger.warning("Cache flush_all ejecutado")
            return True
        except Exception as e:
            logger.error(f"Error en flush_all: {e}")
            return False

# DECORADOR PARA AUTO-CACHÉ
def cached(
    key_prefix: str,
    ttl: Optional[int] = None,
    key_builder: Optional[callable] = None
):
    """
    Decorador para cachear automáticamente resultados de funciones.
    
    Args:
        key_prefix: Prefijo para la clave de caché
        ttl: Time to live en segundos
        key_builder: Función para construir la clave (opcional)
    
    Example:
        >>> @cached(key_prefix="analysis", ttl=3600)
        >>> async def analyze_algorithm(algorithm_id: str):
        ...     # código de análisis
        ...     return result
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Construir clave
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # Clave simple basada en argumentos
                cache_key = f"{key_prefix}:{':'.join(map(str, args))}"
            
            # Intentar obtener de caché
            repo = CacheRepository()
            cached_result = await repo.get(cache_key)
            
            if cached_result is not None:
                logger.debug(f"Cache HIT: {cache_key}")
                return cached_result
            
            # Cache MISS - ejecutar función
            logger.debug(f"Cache MISS: {cache_key}")
            result = await func(*args, **kwargs)
            
            # Guardar en caché
            await repo.set(cache_key, result, ttl=ttl)
            
            return result
        
        return wrapper
    return decorator