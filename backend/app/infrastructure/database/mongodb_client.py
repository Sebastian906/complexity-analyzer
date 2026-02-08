from typing import Optional
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from app.core.config import settings
from app.utils.logger import get_logger
from app.infrastructure.database.models.mongo import (
    Algorithm,
    AnalysisResult,
    PatternDetection,
)

logger = get_logger(__name__)

class MongoDBClient:
    """Cliente MongoDB con Beanie ODM"""

    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self._is_connected = False
        self._connected_loop_id: Optional[int] = None  # ID del loop donde se conectó

    @property
    def is_connected(self) -> bool:
        """Verificar si está conectado"""
        return self._is_connected and self.client is not None

    def needs_reconnect(self) -> bool:
        """Verificar si necesita reconectar (loop cambió o cerrado)"""
        if not self._is_connected or self.client is None:
            return True
        
        try:
            current_loop = asyncio.get_running_loop()
            current_loop_id = id(current_loop)
            
            # Si el loop cambió, necesitamos reconectar
            if self._connected_loop_id is not None and self._connected_loop_id != current_loop_id:
                logger.warning(f"Event loop cambió: {self._connected_loop_id} -> {current_loop_id}")
                return True
            
            # Verificar si el loop está cerrado
            if current_loop.is_closed():
                logger.warning("Event loop está cerrado")
                return True
                
        except RuntimeError as e:
            # No hay loop corriendo
            logger.warning(f"No hay event loop: {e}")
            return True
        
        return False

    async def connect(self):
        """Conectar a MongoDB"""
        # Cerrar conexión anterior si existe para evitar problemas de event loop
        if self.client is not None:
            try:
                self.client.close()
            except Exception:
                pass
            self.client = None
            self._is_connected = False
            
        try:
            logger.info(f"Conectando a MongoDB: {settings.MONGODB_URL}")

            # Motor maneja el event loop automáticamente en versiones recientes
            # No usar io_loop ya que está deprecado
            self.client = AsyncIOMotorClient(
                settings.MONGODB_URL,
                minPoolSize=settings.MONGODB_MIN_POOL_SIZE,
                maxPoolSize=settings.MONGODB_MAX_POOL_SIZE,
            )

            self.db = self.client[settings.MONGODB_DB_NAME]

            # Inicializar Beanie con todos los modelos
            logger.info("Inicializando Beanie con modelos...")
            await init_beanie(
                database=self.db,
                document_models=[
                    Algorithm,
                    AnalysisResult,
                    PatternDetection,
                ]
            )
            logger.info("Beanie inicializado exitosamente")

            # Verificar conexión
            await self.client.admin.command('ping')
            self._is_connected = True
            self._connected_loop_id = id(asyncio.get_running_loop())  # Guardar ID del loop
            logger.info(f"MongoDB conectado exitosamente (loop_id={self._connected_loop_id})")
            
        except Exception as e:
            self._is_connected = False
            logger.error(f"Error conectando a MongoDB: {e}")
            raise

    async def close(self):
        """Cerrar conexión"""
        if self.client:
            self.client.close()
            self._is_connected = False
            logger.info("MongoDB desconectado")

    async def ping(self) -> bool:
        """Verificar conexión"""
        try:
            await self.client.admin.command('ping')
            return True
        except Exception:
            return False

# Singleton
_mongodb_client: Optional[MongoDBClient] = None

def get_mongodb_client() -> MongoDBClient:
    """Obtener instancia singleton del cliente MongoDB"""
    global _mongodb_client
    if _mongodb_client is None:
        _mongodb_client = MongoDBClient()
    return _mongodb_client

def reset_mongodb_client() -> None:
    """Resetear el singleton del cliente MongoDB (para tests)"""
    global _mongodb_client
    if _mongodb_client is not None:
        if _mongodb_client.client is not None:
            try:
                _mongodb_client.client.close()
            except Exception:
                pass
        _mongodb_client = None