"""
Async Utilities - Primitivas async reutilizables

Provee herramientas de control de concurrencia usadas en todo el sistema:
- BoundedSemaphore: semáforo con timeout y métricas de espera
- RateLimiter: sliding window rate limiter async
- AsyncTimeout: context manager para timeouts con cleanup garantizado
- RetryPolicy: política de reintentos configurable con backoff exponencial

Diseño:
    Estas primitivas son independientes entre sí y del resto del sistema.
    No importan nada de app.core ni app.services para evitar dependencias
    circulares. Cualquier módulo del sistema puede importarlas libremente.

Uso típico:
    >>> from app.parallel.async_utils import RetryPolicy, AsyncTimeout
    >>>
    >>> policy = RetryPolicy(max_retries=3, base_delay=1.0)
    >>> async with AsyncTimeout(seconds=10, operation="LLM call"):
    ...     result = await policy.execute(some_async_fn, arg1, arg2)
"""

from __future__ import annotations

import asyncio
import time
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Callable, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

# BoundedSemaphore
@dataclass
class SemaphoreMetrics:
    """Métricas de uso de un semáforo."""
    total_acquisitions: int = 0
    total_wait_time_ms: float = 0.0
    max_wait_time_ms: float = 0.0
    timeouts: int = 0
    current_holders: int = 0

    @property
    def avg_wait_time_ms(self) -> float:
        if self.total_acquisitions == 0:
            return 0.0
        return self.total_wait_time_ms / self.total_acquisitions

class BoundedSemaphore:
    """
    Semáforo async con timeout configurable y métricas de espera.

    Diferencias con asyncio.Semaphore estándar:
    - Timeout por adquisición (no bloquea indefinidamente)
    - Métricas de cuánto tiempo esperan los callers
    - Log automático cuando la espera supera un umbral

    Args:
        limit: Número máximo de holders simultáneos
        timeout: Segundos máximos de espera para adquirir (None = sin límite)
        warn_wait_ms: Umbral en ms para loguear esperas largas

    Example:
        >>> sem = BoundedSemaphore(limit=4, timeout=30.0)
        >>> async with sem:
        ...     await do_work()
        >>> print(sem.metrics.avg_wait_time_ms)
    """

    def __init__(
        self,
        limit: int,
        timeout: Optional[float] = 30.0,
        warn_wait_ms: float = 5000.0,
        name: str = "semaphore",
    ):
        self._sem = asyncio.Semaphore(limit)
        self.limit = limit
        self.timeout = timeout
        self.warn_wait_ms = warn_wait_ms
        self.name = name
        self.metrics = SemaphoreMetrics()

    async def acquire(self) -> None:
        """Adquiere el semáforo, respetando el timeout configurado."""
        start = time.monotonic()

        try:
            if self.timeout is not None:
                await asyncio.wait_for(self._sem.acquire(), timeout=self.timeout)
            else:
                await self._sem.acquire()
        except asyncio.TimeoutError:
            self.metrics.timeouts += 1
            wait_ms = (time.monotonic() - start) * 1000
            logger.warning(
                f"[{self.name}] Timeout esperando semáforo "
                f"después de {wait_ms:.0f}ms (limit={self.limit})"
            )
            raise

        wait_ms = (time.monotonic() - start) * 1000
        self.metrics.total_acquisitions += 1
        self.metrics.total_wait_time_ms += wait_ms
        self.metrics.max_wait_time_ms = max(
            self.metrics.max_wait_time_ms, wait_ms
        )
        self.metrics.current_holders += 1

        if wait_ms > self.warn_wait_ms:
            logger.warning(
                f"[{self.name}] Espera larga: {wait_ms:.0f}ms "
                f"(holders actuales={self.metrics.current_holders})"
            )

    def release(self) -> None:
        """Libera el semáforo."""
        self.metrics.current_holders = max(0, self.metrics.current_holders - 1)
        self._sem.release()

    async def __aenter__(self) -> "BoundedSemaphore":
        await self.acquire()
        return self

    async def __aexit__(self, *exc_info: Any) -> None:
        self.release()

    def get_metrics(self) -> dict:
        """Retorna métricas como diccionario serializable."""
        return {
            "name": self.name,
            "limit": self.limit,
            "current_holders": self.metrics.current_holders,
            "total_acquisitions": self.metrics.total_acquisitions,
            "avg_wait_time_ms": round(self.metrics.avg_wait_time_ms, 2),
            "max_wait_time_ms": round(self.metrics.max_wait_time_ms, 2),
            "timeouts": self.metrics.timeouts,
        }

