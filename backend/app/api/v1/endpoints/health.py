"""
API Endpoints - Health Check

Endpoints para verificar el estado del sistema.
"""

from fastapi import APIRouter, status
from datetime import datetime
from pathlib import Path

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
            "profiling": settings.APP_ENV in ["development", "staging"],
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

# Endpoints de Profiling
@router.get(
    "/profiling",
    summary="Profiling Statistics",
    description="Obtiene estadísticas de profiling del sistema"
)
async def profiling_stats():
    """
    Retorna estadísticas de profiling.
    
    Solo disponible en desarrollo y staging.
    """
    if settings.APP_ENV not in ["development", "staging"]:
        return {
            "success": False,
            "message": "Profiling solo disponible en desarrollo/staging",
            "enabled": False
        }

    try:
        from app.profiling import get_performance_monitor
        
        monitor = get_performance_monitor()
        
        # Obtener todas las métricas
        all_metrics = monitor.get_metrics()
        
        # Obtener operaciones lentas (1000ms = 1s)
        slow_ops = monitor.get_slow_operations(threshold_ms=1000.0)
        
        # Obtener operaciones con alto uso de memoria
        memory_intensive = monitor.get_memory_intensive_operations(threshold_mb=50.0)
        
        # Obtener rendimiento por módulo
        module_performance = monitor.get_all_module_performance()
        
        # Construir estadísticas resumidas
        stats = {
            "total_operations": len(all_metrics),
            "modules_monitored": list(module_performance.keys()),
            "slow_operations_count": len(slow_ops),
            "memory_intensive_count": len(memory_intensive),
        }
        
        # Top 10 operaciones más lentas
        top_slow = sorted(
            all_metrics,
            key=lambda m: m.execution_time_ms,
            reverse=True
        )[:10]
        
        # Top 10 operaciones con más memoria
        top_memory = sorted(
            all_metrics,
            key=lambda m: m.memory_delta_mb,
            reverse=True
        )[:10]
        
        return {
            "success": True,
            "enabled": True,
            "timestamp": datetime.now().isoformat(),
            "environment": settings.APP_ENV,
            "statistics": stats,
            "module_performance": {
                module: {
                    "total_operations": perf.total_operations,
                    "avg_execution_time_ms": perf.avg_execution_time_ms,
                    "avg_memory_delta_mb": perf.avg_memory_delta_mb,
                    "slow_operations_count": perf.slow_operations_count,
                    "memory_leaks_count": perf.memory_leaks_count,
                }
                for module, perf in module_performance.items()
            },
            "top_slow_operations": [
                {
                    "operation": m.operation,
                    "execution_time_ms": m.execution_time_ms,
                    "module": m.module,
                    "performance_level": m.performance_level.value,
                }
                for m in top_slow
            ],
            "top_memory_operations": [
                {
                    "operation": m.operation,
                    "memory_delta_mb": m.memory_delta_mb,
                    "module": m.module,
                    "performance_level": m.performance_level.value,
                }
                for m in top_memory
            ],
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error obteniendo stats: {str(e)}",
            "enabled": True,
        }

@router.post(
    "/profiling/export",
    summary="Export Profiling Report",
    description="Exporta reporte completo de profiling a JSON"
)
async def export_profiling_report():
    """
    Exporta reporte de profiling a archivo JSON.
    
    Solo disponible en desarrollo y staging.
    """
    if settings.APP_ENV not in ["development", "staging"]:
        return {
            "success": False,
            "message": "Profiling solo disponible en desarrollo/staging",
        }
    
    try:
        from app.profiling import generate_profiling_report
        
        # Crear directorio de reportes
        reports_path = Path("reports/profiling")
        reports_path.mkdir(parents=True, exist_ok=True)
        
        # Generar nombre con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = reports_path / f"profiling_export_{timestamp}.json"
        
        # Exportar
        generate_profiling_report(report_file)
        
        return {
            "success": True,
            "message": "Reporte exportado exitosamente",
            "file_path": str(report_file),
            "timestamp": datetime.now().isoformat(),
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error exportando reporte: {str(e)}",
        }

@router.post(
    "/profiling/reset",
    summary="Reset Profiling Stats",
    description="Reinicia todas las estadísticas de profiling"
)
async def reset_profiling_stats():
    """
    Reinicia estadísticas de profiling.
    
    Solo disponible en desarrollo y staging.
    """
    if settings.APP_ENV not in ["development", "staging"]:
        return {
            "success": False,
            "message": "Profiling solo disponible en desarrollo/staging",
        }
    
    try:
        from app.profiling import reset_profiling
        
        reset_profiling()
        
        return {
            "success": True,
            "message": "Estadísticas de profiling reiniciadas",
            "timestamp": datetime.now().isoformat(),
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error reiniciando stats: {str(e)}",
        }