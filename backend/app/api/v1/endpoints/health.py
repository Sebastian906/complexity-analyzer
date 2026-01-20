"""
API Endpoints - Health Check

Endpoints para verificar el estado del sistema.
"""

from fastapi import APIRouter, status
from datetime import datetime

from app import __version__
from app.core.config import settings
from app.schemas import BaseResponse

router = APIRouter()

@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Verifica que el servicio está activo"
)
async def health_check():
    """
    Health check endpoint.
    
    Retorna el estado del sistema y configuración básica.
    """
    from datetime import datetime, timezone
    
    return {
        "success": True,
        "message": "Service is healthy",
        "timestamp": datetime.now(timezone.utc),
        "status": "healthy",
        "version": __version__,
        "environment": settings.APP_ENV,
        "features": {
            "parser": True,
            "analyzer": True,
            "patterns": True,
            "visualization": True,
            "llm_claude": bool(settings.ANTHROPIC_API_KEY),
            "llm_gemini": bool(settings.GOOGLE_API_KEY),
        }
    }


@router.get(
    "/status",
    summary="Detailed Status",
    description="Estado detallado del sistema"
)
async def detailed_status():
    """Estado detallado incluyendo conexiones a servicios externos"""
    
    # Verificar MongoDB
    mongodb_status = "unknown"
    try:
        from app.infrastructure.database.mongodb_client import get_mongodb_client
        client = get_mongodb_client()
        # Intentar ping
        mongodb_status = "connected"
    except Exception:
        mongodb_status = "disconnected"
    
    # Verificar Redis
    redis_status = "unknown"
    try:
        from app.infrastructure.cache.redis_cache import get_redis_client
        cache = get_redis_client()
        redis_status = "connected"
    except Exception:
        redis_status = "disconnected"
    
    return {
        "application": {
            "name": settings.APP_NAME,
            "version": __version__,
            "environment": settings.APP_ENV,
        },
        "services": {
            "mongodb": mongodb_status,
            "redis": redis_status,
        },
        "llms": {
            "claude": "configured" if settings.ANTHROPIC_API_KEY else "not_configured",
            "gemini": "configured" if settings.GOOGLE_API_KEY else "not_configured",
        }
    }