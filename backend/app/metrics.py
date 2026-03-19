"""
Métricas Prometheus del sistema.

Todas las métricas del sistema viven aquí. Los módulos que quieren
registrar métricas importan desde este módulo, no crean sus propios
objetos de Prometheus.

Activar en main.py:
    if settings.ENABLE_PROMETHEUS:
        from prometheus_fastapi_instrumentator import Instrumentator
        Instrumentator().instrument(app).expose(app, endpoint="/metrics")
        from app.metrics import setup_custom_metrics
        setup_custom_metrics()

Usar desde cualquier módulo:
    from app.metrics import METRICS
    METRICS.analysis_total.labels(status="success", pattern="brute_force").inc()
    METRICS.llm_response_score.labels(llm_name="ollama").observe(0.85)
"""

from __future__ import annotations

from dataclasses import dataclass

from prometheus_client import Counter, Gauge, Histogram

# Buckets personalizados para latencias del sistema 
# El análisis típico tarda 50-500ms; el LLM puede tardar 1-10s
_ANALYSIS_BUCKETS = [0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
_LLM_BUCKETS      = [0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0, 60.0]
_STEP_BUCKETS     = [0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0]

@dataclass(frozen=True)
class _Metrics:
    """
    Contenedor de todas las métricas del sistema.

    frozen=True evita que se sobreescriba un contador por accidente.
    """

    # Análisis 
    analysis_total: Counter
    analysis_duration: Histogram
    pipeline_step_duration: Histogram

    # LLM 
    llm_requests_total: Counter
    llm_response_score: Histogram
    llm_circuit_breaker_open: Gauge
    llm_fallback_total: Counter

    # Cache
    cache_hits_total: Counter
    cache_misses_total: Counter

    # Evaluation / Regression
    evaluation_accuracy: Gauge
    regression_passed: Gauge

def _build_metrics() -> _Metrics:
    """Construye todos los objetos Prometheus una única vez."""
    return _Metrics(
        # Análisis 
        analysis_total=Counter(
            "complexity_analyzer_analyses_total",
            "Total de análisis ejecutados",
            ["status", "algorithm_pattern"],
        ),
        analysis_duration=Histogram(
            "complexity_analyzer_analysis_duration_seconds",
            "Duración del análisis completo",
            ["pipeline_version"],
            buckets=_ANALYSIS_BUCKETS,
        ),
        pipeline_step_duration=Histogram(
            "complexity_analyzer_pipeline_step_seconds",
            "Duración por paso del pipeline",
            ["step_name"],
            buckets=_STEP_BUCKETS,
        ),
        # ── LLM ───────────────────────────────────────────────────────────────
        llm_requests_total=Counter(
            "complexity_analyzer_llm_requests_total",
            "Total de llamadas a LLMs",
            ["llm_name", "status"],
        ),
        llm_response_score=Histogram(
            "complexity_analyzer_llm_response_score",
            "Score de calidad de respuesta LLM",
            ["llm_name"],
            buckets=[0.1, 0.3, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
        ),
        llm_circuit_breaker_open=Gauge(
            "complexity_analyzer_circuit_breaker_open",
            "Estado del circuit breaker (1=abierto, 0=cerrado)",
            ["llm_name"],
        ),
        llm_fallback_total=Counter(
            "complexity_analyzer_llm_fallback_total",
            "Veces que se activó el fallback del router",
            ["primary_llm", "fallback_llm"],
        ),
        # ── Cache ──────────────────────────────────────────────────────────────
        cache_hits_total=Counter(
            "complexity_analyzer_cache_hits_total",
            "Cache hits por tipo",
            ["cache_type"],
        ),
        cache_misses_total=Counter(
            "complexity_analyzer_cache_misses_total",
            "Cache misses por tipo",
            ["cache_type"],
        ),
        # ── Evaluation ─────────────────────────────────────────────────────────
        evaluation_accuracy=Gauge(
            "complexity_analyzer_evaluation_accuracy",
            "Accuracy del sistema sobre casos canónicos (0.0-1.0)",
            ["llm_used"],
        ),
        regression_passed=Gauge(
            "complexity_analyzer_regression_passed",
            "Si el último regression check pasó (1=sí, 0=no)",
        ),
    )

# Singleton — se crea una vez al importar el módulo
METRICS: _Metrics = _build_metrics()

def setup_custom_metrics() -> None:
    """
    Inicializa valores por defecto para métricas tipo Gauge.

    Llamar una vez en el startup de FastAPI después de activar
    prometheus_fastapi_instrumentator. Evita que los Gauges aparezcan
    como "no data" en Grafana hasta el primer evento real.
    """
    from app.core.config import settings

    # Circuit breakers en estado inicial (cerrado = 0)
    for llm_name in ["ollama", "claude", "gemini"]:
        METRICS.llm_circuit_breaker_open.labels(llm_name=llm_name).set(0)

    # Regression: desconocido hasta el primer check
    METRICS.regression_passed.set(-1)

    # Accuracy inicial desconocida
    METRICS.evaluation_accuracy.labels(llm_used=settings.PRIMARY_LLM).set(-1)