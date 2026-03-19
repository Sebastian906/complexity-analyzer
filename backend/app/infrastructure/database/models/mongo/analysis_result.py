"""
Modelo MongoDB para Resultados de Análisis.
"""
from datetime import datetime
from typing import Optional, Dict, Any
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

    # Versionado del sistema 
    system_version: str = Field(
        default="1.0.0",
        description="Versión semver del sistema que generó este análisis"
    )
    pipeline_version: str = Field(
        default="2.0",
        description="Versión del pipeline (2.0 = pipeline formal con pasos)"
    )
    analysis_schema_version: str = Field(
        default="1.0",
        description="Versión del schema de resultado — bump si cambia la estructura"
    )
    llm_used: Optional[str] = Field(
        default=None,
        description="LLM que participó en el análisis (None = solo análisis estático)"
    )
    config_snapshot: Dict[str, Any] = Field(
        default_factory=dict,
        description="Feature flags y configuración activa al momento del análisis"
    )

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "analysis_results"
        indexes = [
            "algorithm",
            "created_at",
        ]