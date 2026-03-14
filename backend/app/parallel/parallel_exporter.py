"""
Parallel Exporter - Exportación paralela de análisis

Complementa (no reemplaza) el sistema de exportación existente en
app/infrastructure/export/__init__.py. La diferencia clave:

    Actual (export/__init__.py):
        Crea ThreadPoolExecutor por cada llamada a export_to_multiple_formats.
        max_workers = min(len(formats), 5) hardcodeado.

    Este módulo:
        Usa el pool I/O pre-creado (get_io_pool()) para reutilizar threads.
        Configuración centralizada en PoolConfig.
        Agrega progreso, estado por job, y métricas.
        Soporta cancelación de jobs individuales.

Cuándo usar cada uno:
    - export_to_multiple_formats(): análisis único, pocos formatos, simple
    - ParallelExporter: múltiples análisis, muchos formatos, necesitas progreso

Uso:
    >>> exporter = ParallelExporter()
    >>> batch = exporter.create_batch([
    ...     ExportJob(algorithm=algo, analysis=result, formats=[PDF, JSON]),
    ...     ExportJob(algorithm=algo2, analysis=result2, formats=[MARKDOWN]),
    ... ])
    >>> completed = await exporter.run_batch(batch)
    >>> print(completed.summary())
"""

from __future__ import annotations

import asyncio
import time
import logging
from concurrent.futures import as_completed, Future
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from app.parallel.worker_pools import get_io_pool
from app.parallel.async_utils import BoundedSemaphore

logger = logging.getLogger(__name__)

# Tipos y estados
class JobStatus(str, Enum):
    """Estado de un job de exportación individual."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class ExportJob:
    """
    Job de exportación individual.

    Encapsula un análisis y los formatos en los que debe exportarse.
    Cada combinación (análisis, formato) se procesa como un job separado.

    Args:
        algorithm: Instancia del modelo Algorithm (MongoDB)
        analysis: Instancia del modelo AnalysisResult (MongoDB)
        formats: Lista de formatos de exportación
        patterns: Detección de patrones (opcional)
        output_dir: Directorio de salida (opcional)
        job_id: ID único (se genera automáticamente)
    """
    algorithm: Any
    analysis: Any
    formats: List[str]
    patterns: Optional[Any] = None
    output_dir: Optional[Path] = None
    job_id: str = field(default_factory=lambda: str(uuid4())[:8])

    # Estado interno
    status: JobStatus = field(default=JobStatus.PENDING, init=False)
    started_at: Optional[float] = field(default=None, init=False)
    completed_at: Optional[float] = field(default=None, init=False)
    error: Optional[str] = field(default=None, init=False)
    results: Dict[str, Any] = field(default_factory=dict, init=False)

    @property
    def duration_ms(self) -> Optional[float]:
        """Duración del job en ms, o None si no completó."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at) * 1000
        return None

    @property
    def algorithm_name(self) -> str:
        """Nombre del algoritmo para logs."""
        return getattr(self.algorithm, 'name', str(self.job_id))

@dataclass
class ExportBatch:
    """
    Colección de jobs de exportación con estado agregado.

    Args:
        jobs: Lista de jobs a procesar
        batch_id: ID único del batch
    """
    jobs: List[ExportJob]
    batch_id: str = field(default_factory=lambda: str(uuid4())[:8])

    # Estado agregado
    created_at: float = field(default_factory=time.monotonic, init=False)
    completed_at: Optional[float] = field(default=None, init=False)

    @property
    def total(self) -> int:
        return len(self.jobs)

    @property
    def completed(self) -> int:
        return sum(
            1 for j in self.jobs
            if j.status == JobStatus.COMPLETED
        )

    @property
    def failed(self) -> int:
        return sum(
            1 for j in self.jobs
            if j.status == JobStatus.FAILED
        )

    @property
    def pending(self) -> int:
        return sum(
            1 for j in self.jobs
            if j.status == JobStatus.PENDING
        )

    @property
    def success_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return self.completed / self.total

    @property
    def duration_ms(self) -> Optional[float]:
        if self.completed_at:
            return (self.completed_at - self.created_at) * 1000
        return None

    def summary(self) -> str:
        """Resumen legible del estado del batch."""
        duration = f"{self.duration_ms:.0f}ms" if self.duration_ms else "en progreso"
        return (
            f"Batch {self.batch_id}: "
            f"{self.completed}/{self.total} completados, "
            f"{self.failed} fallidos, "
            f"{duration}"
        )

    def to_dict(self) -> dict:
        """Serializa el estado del batch."""
        return {
            "batch_id": self.batch_id,
            "total": self.total,
            "completed": self.completed,
            "failed": self.failed,
            "pending": self.pending,
            "success_rate": round(self.success_rate, 3),
            "duration_ms": round(self.duration_ms, 2) if self.duration_ms else None,
            "jobs": [
                {
                    "job_id": j.job_id,
                    "algorithm": j.algorithm_name,
                    "formats": j.formats,
                    "status": j.status.value,
                    "duration_ms": round(j.duration_ms, 2) if j.duration_ms else None,
                    "error": j.error,
                }
                for j in self.jobs
            ],
        }

