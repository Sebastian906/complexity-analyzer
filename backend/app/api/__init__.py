"""
API package initialization.

Expone el router principal de la API y las dependencias compartidas.
"""

from .dependencies import get_parser, verify_api_key, rate_limit, RateLimiter
from .v1.router import api_router as v1_router

__all__ = [
    "get_parser",
    "verify_api_key",
    "rate_limit",
    "RateLimiter",
    "v1_router",
]