"""
Database Connection Manager

Gestiona las conexiones a todas las bases de datos del sistema:
- MongoDB (principal para algoritmos y análisis)
- PostgreSQL (usuarios y métricas)
- Redis (caché)

Proporciona un punto centralizado para inicialización,
health checks y cierre de conexiones.
"""

from typing import Optional, Dict, Any
from enum import Enum

from app.core.config import settings
from app.core.exceptions import DatabaseConnectionException
from app.utils.logger import get_logger

logger = get_logger(__name__)

# DATABASE TYPES
class DatabaseType(str, Enum):
    """Tipos de bases de datos soportadas"""
    MONGODB = "mongodb"
    POSTGRESQL = "postgresql"
    REDIS = "redis"

# CONNECTION STATUS
class ConnectionStatus(str, Enum):
    """Estados de conexión"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"

# DATABASE CONNECTION MANAGER
class DatabaseConnectionManager:
    """
    Gestor centralizado de conexiones a bases de datos.
    
    Maneja el ciclo de vida de todas las conexiones:
    - Inicialización
    - Health checks
    - Reconexión automática
    - Cierre ordenado
    """
    
    def __init__(self):
        """Inicializar el gestor de conexiones"""
        self.connections: Dict[DatabaseType, Any] = {}
        self.status: Dict[DatabaseType, ConnectionStatus] = {
            DatabaseType.MONGODB: ConnectionStatus.DISCONNECTED,
            DatabaseType.POSTGRESQL: ConnectionStatus.DISCONNECTED,
            DatabaseType.REDIS: ConnectionStatus.DISCONNECTED,
        }
    
    async def connect_all(self) -> Dict[DatabaseType, bool]:
        """
        Conectar a todas las bases de datos configuradas.
        
        Returns:
            Dict con DatabaseType -> success (bool)
        
        Example:
            >>> manager = DatabaseConnectionManager()
            >>> results = await manager.connect_all()
            >>> print(results)
            {DatabaseType.MONGODB: True, DatabaseType.REDIS: True}
        """
        results = {}
        
        # Conectar MongoDB si está configurado
        if settings.MONGODB_URL:
            results[DatabaseType.MONGODB] = await self.connect_mongodb()
        
        # Conectar PostgreSQL si está configurado
        if settings.POSTGRES_HOST:
            results[DatabaseType.POSTGRESQL] = await self.connect_postgresql()
        
        # Conectar Redis si está configurado
        if settings.REDIS_HOST:
            results[DatabaseType.REDIS] = await self.connect_redis()
        
        # Log resumen
        successful = sum(1 for success in results.values() if success)
        total = len(results)
        logger.info(f"Conexiones establecidas: {successful}/{total}")
        
        return results
    
    async def connect_mongodb(self) -> bool:
        """
        Conectar a MongoDB.
        
        Returns:
            bool: True si la conexión fue exitosa
        """
        try:
            self.status[DatabaseType.MONGODB] = ConnectionStatus.CONNECTING
            logger.info("Conectando a MongoDB...")
            
            from app.infrastructure.database.mongodb_client import get_mongodb_client
            
            client = get_mongodb_client()
            await client.connect()
            
            self.connections[DatabaseType.MONGODB] = client
            self.status[DatabaseType.MONGODB] = ConnectionStatus.CONNECTED
            
            logger.info("✓ MongoDB conectado exitosamente")
            return True
            
        except Exception as e:
            self.status[DatabaseType.MONGODB] = ConnectionStatus.ERROR
            logger.error(f"✗ Error conectando a MongoDB: {e}")
            return False
    
    async def connect_postgresql(self) -> bool:
        """
        Conectar a PostgreSQL.
        
        Returns:
            bool: True si la conexión fue exitosa
        """
        try:
            self.status[DatabaseType.POSTGRESQL] = ConnectionStatus.CONNECTING
            logger.info("Conectando a PostgreSQL...")
            
            from app.infrastructure.database.postgresql_client import get_postgresql_client
            
            client = get_postgresql_client()
            await client.connect()
            
            self.connections[DatabaseType.POSTGRESQL] = client
            self.status[DatabaseType.POSTGRESQL] = ConnectionStatus.CONNECTED
            
            logger.info("✓ PostgreSQL conectado exitosamente")
            return True
            
        except Exception as e:
            self.status[DatabaseType.POSTGRESQL] = ConnectionStatus.ERROR
            logger.error(f"✗ Error conectando a PostgreSQL: {e}")
            return False
    
    async def connect_redis(self) -> bool:
        """
        Conectar a Redis.
        
        Returns:
            bool: True si la conexión fue exitosa
        """
        try:
            self.status[DatabaseType.REDIS] = ConnectionStatus.CONNECTING
            logger.info("Conectando a Redis...")
            
            from app.infrastructure.cache.redis_cache import get_redis_client
            
            client = get_redis_client()
            await client.connect()
            
            self.connections[DatabaseType.REDIS] = client
            self.status[DatabaseType.REDIS] = ConnectionStatus.CONNECTED
            
            logger.info("✓ Redis conectado exitosamente")
            return True
            
        except Exception as e:
            self.status[DatabaseType.REDIS] = ConnectionStatus.ERROR
            logger.error(f"✗ Error conectando a Redis: {e}")
            return False
    
    async def disconnect_all(self) -> None:
        """
        Desconectar todas las bases de datos.
        
        Cierra ordenadamente todas las conexiones activas.
        """
        logger.info("Cerrando conexiones a bases de datos...")
        
        # Desconectar MongoDB
        if DatabaseType.MONGODB in self.connections:
            await self._disconnect_mongodb()
        
        # Desconectar PostgreSQL
        if DatabaseType.POSTGRESQL in self.connections:
            await self._disconnect_postgresql()
        
        # Desconectar Redis
        if DatabaseType.REDIS in self.connections:
            await self._disconnect_redis()
        
        logger.info("Todas las conexiones cerradas")
    
    async def _disconnect_mongodb(self) -> None:
        """Desconectar MongoDB"""
        try:
            client = self.connections[DatabaseType.MONGODB]
            await client.close()
            del self.connections[DatabaseType.MONGODB]
            self.status[DatabaseType.MONGODB] = ConnectionStatus.DISCONNECTED
            logger.info("✓ MongoDB desconectado")
        except Exception as e:
            logger.error(f"Error desconectando MongoDB: {e}")
    
    async def _disconnect_postgresql(self) -> None:
        """Desconectar PostgreSQL"""
        try:
            client = self.connections[DatabaseType.POSTGRESQL]
            await client.close()
            del self.connections[DatabaseType.POSTGRESQL]
            self.status[DatabaseType.POSTGRESQL] = ConnectionStatus.DISCONNECTED
            logger.info("✓ PostgreSQL desconectado")
        except Exception as e:
            logger.error(f"Error desconectando PostgreSQL: {e}")
    
    async def _disconnect_redis(self) -> None:
        """Desconectar Redis"""
        try:
            client = self.connections[DatabaseType.REDIS]
            await client.close()
            del self.connections[DatabaseType.REDIS]
            self.status[DatabaseType.REDIS] = ConnectionStatus.DISCONNECTED
            logger.info("✓ Redis desconectado")
        except Exception as e:
            logger.error(f"Error desconectando Redis: {e}")
    
    async def health_check(self) -> Dict[DatabaseType, bool]:
        """
        Verificar el estado de salud de todas las conexiones.
        
        Returns:
            Dict con DatabaseType -> is_healthy (bool)
        
        Example:
            >>> health = await manager.health_check()
            >>> print(health)
            {DatabaseType.MONGODB: True, DatabaseType.REDIS: True}
        """
        health_status = {}
        
        # Check MongoDB
        if DatabaseType.MONGODB in self.connections:
            health_status[DatabaseType.MONGODB] = await self._check_mongodb()
        
        # Check PostgreSQL
        if DatabaseType.POSTGRESQL in self.connections:
            health_status[DatabaseType.POSTGRESQL] = await self._check_postgresql()
        
        # Check Redis
        if DatabaseType.REDIS in self.connections:
            health_status[DatabaseType.REDIS] = await self._check_redis()
        
        return health_status
    
    async def _check_mongodb(self) -> bool:
        """Health check para MongoDB"""
        try:
            client = self.connections[DatabaseType.MONGODB]
            return await client.ping()
        except Exception as e:
            logger.warning(f"MongoDB health check falló: {e}")
            return False
    
    async def _check_postgresql(self) -> bool:
        """Health check para PostgreSQL"""
        try:
            client = self.connections[DatabaseType.POSTGRESQL]
            # PostgreSQL no tiene método ping en el cliente actual
            # Verificar si el engine existe y no está disposed
            return client.engine is not None
        except Exception as e:
            logger.warning(f"PostgreSQL health check falló: {e}")
            return False
    
    async def _check_redis(self) -> bool:
        """Health check para Redis"""
        try:
            client = self.connections[DatabaseType.REDIS]
            return await client.ping()
        except Exception as e:
            logger.warning(f"Redis health check falló: {e}")
            return False
    
    def get_connection(self, db_type: DatabaseType) -> Optional[Any]:
        """
        Obtener una conexión específica.
        
        Args:
            db_type: Tipo de base de datos
        
        Returns:
            Cliente de la base de datos o None
        
        Raises:
            DatabaseConnectionException: Si la conexión no está disponible
        """
        if db_type not in self.connections:
            raise DatabaseConnectionException(
                f"No hay conexión activa para {db_type.value}",
                database_type=db_type.value
            )
        
        return self.connections[db_type]
    
    def is_connected(self, db_type: DatabaseType) -> bool:
        """
        Verificar si hay conexión activa.
        
        Args:
            db_type: Tipo de base de datos
        
        Returns:
            bool: True si está conectado
        """
        return (
            db_type in self.connections and
            self.status[db_type] == ConnectionStatus.CONNECTED
        )
    
    def get_status_summary(self) -> Dict[str, Any]:
        """
        Obtener resumen del estado de todas las conexiones.
        
        Returns:
            Dict con información detallada del estado
        """
        return {
            "mongodb": {
                "configured": bool(settings.MONGODB_URL),
                "status": self.status[DatabaseType.MONGODB].value,
                "connected": self.is_connected(DatabaseType.MONGODB),
            },
            "postgresql": {
                "configured": bool(settings.POSTGRES_HOST),
                "status": self.status[DatabaseType.POSTGRESQL].value,
                "connected": self.is_connected(DatabaseType.POSTGRESQL),
            },
            "redis": {
                "configured": bool(settings.REDIS_HOST),
                "status": self.status[DatabaseType.REDIS].value,
                "connected": self.is_connected(DatabaseType.REDIS),
            },
        }

# SINGLETON INSTANCE
_connection_manager: Optional[DatabaseConnectionManager] = None

def get_connection_manager() -> DatabaseConnectionManager:
    """
    Obtener instancia singleton del gestor de conexiones.
    
    Returns:
        DatabaseConnectionManager: Instancia única
    
    Example:
        >>> from app.infrastructure.database.connection import get_connection_manager
        >>> manager = get_connection_manager()
        >>> await manager.connect_all()
    """
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = DatabaseConnectionManager()
    return _connection_manager

# CONVENIENCE FUNCTIONS
async def init_databases() -> Dict[DatabaseType, bool]:
    """
    Inicializar todas las bases de datos.
    
    Función de conveniencia para uso en startup.
    
    Returns:
        Dict con resultados de conexión
    """
    manager = get_connection_manager()
    return await manager.connect_all()

async def close_databases() -> None:
    """
    Cerrar todas las bases de datos.
    
    Función de conveniencia para uso en shutdown.
    """
    manager = get_connection_manager()
    await manager.disconnect_all()

async def check_database_health() -> Dict[DatabaseType, bool]:
    """
    Health check de todas las bases de datos.
    
    Returns:
        Dict con estado de salud
    """
    manager = get_connection_manager()
    return await manager.health_check()