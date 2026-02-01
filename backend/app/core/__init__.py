"""
Core package initialization.

Expone los submódulos principales del núcleo de la aplicación.

Contiene los módulos principales:
- config: Configuración del sistema
- constants: Constantes
- exceptions: Excepciones personalizadas
- security: Seguridad y autenticación
- parser: Parsing de pseudocódigo
- analyzer: Análisis de complejidad
- patterns: Detección de patrones
- data_structures: Detección de estructuras
- visualization: Generación de visualizaciones
"""

from . import analyzer
from . import parser
from . import patterns
from . import visualization
from . import data_structures
from .config import settings, get_settings, Settings
from .constants import *
from .exceptions import *
from . import security

__all__ = [
    # Módulos principales
    "analyzer",
    "parser",
    "patterns",
    "visualization",
    "data_structures",
    "security",
    
    # Config
    "settings",
    "get_settings",
    "Settings",
]