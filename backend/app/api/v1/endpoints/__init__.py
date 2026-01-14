"""
API Endpoints v1

Endpoints REST de la versión 1 de la API.
"""

# Importar todos los routers para que FastAPI los detecte
from app.api.v1.endpoints import analysis
from app.api.v1.endpoints import patterns
from app.api.v1.endpoints import structures
from app.api.v1.endpoints import visualization
from app.api.v1.endpoints import services
from app.api.v1.endpoints import export

__all__ = [
    "analysis",
    "patterns",
    "structures",
    "visualization",
    "services",
    "export",
]