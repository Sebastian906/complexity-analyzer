"""
Cache Service - Servicio de Caché

Proporciona caché en memoria para optimizar análisis repetidos.
Preparado para integrar Redis en el futuro (Módulo 6).
"""

import asyncio
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any

from app.core.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# Enums
class CacheKey(str, Enum):
    """Tipos de claves de caché"""
    ANALYSIS = "analysis"
    PATTERN = "pattern"
    STRUCTURE = "structure"
    VISUALIZATION = "visualization"
    PARSING = "parsing"

# Helper Functions
def generate_cache_key(prefix: CacheKey, code: str, **kwargs) -> str:
    """
    Genera clave de caché única.

    Args:
        prefix: Prefijo de clave
        code: Código del algoritmo
        **kwargs: Parámetros adicionales

    Returns:
        str: Clave de caché
    """
    # Hash del código
    code_hash = hashlib.sha256(code.encode('utf-8')).hexdigest()[:16]

    # Hash de parámetros
    params_str = json.dumps(kwargs, sort_keys=True)
    params_hash = hashlib.md5(params_str.encode('utf-8')).hexdigest()[:8]

    # Si prefix es Enum, usar .value, si es str, usar directamente
    if hasattr(prefix, 'value'):
        prefix_val = prefix.value
    else:
        prefix_val = str(prefix)
    return f"{prefix_val}:{code_hash}:{params_hash}"

@dataclass
class CacheEntry:
    """Entrada de caché"""
    key: str
    value: Any
    created_at: datetime
    expires_at: datetime
    hits: int = 0

    def is_expired(self) -> bool:
        """Verifica si está expirada"""
        return datetime.utcnow() > self.expires_at

    def increment_hits(self):
        """Incrementa contador de hits"""
        self.hits += 1

