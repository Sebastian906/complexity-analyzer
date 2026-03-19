"""
CircuitBreaker — Detecta LLMs degradados y evita llamadas en cascada.

Patrón Circuit Breaker clásico con tres estados:
    CLOSED   → llamadas permitidas (operación normal)
    OPEN     → llamadas bloqueadas (demasiados fallos recientes)
    HALF_OPEN → probando si el LLM se recuperó (una llamada de prueba)

Transiciones:
    CLOSED  → OPEN      cuando failures >= threshold en la ventana
    OPEN    → HALF_OPEN cuando pasa recovery_timeout segundos
    HALF_OPEN → CLOSED  cuando la llamada de prueba tiene éxito
    HALF_OPEN → OPEN    cuando la llamada de prueba falla

Diseño:
    - Sin dependencias externas (solo stdlib)
    - Thread-safe para uso en contextos async (asyncio es single-threaded)
    - Serializable a dict para métricas Prometheus
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

class CircuitState(str, Enum):
    CLOSED    = "closed"
    OPEN      = "open"
    HALF_OPEN = "half_open"

@dataclass
class CircuitBreakerMetrics:
    """Snapshot del estado del circuit breaker para métricas."""
    name: str
    state: CircuitState
    failure_count: int
    last_failure_time: Optional[float]
    seconds_until_retry: float

    def to_dict(self) -> dict:
        return {
            "name":                self.name,
            "state":               self.state.value,
            "failure_count":       self.failure_count,
            "last_failure_time":   self.last_failure_time,
            "seconds_until_retry": round(self.seconds_until_retry, 1),
        }

class CircuitBreaker:
    """
    Circuit breaker para un LLM específico.

    Un CircuitBreaker por LLM — el LLMRouter mantiene uno por adaptador.

    Args:
        name:              Nombre del LLM (para logs y métricas).
        failure_threshold: Fallos consecutivos para abrir el circuito.
        recovery_timeout:  Segundos antes de intentar HALF_OPEN.
        window_size:       Tamaño de la ventana deslizante de fallos.

    Example:
        >>> cb = CircuitBreaker("ollama", failure_threshold=3)
        >>> if cb.is_open:
        ...     raise RuntimeError("LLM no disponible")
        >>> try:
        ...     result = await llm.generate(prompt)
        ...     cb.record_success()
        ... except Exception:
        ...     cb.record_failure()
        ...     raise
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        window_size: int = 10,
    ) -> None:
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout

        self._state: CircuitState = CircuitState.CLOSED
        self._failures: deque[float] = deque(maxlen=window_size)
        self._last_failure_time: float = 0.0

    #  Estado público                                                     
    @property
    def is_open(self) -> bool:
        """
        True si las llamadas deben ser bloqueadas.

        También maneja la transición OPEN → HALF_OPEN cuando
        ha pasado suficiente tiempo.
        """
        if self._state == CircuitState.OPEN:
            elapsed = time.time() - self._last_failure_time
            if elapsed >= self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                return False
            return True
        return False

    @property
    def state(self) -> CircuitState:
        """Estado actual (evalúa transición OPEN→HALF_OPEN si aplica)."""
        _ = self.is_open
        return self._state

    @property
    def is_half_open(self) -> bool:
        """True si estamos en modo de prueba (una llamada permitida)."""
        return self.state == CircuitState.HALF_OPEN

    #  Registro de resultados                                             
    def record_success(self) -> None:
        """
        Registra una llamada exitosa.

        Si estábamos HALF_OPEN, cierra el circuito (LLM se recuperó).
        Si estábamos CLOSED, limpia el historial de fallos.
        """
        was_half_open = self._state == CircuitState.HALF_OPEN
        self._failures.clear()
        self._state = CircuitState.CLOSED
        if was_half_open:
            from app.utils.logger import setup_logger
            setup_logger(__name__).info(
                f"CircuitBreaker '{self.name}': HALF_OPEN → CLOSED (recuperado)"
            )

    def record_failure(self) -> None:
        """
        Registra un fallo.

        Si los fallos superan el threshold, abre el circuito.
        Si estábamos HALF_OPEN, vuelve a OPEN.
        """
        now = time.time()
        self._failures.append(now)
        self._last_failure_time = now

        if self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.OPEN
            from app.utils.logger import setup_logger
            setup_logger(__name__).warning(
                f"CircuitBreaker '{self.name}': HALF_OPEN → OPEN "
                f"(fallo en llamada de prueba)"
            )
            return

        if len(self._failures) >= self.failure_threshold:
            if self._state != CircuitState.OPEN:
                self._state = CircuitState.OPEN
                from app.utils.logger import setup_logger
                setup_logger(__name__).warning(
                    f"CircuitBreaker '{self.name}': CLOSED → OPEN "
                    f"({len(self._failures)} fallos en ventana)"
                )

    #  Métricas                                                           
    def get_metrics(self) -> CircuitBreakerMetrics:
        """Snapshot del estado actual para Prometheus o logging."""
        retry_in = 0.0
        if self._state == CircuitState.OPEN:
            elapsed = time.time() - self._last_failure_time
            retry_in = max(0.0, self.recovery_timeout - elapsed)

        return CircuitBreakerMetrics(
            name=self.name,
            state=self.state,
            failure_count=len(self._failures),
            last_failure_time=self._last_failure_time or None,
            seconds_until_retry=retry_in,
        )

    def reset(self) -> None:
        """Resetea el circuit breaker a estado inicial. Solo para tests."""
        self._state = CircuitState.CLOSED
        self._failures.clear()
        self._last_failure_time = 0.0

    def __repr__(self) -> str:
        return (
            f"<CircuitBreaker name={self.name!r} "
            f"state={self.state.value} "
            f"failures={len(self._failures)}/{self.failure_threshold}>"
        )