# RateLimiter
class RateLimiter:
    """
    Rate limiter async con ventana deslizante.

    Limita cuántas operaciones pueden iniciarse en una ventana de tiempo.
    Thread-safe para uso concurrente con asyncio.

    A diferencia del RateLimiter de dependencies.py (que es por IP/request),
    este es para controlar la tasa de operaciones internas (llamadas a LLMs,
    escrituras a disco, etc.).

    Args:
        max_calls: Número máximo de llamadas en la ventana
        window_seconds: Duración de la ventana en segundos
        name: Nombre identificador para logs

    Example:
        >>> limiter = RateLimiter(max_calls=10, window_seconds=60.0)
        >>> async with limiter:
        ...     await call_external_api()
    """

    def __init__(
        self,
        max_calls: int,
        window_seconds: float,
        name: str = "rate_limiter",
    ):
        self.max_calls = max_calls
        self.window_seconds = window_seconds
        self.name = name
        self._calls: list[float] = []  # timestamps de llamadas recientes
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """
        Espera si es necesario para respetar el rate limit.

        Si la ventana está llena, espera hasta que la llamada más antigua
        salga de la ventana.
        """
        async with self._lock:
            now = time.monotonic()

            # Eliminar llamadas fuera de la ventana
            cutoff = now - self.window_seconds
            self._calls = [t for t in self._calls if t > cutoff]

            if len(self._calls) >= self.max_calls:
                # Calcular cuánto esperar
                oldest = self._calls[0]
                wait = self.window_seconds - (now - oldest) + 0.001
                if wait > 0:
                    logger.debug(
                        f"[{self.name}] Rate limit activo, "
                        f"esperando {wait:.2f}s"
                    )
                    await asyncio.sleep(wait)
                    # Re-limpiar después de esperar
                    now = time.monotonic()
                    cutoff = now - self.window_seconds
                    self._calls = [t for t in self._calls if t > cutoff]

            self._calls.append(time.monotonic())

    async def __aenter__(self) -> "RateLimiter":
        await self.acquire()
        return self

    async def __aexit__(self, *exc_info: Any) -> None:
        pass  # El timestamp ya fue registrado en acquire()

    @property
    def current_usage(self) -> int:
        """Número de llamadas en la ventana actual."""
        now = time.monotonic()
        cutoff = now - self.window_seconds
        return sum(1 for t in self._calls if t > cutoff)

# AsyncTimeout
class AsyncTimeout:
    """
    Context manager para timeouts con cleanup garantizado y logs claros.

    Diferencias con asyncio.wait_for():
    - Mensajes de error más descriptivos (incluye nombre de operación)
    - Loguea automáticamente cuando ocurre timeout
    - Puede usarse como context manager anidado

    Args:
        seconds: Segundos hasta timeout
        operation: Nombre de la operación para mensajes de error y logs

    Raises:
        asyncio.TimeoutError: Si la operación supera el tiempo límite

    Example:
        >>> async with AsyncTimeout(seconds=30, operation="parse_algorithm"):
        ...     ast = await parser.parse(code)
    """

    def __init__(self, seconds: float, operation: str = "operation"):
        self.seconds = seconds
        self.operation = operation
        self._task: Optional[asyncio.Task] = None

    async def __aenter__(self) -> "AsyncTimeout":
        return self

    async def __aexit__(
        self,
        exc_type: Any,
        exc_val: Any,
        exc_tb: Any,
    ) -> bool:
        # No suprime excepciones — solo loguea timeouts
        if exc_type is asyncio.TimeoutError:
            logger.error(
                f"Timeout en '{self.operation}' después de {self.seconds}s"
            )
        return False  # No suprimir la excepción

    @asynccontextmanager
    @staticmethod
    async def wrap(
        seconds: float,
        operation: str = "operation",
    ) -> AsyncGenerator[None, None]:
        """
        Alternativa como context manager estático con asyncio.wait_for.

        Uso:
            async with AsyncTimeout.wrap(30, "analyze_complexity"):
                result = await expensive_operation()
        """
        try:
            async with asyncio.timeout(seconds):
                yield
        except asyncio.TimeoutError:
            logger.error(
                f"Timeout en '{operation}' después de {seconds}s"
            )
            raise

