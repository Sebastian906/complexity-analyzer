"""
Memory Profiler - Sistema de Profiling de Memoria

Proporciona herramientas para monitorear uso de memoria, detectar leaks
y obtener estadísticas de consumo.
"""

import gc
import sys
import tracemalloc
from typing import Any, Callable, Dict, List, Optional, TypeVar, cast
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from app.utils.logger import setup_logger

logger = setup_logger(__name__)

F = TypeVar('F', bound=Callable[..., Any])

@dataclass
class MemorySnapshot:
    """Snapshot de uso de memoria en un punto del tiempo"""
    timestamp: datetime
    current_mb: float
    peak_mb: float
    
    # Si tracemalloc está habilitado
    traced_current_mb: Optional[float] = None
    traced_peak_mb: Optional[float] = None
    
    # Top allocations (si está disponible)
    top_allocations: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    operation: Optional[str] = None
    module: Optional[str] = None
    
    @property
    def current_readable(self) -> str:
        """Memoria actual en formato legible"""
        return self._format_bytes(self.current_mb * 1024 * 1024)
    
    @property
    def peak_readable(self) -> str:
        """Memoria pico en formato legible"""
        return self._format_bytes(self.peak_mb * 1024 * 1024)
    
    @staticmethod
    def _format_bytes(bytes_value: float) -> str:
        """Formatea bytes a formato legible"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} TB"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "current_mb": self.current_mb,
            "peak_mb": self.peak_mb,
            "current_readable": self.current_readable,
            "peak_readable": self.peak_readable,
            "traced_current_mb": self.traced_current_mb,
            "traced_peak_mb": self.traced_peak_mb,
            "top_allocations": self.top_allocations,
            "operation": self.operation,
            "module": self.module,
        }

@dataclass
class MemoryDiff:
    """Diferencia de memoria entre dos snapshots"""
    start_snapshot: MemorySnapshot
    end_snapshot: MemorySnapshot
    
    @property
    def current_diff_mb(self) -> float:
        """Diferencia en memoria actual"""
        return self.end_snapshot.current_mb - self.start_snapshot.current_mb
    
    @property
    def peak_diff_mb(self) -> float:
        """Diferencia en memoria pico"""
        return self.end_snapshot.peak_mb - self.start_snapshot.peak_mb
    
    @property
    def current_diff_readable(self) -> str:
        """Diferencia en memoria actual (legible)"""
        diff = self.current_diff_mb * 1024 * 1024
        sign = "+" if diff >= 0 else ""
        return sign + MemorySnapshot._format_bytes(abs(diff))
    
    @property
    def has_leak(self) -> bool:
        """Indica si hay probable leak (memoria no liberada)"""
        # Si la diferencia es > 1 MB, probablemente hay leak
        return self.current_diff_mb > 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario"""
        return {
            "start": self.start_snapshot.to_dict(),
            "end": self.end_snapshot.to_dict(),
            "current_diff_mb": self.current_diff_mb,
            "peak_diff_mb": self.peak_diff_mb,
            "current_diff_readable": self.current_diff_readable,
            "has_potential_leak": self.has_leak,
        }

