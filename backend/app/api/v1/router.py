"""
Router Principal API v1

Registra todos los endpoints de la API versión 1.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import analysis
from app.api.v1.endpoints import patterns
from app.api.v1.endpoints import structures

# Router principal
api_router = APIRouter()

# Incluir endpoints
# api_router.include_router(
#     health.router,
#     prefix="/health",
#     tags=["Health Check"]
# )

# api_router.include_router(
#     algorithms.router,
#     prefix="/algorithms",
#     tags=["Algorithms"]
# )

api_router.include_router(
    analysis.router,
    prefix="/analysis",
    tags=["Analysis"]
)

api_router.include_router(
    patterns.router,
    prefix="/patterns",
    tags=["Patterns"]
)

api_router.include_router(
    structures.router,
    prefix="/structures",
    tags=["Data Structures"]
)