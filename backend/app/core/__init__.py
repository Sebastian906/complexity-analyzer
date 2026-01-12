"""
Core package initialization.

Expone los submódulos principales del núcleo de la aplicación.
"""

from . import analyzer
from . import parser
from . import patterns
from . import visualization
from . import data_structures
from .config import *
from .constants import *
from .exceptions import *

__all__ = [
    "analyzer",
    "parser",
    "patterns",
    "visualization",
    "data_structures",
]