class MemoryProfiler:
    """
    Profiler de memoria con soporte para tracemalloc.
    
    Permite monitorear uso de memoria y detectar leaks.
    
    Example:
        >>> profiler = MemoryProfiler(use_tracemalloc=True)
        >>> 
        >>> # Context manager
        >>> with profiler.profile("mi_operacion") as diff:
        >>>     # código a perfilar
        >>>     process_large_data()
        >>> 
        >>> print(f"Memoria usada: {diff.current_diff_readable}")
        >>> 
        >>> # Decorador
        >>> @profiler.profile_function()
        >>> def my_function():
        >>>     pass
    """
    
    def __init__(
        self,
        enabled: bool = True,
        use_tracemalloc: bool = False,
        top_allocations: int = 10
    ):
        """
        Inicializa el profiler.
        
        Args:
            enabled: Si False, el profiler no hace nada
            use_tracemalloc: Si True, usa tracemalloc para tracking detallado
            top_allocations: Número de top allocations a guardar
        """
        self.enabled = enabled
        self.use_tracemalloc = use_tracemalloc
        self.top_allocations = top_allocations
        
        self._snapshots: List[MemorySnapshot] = []
        self._diffs: Dict[str, List[MemoryDiff]] = {}
        
        if self.enabled and self.use_tracemalloc:
            if not tracemalloc.is_tracing():
                tracemalloc.start()
                logger.debug("tracemalloc iniciado")
    
    def take_snapshot(
        self,
        operation: Optional[str] = None,
        module: Optional[str] = None
    ) -> MemorySnapshot:
        """
        Toma snapshot del uso actual de memoria.
        
        Args:
            operation: Nombre de la operación
            module: Nombre del módulo
        
        Returns:
            MemorySnapshot: Snapshot de memoria
        """
        if not self.enabled:
            return MemorySnapshot(
                timestamp=datetime.now(),
                current_mb=0.0,
                peak_mb=0.0,
            )
        
        # Forzar garbage collection para mediciones más precisas
        gc.collect()

        # Obtener info de proceso (RSS) con fallbacks multiplataforma
        current_mb = 0.0
        peak_mb = 0.0

        try:
            # En sistemas POSIX (Linux/Mac)
            import resource  # type: ignore
            usage = resource.getrusage(resource.RUSAGE_SELF)
            current_mb = usage.ru_maxrss / 1024  # En MB (Linux/Mac: ru_maxrss suele venir en KB)
            peak_mb = current_mb
        except Exception:
            try:
                # Intentar psutil si está disponible (funciona en Windows)
                import psutil  # type: ignore
                proc = psutil.Process()
                current_mb = proc.memory_info().rss / 1024 / 1024
                peak_mb = current_mb
            except Exception:
                # Fallback: si tracemalloc está activo, usar sus valores trazados
                if self.use_tracemalloc and tracemalloc.is_tracing():
                    current, peak = tracemalloc.get_traced_memory()
                    current_mb = current / 1024 / 1024
                    peak_mb = peak / 1024 / 1024
                else:
                    # No se pudo obtener memoria; dejar 0.0 para no fallar en Windows
                    current_mb = 0.0
                    peak_mb = 0.0

        snapshot = MemorySnapshot(
            timestamp=datetime.now(),
            current_mb=current_mb,
            peak_mb=peak_mb,
            operation=operation,
            module=module,
        )
        
        # Si tracemalloc está habilitado
        if self.use_tracemalloc and tracemalloc.is_tracing():
            current, peak = tracemalloc.get_traced_memory()
            snapshot.traced_current_mb = current / 1024 / 1024  # Bytes -> MB
            snapshot.traced_peak_mb = peak / 1024 / 1024
            
            # Top allocations
            snapshot.top_allocations = self._get_top_allocations()
        
        self._snapshots.append(snapshot)
        return snapshot
    
    @contextmanager
    def profile(
        self,
        operation: str,
        module: Optional[str] = None,
        log_result: bool = True
    ):
        """
        Context manager para perfilar memoria.
        
        Args:
            operation: Nombre de la operación
            module: Nombre del módulo
            log_result: Si True, loggea el resultado
        
        Yields:
            MemoryDiff: Diferencia de memoria
        
        Example:
            >>> profiler = MemoryProfiler()
            >>> with profiler.profile("parse_code") as diff:
            >>>     ast = parser.parse(code)
            >>> print(f"Memoria: {diff.current_diff_readable}")
        """
        if not self.enabled:
            yield None
            return
        
        start_snapshot = self.take_snapshot(operation=operation, module=module)
        
        diff = MemoryDiff(
            start_snapshot=start_snapshot,
            end_snapshot=start_snapshot,  # Se actualizará
        )
        
        try:
            yield diff
        finally:
            end_snapshot = self.take_snapshot(operation=operation, module=module)
            diff.end_snapshot = end_snapshot
            
            # Guardar diff
            if operation not in self._diffs:
                self._diffs[operation] = []
            self._diffs[operation].append(diff)
            
            if log_result:
                leak_warning = "POSIBLE LEAK" if diff.has_leak else ""
                logger.debug(
                    f"{operation}: {diff.current_diff_readable}"
                    + (f" (module: {module})" if module else "")
                    + leak_warning
                )
    
    def profile_function(
        self,
        operation: Optional[str] = None,
        module: Optional[str] = None,
        log_result: bool = True
    ) -> Callable[[F], F]:
        """
        Decorador para perfilar memoria de funciones.
        
        Args:
            operation: Nombre de la operación (default: nombre función)
            module: Nombre del módulo (default: módulo de la función)
            log_result: Si True, loggea el resultado
        
        Returns:
            Decorador que perfila memoria
        
        Example:
            >>> profiler = MemoryProfiler()
            >>> 
            >>> @profiler.profile_function()
            >>> def process_data(data):
            >>>     return analyze(data)
        """
        def decorator(func: F) -> F:
            if not self.enabled:
                return func
            
            op_name = operation or func.__name__
            op_module = module or func.__module__
            
            def wrapper(*args, **kwargs):
                with self.profile(
                    op_name,
                    module=op_module,
                    log_result=log_result
                ):
                    return func(*args, **kwargs)
            
            return cast(F, wrapper)
        
        return decorator
    
    def get_diffs(self, operation: str) -> List[MemoryDiff]:
        """
        Obtiene diferencias de memoria para una operación.
        
        Args:
            operation: Nombre de la operación
        
        Returns:
            Lista de MemoryDiff
        """
        return self._diffs.get(operation, [])
    
    def get_all_diffs(self) -> Dict[str, List[MemoryDiff]]:
        """Obtiene todas las diferencias"""
        return self._diffs.copy()
    
    def get_snapshots(self) -> List[MemorySnapshot]:
        """Obtiene todos los snapshots"""
        return self._snapshots.copy()
    
    def detect_leaks(self, threshold_mb: float = 1.0) -> Dict[str, List[MemoryDiff]]:
        """
        Detecta operaciones con posibles memory leaks.
        
        Args:
            threshold_mb: Umbral de diferencia en MB para considerar leak
        
        Returns:
            Diccionario de operaciones con leaks
        """
        leaks = {}
        
        for operation, diffs in self._diffs.items():
            leaky_diffs = [
                diff for diff in diffs
                if diff.current_diff_mb > threshold_mb
            ]
            
            if leaky_diffs:
                leaks[operation] = leaky_diffs
        
        return leaks
    
    def print_summary(self):
        """Imprime resumen de memoria"""
        if not self._diffs:
            print("No hay datos de profiling de memoria.")
            return
        
        print("\n" + "="*80)
        print("RESUMEN DE MEMORIA")
        print("="*80)
        print(f"{'Operación':<30} {'Ejecuciones':>12} {'Promedio':>15} {'Max':>15} {'Leaks':>8}")
        print("-"*80)
        
        for operation, diffs in self._diffs.items():
            avg_diff = sum(d.current_diff_mb for d in diffs) / len(diffs)
            max_diff = max(d.current_diff_mb for d in diffs)
            leak_count = sum(1 for d in diffs if d.has_leak)
            
            print(
                f"{operation:<30} "
                f"{len(diffs):>12} "
                f"{avg_diff:>14.2f}MB "
                f"{max_diff:>14.2f}MB "
                f"{leak_count:>8}"
            )
        
        # Mostrar leaks detectados
        leaks = self.detect_leaks()
        if leaks:
            print("\nPOSIBLES MEMORY LEAKS DETECTADOS:")
            for operation, leak_diffs in leaks.items():
                print(f"  - {operation}: {len(leak_diffs)} casos")
        
        print("="*80 + "\n")
    
    def export_report(self, output_path: Path):
        """
        Exporta reporte completo a JSON.
        
        Args:
            output_path: Ruta del archivo de salida
        """
        import json
        
        report = {
            "snapshots": [s.to_dict() for s in self._snapshots],
            "diffs": {
                operation: [d.to_dict() for d in diffs]
                for operation, diffs in self._diffs.items()
            },
            "leaks_detected": {
                operation: [d.to_dict() for d in leak_diffs]
                for operation, leak_diffs in self.detect_leaks().items()
            },
        }
        
        output_path.write_text(
            json.dumps(report, indent=2),
            encoding='utf-8'
        )
        
        logger.info(f"Reporte de memoria exportado a: {output_path}")
    
    def reset(self):
        """Resetea estadísticas"""
        self._snapshots.clear()
        self._diffs.clear()
        
        if self.use_tracemalloc and tracemalloc.is_tracing():
            tracemalloc.clear_traces()
    
    def stop(self):
        """Detiene profiling (libera recursos)"""
        if self.use_tracemalloc and tracemalloc.is_tracing():
            tracemalloc.stop()
            logger.debug("tracemalloc detenido")
    
    def _get_top_allocations(self) -> List[Dict[str, Any]]:
        """Obtiene top allocations de tracemalloc"""
        if not tracemalloc.is_tracing():
            return []
        
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics('lineno')
        
        allocations = []
        for stat in top_stats[:self.top_allocations]:
            allocations.append({
                "filename": stat.traceback.format()[0],
                "size_mb": stat.size / 1024 / 1024,
                "count": stat.count,
            })
        
        return allocations

# Instancia global
_global_profiler: Optional[MemoryProfiler] = None

def get_memory_profiler(
    enabled: bool = True,
    use_tracemalloc: bool = False
) -> MemoryProfiler:
    """
    Obtiene instancia global del memory profiler.
    
    Args:
        enabled: Si el profiler está habilitado
        use_tracemalloc: Si usa tracemalloc
    
    Returns:
        MemoryProfiler: Instancia global
    """
    global _global_profiler
    if _global_profiler is None:
        _global_profiler = MemoryProfiler(
            enabled=enabled,
            use_tracemalloc=use_tracemalloc
        )
    return _global_profiler

# Helper functions usando profiler global
def profile_memory(
    operation: str,
    module: Optional[str] = None,
    log_result: bool = True
):
    """
    Context manager global para profiling de memoria.
    
    Example:
        >>> from app.profiling.memory_profiler import profile_memory
        >>> 
        >>> with profile_memory("my_operation"):
        >>>     process_large_data()
    """
    profiler = get_memory_profiler()
    return profiler.profile(operation, module=module, log_result=log_result)