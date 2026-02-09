# scripts/validate_integrations.py
"""Valida que las integraciones externas estén configuradas"""

# Ensure project root is on sys.path so `app` package is importable
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from app.core.config import settings
from app.infrastructure import validate_infrastructure

def main():
    print("VALIDACIÓN DE INTEGRACIONES\n")
    
    status = validate_infrastructure()
    
    # Mostrar estado
    for component, is_ready in status.items():
        icon = "✓" if is_ready else "✗"
        print(f"{icon} {component}: {'Ready' if is_ready else 'Not configured'}")
    
    # Advertencias
    if not status['mongodb'] and not status['postgresql']:
        print("\n⚠️  ADVERTENCIA: No hay base de datos configurada")
    
    if not status['claude'] and not status['gemini']:
        print("⚠️  ADVERTENCIA: No hay LLMs configurados")
    
    if not status['redis']:
        print("⚠️  INFO: Redis no configurado (caché deshabilitado)")

if __name__ == "__main__":
    main()