"""
Cache Service - Servicio de Caché

Proporciona caché en memoria para optimizar análisis repetidos.
Preparado para integrar Redis en el futuro (Módulo 6).
"""

import asyncio
import hashlib
import json
from enum import Enum
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.infrastructure.cache.cache_backend import CacheBackend, create_cache_backend
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# Enums y helpers
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
    prefix_val = prefix.value if hasattr(prefix, "value") else str(prefix)
    return f"{prefix_val}:{code_hash}:{params_hash}"

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

    def __init__(self, backend: Optional[CacheBackend] = None) -> None:
        """Inicializa el servicio de caché"""
        # Caché en memoria (dict)
        # En producción: usar Redis
        self._backend = backend or create_cache_backend()

        # TTL por defecto
        self.default_ttl = {
            CacheKey.ANALYSIS: settings.CACHE_TTL_ANALYSIS,
            CacheKey.PATTERN: settings.CACHE_TTL_PATTERN,
            CacheKey.STRUCTURE: settings.CACHE_TTL_ANALYSIS,
            CacheKey.VISUALIZATION: settings.CACHE_TTL_ANALYSIS,
            CacheKey.PARSING: settings.CACHE_TTL_ANALYSIS,
        }

        logger.info(f"CacheService iniciado — backend: {self._backend.backend_name()}")

    # Operaciones básicas
    async def get(self, key: str) -> Optional[Any]:
        """
        Obtiene valor del caché.

        Args:
            key: Clave de caché

        Returns:
            Valor almacenado o None si no existe/expiró
        """
        value = await self._backend.get(key)
        if value is None:
            logger.debug(f"Cache MISS: {key[:40]}")
        else:
            logger.debug(f"Cache HIT:  {key[:40]}")
        return value

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        cache_type: Optional[str] = None,
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
        resolved_ttl = ttl
        if resolved_ttl is None:
            if cache_type:
                # cache_type puede llegar como string o CacheKey enum
                try:
                    ck = CacheKey(cache_type) if isinstance(cache_type, str) else cache_type
                    resolved_ttl = self.default_ttl.get(ck, 3600)
                except ValueError:
                    resolved_ttl = 3600
            else:
                resolved_ttl = 3600

        result = await self._backend.set(key, value, ttl=resolved_ttl)
        logger.debug(f"Cache SET: {key[:40]} (TTL={resolved_ttl}s)")
        return result

    async def delete(self, key: str) -> bool:
        """
        Elimina entrada del caché.

        Args:
            key: Clave a eliminar

        Returns:
            bool: True si existía y se eliminó
        """
        result = await self._backend.delete(key)
        if result:
            logger.debug(f"Cache DELETE: {key[:40]}")
        return result

    async def clear(self, prefix: Optional[str] = None) -> int:
        """
        Limpia el caché.

        Args:
            prefix: Si se especifica, solo elimina claves con ese prefijo

        Returns:
            int: Número de claves eliminadas
        """
        count = await self._backend.clear(prefix)
        logger.info(f"Cache CLEAR: {count} entradas eliminadas (prefix={prefix!r})")
        return count

    async def exists(self, key: str) -> bool:
        """Verifica si una clave existe y no está expirada"""
        return await self._backend.exists(key)

    # Operaciones en lote
    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """
        Obtiene múltiples valores del caché en paralelo.

        Args:
            keys: Lista de claves

        Returns:
            Dict con {key: value} solo para claves existentes
        """

        # Ejecutar gets en paralelo
        async def _get(k: str):
            return k, await self.get(k)

        pairs = await asyncio.gather(*[_get(k) for k in keys])
        return {k: v for k, v in pairs if v is not None}

    async def set_many(
        self,
        items: Dict[str, Any],
        ttl: Optional[int] = None,
        cache_type: Optional[str] = None,
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
        results = await asyncio.gather(
            *[self.set(k, v, ttl=ttl, cache_type=cache_type) for k, v in items.items()]
        )
        return sum(1 for r in results if r)

    async def delete_many(self, keys: List[str]) -> int:
        """
        Elimina múltiples claves en paralelo.
        
        Args:
            keys: Lista de claves
            
        Returns:
            int: Número de claves eliminadas
        """
        results = await asyncio.gather(*[self.delete(k) for k in keys])
        return sum(1 for r in results if r)

    # Estadísticas
    def get_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del caché.

        Returns:
            Dict: Estadísticas
        """
        base = {"backend": self._backend.backend_name()}

        # InMemory tiene stats detalladas
        if hasattr(self._backend, "stats"):
            base.update(self._backend.stats())

        return base
    
    async def cleanup_expired(self) -> int:
        """
        Limpia entradas expiradas.

        Returns:
            int: Número de entradas eliminadas
        """
        if hasattr(self._backend, "cleanup_expired"):
            return await self._backend.cleanup_expired()
        return 0
    
    @property
    def backend_name(self) -> str:
        """Nombre del backend activo."""
        return self._backend.backend_name()

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

def reset_cache_service() -> None:
    """
    Resetea el singleton. Solo para tests.

    Permite usar un backend diferente por test sin afectar otros.

    Example (en conftest.py):
        >>> from app.services.cache_service import reset_cache_service
        >>> from app.infrastructure.cache.cache_backend import InMemoryCacheBackend
        >>>
        >>> @pytest.fixture(autouse=True)
        >>> def fresh_cache():
        ...     reset_cache_service()
        ...     yield
        ...     reset_cache_service()
    """
    global _cache_service
    _cache_service = None