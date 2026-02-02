"""
Database Factory Pattern

Proporciona un Factory para crear instancias de clientes de base de datos
según el tipo configurado en settings.

Implementa el patrón Factory para desacoplar la creación de clientes
de base de datos del código que los utiliza.
"""

from typing import Optional, Union
from enum import Enum

from app.core.config import settings
from app.core.exceptions import DatabaseException
from app.utils.logger import get_logger
from app.infrastructure.database.mongodb_client import MongoDBClient
from app.infrastructure.database.postgresql_client import PostgreSQLClient

logger = get_logger(__name__)

# DATABASE TYPES
class DatabaseBackend(str, Enum):
    """Tipos de backend de base de datos soportados"""
    MONGODB = "mongodb"
    POSTGRESQL = "postgresql"

# DATABASE FACTORY
class DatabaseFactory:
    """
    Factory para crear instancias de clientes de base de datos.
    
    Selecciona automáticamente el cliente correcto basado en
    la configuración del sistema.
    
    Example:
        >>> factory = DatabaseFactory()
        >>> client = await factory.create_client()
        >>> await client.connect()
    """
    
    @staticmethod
    async def create_client(
        backend: Optional[DatabaseBackend] = None
    ) -> Union['MongoDBClient', 'PostgreSQLClient']:
        """
        Crear cliente de base de datos.
        
        Args:
            backend: Tipo de backend (opcional, usa settings.DATABASE_TYPE)
        
        Returns:
            Cliente de base de datos configurado
        
        Raises:
            DatabaseException: Si el backend no está soportado
        
        Example:
            >>> client = await DatabaseFactory.create_client()
            >>> # O especificar backend:
            >>> client = await DatabaseFactory.create_client(DatabaseBackend.MONGODB)
        """
        # Determinar backend a usar
        if backend is None:
            backend_str = settings.DATABASE_TYPE.lower()
            try:
                backend = DatabaseBackend(backend_str)
            except ValueError:
                raise DatabaseException(
                    f"Backend de base de datos no soportado: {backend_str}",
                    database_type=backend_str
                )
        
        # Crear cliente según backend
        if backend == DatabaseBackend.MONGODB:
            return await DatabaseFactory._create_mongodb_client()
        
        elif backend == DatabaseBackend.POSTGRESQL:
            return await DatabaseFactory._create_postgresql_client()
        
        else:
            raise DatabaseException(
                f"Backend no soportado: {backend}",
                database_type=backend.value
            )
    
    @staticmethod
    async def _create_mongodb_client():
        """Crear y conectar cliente MongoDB"""
        from app.infrastructure.database.mongodb_client import get_mongodb_client
        
        logger.info("Creando cliente MongoDB...")
        client = get_mongodb_client()
        await client.connect()
        logger.info("✓ Cliente MongoDB creado y conectado")
        
        return client
    
    @staticmethod
    async def _create_postgresql_client():
        """Crear y conectar cliente PostgreSQL"""
        from app.infrastructure.database.postgresql_client import get_postgresql_client
        
        logger.info("Creando cliente PostgreSQL...")
        client = get_postgresql_client()
        await client.connect()
        logger.info("✓ Cliente PostgreSQL creado y conectado")
        
        return client
    
    @staticmethod
    def get_repository_factory(
        backend: Optional[DatabaseBackend] = None
    ) -> 'RepositoryFactory':
        """
        Obtener factory de repositorios para el backend.
        
        Args:
            backend: Tipo de backend (opcional)
        
        Returns:
            RepositoryFactory configurado para el backend
        
        Example:
            >>> repo_factory = DatabaseFactory.get_repository_factory()
            >>> algorithm_repo = repo_factory.create_algorithm_repository()
        """
        if backend is None:
            backend_str = settings.DATABASE_TYPE.lower()
            backend = DatabaseBackend(backend_str)
        
        return RepositoryFactory(backend)

