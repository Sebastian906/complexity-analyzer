"""
Mappers package - Conversores entre objetos del core y schemas de la API

Exporta los mappers disponibles para ser usados por los servicios y endpoints.

Actualmente incluye:
- `PatternMapper`: convertir resultados de detección de patrones a schemas Pydantic
"""

from .pattern_mapper import PatternMapper

__all__ = [
	"PatternMapper",
]
