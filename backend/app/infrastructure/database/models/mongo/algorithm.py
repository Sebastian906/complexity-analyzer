from datetime import datetime
from typing import Optional, List, Dict, Any
from beanie import Document
from pydantic import Field

class Algorithm(Document):
    """Modelo MongoDB para Algoritmos"""

    # Identificación
    name: str = Field(..., description="Nombre del algoritmo")
    code: str = Field(..., description="Código del algoritmo")
    language: str = Field(default="pseudocode", description="Lenguaje del código")

    # Clasificación
    category: Optional[str] = Field(None, description="Categoría del algoritmo")
    tags: List[str] = Field(default_factory=list, description="Tags de búsqueda")

    # Metadata
    description: Optional[str] = None
    author: Optional[str] = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "algorithms"
        indexes = [
            "name",
            "category",
            "tags",
            "created_at",
        ]

    class Config:
        json_schema_extra = {
            "example": {
                "name": "bubble_sort",
                "code": "algorithm bubbleSort(A[n])...",
                "category": "sorting",
                "tags": ["sorting", "quadratic"]
            }
        }