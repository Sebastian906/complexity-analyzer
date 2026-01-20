"""
Router Principal API v1

Registra todos los endpoints de la API versión 1.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import health
from app.api.v1.endpoints import algorithms
from app.api.v1.endpoints import analysis
from app.api.v1.endpoints import patterns
from app.api.v1.endpoints import structures
from app.api.v1.endpoints import visualization
from app.api.v1.endpoints import validation
from app.api.v1.endpoints import services
from app.api.v1.endpoints import export
# Router principal
api_router = APIRouter()

# Incluir endpoints
api_router.include_router(
    health.router,
    prefix="/health",
    tags=["Health Check"]
)

api_router.include_router(
    algorithms.router,
    prefix="/algorithms",
    tags=["Algorithms"]
)

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

api_router.include_router(
    visualization.router,
    prefix="/visualizations", 
    tags=["Visualization"]
)

api_router.include_router(
    validation.router,
    prefix="/validation",
    tags=["Validation"]
)

api_router.include_router(
    services.router,
    prefix="/services",
    tags=["Services"]
)

api_router.include_router(
    export.router,
    prefix="/export",
    tags=["Export"]
)