# Service
class CacheService:
    """
    Servicio de caché en memoria.

    Proporciona caché temporal de resultados para optimizar
    análisis repetidos. En producción, usar Redis (Módulo 6).

    Example:
        >>> cache = CacheService()
        >>> key = generate_cache_key(CacheKey.ANALYSIS, code)
        >>> await cache.set(key, result, ttl=3600)
        >>> cached = await cache.get(key)
    """

    def __init__(self):
        """Inicializa el servicio de caché"""
        # Caché en memoria (dict)
        # En producción: usar Redis
        self._cache: Dict[str, CacheEntry] = {}

        # TTL por defecto
        self.default_ttl = {
            CacheKey.ANALYSIS: settings.CACHE_TTL_ANALYSIS,
            CacheKey.PATTERN: settings.CACHE_TTL_PATTERN,
            CacheKey.STRUCTURE: settings.CACHE_TTL_ANALYSIS,
            CacheKey.VISUALIZATION: settings.CACHE_TTL_ANALYSIS,
            CacheKey.PARSING: settings.CACHE_TTL_ANALYSIS,
        }

        logger.info("CacheService inicializado (in-memory)")

    async def get(self, key: str) -> Optional[Any]:
        """
        Obtiene valor del caché.

        Args:
            key: Clave de caché

        Returns:
            Valor almacenado o None si no existe/expiró
        """
        entry = self._cache.get(key)

        if not entry:
            logger.debug(f"Cache MISS: {key}")
            return None

        if entry.is_expired():
            logger.debug(f"Cache EXPIRED: {key}")
            await self.delete(key)
            return None

        logger.debug(f"Cache HIT: {key}")
        entry.increment_hits()
        return entry.value

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        cache_type: Optional[str] = None
    ) -> bool:
        """
        Almacena valor en caché.

        Args:
            key: Clave de caché
            value: Valor a almacenar
            ttl: Time to live en segundos (opcional)
            cache_type: Tipo de caché para TTL automático

        Returns:
            bool: True si se almacenó correctamente
        """
        # Determinar TTL
        if ttl is None:
            if cache_type:
                ttl = self.default_ttl.get(cache_type, 3600)
            else:
                ttl = 3600

        # Crear entrada
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(seconds=ttl)
        )

        self._cache[key] = entry
        logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")

        return True

    async def delete(self, key: str) -> bool:
        """
        Elimina entrada del caché.

        Args:
            key: Clave a eliminar

        Returns:
            bool: True si existía y se eliminó
        """
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Cache DELETE: {key}")
            return True
        return False

    async def clear(self, prefix: Optional[str] = None) -> int:
        """
        Limpia el caché.

        Args:
            prefix: Si se especifica, solo elimina claves con ese prefijo

        Returns:
            int: Número de claves eliminadas
        """
        if prefix:
            keys_to_delete = [k for k in self._cache.keys() if k.startswith(prefix)]
            for key in keys_to_delete:
                del self._cache[key]
            count = len(keys_to_delete)
        else:
            count = len(self._cache)
            self._cache.clear()

        logger.info(f"Cache cleared: {count} entries")
        return count

    async def cleanup_expired(self) -> int:
        """
        Limpia entradas expiradas.

        Returns:
            int: Número de entradas eliminadas
        """
        expired_keys = [
            k for k, v in self._cache.items()
            if v.is_expired()
        ]

        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            logger.info(f"Cleaned {len(expired_keys)} expired entries")

        return len(expired_keys)

    def get_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del caché.

        Returns:
            Dict: Estadísticas
        """
        total = len(self._cache)
        expired = sum(1 for v in self._cache.values() if v.is_expired())
        total_hits = sum(v.hits for v in self._cache.values())

        return {
            "total_entries": total,
            "expired_entries": expired,
            "active_entries": total - expired,
            "total_hits": total_hits,
            "avg_hits": total_hits / total if total > 0 else 0,
        }

    async def exists(self, key: str) -> bool:
        """Verifica si una clave existe y no está expirada"""
        value = await self.get(key)
        return value is not None

    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """
        Obtiene múltiples valores del caché en paralelo.

        Args:
            keys: Lista de claves

        Returns:
            Dict con {key: value} solo para claves existentes
        """
        results = {}

        # Ejecutar gets en paralelo
        async def get_single(key):
            value = await self.get(key)
            return key, value

        tasks = [get_single(key) for key in keys]
        key_value_pairs = await asyncio.gather(*tasks)

        # Filtrar None
        for key, value in key_value_pairs:
            if value is not None:
                results[key] = value

        logger.debug(f"Cache GET_MANY: {len(results)}/{len(keys)} hits")
        return results

    async def set_many(
        self,
        items: Dict[str, Any],
        ttl: Optional[int] = None,
        cache_type: Optional[str] = None
    ) -> int:
        """
        Almacena múltiples valores en caché en paralelo.

        Args:
            items: Dict {key: value}
            ttl: Time to live (opcional)
            cache_type: Tipo de caché (opcional)

        Returns:
            int: Número de items almacenados exitosamente
        """
        async def set_single(key, value):
            return await self.set(key, value, ttl=ttl, cache_type=cache_type)

        tasks = [set_single(k, v) for k, v in items.items()]
        results = await asyncio.gather(*tasks)

        success_count = sum(1 for r in results if r)
        logger.debug(f"Cache SET_MANY: {success_count}/{len(items)} successful")

        return success_count

    async def delete_many(self, keys: List[str]) -> int:
        """
        Elimina múltiples claves en paralelo.
        
        Args:
            keys: Lista de claves
            
        Returns:
            int: Número de claves eliminadas
        """
        async def delete_single(key):
            return await self.delete(key)

        tasks = [delete_single(key) for key in keys]
        results = await asyncio.gather(*tasks)

        deleted_count = sum(1 for r in results if r)
        logger.debug(f"Cache DELETE_MANY: {deleted_count}/{len(keys)} deleted")

        return deleted_count


# Singleton
_cache_service: Optional[CacheService] = None

def get_cache_service() -> CacheService:
    """
    Obtiene instancia singleton del servicio de caché.
    
    Returns:
        CacheService: Instancia global
    """
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service