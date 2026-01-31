"""
Profiling Module - Sistema de Profiling de Performance

Proporciona herramientas para medir y monitorear performance del sistema:
- ExecutionTimer: Timing de operaciones
- MemoryProfiler: Profiling de memoria
- PerformanceMonitor: Monitor integral (timing + memoria)

Example:
    >>> from app.profiling import get_performance_monitor, timed
    >>> 
    >>> # Usar monitor global
    >>> monitor = get_performance_monitor(enable_memory=True)
    >>> 
    >>> with monitor.monitor("parse_algorithm", module="parser") as metrics:
    >>>     ast = parser.parse(code)
    >>> 
    >>> print(f"Tiempo: {metrics.execution_time_ms:.2f}ms")
    >>> print(f"Memoria: {metrics.memory_delta_mb:.2f}MB")
    >>> 
    >>> # O usar decorador
    >>> @timed()
    >>> def my_function():
    >>>     pass
    >>> 
    >>> # Generar reporte
    >>> monitor.generate_report(Path("report.json"))
"""

# Execution Timer
from app.profiling.execution_timer import (
    ExecutionTimer,
    TimingResult,
    TimingStats,
    get_timer,
    timed,
    time_block,
)

# Memory Profiler
from app.profiling.memory_profiler import (
    MemoryProfiler,
    MemorySnapshot,
    MemoryDiff,
    get_memory_profiler,
    profile_memory,
)

# Performance Monitor
from app.profiling.performance_monitor import (
    PerformanceMonitor,
    PerformanceMetrics,
    ModulePerformance,
    PerformanceLevel,
    get_performance_monitor,
)

__all__ = [
    # Execution Timer
    "ExecutionTimer",
    "TimingResult",
    "TimingStats",
    "get_timer",
    "timed",
    "time_block",
    
    # Memory Profiler
    "MemoryProfiler",
    "MemorySnapshot",
    "MemoryDiff",
    "get_memory_profiler",
    "profile_memory",
    
    # Performance Monitor
    "PerformanceMonitor",
    "PerformanceMetrics",
    "ModulePerformance",
    "PerformanceLevel",
    "get_performance_monitor",
]

# Helper Functions Globales
def profile_module(module_name: str, enable_memory: bool = False):
    """
    Decorador helper para perfilar todas las funciones de un módulo.
    
    Args:
        module_name: Nombre del módulo
        enable_memory: Si True, habilita memory profiling
    
    Returns:
        Decorador que perfila funciones
    
    Example:
        >>> from app.profiling import profile_module
        >>> 
        >>> @profile_module("parser", enable_memory=True)
        >>> def parse_code(code):
        >>>     return parser.parse(code)
    """
    monitor = get_performance_monitor(enable_memory=enable_memory)
    return monitor.monitored(module=module_name)

def enable_profiling(
    enable_timing: bool = True,
    enable_memory: bool = False,
    use_tracemalloc: bool = False
):
    """
    Habilita profiling global.
    
    Args:
        enable_timing: Habilita timing
        enable_memory: Habilita memory profiling
        use_tracemalloc: Usa tracemalloc (más detallado pero más lento)
    
    Example:
        >>> from app.profiling import enable_profiling
        >>> 
        >>> # Habilitar al inicio de la aplicación
        >>> enable_profiling(enable_timing=True, enable_memory=True)
    """
    global _global_monitor
    _global_monitor = PerformanceMonitor(
        enabled=True,
        enable_timing=enable_timing,
        enable_memory=enable_memory,
        use_tracemalloc=use_tracemalloc,
    )

def disable_profiling():
    """
    Deshabilita profiling global.
    
    Example:
        >>> from app.profiling import disable_profiling
        >>> 
        >>> # Deshabilitar en producción
        >>> disable_profiling()
    """
    global _global_monitor
    if _global_monitor:
        _global_monitor.stop()
        _global_monitor = None

def generate_profiling_report(output_path):
    """
    Genera reporte completo de profiling.
    
    Args:
        output_path: Ruta del archivo de salida (Path o str)
    
    Example:
        >>> from app.profiling import generate_profiling_report
        >>> from pathlib import Path
        >>> 
        >>> generate_profiling_report(Path("logs/profiling_report.json"))
    """
    from pathlib import Path
    
    monitor = get_performance_monitor()
    monitor.generate_report(Path(output_path))

def print_profiling_summary():
    """
    Imprime resumen de profiling en consola.
    
    Example:
        >>> from app.profiling import print_profiling_summary
        >>> 
        >>> # Al finalizar ejecución
        >>> print_profiling_summary()
    """
    monitor = get_performance_monitor()
    monitor.print_summary()

def reset_profiling():
    """
    Resetea todas las métricas de profiling.
    
    Example:
        >>> from app.profiling import reset_profiling
        >>> 
        >>> # Resetear antes de nuevo test
        >>> reset_profiling()
    """
    monitor = get_performance_monitor()
    monitor.reset()