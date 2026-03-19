"""
VersioningMixin — Campos de versionado reutilizables para modelos MongoDB.

En lugar de duplicar los campos en cada modelo, heredar este mixin.

Uso:
    from app.infrastructure.database.models.mongo.versioning import VersioningMixin
    from beanie import Document
    from pydantic import Field

    class AnalysisResult(Document, VersioningMixin):
        # ... campos existentes ...
        pass

O como campos directos si el modelo no puede heredar del mixin:
    system_version: str = Field(default="1.0.0")
    pipeline_version: str = Field(default="2.0")
    analysis_schema_version: str = Field(default="1.0")
    llm_used: Optional[str] = Field(default=None)
    config_snapshot: dict = Field(default_factory=dict)
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

class VersioningMixin(BaseModel):
    """
    Mixin con campos de versionado para modelos MongoDB.

    Permite reproducir exactamente qué configuración generó
    un resultado específico y comparar entre versiones del sistema.

    Todos los campos tienen defaults seguros para que documentos
    históricos sin estos campos sigan siendo válidos.
    """

    system_version: str = Field(
        default="1.0.0",
        description="Versión semver del sistema (app.core.config.APP_VERSION)"
    )
    pipeline_version: str = Field(
        default="2.0",
        description="Versión del pipeline de análisis"
    )
    analysis_schema_version: str = Field(
        default="1.0",
        description="Versión del schema de resultado"
    )
    llm_used: Optional[str] = Field(
        default=None,
        description="LLM que participó en el análisis (None = sin LLM)"
    )
    config_snapshot: dict = Field(
        default_factory=dict,
        description="Snapshot de feature flags activos al momento del análisis"
    )

    @classmethod
    def build_config_snapshot(cls, pipeline_steps: list[str] = None) -> dict:
        """
        Construye el snapshot de configuración desde settings actuales.

        Llamar antes de guardar un documento para capturar la configuración
        que produjo ese resultado específico.

        Args:
            pipeline_steps: Lista de nombres de pasos activos en el pipeline.

        Returns:
            Dict con la configuración relevante del momento.

        Example:
            result_doc.config_snapshot = VersioningMixin.build_config_snapshot(
                pipeline_steps=["parse", "complexity", "patterns", "structures"]
            )
        """
        try:
            from app.core.config import settings
            return {
                "primary_llm":            settings.PRIMARY_LLM,
                "fallback_llm":           settings.FALLBACK_LLM,
                "multiagent_enabled":     settings.ENABLE_MULTIAGENT_SYSTEM,
                "llm_validation_enabled": getattr(
                    settings, "LLM_VALIDATION_ENABLED", False
                ),
                "pipeline_steps":         pipeline_steps or [],
                "cache_ttl_analysis":     settings.CACHE_TTL_ANALYSIS,
            }
        except Exception:
            return {"pipeline_steps": pipeline_steps or []}