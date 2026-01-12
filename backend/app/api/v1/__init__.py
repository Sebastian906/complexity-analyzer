"""
API v1 package initialization.

Expone el router principal de la versión 1 y los módulos de endpoints.
"""

from .router import api_router
from .endpoints import analysis, patterns, structures, visualization, services

__all__ = [
    "api_router",
    "analysis",
    "patterns",
    "structures",
    "visualization",
    "services",
]