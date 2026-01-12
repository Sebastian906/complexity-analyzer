from datetime import datetime
from typing import Optional, Dict, Any, List
from beanie import Document, Link
from pydantic import Field

from app.infrastructure.database.models.mongo.algorithm import Algorithm

class AnalysisResult(Document):
    """Modelo MongoDB para Resultados de Análisis"""

    # Relación con algoritmo
    algorithm: Link[Algorithm]

    # Complejidades
    big_o: str = Field(..., description="Complejidad O (peor caso)")
    omega: str = Field(..., description="Complejidad Ω (mejor caso)")
    theta: Optional[str] = Field(None, description="Complejidad Θ (caso promedio)")
    space_complexity: Optional[str] = None

    # Ecuaciones de recurrencia
    temporal_recurrence: Optional[str] = None
    spatial_recurrence: Optional[str] = None

    # Análisis línea por línea
    line_by_line: Optional[Dict[str, Any]] = None

    # Metadata
    analysis_time: float = Field(..., description="Tiempo de análisis en segundos")
    analyzer_version: str = Field(default="1.0.0")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "analysis_results"
        indexes = [
            "algorithm",
            "created_at",
        ]