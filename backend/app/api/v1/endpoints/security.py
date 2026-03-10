"""
Security Endpoint - Estado y métricas del IDS

Sigue el mismo patrón que health.py:
    GET /api/v1/security/ids/status   → resumen del IDS
    GET /api/v1/security/ids/threats  → amenazas activas
    GET /api/v1/security/ids/check/{ip} → ¿IP bloqueada?
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()

def _get_monitor():
    """Retorna el singleton del monitor IDS desde main.py (o None)."""
    try:
        import app.main as main_module
        return getattr(main_module, "_ids_monitor", None)
    except Exception:
        return None

@router.get("/ids/status", summary="Estado del IDS")
async def ids_status():
    """Resumen general del sistema de detección de intrusiones."""
    monitor = _get_monitor()
    if monitor is None:
        return JSONResponse(
            status_code=200,
            content={"available": False, "reason": "IDS deshabilitado o no inicializado"},
        )
    return {"available": True, **monitor.get_threat_summary()}

@router.get("/ids/threats", summary="Amenazas activas")
async def active_threats():
    """Lista de amenazas activas dentro de la ventana TTL configurada."""
    monitor = _get_monitor()
    if monitor is None:
        return {"available": False, "count": 0, "threats": []}

    threats = monitor.get_active_threats()
    return {
        "available": True,
        "count":     len(threats),
        "threats":   [t.to_dict() for t in threats],
    }

@router.get("/ids/check/{ip}", summary="Verificar IP")
async def check_ip(ip: str):
    """Verifica si una IP está actualmente bloqueada por el IDS."""
    monitor = _get_monitor()
    return {
        "ip":        ip,
        "blocked":   monitor.is_ip_blocked(ip) if monitor else False,
        "available": monitor is not None,
    }