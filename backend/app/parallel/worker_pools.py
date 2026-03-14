"""
Worker Pools - Pools de threads/procesos reutilizables

El problema que resuelve:
    Crear un ThreadPoolExecutor por cada request (como hace el código actual
    en export/__init__.py y diagram_renderer.py) tiene un overhead real:
    - Creación de N threads en cada llamada
    - Destrucción al salir del with
    - Sin control de cuántos pools existen simultáneamente

    Con pools pre-creados y reutilizables:
    - Los threads se crean una sola vez al inicio
    - Cada request reutiliza el pool existente
    - Control centralizado de cuántos workers hay por tipo de trabajo

Pools disponibles:
    - IO Pool: para operaciones de disco, Redis, MongoDB (I/O-bound)
    - CPU Pool: para análisis pesado cuando se quiera paralelismo real
    - Graphviz Pool: dedicado a subprocesos de Graphviz (limitado a 2-4)

Integración con código existente:
    diagram_renderer.py usa run_in_executor(None, ...) que usa el default
    thread pool de asyncio. Este módulo permite usar pools específicos
    cuando se necesita control más fino.

Uso:
    >>> from app.parallel.worker_pools import get_io_pool, get_graphviz_pool
    >>>
    >>> # En diagram_renderer.py (async)
    >>> loop = asyncio.get_event_loop()
    >>> result = await loop.run_in_executor(get_graphviz_pool(), blocking_fn)
    >>>
    >>> # En parallel_exporter.py
    >>> with get_io_pool() as pool:
    ...     futures = [pool.submit(export_fn, job) for job in jobs]
"""

from __future__ import annotations

import atexit
import logging
import os
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from dataclasses import dataclass, field
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Configuración de pools
@dataclass
class PoolConfig:
    """
    Configuración de workers por tipo de pool.

    Los valores por defecto están calibrados para un servidor con 2-4 CPUs.
    Ajustar vía variables de entorno en producción.

    Reglas generales:
        - IO-bound: 2-4x número de CPUs (los threads esperan mucho)
        - CPU-bound: 1x número de CPUs (más no ayuda, solo añade context switch)
        - Graphviz: limitado porque cada proceso lanza un subprocess del SO
    """
    # Pool I/O: exportaciones a disco, Redis, escritura de archivos
    io_workers: int = field(
        default_factory=lambda: int(
            os.environ.get("PARALLEL_IO_WORKERS", min(os.cpu_count() * 2, 8))
        )
    )

    # Pool CPU: análisis de patrones batch, cálculos simbólicos
    cpu_workers: int = field(
        default_factory=lambda: int(
            os.environ.get("PARALLEL_CPU_WORKERS", max(os.cpu_count() - 1, 1))
        )
    )

    # Pool Graphviz: subprocesos de renderizado — limitado intencionalmente
    # para no saturar el sistema con subprocesos del SO
    graphviz_workers: int = field(
        default_factory=lambda: int(
            os.environ.get("PARALLEL_GRAPHVIZ_WORKERS", min(os.cpu_count(), 4))
        )
    )

    def __post_init__(self) -> None:
        logger.info(
            f"PoolConfig: io={self.io_workers}, "
            f"cpu={self.cpu_workers}, "
            f"graphviz={self.graphviz_workers}"
        )

# ThreadPoolRegistry — registro singleton de pools
class ThreadPoolRegistry:
    """
    Registro singleton de ThreadPoolExecutors reutilizables.

    Garantiza que:
    - Cada tipo de pool se crea una sola vez (al primer uso)
    - Los pools se cierran correctamente al apagar la aplicación
    - No hay pools huérfanos en memoria

    No instanciar directamente — usar las funciones get_*_pool().
    """

    _instance: Optional["ThreadPoolRegistry"] = None
    _pools: Dict[str, ThreadPoolExecutor] = {}
    _config: Optional[PoolConfig] = None

    def __new__(cls) -> "ThreadPoolRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._config = PoolConfig()
            atexit.register(cls._instance.shutdown_all)
            logger.info("ThreadPoolRegistry inicializado")
        return cls._instance

    def get_or_create(
        self,
        name: str,
        max_workers: int,
    ) -> ThreadPoolExecutor:
        """
        Obtiene o crea un pool con el nombre dado.

        Args:
            name: Identificador del pool
            max_workers: Número máximo de workers

        Returns:
            ThreadPoolExecutor listo para usar
        """
        if name not in self._pools:
            self._pools[name] = ThreadPoolExecutor(
                max_workers=max_workers,
                thread_name_prefix=f"complexity_analyzer_{name}",
            )
            logger.info(
                f"Pool '{name}' creado con {max_workers} workers"
            )
        return self._pools[name]

    def shutdown_all(self, wait: bool = True) -> None:
        """
        Cierra todos los pools registrados.

        Se llama automáticamente vía atexit al apagar la aplicación.
        También puede llamarse manualmente desde el lifespan de FastAPI.

        Args:
            wait: Si True, espera que las tareas en curso terminen
        """
        for name, pool in self._pools.items():
            try:
                pool.shutdown(wait=wait)
                logger.info(f"Pool '{name}' cerrado correctamente")
            except Exception as e:
                logger.error(f"Error cerrando pool '{name}': {e}")
        self._pools.clear()

    def get_stats(self) -> Dict[str, dict]:
        """Retorna estadísticas básicas de todos los pools activos."""
        return {
            name: {
                "max_workers": pool._max_workers,  # type: ignore[attr-defined]
                "active": not pool._shutdown,       # type: ignore[attr-defined]
            }
            for name, pool in self._pools.items()
        }

    @property
    def config(self) -> PoolConfig:
        """Configuración actual de los pools."""
        return self._config  # type: ignore[return-value]