# REPOSITORY FACTORY
class RepositoryFactory:
    """
    Factory para crear repositorios según el backend.
    
    Proporciona una interfaz unificada para obtener repositorios
    independientemente del backend de base de datos usado.
    """
    
    def __init__(self, backend: DatabaseBackend):
        """
        Inicializar factory de repositorios.
        
        Args:
            backend: Backend de base de datos a usar
        """
        self.backend = backend
        logger.info(f"RepositoryFactory inicializado para {backend.value}")
    
    def create_algorithm_repository(self):
        """
        Crear repositorio de algoritmos.
        
        Returns:
            AlgorithmRepository para el backend configurado
        
        Example:
            >>> factory = RepositoryFactory(DatabaseBackend.MONGODB)
            >>> repo = factory.create_algorithm_repository()
            >>> algorithms = await repo.list()
        """
        if self.backend == DatabaseBackend.MONGODB:
            from app.infrastructure.database.repositories.algorithm_repository import (
                AlgorithmRepository
            )
            logger.debug("Creando AlgorithmRepository (MongoDB)")
            return AlgorithmRepository()
        
        elif self.backend == DatabaseBackend.POSTGRESQL:
            # TODO: Implementar AlgorithmRepository para PostgreSQL
            raise NotImplementedError(
                "AlgorithmRepository no implementado para PostgreSQL"
            )
        
        else:
            raise DatabaseException(
                f"Backend no soportado: {self.backend}",
                database_type=self.backend.value
            )
    
    def create_analysis_repository(self):
        """
        Crear repositorio de análisis.
        
        Returns:
            AnalysisRepository para el backend configurado
        """
        if self.backend == DatabaseBackend.MONGODB:
            from app.infrastructure.database.repositories.analysis_repository import (
                AnalysisRepository
            )
            logger.debug("Creando AnalysisRepository (MongoDB)")
            return AnalysisRepository()
        
        elif self.backend == DatabaseBackend.POSTGRESQL:
            raise NotImplementedError(
                "AnalysisRepository no implementado para PostgreSQL"
            )
        
        else:
            raise DatabaseException(
                f"Backend no soportado: {self.backend}",
                database_type=self.backend.value
            )
    
    def create_user_repository(self):
        """
        Crear repositorio de usuarios.
        
        Returns:
            UserRepository para el backend configurado
        
        Note:
            Usuarios típicamente se almacenan en PostgreSQL
        """
        if self.backend == DatabaseBackend.POSTGRESQL:
            from app.infrastructure.database.repositories.user_repository import (
                UserRepository
            )
            logger.debug("Creando UserRepository (PostgreSQL)")
            return UserRepository()
        
        elif self.backend == DatabaseBackend.MONGODB:
            # MongoDB puede usarse pero PostgreSQL es preferido
            logger.warning(
                "UserRepository solicitado para MongoDB. "
                "PostgreSQL es el backend recomendado para usuarios."
            )
            raise NotImplementedError(
                "UserRepository preferentemente usa PostgreSQL"
            )
        
        else:
            raise DatabaseException(
                f"Backend no soportado: {self.backend}",
                database_type=self.backend.value
            )
    
    def create_metrics_repository(self):
        """
        Crear repositorio de métricas.
        
        Returns:
            MetricsRepository para el backend configurado
        """
        if self.backend == DatabaseBackend.POSTGRESQL:
            from app.infrastructure.database.repositories.metrics_repository import (
                MetricsRepository
            )
            logger.debug("Creando MetricsRepository (PostgreSQL)")
            return MetricsRepository()
        
        elif self.backend == DatabaseBackend.MONGODB:
            logger.warning(
                "MetricsRepository solicitado para MongoDB. "
                "PostgreSQL es el backend recomendado para métricas."
            )
            raise NotImplementedError(
                "MetricsRepository preferentemente usa PostgreSQL"
            )
        
        else:
            raise DatabaseException(
                f"Backend no soportado: {self.backend}",
                database_type=self.backend.value
            )
    
    def create_cache_repository(self):
        """
        Crear repositorio de caché.
        
        Returns:
            CacheRepository (siempre usa Redis)
        
        Note:
            El caché siempre usa Redis independientemente del backend principal
        """
        from app.infrastructure.database.repositories.cache_repository import (
            CacheRepository
        )
        logger.debug("Creando CacheRepository (Redis)")
        return CacheRepository()

# CONVENIENCE FUNCTIONS
async def get_default_client():
    """
    Obtener cliente de base de datos por defecto.
    
    Usa la configuración de settings.DATABASE_TYPE.
    
    Returns:
        Cliente de base de datos configurado y conectado
    
    Example:
        >>> from app.infrastructure.database.database_factory import get_default_client
        >>> client = await get_default_client()
    """
    factory = DatabaseFactory()
    return await factory.create_client()

