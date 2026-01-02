"""
Script para ejecutar el servidor de desarrollo.

Uso:
    python scripts/run_dev.py
"""

import sys
from pathlib import Path

# Agregar directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

import uvicorn

from app.core.config import settings


def main():
    """Ejecuta el servidor de desarrollo"""
    print(f"Iniciando {settings.APP_NAME} en modo desarrollo...")
    print(f"Entorno: {settings.APP_ENV}")
    print(f"Debug: {settings.DEBUG}")
    print()
    print(f"Servidor corriendo en: http://{settings.HOST}:{settings.PORT}")
    print(f"Documentación Swagger: http://{settings.HOST}:{settings.PORT}/docs")
    print(f"Documentación ReDoc: http://{settings.HOST}:{settings.PORT}/redoc")
    print()
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    main()