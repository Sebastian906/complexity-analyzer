"""
Batch Analyzer - Análisis paralelo de múltiples algoritmos

Permite analizar N algoritmos simultáneamente con control de concurrencia,
caché por job, y reporte de progreso.

Cuándo usar:
    - Dataset processing: analizar 100+ algoritmos de una vez
    - Comparación: analizar variantes del mismo algoritmo en paralelo
    - Regeneración de caché: re-analizar algoritmos guardados en MongoDB

Cuándo NO usar:
    - Un solo algoritmo → usar AnalysisOrchestrator.analyze_complete()
    - Menos de 5 algoritmos → el overhead de paralelización no vale la pena

Relación con el sistema:
    BatchAnalyzer usa AnalysisOrchestrator internamente para cada job.
    No duplica lógica de análisis — solo orquesta la concurrencia.

Uso:
    >>> analyzer = BatchAnalyzer(max_concurrent=4)
    >>>
    >>> jobs = [
    ...     AnalysisJob(code=code1, name="bubble_sort"),
    ...     AnalysisJob(code=code2, name="merge_sort"),
    ...     AnalysisJob(code=code3, name="quick_sort"),
    ... ]
    >>>
    >>> result = await analyzer.analyze_batch(jobs)
    >>> print(result.summary())
    >>>
    >>> for job in result.completed_jobs:
    ...     print(f"{job.name}: {job.result.complexity.big_o}")
"""

from __future__ import annotations

import asyncio
import hashlib
import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from app.parallel.async_utils import BoundedSemaphore, RetryPolicy
from app.parallel.worker_pools import get_io_pool

logger = logging.getLogger(__name__)

# Tipos y estados
class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"   # Resultado encontrado en caché

@dataclass
class ConcurrencyConfig:
    """
    Configuración de concurrencia para el batch analyzer.

    Args:
        max_concurrent: Máximo de análisis simultáneos
        timeout_per_job: Segundos máximos por análisis individual
        use_cache: Si True, verifica caché antes de analizar
        retry_failed: Si True, reintenta jobs fallidos una vez
        analyze_complexity: Activar análisis de complejidad
        analyze_patterns: Activar detección de patrones
        analyze_structures: Activar detección de estructuras
    """
    max_concurrent: int = 4
    timeout_per_job: float = 60.0
    use_cache: bool = True
    retry_failed: bool = True
    # Opciones de análisis aplicadas a todos los jobs del batch
    analyze_complexity: bool = True
    analyze_patterns: bool = True
    analyze_structures: bool = True
    generate_visualizations: bool = False  # Desactivado por defecto en batch

@dataclass
class AnalysisJob:
    """
    Job de análisis individual para un algoritmo.

    Args:
        code: Código pseudocódigo del algoritmo
        name: Nombre descriptivo (para logs y resultados)
        options: Opciones específicas para este job (sobreescribe ConcurrencyConfig)
        job_id: ID único (generado automáticamente)
        metadata: Información adicional para el caller
    """
    code: str
    name: str = ""
    options: Optional[Dict[str, Any]] = None
    job_id: str = field(default_factory=lambda: str(uuid4())[:8])
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Estado interno — no inicializar
    status: JobStatus = field(default=JobStatus.PENDING, init=False)
    result: Optional[Any] = field(default=None, init=False)
    error: Optional[str] = field(default=None, init=False)
    started_at: Optional[float] = field(default=None, init=False)
    completed_at: Optional[float] = field(default=None, init=False)
    from_cache: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        # Auto-generar nombre si no se proveyó
        if not self.name:
            self.name = f"algorithm_{self.job_id}"

    @property
    def code_hash(self) -> str:
        """Hash del código para identificación en caché."""
        return hashlib.sha256(self.code.encode()).hexdigest()[:16]

    @property
    def duration_ms(self) -> Optional[float]:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at) * 1000
        return None

    @property
    def succeeded(self) -> bool:
        return self.status == JobStatus.COMPLETED

