"""
Parallel Module - Control de concurrencia y procesamiento paralelo

Este módulo provee herramientas para ejecutar análisis y exportaciones
de forma paralela y controlada.

Componentes:
    async_utils:        Primitivas async reutilizables
    worker_pools:       Pools de threads pre-creados y reutilizables
    parallel_exporter:  Exportación paralela usando pools centralizados
    batch_analyzer:     Análisis de múltiples algoritmos en paralelo

Relación con el resto del sistema:
    - NO reemplaza asyncio.gather() en analysis_orchestrator.py
      (que paraleliza los pasos de un solo análisis)
    - SÍ añade paralelismo a nivel de múltiples algoritmos/exportaciones
    - Los pools de worker_pools mejoran diagram_renderer.py y export/__init__.py

Uso básico:
    >>> # Analizar N algoritmos en paralelo
    >>> from app.parallel import BatchAnalyzer, AnalysisJob, ConcurrencyConfig
    >>>
    >>> analyzer = BatchAnalyzer(ConcurrencyConfig(max_concurrent=4))
    >>> result = await analyzer.analyze_batch([
    ...     AnalysisJob(code=code1, name="algo1"),
    ...     AnalysisJob(code=code2, name="algo2"),
    ... ])
    >>> print(result.summary())

    >>> # Exportar N análisis en paralelo
    >>> from app.parallel import ParallelExporter, ExportJob
    >>>
    >>> exporter = ParallelExporter(max_concurrent=4)
    >>> batch = exporter.create_batch([
    ...     ExportJob(algorithm=a, analysis=r, formats=["json", "pdf"]),
    ... ])
    >>> completed = await exporter.run_batch(batch)

    >>> # Integración con diagram_renderer (pools dedicados)
    >>> from app.parallel import get_graphviz_pool
    >>> loop = asyncio.get_event_loop()
    >>> result = await loop.run_in_executor(get_graphviz_pool(), dot.pipe)
"""

# Async utilities
from app.parallel.async_utils import (
    BoundedSemaphore,
    SemaphoreMetrics,
    RateLimiter,
    AsyncTimeout,
    RetryPolicy,
    RetryPolicyWithTimeout,
    gather_with_semaphore,
    gather_with_timeout,
)

# Worker pools
from app.parallel.worker_pools import (
    PoolConfig,
    ThreadPoolRegistry,
    get_io_pool,
    get_cpu_pool,
    get_graphviz_pool,
    shutdown_all_pools,
    get_pool_stats,
)

# Parallel exporter
from app.parallel.parallel_exporter import (
    ParallelExporter,
    ExportJob,
    ExportBatch,
    JobStatus as ExportJobStatus,
)

# Batch analyzer
from app.parallel.batch_analyzer import (
    BatchAnalyzer,
    AnalysisJob,
    BatchResult,
    ConcurrencyConfig,
    JobStatus as AnalysisJobStatus,
)

__all__ = [
    # async_utils
    "BoundedSemaphore",
    "SemaphoreMetrics",
    "RateLimiter",
    "AsyncTimeout",
    "RetryPolicy",
    "RetryPolicyWithTimeout",
    "gather_with_semaphore",
    "gather_with_timeout",

    # worker_pools
    "PoolConfig",
    "ThreadPoolRegistry",
    "get_io_pool",
    "get_cpu_pool",
    "get_graphviz_pool",
    "shutdown_all_pools",
    "get_pool_stats",

    # parallel_exporter
    "ParallelExporter",
    "ExportJob",
    "ExportBatch",
    "ExportJobStatus",

    # batch_analyzer
    "BatchAnalyzer",
    "AnalysisJob",
    "BatchResult",
    "ConcurrencyConfig",
    "AnalysisJobStatus",
]