# RetryPolicy
@dataclass
class RetryPolicy:
    """
    Política de reintentos con backoff exponencial configurable.

    Diseñada para operaciones que pueden fallar transitoriamente:
    - Llamadas a LLMs (rate limits, timeouts)
    - Escrituras a Redis/MongoDB
    - Renderizado de Graphviz

    No debe usarse para:
    - Errores de validación (código inválido no mejora con reintentos)
    - Errores de configuración

    Args:
        max_retries: Número máximo de reintentos (0 = sin reintentos)
        base_delay: Delay inicial en segundos
        max_delay: Delay máximo en segundos (cap del backoff)
        exponential_base: Base del backoff (2.0 = duplica cada intento)
        jitter: Si True, añade variación aleatoria al delay
        retryable_exceptions: Tupla de excepciones que activan reintento.
                              None = reintentar en cualquier Exception.

    Example:
        >>> policy = RetryPolicy(max_retries=3, base_delay=1.0, max_delay=10.0)
        >>>
        >>> async def call_llm():
        ...     return await claude.generate(prompt)
        >>>
        >>> result = await policy.execute(call_llm)
    """

    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_exceptions: tuple = field(default_factory=lambda: (Exception,))

    def _compute_delay(self, attempt: int) -> float:
        """Calcula el delay para el intento N con backoff exponencial."""
        import random
        delay = min(
            self.base_delay * (self.exponential_base ** attempt),
            self.max_delay,
        )
        if self.jitter:
            delay *= (0.5 + random.random() * 0.5)  # ±50% de variación
        return delay

    async def execute(
        self,
        fn: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Ejecuta la función con reintentos según la política.

        Args:
            fn: Función async a ejecutar
            *args, **kwargs: Argumentos para fn

        Returns:
            Resultado de fn si tiene éxito

        Raises:
            La última excepción si se agotan los reintentos
        """
        last_exception: Optional[Exception] = None

        for attempt in range(self.max_retries + 1):
            try:
                return await fn(*args, **kwargs)

            except self.retryable_exceptions as exc:
                last_exception = exc

                if attempt == self.max_retries:
                    logger.error(
                        f"Agotados {self.max_retries + 1} intentos. "
                        f"Último error: {exc}"
                    )
                    raise

                delay = self._compute_delay(attempt)
                logger.warning(
                    f"Intento {attempt + 1}/{self.max_retries + 1} falló "
                    f"({type(exc).__name__}: {exc}). "
                    f"Reintentando en {delay:.2f}s..."
                )
                await asyncio.sleep(delay)

        # Nunca se llega aquí, pero satisface al type checker
        raise last_exception  # type: ignore[misc]

    def with_timeout(
        self, seconds: float, operation: str = "operation"
    ) -> "RetryPolicyWithTimeout":
        """
        Combina esta política con un timeout por intento.

        Example:
            >>> policy = RetryPolicy(max_retries=2, base_delay=1.0)
            >>> combined = policy.with_timeout(seconds=15, operation="LLM")
            >>> result = await combined.execute(llm_call)
        """
        return RetryPolicyWithTimeout(
            policy=self,
            timeout_seconds=seconds,
            operation=operation,
        )

@dataclass
class RetryPolicyWithTimeout:
    """Combina RetryPolicy con timeout por intento."""

    policy: RetryPolicy
    timeout_seconds: float
    operation: str = "operation"

    async def execute(
        self,
        fn: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Ejecuta con timeout por intento y reintentos."""

        async def fn_with_timeout(*a: Any, **kw: Any) -> Any:
            try:
                return await asyncio.wait_for(
                    fn(*a, **kw),
                    timeout=self.timeout_seconds,
                )
            except asyncio.TimeoutError:
                logger.error(
                    f"Timeout en '{self.operation}' "
                    f"después de {self.timeout_seconds}s"
                )
                raise

        return await self.policy.execute(fn_with_timeout, *args, **kwargs)

# Utilidades de gather con control de errores
async def gather_with_semaphore(
    tasks: list[Callable[[], Any]],
    semaphore: BoundedSemaphore,
    return_exceptions: bool = True,
) -> list[Any]:
    """
    Ejecuta una lista de callables async con control de concurrencia.

    Combina asyncio.gather con un semáforo para limitar cuántas tareas
    corren simultáneamente.

    Args:
        tasks: Lista de callables async (sin argumentos)
        semaphore: Semáforo que controla la concurrencia máxima
        return_exceptions: Si True, excepciones se retornan como valores

    Returns:
        Lista de resultados en el mismo orden que tasks

    Example:
        >>> sem = BoundedSemaphore(limit=4, timeout=30.0)
        >>> results = await gather_with_semaphore(
        ...     tasks=[lambda: analyze(code) for code in codes],
        ...     semaphore=sem,
        ... )
    """

    async def run_with_sem(task: Callable[[], Any]) -> Any:
        async with semaphore:
            return await task()

    return await asyncio.gather(
        *[run_with_sem(t) for t in tasks],
        return_exceptions=return_exceptions,
    )

async def gather_with_timeout(
    coroutines: list[Any],
    timeout: float,
    operation: str = "batch operation",
) -> list[Any]:
    """
    Ejecuta coroutines con timeout global para todo el batch.

    Si el timeout expira, cancela todas las tareas pendientes y retorna
    los resultados parciales que se hayan completado.

    Args:
        coroutines: Lista de coroutines a ejecutar
        timeout: Segundos hasta cancelar todo el batch
        operation: Nombre para logs

    Returns:
        Lista de resultados (None para las tareas canceladas)
    """
    tasks = [asyncio.create_task(c) for c in coroutines]

    try:
        return await asyncio.wait_for(
            asyncio.gather(*tasks, return_exceptions=True),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        logger.warning(
            f"Timeout global en '{operation}' después de {timeout}s. "
            f"Cancelando tareas pendientes..."
        )
        for task in tasks:
            if not task.done():
                task.cancel()

        # Esperar que todas las tareas procesen la cancelación
        await asyncio.gather(*tasks, return_exceptions=True)

        # Retornar resultados parciales
        results = []
        for task in tasks:
            if task.cancelled():
                results.append(None)
            elif task.exception():
                results.append(task.exception())
            else:
                results.append(task.result())
        return results