"""
API package initialization.

Expone el router principal de la API y las dependencias compartidas.

Contiene:
- dependencies: Dependency injection
- middleware: Middlewares personalizados
- v1: API versión 1
"""

from .dependencies import get_parser, verify_api_key, rate_limit, RateLimiter
from .v1.router import api_router as v1_router
from . import middleware

__all__ = [
    # Dependencies
    "get_parser",
    "verify_api_key",
    "rate_limit",
    "RateLimiter",
    
    # Routers
    "v1_router",
    
    # Middleware
    "middleware",
]