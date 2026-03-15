"""
Telemetry Infrastructure - OpenTelemetry

Expone la API pública del módulo de telemetría.

Uso desde cualquier parte del proyecto:
    from app.infrastructure.telemetry import setup_telemetry, trace_operation
"""

from app.infrastructure.telemetry.telemetry import (
    setup_telemetry,
    shutdown_telemetry,
    trace_operation,
    get_current_trace_id,
    is_telemetry_enabled,
)

__all__ = [
    "setup_telemetry",
    "shutdown_telemetry",
    "trace_operation",
    "get_current_trace_id",
    "is_telemetry_enabled",
]