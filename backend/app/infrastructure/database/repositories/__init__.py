"""
Repositories Package

Repositorios para acceso a datos:
- BaseRepository: Clase base abstracta
- AlgorithmRepository: Algoritmos (MongoDB)
- AnalysisRepository: Resultados de análisis (MongoDB)
- UserRepository: Usuarios (PostgreSQL)
- MetricsRepository: Métricas (PostgreSQL)
- CacheRepository: Caché (Redis)
"""

from .base_repository import BaseRepository
from .algorithm_repository import AlgorithmRepository
from .analysis_repository import AnalysisRepository
from .user_repository import UserRepository
from .metrics_repository import MetricsRepository
from .cache_repository import CacheRepository, cached

__all__ = [
    # Base
    "BaseRepository",
    
    # MongoDB Repositories
    "AlgorithmRepository",
    "AnalysisRepository",
    
    # PostgreSQL Repositories
    "UserRepository",
    "MetricsRepository",
    
    # Redis Repository
    "CacheRepository",
    "cached",
]