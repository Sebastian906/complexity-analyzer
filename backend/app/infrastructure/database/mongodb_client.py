import asyncio
from typing import Optional
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

    async def connect(self):
        """Conectar a MongoDB"""
        try:
            logger.info(f"Conectando a MongoDB: {settings.MONGODB_URL}")

            # Obtener el event loop actual y pasarlo explícitamente a Motor
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.get_event_loop()

            self.client = AsyncIOMotorClient(
                settings.MONGODB_URL,
                minPoolSize=settings.MONGODB_MIN_POOL_SIZE,
                maxPoolSize=settings.MONGODB_MAX_POOL_SIZE,
                io_loop=loop,
            )

            self.db = self.client[settings.MONGODB_DB_NAME]

            # Inicializar Beanie con todos los modelos
            await init_beanie(
                database=self.db,
                document_models=[
                    Algorithm,
                    AnalysisResult,
                    PatternDetection,
                ]
            )

            # Verificar conexión
            await self.client.admin.command('ping')
            logger.info("MongoDB conectado exitosamente")
            
        except Exception as e:
            logger.error(f"Error conectando a MongoDB: {e}")
            raise

    async def close(self):
        """Cerrar conexión"""
        if self.client:
            self.client.close()
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