@dataclass
class BatchResult:
    """
    Resultado agregado de un batch de análisis.

    Contiene todos los jobs con su estado final y métricas del batch completo.
    """
    jobs: List[AnalysisJob]
    batch_id: str = field(default_factory=lambda: str(uuid4())[:8])
    created_at: float = field(default_factory=time.monotonic, init=False)
    completed_at: Optional[float] = field(default=None, init=False)

    @property
    def total(self) -> int:
        return len(self.jobs)

    @property
    def completed_jobs(self) -> List[AnalysisJob]:
        return [j for j in self.jobs if j.status == JobStatus.COMPLETED]

    @property
    def failed_jobs(self) -> List[AnalysisJob]:
        return [j for j in self.jobs if j.status == JobStatus.FAILED]

    @property
    def cache_hits(self) -> int:
        return sum(1 for j in self.jobs if j.from_cache)

    @property
    def success_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return len(self.completed_jobs) / self.total

    @property
    def duration_ms(self) -> Optional[float]:
        if self.completed_at:
            return (self.completed_at - self.created_at) * 1000
        return None

    @property
    def avg_job_duration_ms(self) -> float:
        durations = [
            j.duration_ms for j in self.completed_jobs
            if j.duration_ms is not None and not j.from_cache
        ]
        if not durations:
            return 0.0
        return sum(durations) / len(durations)

    def summary(self) -> str:
        """Resumen legible del batch."""
        duration = (
            f"{self.duration_ms:.0f}ms"
            if self.duration_ms
            else "en progreso"
        )
        return (
            f"Batch {self.batch_id}: "
            f"{len(self.completed_jobs)}/{self.total} exitosos, "
            f"{len(self.failed_jobs)} fallidos, "
            f"{self.cache_hits} desde caché, "
            f"duración: {duration}, "
            f"avg/job: {self.avg_job_duration_ms:.0f}ms"
        )

    def to_dict(self) -> dict:
        """Serializa el resultado del batch."""
        return {
            "batch_id": self.batch_id,
            "total": self.total,
            "completed": len(self.completed_jobs),
            "failed": len(self.failed_jobs),
            "cache_hits": self.cache_hits,
            "success_rate": round(self.success_rate, 3),
            "duration_ms": round(self.duration_ms, 2) if self.duration_ms else None,
            "avg_job_duration_ms": round(self.avg_job_duration_ms, 2),
            "jobs": [
                {
                    "job_id": j.job_id,
                    "name": j.name,
                    "status": j.status.value,
                    "from_cache": j.from_cache,
                    "duration_ms": (
                        round(j.duration_ms, 2) if j.duration_ms else None
                    ),
                    "error": j.error,
                    "has_result": j.result is not None,
                }
                for j in self.jobs
            ],
        }

