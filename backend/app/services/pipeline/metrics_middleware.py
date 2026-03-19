"""
services/pipeline/metrics_middleware.py

Instrumenta el pipeline con métricas Prometheus sin modificar
la lógica de ningún paso. Se activa como wrapper opcional.

Uso en el orchestrator:
    from app.services.pipeline.metrics_middleware import MetricsPipelineMiddleware

    pipeline = MetricsPipelineMiddleware(AnalysisPipeline([...]))
    ctx = await pipeline.run(ctx)

Si Prometheus no está habilitado, MetricsPipelineMiddleware es un no-op
que simplemente delega al pipeline original.
"""

from __future__ import annotations

import time

from app.services.pipeline.context import PipelineContext
from app.services.pipeline.pipeline import AnalysisPipeline

class MetricsPipelineMiddleware:
    """
    Wrapper del pipeline que registra métricas Prometheus.

    Instrumenta:
    - Duración total del análisis
    - Duración por paso (ctx.step_times ya los tiene, solo los expone)
    - Contador de análisis exitosos/fallidos con label del patrón primario
    """

    def __init__(self, pipeline: AnalysisPipeline) -> None:
        self._pipeline = pipeline
        self._enabled = self._check_enabled()

    def _check_enabled(self) -> bool:
        try:
            from app.core.config import settings
            return settings.ENABLE_PROMETHEUS
        except Exception:
            return False

    async def run(self, ctx: PipelineContext) -> PipelineContext:
        if not self._enabled:
            return await self._pipeline.run(ctx)

        from app.metrics import METRICS

        start = time.perf_counter()
        ctx = await self._pipeline.run(ctx)
        elapsed = time.perf_counter() - start

        # Duración total
        METRICS.analysis_duration.labels(
            pipeline_version=ctx.pipeline_version
        ).observe(elapsed)

        # Duración por paso (ya están en ctx.step_times)
        for step_name, duration in ctx.step_times.items():
            METRICS.pipeline_step_duration.labels(
                step_name=step_name
            ).observe(duration)

        # Contador análisis total
        status = "success" if not ctx.errors else "error"
        pattern = "unknown"
        if ctx.patterns and ctx.patterns.primary_pattern:
            pattern = ctx.patterns.primary_pattern.pattern.pattern_type.value

        METRICS.analysis_total.labels(
            status=status,
            algorithm_pattern=pattern,
        ).inc()

        return ctx

    # Delegación de la interfaz de AnalysisPipeline
    def register_step(self, step, position: int = -1) -> None:
        self._pipeline.register_step(step, position)

    def remove_step(self, name: str) -> bool:
        return self._pipeline.remove_step(name)

    @property
    def step_names(self) -> list[str]:
        return self._pipeline.step_names