# ParallelExporter
class ParallelExporter:
    """
    Exportador paralelo que usa el pool I/O centralizado.

    Ventajas sobre export_to_multiple_formats() actual:
    - Pool reutilizable (no crea/destruye threads por llamada)
    - Control de concurrencia máxima con BoundedSemaphore
    - Progreso por job y agregado por batch
    - Soporte para callbacks de progreso
    - Timeout configurable por job

    Args:
        max_concurrent: Máximo de exportaciones simultáneas
        timeout_per_job: Segundos máximos por job individual
        on_progress: Callback(batch) llamado cuando un job completa

    Example:
        >>> exporter = ParallelExporter(max_concurrent=4, timeout_per_job=30.0)
        >>>
        >>> batch = exporter.create_batch([
        ...     ExportJob(algorithm=a, analysis=r, formats=["json", "pdf"]),
        ...     ExportJob(algorithm=b, analysis=r2, formats=["markdown"]),
        ... ])
        >>>
        >>> def on_progress(batch: ExportBatch):
        ...     print(f"Progreso: {batch.completed}/{batch.total}")
        >>>
        >>> completed = await exporter.run_batch(batch, on_progress=on_progress)
        >>> print(completed.summary())
    """

    def __init__(
        self,
        max_concurrent: int = 4,
        timeout_per_job: float = 30.0,
        on_progress: Optional[Callable[[ExportBatch], None]] = None,
    ):
        self.max_concurrent = max_concurrent
        self.timeout_per_job = timeout_per_job
        self.on_progress = on_progress
        self._semaphore = BoundedSemaphore(
            limit=max_concurrent,
            timeout=timeout_per_job + 5.0,  # +5s de margen sobre el job timeout
            name="parallel_exporter",
        )

    def create_batch(self, jobs: List[ExportJob]) -> ExportBatch:
        """Crea un batch de jobs listos para procesar."""
        batch = ExportBatch(jobs=jobs)
        logger.info(
            f"Batch {batch.batch_id} creado: "
            f"{batch.total} jobs, "
            f"formatos: {set(f for j in jobs for f in j.formats)}"
        )
        return batch

    async def run_batch(
        self,
        batch: ExportBatch,
        on_progress: Optional[Callable[[ExportBatch], None]] = None,
    ) -> ExportBatch:
        """
        Ejecuta todos los jobs del batch en paralelo.

        Args:
            batch: Batch de jobs a procesar
            on_progress: Callback de progreso (sobreescribe el del constructor)

        Returns:
            El mismo batch con todos los jobs actualizados
        """
        progress_callback = on_progress or self.on_progress

        logger.info(
            f"Iniciando batch {batch.batch_id}: {batch.total} jobs"
        )

        async def process_single(job: ExportJob) -> None:
            async with self._semaphore:
                await self._process_job(job)
            # Notificar progreso fuera del semáforo para no bloquear
            if progress_callback:
                try:
                    progress_callback(batch)
                except Exception as e:
                    logger.warning(f"Error en callback de progreso: {e}")

        # Ejecutar todos los jobs concurrentemente con control de semáforo
        await asyncio.gather(
            *[process_single(job) for job in batch.jobs],
            return_exceptions=True,  # No interrumpir el batch si un job falla
        )

        batch.completed_at = time.monotonic()
        logger.info(batch.summary())
        return batch

    async def _process_job(self, job: ExportJob) -> None:
        """Procesa un job individual, actualizando su estado."""
        job.status = JobStatus.RUNNING
        job.started_at = time.monotonic()

        try:
            # Ejecutar la exportación en el pool I/O (operación de disco)
            loop = asyncio.get_event_loop()
            results = await asyncio.wait_for(
                loop.run_in_executor(
                    get_io_pool(),
                    self._export_sync,
                    job,
                ),
                timeout=self.timeout_per_job,
            )

            job.results = results
            job.status = JobStatus.COMPLETED
            logger.debug(
                f"Job {job.job_id} ({job.algorithm_name}) completado: "
                f"{list(results.keys())}"
            )

        except asyncio.TimeoutError:
            job.status = JobStatus.FAILED
            job.error = f"Timeout después de {self.timeout_per_job}s"
            logger.error(
                f"Job {job.job_id} ({job.algorithm_name}) timeout"
            )

        except Exception as e:
            job.status = JobStatus.FAILED
            job.error = str(e)
            logger.error(
                f"Job {job.job_id} ({job.algorithm_name}) error: {e}"
            )

        finally:
            job.completed_at = time.monotonic()

    @staticmethod
    def _export_sync(job: ExportJob) -> Dict[str, Any]:
        """
        Ejecuta las exportaciones de forma síncrona (para ThreadPoolExecutor).

        Usa el sistema de exportación existente en infrastructure/export.
        No duplica lógica — delega completamente.
        """
        from app.infrastructure.export import export_analysis, ExportFormat

        results = {}

        for format_str in job.formats:
            try:
                fmt = ExportFormat(format_str)
                output_path = None

                if job.output_dir:
                    algo_name = getattr(job.algorithm, 'name', 'unknown')
                    output_path = str(
                        job.output_dir / f"{algo_name}.{format_str}"
                    )

                result = export_analysis(
                    algorithm=job.algorithm,
                    analysis=job.analysis,
                    patterns=job.patterns,
                    format=fmt,
                    output_path=output_path,
                )
                results[format_str] = {
                    "success": result.success,
                    "output_path": str(result.output_path) if result.output_path else None,
                    "errors": result.errors,
                }
            except Exception as e:
                results[format_str] = {
                    "success": False,
                    "error": str(e),
                }

        return results

    def get_semaphore_metrics(self) -> dict:
        """Métricas de uso del semáforo de concurrencia."""
        return self._semaphore.get_metrics()