# Funciones de acceso públicas
def get_io_pool() -> ThreadPoolExecutor:
    """
    Pool para operaciones I/O-bound.

    Usar para: exportaciones a disco, escritura de archivos, llamadas Redis
    síncronas, operaciones de red síncronas.

    Workers: 2x CPUs (los threads pasan mucho tiempo esperando I/O).

    Example:
        >>> loop = asyncio.get_event_loop()
        >>> result = await loop.run_in_executor(get_io_pool(), write_file, path, content)
    """
    registry = ThreadPoolRegistry()
    return registry.get_or_create(
        name="io",
        max_workers=registry.config.io_workers,
    )

def get_cpu_pool() -> ThreadPoolExecutor:
    """
    Pool para operaciones CPU-bound.

    Usar para: análisis de complejidad batch, cálculos simbólicos pesados,
    procesamiento de ASTs grandes en paralelo.

    Workers: CPUs - 1 (dejar un CPU para el event loop principal).

    Nota: Para operaciones genuinamente CPU-bound en producción con alta
    carga, considerar ProcessPoolExecutor en su lugar (evita el GIL).
    Sin embargo, ProcessPoolExecutor requiere que los objetos sean
    serializables (pickle), lo que no siempre es posible con ASTs.

    Example:
        >>> loop = asyncio.get_event_loop()
        >>> result = await loop.run_in_executor(get_cpu_pool(), heavy_analysis, ast)
    """
    registry = ThreadPoolRegistry()
    return registry.get_or_create(
        name="cpu",
        max_workers=registry.config.cpu_workers,
    )

def get_graphviz_pool() -> ThreadPoolExecutor:
    """
    Pool dedicado a subprocesos de Graphviz.

    Por qué un pool separado:
    - Graphviz lanza procesos del SO (dot, neato, etc.)
    - Cada proceso consume memoria real del sistema
    - Limitar a 4 workers previene saturación de subprocesos

    Si diagram_renderer.py usa run_in_executor(None, ...) (pool por defecto),
    reemplazar None por get_graphviz_pool() para control más fino.

    Example:
        >>> loop = asyncio.get_event_loop()
        >>> svg = await loop.run_in_executor(
        ...     get_graphviz_pool(),
        ...     dot.pipe,  # método bloqueante de graphviz
        ... )
    """
    registry = ThreadPoolRegistry()
    return registry.get_or_create(
        name="graphviz",
        max_workers=registry.config.graphviz_workers,
    )

def shutdown_all_pools(wait: bool = True) -> None:
    """
    Cierra todos los pools activos.

    Llamar desde el lifespan de FastAPI en el evento de shutdown para
    asegurar que todos los threads terminan limpiamente antes de que
    el proceso muera.

    Example:
        >>> # En app/main.py, dentro del bloque de shutdown del lifespan:
        >>> from app.parallel.worker_pools import shutdown_all_pools
        >>> shutdown_all_pools(wait=True)
    """
    if ThreadPoolRegistry._instance is not None:
        ThreadPoolRegistry._instance.shutdown_all(wait=wait)

def get_pool_stats() -> Dict[str, dict]:
    """
    Retorna estadísticas de todos los pools activos.

    Útil para el endpoint /health o para métricas de Prometheus.

    Example:
        >>> stats = get_pool_stats()
        >>> print(stats)
        >>> # {'io': {'max_workers': 8, 'active': True}, ...}
    """
    if ThreadPoolRegistry._instance is None:
        return {}
    return ThreadPoolRegistry._instance.get_stats()