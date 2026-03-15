"""
Telemetry - Observabilidad con OpenTelemetry

Ubicación: app/infrastructure/telemetry/telemetry.py

Por qué aquí y no en app/telemetry.py:
    OpenTelemetry es una dependencia de infraestructura (exporta datos a
    Jaeger, OTLP, consola). Igual que Redis o MongoDB, es un servicio
    externo al dominio. La arquitectura hexagonal del proyecto coloca
    estas integraciones en app/infrastructure/.

Qué instrumenta:
    - FastAPI: cada request HTTP se convierte en un span automáticamente
    - httpx: llamadas a LLMs (Claude, Gemini, Ollama) se trazan
    - Redis: operaciones de caché se trazan
    - Spans manuales: parse, analyze, detect_patterns, detect_structures

Activar con:
    OTEL_ENABLED=true en .env
    pip install opentelemetry-sdk opentelemetry-instrumentation-fastapi

Ver trazas en consola (sin instalar Jaeger):
    OTEL_EXPORTER=console
    Las trazas aparecen en stdout al completar cada request.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any, Generator, Optional

logger = logging.getLogger(__name__)

# Importaciones opcionales — el sistema funciona sin OpenTelemetry
try:
    from opentelemetry import trace
    from opentelemetry.sdk.resources import Resource, SERVICE_NAME
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    OTEL_SDK = True
except ImportError:
    OTEL_SDK = False
    trace = None  # type: ignore[assignment]

try:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    OTEL_FASTAPI = True
except ImportError:
    OTEL_FASTAPI = False

try:
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    OTEL_HTTPX = True
except ImportError:
    OTEL_HTTPX = False

try:
    from opentelemetry.instrumentation.redis import RedisInstrumentor
    OTEL_REDIS = True
except ImportError:
    OTEL_REDIS = False

# Estado interno
_tracer: Optional[Any] = None
_initialized: bool = False

def setup_telemetry(app: Any = None) -> bool:
    """
    Configura OpenTelemetry. Llamar desde el lifespan de FastAPI.

    Args:
        app: Instancia de FastAPI (para instrumentar endpoints automáticamente)

    Returns:
        True si se configuró, False si está deshabilitado o no disponible.

    Ejemplo en main.py (dentro del lifespan, bloque STARTUP):
        from app.infrastructure.telemetry import setup_telemetry
        setup_telemetry(app)
    """
    global _tracer, _initialized

    if _initialized:
        return True

    try:
        from app.core.config import settings
        if not getattr(settings, "OTEL_ENABLED", False):
            logger.info("OpenTelemetry deshabilitado (OTEL_ENABLED=false)")
            return False
    except Exception:
        return False

    if not OTEL_SDK:
        logger.warning(
            "OpenTelemetry SDK no instalado. "
            "Ejecutar: pip install opentelemetry-sdk "
            "opentelemetry-instrumentation-fastapi "
            "opentelemetry-instrumentation-httpx"
        )
        return False

    try:
        from app.core.config import settings

        service_name = getattr(settings, "OTEL_SERVICE_NAME", "complexity-analyzer")
        exporter_type = getattr(settings, "OTEL_EXPORTER", "console")
        exporter_endpoint = getattr(settings, "OTEL_EXPORTER_ENDPOINT", "")

        resource = Resource(attributes={
            SERVICE_NAME: service_name,
            "service.version": getattr(settings, "APP_VERSION", "1.0.0"),
            "deployment.environment": getattr(settings, "APP_ENV", "development"),
        })

        provider = TracerProvider(resource=resource)
        exporter = _create_exporter(exporter_type, exporter_endpoint)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)

        _tracer = trace.get_tracer("complexity-analyzer")

        # Instrumentar FastAPI — crea spans automáticos para cada endpoint
        if app and OTEL_FASTAPI:
            FastAPIInstrumentor.instrument_app(
                app,
                tracer_provider=provider,
                excluded_urls="/api/v1/health,/,/docs,/redoc,/openapi.json",
            )
            logger.info("FastAPI instrumentado con OpenTelemetry")

        # Instrumentar httpx — trazas para llamadas a Claude, Gemini, Ollama
        if OTEL_HTTPX:
            HTTPXClientInstrumentor().instrument()
            logger.info("httpx instrumentado (llamadas a LLMs serán trazadas)")

        # Instrumentar Redis — trazas para operaciones de caché
        if OTEL_REDIS:
            RedisInstrumentor().instrument()
            logger.info("Redis instrumentado (operaciones de caché serán trazadas)")

        _initialized = True
        logger.info(
            f"OpenTelemetry activo: service={service_name}, "
            f"exporter={exporter_type}"
        )
        return True

    except Exception as e:
        logger.error(f"Error configurando OpenTelemetry: {e}")
        return False

def shutdown_telemetry() -> None:
    """
    Cierra OpenTelemetry. Llamar desde el lifespan de FastAPI (bloque SHUTDOWN).

    Hace flush de todos los spans pendientes antes de cerrar.

    Ejemplo en main.py:
        from app.infrastructure.telemetry import shutdown_telemetry
        shutdown_telemetry()
    """
    global _initialized
    if not _initialized or not OTEL_SDK:
        return
    try:
        provider = trace.get_tracer_provider()
        if hasattr(provider, "shutdown"):
            provider.shutdown()
        _initialized = False
        logger.info("OpenTelemetry cerrado y spans exportados")
    except Exception as e:
        logger.warning(f"Error cerrando OpenTelemetry: {e}")

def _create_exporter(exporter_type: str, endpoint: str) -> Any:
    """Crea el exporter según configuración."""
    if exporter_type == "otlp":
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                OTLPSpanExporter,
            )
            url = endpoint or "http://localhost:4317"
            logger.info(f"OTLP exporter → {url}")
            return OTLPSpanExporter(endpoint=url)
        except ImportError:
            logger.warning(
                "opentelemetry-exporter-otlp no instalado. "
                "Ejecutar: pip install opentelemetry-exporter-otlp. "
                "Usando consola como fallback."
            )

    elif exporter_type == "jaeger":
        try:
            from opentelemetry.exporter.jaeger.thrift import JaegerExporter
            url = endpoint or "http://localhost:14268/api/traces"
            logger.info(f"Jaeger exporter → {url}")
            return JaegerExporter(collector_endpoint=url)
        except ImportError:
            logger.warning(
                "opentelemetry-exporter-jaeger no instalado. "
                "Usando consola como fallback."
            )

    logger.info("OpenTelemetry exporter: consola (stdout)")
    return ConsoleSpanExporter()

# API pública para uso en el dominio
@contextmanager
def trace_operation(
    name: str,
    attributes: Optional[dict] = None,
) -> Generator[Any, None, None]:
    """
    Context manager para instrumentar una operación con un span.

    Si OpenTelemetry no está activo, es un no-op completamente transparente.
    El código de dominio no necesita saber si OTel está habilitado.

    Args:
        name: Nombre del span. Convención: "module.operation"
              Ej: "parser.parse_algorithm", "analyzer.compute_big_o"
        attributes: Atributos del span para búsqueda y filtrado.
              Ej: {"algorithm.name": "mergeSort", "algorithm.big_o": "O(n log n)"}

    Yields:
        El span activo (o None si OTel no está activo)

    Ejemplo en analysis_orchestrator.py:
        from app.infrastructure.telemetry import trace_operation

        with trace_operation("orchestrator.parse", {"algorithm.code_length": len(code)}):
            ast = parser.parse(code)

        with trace_operation("orchestrator.analyze") as span:
            result = engine.analyze(ast)
            if span:
                span.set_attribute("algorithm.big_o", result.big_o)
                span.set_attribute("algorithm.is_recursive", result.is_recursive)
    """
    if not _initialized or not OTEL_SDK or _tracer is None:
        yield None
        return

    with _tracer.start_as_current_span(name) as span:
        if attributes:
            for key, value in attributes.items():
                if value is not None:
                    span.set_attribute(key, str(value))
        try:
            yield span
        except Exception as exc:
            span.record_exception(exc)
            span.set_status(trace.StatusCode.ERROR, str(exc))
            raise

def get_current_trace_id() -> Optional[str]:
    """
    Retorna el trace ID del request actual.

    Úsalo para correlacionar logs con trazas en Jaeger:
        logger.error("Fallo en análisis", extra={"trace_id": get_current_trace_id()})

    Returns:
        String hexadecimal de 32 caracteres, o None si OTel no está activo.
    """
    if not OTEL_SDK:
        return None
    try:
        span = trace.get_current_span()
        ctx = span.get_span_context()
        if ctx and ctx.is_valid:
            return format(ctx.trace_id, "032x")
    except Exception:
        pass
    return None

def is_telemetry_enabled() -> bool:
    """Retorna True si OpenTelemetry está activo."""
    return _initialized