"""
Cache Backend - Abstracción del sistema de caché

Problema que resuelve:
    Con WORKERS=4 en uvicorn, cada worker tiene su propio diccionario en
    memoria. El caché no existe entre workers. Un análisis hecho por el
    worker 1 no beneficia al worker 2. Este módulo elimina ese problema.

Arquitectura:
    CacheBackend (ABC)
        ├── InMemoryCacheBackend   ← código actual de cache_service.py
        └── RedisCacheBackend      ← usa RedisCache ya existente

    CacheService elige el backend según settings.REDIS_HOST:
        - Con REDIS_HOST configurado → RedisCacheBackend (distribuido)
        - Sin REDIS_HOST             → InMemoryCacheBackend (desarrollo)

Compatibilidad:
    La interfaz de CacheService NO cambia. Todos los callers existentes
    (analysis_orchestrator.py, endpoints) siguen funcionando sin modificación.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Optional

import logging

logger = logging.getLogger(__name__)

# Interfaz abstracta
class CacheBackend(ABC):
    """
    Interfaz que deben implementar todos los backends de caché.

    Operaciones mínimas: get, set, delete, clear.
    Todos los métodos son async para uniformidad, incluso si la
    implementación subyacente es síncrona.
    """

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Obtiene un valor. Retorna None si no existe o expiró."""
        ...

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Almacena un valor con TTL en segundos."""
        ...

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Elimina una clave. Retorna True si existía."""
        ...

    @abstractmethod
    async def clear(self, prefix: Optional[str] = None) -> int:
        """Elimina claves (con prefijo si se especifica). Retorna cantidad."""
        ...

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Verifica si una clave existe y no ha expirado."""
        ...

    @abstractmethod
    def backend_name(self) -> str:
        """Nombre del backend para logs y métricas."""
        ...

# Backend en memoria (desarrollo / fallback)
@dataclass
class _CacheEntry:
    """Entrada individual del caché en memoria."""
    key: str
    value: Any
    created_at: datetime
    expires_at: datetime
    hits: int = 0

    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at

    def touch(self) -> None:
        self.hits += 1

class InMemoryCacheBackend(CacheBackend):
    """
    Backend en memoria usando un diccionario Python.

    Limitaciones (intencionadas):
    - No compartido entre workers de uvicorn
    - No persiste entre reinicios
    - Solo apto para desarrollo o instancia única

    Úsalo cuando REDIS_HOST no esté configurado.
    """

    def __init__(self) -> None:
        self._store: dict[str, _CacheEntry] = {}
        logger.info("CacheBackend: InMemory activo (solo apto para desarrollo)")

    def backend_name(self) -> str:
        return "in_memory"

    async def get(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)
        if entry is None:
            return None
        if entry.is_expired():
            del self._store[key]
            return None
        entry.touch()
        return entry.value

    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        now = datetime.utcnow()
        self._store[key] = _CacheEntry(
            key=key,
            value=value,
            created_at=now,
            expires_at=now + timedelta(seconds=ttl),
        )
        return True

    async def delete(self, key: str) -> bool:
        if key in self._store:
            del self._store[key]
            return True
        return False

    async def clear(self, prefix: Optional[str] = None) -> int:
        if prefix:
            keys = [k for k in self._store if k.startswith(prefix)]
        else:
            keys = list(self._store.keys())
        for k in keys:
            del self._store[k]
        return len(keys)

    async def exists(self, key: str) -> bool:
        return await self.get(key) is not None

    async def cleanup_expired(self) -> int:
        """Elimina entradas expiradas. Llamar periódicamente."""
        expired = [k for k, v in self._store.items() if v.is_expired()]
        for k in expired:
            del self._store[k]
        return len(expired)

    def stats(self) -> dict:
        total = len(self._store)
        expired = sum(1 for v in self._store.values() if v.is_expired())
        return {
            "backend": "in_memory",
            "total_entries": total,
            "active_entries": total - expired,
            "expired_entries": expired,
            "total_hits": sum(v.hits for v in self._store.values()),
        }

# Backend Redis (producción / multi-worker)
class RedisCacheBackend(CacheBackend):
    """
    Backend Redis usando RedisCache ya existente en infrastructure/cache.

    Ventajas sobre InMemory:
    - Compartido entre todos los workers de uvicorn
    - Persiste entre reinicios (con Redis AOF)
    - TTL gestionado por Redis (más eficiente)
    - Soporta distribución horizontal

    Requiere REDIS_HOST configurado en settings.
    """

    def __init__(self) -> None:
        # Lazy import para evitar error si redis no está disponible
        from app.infrastructure.cache.redis_cache import get_redis_client
        self._redis = get_redis_client()
        logger.info("CacheBackend: Redis activo (multi-worker seguro)")

    def backend_name(self) -> str:
        return "redis"

    async def get(self, key: str) -> Optional[Any]:
        try:
            raw = await self._redis.get(key)
            if raw is None:
                return None
            # RedisCache ya deserializa JSON internamente si lo configuramos
            # Si devuelve string, intentar deserializar
            if isinstance(raw, str):
                try:
                    return json.loads(raw)
                except (json.JSONDecodeError, TypeError):
                    return raw
            return raw
        except Exception as e:
            logger.warning(f"Redis GET falló para '{key}': {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        try:
            # Serializar a JSON para almacenamiento uniforme
            serialized = json.dumps(value, default=str)
            await self._redis.set(key, serialized, ttl=ttl)
            return True
        except Exception as e:
            logger.warning(f"Redis SET falló para '{key}': {e}")
            return False

    async def delete(self, key: str) -> bool:
        try:
            result = await self._redis.delete(key)
            return bool(result)
        except Exception as e:
            logger.warning(f"Redis DELETE falló para '{key}': {e}")
            return False

    async def clear(self, prefix: Optional[str] = None) -> int:
        try:
            if prefix:
                keys = await self._redis.keys(f"{prefix}*")
                if keys:
                    deleted = 0
                    for k in keys:
                        if await self._redis.delete(k):
                            deleted += 1
                    return deleted
                return 0
            else:
                # Limpiar todo — solo en testing, nunca en producción directamente
                logger.warning("CacheBackend: clear() sin prefijo en Redis")
                return 0
        except Exception as e:
            logger.warning(f"Redis CLEAR falló: {e}")
            return 0

    async def exists(self, key: str) -> bool:
        try:
            return await self._redis.exists(key)
        except Exception as e:
            logger.warning(f"Redis EXISTS falló para '{key}': {e}")
            return False

# Factory
def create_cache_backend() -> CacheBackend:
    """
    Crea el backend apropiado según la configuración.

    Lógica de selección:
        1. Si REDIS_HOST está configurado → RedisCacheBackend
        2. Si no                          → InMemoryCacheBackend

    En tests, se puede forzar InMemory sobreescribiendo REDIS_HOST="".
    """
    try:
        from app.core.config import settings
        if settings.REDIS_HOST:
            try:
                backend = RedisCacheBackend()
                logger.info(
                    f"CacheBackend seleccionado: Redis "
                    f"({settings.REDIS_HOST}:{settings.REDIS_PORT})"
                )
                return backend
            except Exception as e:
                logger.warning(
                    f"Redis no disponible ({e}), "
                    f"usando InMemory como fallback"
                )
    except Exception:
        pass

    return InMemoryCacheBackend()