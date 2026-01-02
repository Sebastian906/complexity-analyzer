"""
Router Principal API v1

Registra todos los endpoints de la API versión 1.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import analysis

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