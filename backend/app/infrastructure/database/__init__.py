"""
Database Infrastructure Package

Proporciona:
- Clientes para MongoDB, PostgreSQL
- Factory para creación de clientes
- Gestor de conexiones
- Modelos de datos
- Repositorios
"""

from .mongodb_client import MongoDBClient, get_mongodb_client
from .postgresql_client import PostgreSQLClient, get_postgresql_client
from .connection import (
    DatabaseConnectionManager,
    get_connection_manager,
    init_databases,
    close_databases,
    check_database_health
)
from .database_factory import (
    DatabaseFactory,
    RepositoryFactory,
    DatabaseBackend,
    get_default_client,
    get_default_repository_factory,
    MultiBackendManager,
    get_multi_backend_manager
)

__all__ = [
    # MongoDB
    "MongoDBClient",
    "get_mongodb_client",
    
    # PostgreSQL
    "PostgreSQLClient",
    "get_postgresql_client",
    
    # Connection Manager
    "DatabaseConnectionManager",
    "get_connection_manager",
    "init_databases",
    "close_databases",
    "check_database_health",
    
    # Factory
    "DatabaseFactory",
    "RepositoryFactory",
    "DatabaseBackend",
    "get_default_client",
    "get_default_repository_factory",
    "MultiBackendManager",
    "get_multi_backend_manager",
]