def get_default_repository_factory() -> RepositoryFactory:
    """
    Obtener factory de repositorios por defecto.
    
    Returns:
        RepositoryFactory configurado para el backend por defecto
    
    Example:
        >>> from app.infrastructure.database.database_factory import get_default_repository_factory
        >>> factory = get_default_repository_factory()
        >>> algo_repo = factory.create_algorithm_repository()
    """
    return DatabaseFactory.get_repository_factory()

# MULTI-BACKEND SUPPORT
class MultiBackendManager:
    """
    Gestor para usar múltiples backends simultáneamente.
    
    Útil cuando se necesita MongoDB para algoritmos y PostgreSQL para usuarios.
    
    Example:
        >>> manager = MultiBackendManager()
        >>> await manager.initialize()
        >>> 
        >>> # Obtener repositorios de diferentes backends
        >>> algo_repo = manager.get_repository('algorithm', DatabaseBackend.MONGODB)
        >>> user_repo = manager.get_repository('user', DatabaseBackend.POSTGRESQL)
    """
    
    def __init__(self):
        """Inicializar gestor multi-backend"""
        self.clients: dict = {}
        self.factories: dict = {}
    
    async def initialize(
        self,
        backends: Optional[list[DatabaseBackend]] = None
    ) -> None:
        """
        Inicializar backends especificados.
        
        Args:
            backends: Lista de backends a inicializar (None = todos configurados)
        """
        if backends is None:
            # Detectar backends configurados
            backends = []
            if settings.MONGODB_URL:
                backends.append(DatabaseBackend.MONGODB)
            if settings.POSTGRES_HOST:
                backends.append(DatabaseBackend.POSTGRESQL)
        
        logger.info(f"Inicializando backends: {[b.value for b in backends]}")
        
        for backend in backends:
            try:
                client = await DatabaseFactory.create_client(backend)
                self.clients[backend] = client
                self.factories[backend] = RepositoryFactory(backend)
                logger.info(f"✓ Backend {backend.value} inicializado")
            except Exception as e:
                logger.error(f"✗ Error inicializando {backend.value}: {e}")
    
    async def close_all(self) -> None:
        """Cerrar todos los clientes"""
        for backend, client in self.clients.items():
            try:
                await client.close()
                logger.info(f"✓ Backend {backend.value} cerrado")
            except Exception as e:
                logger.error(f"Error cerrando {backend.value}: {e}")
        
        self.clients.clear()
        self.factories.clear()
    
    def get_repository(
        self,
        repository_type: str,
        backend: Optional[DatabaseBackend] = None
    ):
        """
        Obtener repositorio de un tipo específico.
        
        Args:
            repository_type: Tipo de repositorio ('algorithm', 'user', etc.)
            backend: Backend a usar (None = usar por defecto)
        
        Returns:
            Instancia del repositorio
        """
        if backend is None:
            backend_str = settings.DATABASE_TYPE.lower()
            backend = DatabaseBackend(backend_str)
        
        factory = self.factories.get(backend)
        if not factory:
            raise DatabaseException(
                f"Backend {backend.value} no inicializado",
                database_type=backend.value
            )
        
        # Mapear tipo a método del factory
        repo_methods = {
            'algorithm': 'create_algorithm_repository',
            'analysis': 'create_analysis_repository',
            'user': 'create_user_repository',
            'metrics': 'create_metrics_repository',
            'cache': 'create_cache_repository',
        }
        
        method_name = repo_methods.get(repository_type.lower())
        if not method_name:
            raise ValueError(f"Tipo de repositorio desconocido: {repository_type}")
        
        method = getattr(factory, method_name)
        return method()

# SINGLETON MANAGER
_multi_backend_manager: Optional[MultiBackendManager] = None

def get_multi_backend_manager() -> MultiBackendManager:
    """
    Obtener instancia singleton del gestor multi-backend.
    
    Returns:
        MultiBackendManager singleton
    """
    global _multi_backend_manager
    if _multi_backend_manager is None:
        _multi_backend_manager = MultiBackendManager()
    return _multi_backend_manager