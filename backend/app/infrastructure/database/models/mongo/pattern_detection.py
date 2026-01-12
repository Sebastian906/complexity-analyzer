from datetime import datetime
from typing import List, Dict, Any, Optional
from beanie import Document, Link
from pydantic import Field

from app.infrastructure.database.models.mongo.algorithm import Algorithm

class PatternDetection(Document):
    """Modelo MongoDB para Detección de Patrones"""

    # Relación
    algorithm: Link[Algorithm]

    # Patrón principal
    primary_pattern: str = Field(..., description="Patrón principal detectado")
    primary_confidence: float = Field(..., ge=0.0, le=1.0)

    # Todos los patrones detectados
    patterns_found: List[Dict[str, Any]] = Field(default_factory=list)

    # Estructuras de datos
    structures_found: List[Dict[str, Any]] = Field(default_factory=list)

    # Metadata
    detection_time: float

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "pattern_detections"
        indexes = [
            "algorithm",
            "primary_pattern",
            "created_at",
        ]