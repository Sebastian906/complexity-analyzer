from typing import Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.core.config import settings
from app.utils.logger import get_logger
from app.infrastructure.database.models.postgres.base import Base

logger = get_logger(__name__)

class PostgreSQLClient:
    """Cliente PostgreSQL con SQLAlchemy async"""

    def __init__(self):
        self.engine = None
        self.session_factory = None

    async def connect(self):
        """Conectar a PostgreSQL"""
        try:
            logger.info(f"Conectando a PostgreSQL: {settings.POSTGRES_HOST}")

            self.engine = create_async_engine(
                settings.DATABASE_URL,
                echo=settings.POSTGRES_ECHO,
                pool_size=settings.POSTGRES_POOL_SIZE,
                max_overflow=settings.POSTGRES_MAX_OVERFLOW,
            )

            self.session_factory = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )

            # Crear tablas
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            logger.info("PostgreSQL conectado exitosamente")

        except Exception as e:
            logger.error(f"Error conectando a PostgreSQL: {e}")
            raise

    async def close(self):
        """Cerrar conexión"""
        if self.engine:
            await self.engine.dispose()
            logger.info("PostgreSQL desconectado")

    def get_session(self) -> AsyncSession:
        """Obtener sesión de base de datos"""
        return self.session_factory()

# Singleton
_postgresql_client: Optional[PostgreSQLClient] = None

def get_postgresql_client() -> PostgreSQLClient:
    """Obtener instancia singleton"""
    global _postgresql_client
    if _postgresql_client is None:
        _postgresql_client = PostgreSQLClient()
    return _postgresql_client