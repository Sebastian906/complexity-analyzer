from typing import Optional, Any
import json
import redis.asyncio as redis

from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

class RedisCache:
    """Cliente Redis para caché"""

    def __init__(self):
        self.client: Optional[redis.Redis] = None

    async def connect(self):
        """Conectar a Redis"""
        try:
            logger.info(f"Conectando a Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT}")

            self.client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                decode_responses=settings.REDIS_DECODE_RESPONSES,
                max_connections=settings.REDIS_MAX_CONNECTIONS,
            )

            # Verificar conexión
            await self.client.ping()
            logger.info("Redis conectado exitosamente")

        except Exception as e:
            logger.error(f"Error conectando a Redis: {e}")
            raise

    async def close(self):
        """Cerrar conexión"""
        if self.client:
            await self.client.close()
            logger.info("Redis desconectado")

    async def get(self, key: str) -> Optional[Any]:
        """Obtener valor"""
        try:
            value = await self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Error obteniendo de caché: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Guardar valor"""
        try:
            serialized = json.dumps(value)
            await self.client.set(key, serialized, ex=ttl)
            return True
        except Exception as e:
            logger.error(f"Error guardando en caché: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Eliminar valor"""
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error eliminando de caché: {e}")
            return False

    async def ping(self) -> bool:
        """Verificar conexión"""
        try:
            return await self.client.ping()
        except Exception:
            return False

# Singleton
_redis_cache: Optional[RedisCache] = None

def get_redis_client() -> RedisCache:
    """Obtener instancia singleton"""
    global _redis_cache
    if _redis_cache is None:
        _redis_cache = RedisCache()
    return _redis_cache