# BatchAnalyzer
class BatchAnalyzer:
    """
    Analizador de múltiples algoritmos en paralelo.

    Gestiona:
    - Concurrencia máxima via BoundedSemaphore
    - Caché por job (hash del código)
    - Retry de jobs fallidos
    - Progreso en tiempo real via callback
    - Timeout por job y global

    Args:
        config: Configuración de concurrencia y análisis
        on_job_complete: Callback(job, batch_result) llamado al completar cada job

    Example:
        >>> config = ConcurrencyConfig(max_concurrent=4, timeout_per_job=30.0)
        >>> analyzer = BatchAnalyzer(config=config)
        >>>
        >>> jobs = [AnalysisJob(code=c, name=n) for c, n in algorithms]
        >>> result = await analyzer.analyze_batch(jobs)
        >>> print(result.summary())
    """

    def __init__(
        self,
        config: Optional[ConcurrencyConfig] = None,
        on_job_complete: Optional[Callable[[AnalysisJob, BatchResult], None]] = None,
    ):
        self.config = config or ConcurrencyConfig()
        self.on_job_complete = on_job_complete
        self._semaphore = BoundedSemaphore(
            limit=self.config.max_concurrent,
            timeout=self.config.timeout_per_job + 10.0,
            name="batch_analyzer",
        )
        self._retry_policy = RetryPolicy(
            max_retries=1 if self.config.retry_failed else 0,
            base_delay=2.0,
            max_delay=5.0,
            jitter=True,
        )

    async def analyze_batch(
        self,
        jobs: List[AnalysisJob],
        on_job_complete: Optional[
            Callable[[AnalysisJob, BatchResult], None]
        ] = None,
    ) -> BatchResult:
        """
        Analiza todos los jobs del batch en paralelo.

        Args:
            jobs: Lista de jobs a analizar
            on_job_complete: Callback de progreso (sobreescribe el del constructor)

        Returns:
            BatchResult con todos los jobs completados/fallidos
        """
        batch = BatchResult(jobs=jobs)
        callback = on_job_complete or self.on_job_complete

        logger.info(
            f"Iniciando batch {batch.batch_id}: "
            f"{len(jobs)} jobs, "
            f"max_concurrent={self.config.max_concurrent}"
        )

        async def process_with_tracking(job: AnalysisJob) -> None:
            async with self._semaphore:
                await self._process_job(job)

            # Notificar fuera del semáforo
            if callback:
                try:
                    callback(job, batch)
                except Exception as e:
                    logger.warning(f"Error en callback de progreso: {e}")

        # Ejecutar todos en paralelo — cada uno respeta el semáforo
        await asyncio.gather(
            *[process_with_tracking(job) for job in jobs],
            return_exceptions=True,
        )

        batch.completed_at = time.monotonic()
        logger.info(batch.summary())
        return batch

    async def _process_job(self, job: AnalysisJob) -> None:
        """Procesa un job: caché → análisis → retry si falla."""
        job.status = JobStatus.RUNNING
        job.started_at = time.monotonic()

        try:
            # 1. Verificar caché
            if self.config.use_cache:
                cached = await self._check_cache(job)
                if cached is not None:
                    job.result = cached
                    job.status = JobStatus.COMPLETED
                    job.from_cache = True
                    job.completed_at = time.monotonic()
                    logger.debug(f"Job {job.job_id} ({job.name}): cache HIT")
                    return

            # 2. Ejecutar análisis con retry si está configurado
            async def do_analyze() -> Any:
                return await self._execute_analysis(job)

            job.result = await self._retry_policy.execute(do_analyze)
            job.status = JobStatus.COMPLETED

            # 3. Guardar en caché si fue exitoso
            if self.config.use_cache and job.result:
                await self._save_to_cache(job)

            logger.debug(
                f"Job {job.job_id} ({job.name}) completado en "
                f"{job.duration_ms:.0f}ms"
            )

        except asyncio.TimeoutError:
            job.status = JobStatus.FAILED
            job.error = f"Timeout después de {self.config.timeout_per_job}s"
            logger.error(f"Job {job.job_id} ({job.name}): timeout")

        except Exception as e:
            job.status = JobStatus.FAILED
            job.error = str(e)
            logger.error(f"Job {job.job_id} ({job.name}) falló: {e}")

        finally:
            job.completed_at = time.monotonic()

    async def _execute_analysis(self, job: AnalysisJob) -> Any:
        """
        Ejecuta el análisis usando AnalysisOrchestrator.

        No duplica la lógica de análisis — delega completamente al orchestrator
        con las opciones del job o las del config del batch.
        """
        from app.services.analysis_orchestrator import AnalysisOrchestrator
        from app.schemas import CompleteAnalysisRequest

        # Merge de opciones: job-level sobreescribe batch-level
        job_opts = job.options or {}

        request = CompleteAnalysisRequest(
            code=job.code,
            analyze_complexity=job_opts.get(
                "analyze_complexity", self.config.analyze_complexity
            ),
            analyze_patterns=job_opts.get(
                "analyze_patterns", self.config.analyze_patterns
            ),
            analyze_structures=job_opts.get(
                "analyze_structures", self.config.analyze_structures
            ),
            generate_visualizations=job_opts.get(
                "generate_visualizations", self.config.generate_visualizations
            ),
        )

        # Usar timeout del config para este job individual
        orchestrator = AnalysisOrchestrator()
        return await asyncio.wait_for(
            orchestrator.analyze_complete(request),
            timeout=self.config.timeout_per_job,
        )

    async def _check_cache(self, job: AnalysisJob) -> Optional[Any]:
        """Verifica si el resultado existe en caché."""
        try:
            from app.services.cache_service import (
                get_cache_service,
                generate_cache_key,
                CacheKey,
            )
            cache = get_cache_service()
            cache_key = generate_cache_key(
                CacheKey.ANALYSIS,
                job.code,
                analyze_complexity=self.config.analyze_complexity,
                analyze_patterns=self.config.analyze_patterns,
                analyze_structures=self.config.analyze_structures,
                generate_visualizations=self.config.generate_visualizations,
            )
            return await cache.get(cache_key)
        except Exception as e:
            logger.debug(f"Error verificando caché para job {job.job_id}: {e}")
            return None

    async def _save_to_cache(self, job: AnalysisJob) -> None:
        """Guarda el resultado en caché."""
        try:
            from app.services.cache_service import (
                get_cache_service,
                generate_cache_key,
                CacheKey,
            )
            from app.core.config import settings

            cache = get_cache_service()
            cache_key = generate_cache_key(
                CacheKey.ANALYSIS,
                job.code,
                analyze_complexity=self.config.analyze_complexity,
                analyze_patterns=self.config.analyze_patterns,
                analyze_structures=self.config.analyze_structures,
                generate_visualizations=self.config.generate_visualizations,
            )
            await cache.set(
                cache_key, job.result, ttl=settings.CACHE_TTL_ANALYSIS
            )
        except Exception as e:
            logger.debug(f"Error guardando caché para job {job.job_id}: {e}")

    def get_semaphore_metrics(self) -> dict:
        """Métricas del semáforo de concurrencia."""
        return self._semaphore.get_metrics()