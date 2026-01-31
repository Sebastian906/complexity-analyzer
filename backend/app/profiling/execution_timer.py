"""
Execution Timer - Sistema de Medición de Tiempo de Ejecución

Proporciona decoradores y contextos para medir tiempos de ejecución
de funciones y bloques de código.
"""

import time
import functools
from typing import Any, Callable, Dict, List, Optional, TypeVar, cast
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# Type variables para decoradores
F = TypeVar('F', bound=Callable[..., Any])

@dataclass
class TimingResult:
    """Resultado de una medición de tiempo"""
    name: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    duration_ms: float
    
    # Metadata adicional
    module: Optional[str] = None
    function: Optional[str] = None
    args_summary: Optional[str] = None
    
    # Estadísticas (para múltiples ejecuciones)
    execution_count: int = 1
    min_duration: Optional[float] = None
    max_duration: Optional[float] = None
    avg_duration: Optional[float] = None
    
    @property
    def duration_readable(self) -> str:
        """Duración en formato legible"""
        if self.duration_seconds < 0.001:
            return f"{self.duration_ms * 1000:.2f} μs"
        elif self.duration_seconds < 1.0:
            return f"{self.duration_ms:.2f} ms"
        elif self.duration_seconds < 60:
            return f"{self.duration_seconds:.2f} s"
        else:
            minutes = int(self.duration_seconds // 60)
            seconds = self.duration_seconds % 60
            return f"{minutes}m {seconds:.2f}s"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario"""
        return {
            "name": self.name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_seconds": self.duration_seconds,
            "duration_ms": self.duration_ms,
            "duration_readable": self.duration_readable,
            "module": self.module,
            "function": self.function,
            "args_summary": self.args_summary,
            "execution_count": self.execution_count,
            "min_duration": self.min_duration,
            "max_duration": self.max_duration,
            "avg_duration": self.avg_duration,
        }

@dataclass
class TimingStats:
    """Estadísticas de timing para una operación"""
    name: str
    executions: List[TimingResult] = field(default_factory=list)
    
    @property
    def total_executions(self) -> int:
        """Total de ejecuciones"""
        return len(self.executions)
    
    @property
    def total_time(self) -> float:
        """Tiempo total acumulado"""
        return sum(e.duration_seconds for e in self.executions)
    
    @property
    def avg_time(self) -> float:
        """Tiempo promedio"""
        if not self.executions:
            return 0.0
        return self.total_time / len(self.executions)
    
    @property
    def min_time(self) -> float:
        """Tiempo mínimo"""
        if not self.executions:
            return 0.0
        return min(e.duration_seconds for e in self.executions)

    @property
    def max_time(self) -> float:
        """Tiempo máximo"""
        if not self.executions:
            return 0.0
        return max(e.duration_seconds for e in self.executions)

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario"""
        return {
            "name": self.name,
            "total_executions": self.total_executions,
            "total_time_seconds": self.total_time,
            "avg_time_seconds": self.avg_time,
            "min_time_seconds": self.min_time,
            "max_time_seconds": self.max_time,
            "executions": [e.to_dict() for e in self.executions],
        }

class ExecutionTimer:
    """
    Timer de ejecución con soporte para estadísticas acumulativas.
    
    Permite medir tiempos de ejecución y mantener estadísticas.
    
    Example:
        >>> timer = ExecutionTimer()
        >>> 
        >>> # Context manager
        >>> with timer.time("mi_operacion"):
        >>>     # código a medir
        >>>     process_data()
        >>> 
        >>> # Decorador
        >>> @timer.timed()
        >>> def my_function():
        >>>     pass
        >>> 
        >>> # Obtener estadísticas
        >>> stats = timer.get_stats("mi_operacion")
        >>> print(f"Promedio: {stats.avg_time:.3f}s")
    """

    def __init__(self, enabled: bool = True):
        """
        Inicializa el timer.
        
        Args:
            enabled: Si False, el timer no hace nada (útil para producción)
        """
        self.enabled = enabled
        self._stats: Dict[str, TimingStats] = {}
        self._current_timings: Dict[str, datetime] = {}
    
    @contextmanager
    def time(
        self,
        name: str,
        module: Optional[str] = None,
        log_result: bool = True
    ):
        """
        Context manager para medir tiempo de ejecución.
        
        Args:
            name: Nombre de la operación
            module: Nombre del módulo (opcional)
            log_result: Si True, loggea el resultado
        
        Yields:
            TimingResult: Resultado de timing (disponible al finalizar)
        
        Example:
            >>> timer = ExecutionTimer()
            >>> with timer.time("parse_algorithm") as result:
            >>>     ast = parser.parse(code)
            >>> print(f"Parsing tomó {result.duration_readable}")
        """
        if not self.enabled:
            yield None
            return
        
        start_time = datetime.now()
        start_perf = time.perf_counter()
        
        result = TimingResult(
            name=name,
            start_time=start_time,
            end_time=start_time,  # Se actualizará
            duration_seconds=0.0,
            duration_ms=0.0,
            module=module,
        )
        
        try:
            yield result
        finally:
            end_time = datetime.now()
            end_perf = time.perf_counter()
            
            duration_seconds = end_perf - start_perf
            duration_ms = duration_seconds * 1000
            
            result.end_time = end_time
            result.duration_seconds = duration_seconds
            result.duration_ms = duration_ms
            
            # Guardar en estadísticas
            if name not in self._stats:
                self._stats[name] = TimingStats(name=name)
            
            self._stats[name].executions.append(result)
            
            if log_result:
                logger.debug(
                    f"{name}: {result.duration_readable}"
                    + (f" (module: {module})" if module else "")
                )
    
    def timed(
        self,
        name: Optional[str] = None,
        module: Optional[str] = None,
        log_result: bool = True
    ) -> Callable[[F], F]:
        """
        Decorador para medir tiempo de ejecución de funciones.
        
        Args:
            name: Nombre de la operación (default: nombre de la función)
            module: Nombre del módulo (default: módulo de la función)
            log_result: Si True, loggea el resultado
        
        Returns:
            Decorador que mide el tiempo
        
        Example:
            >>> timer = ExecutionTimer()
            >>> 
            >>> @timer.timed()
            >>> def process_data(data):
            >>>     return analyze(data)
            >>> 
            >>> # O con nombre custom
            >>> @timer.timed(name="custom_analysis", module="analyzer")
            >>> def analyze():
            >>>     pass
        """
        def decorator(func: F) -> F:
            if not self.enabled:
                return func
            
            operation_name = name or func.__name__
            operation_module = module or func.__module__
            
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Crear resumen de args
                args_summary = self._create_args_summary(args, kwargs)
                
                with self.time(
                    operation_name,
                    module=operation_module,
                    log_result=log_result
                ) as result:
                    if result:
                        result.function = func.__name__
                        result.args_summary = args_summary

                    return func(*args, **kwargs)

            return cast(F, wrapper)

        return decorator

    def get_stats(self, name: str) -> Optional[TimingStats]:
        """
        Obtiene estadísticas de una operación.

        Args:
            name: Nombre de la operación

        Returns:
            TimingStats o None si no existe
        """
        return self._stats.get(name)

    def get_all_stats(self) -> Dict[str, TimingStats]:
        """
        Obtiene todas las estadísticas.

        Returns:
            Diccionario de estadísticas
        """
        return self._stats.copy()

    def reset_stats(self, name: Optional[str] = None):
        """
        Resetea estadísticas.

        Args:
            name: Nombre de operación específica, o None para resetear todo
        """
        if name:
            if name in self._stats:
                del self._stats[name]
        else:
            self._stats.clear()

    def print_summary(self, top_n: int = 10):
        """
        Imprime resumen de estadísticas.

        Args:
            top_n: Número de operaciones a mostrar (las más lentas)
        """
        if not self._stats:
            print("No hay estadísticas de timing.")
            return

        # Ordenar por tiempo total
        sorted_stats = sorted(
            self._stats.items(),
            key=lambda x: x[1].total_time,
            reverse=True
        )

        print("\n" + "="*80)
        print("RESUMEN DE TIMING")
        print("="*80)
        print(f"{'Operación':<30} {'Ejecuciones':>12} {'Total':>12} {'Promedio':>12} {'Min':>12} {'Max':>12}")
        print("-"*80)

        for name, stats in sorted_stats[:top_n]:
            print(
                f"{name:<30} "
                f"{stats.total_executions:>12} "
                f"{stats.total_time:>11.3f}s "
                f"{stats.avg_time:>11.3f}s "
                f"{stats.min_time:>11.3f}s "
                f"{stats.max_time:>11.3f}s"
            )
        
        print("="*80 + "\n")
    
    def export_stats(self, output_path: Path):
        """
        Exporta estadísticas a JSON.
        
        Args:
            output_path: Ruta del archivo de salida
        """
        import json
        
        stats_dict = {
            name: stats.to_dict()
            for name, stats in self._stats.items()
        }
        
        output_path.write_text(
            json.dumps(stats_dict, indent=2),
            encoding='utf-8'
        )
        
        logger.info(f"Estadísticas exportadas a: {output_path}")
    
    @staticmethod
    def _create_args_summary(args: tuple, kwargs: dict) -> str:
        """Crea resumen legible de argumentos"""
        parts = []
        
        if args:
            args_str = ", ".join(repr(a)[:50] for a in args[:3])
            if len(args) > 3:
                args_str += f", ... (+{len(args)-3} more)"
            parts.append(args_str)
        
        if kwargs:
            kwargs_str = ", ".join(
                f"{k}={repr(v)[:30]}"
                for k, v in list(kwargs.items())[:3]
            )
            if len(kwargs) > 3:
                kwargs_str += f", ... (+{len(kwargs)-3} more)"
            parts.append(kwargs_str)

        return "(" + ", ".join(parts) + ")"

# Instancia global (singleton pattern)
_global_timer: Optional[ExecutionTimer] = None

def get_timer(enabled: bool = True) -> ExecutionTimer:
    """
    Obtiene instancia global del timer.

    Args:
        enabled: Si el timer está habilitado

    Returns:
        ExecutionTimer: Instancia global
    """
    global _global_timer
    if _global_timer is None:
        _global_timer = ExecutionTimer(enabled=enabled)
    return _global_timer

# Decoradores y funciones helper que usan el timer global
def timed(
    name: Optional[str] = None,
    module: Optional[str] = None,
    log_result: bool = True
) -> Callable[[F], F]:
    """
    Decorador global para timing (usa timer global).

    Example:
        >>> from app.profiling.execution_timer import timed
        >>> 
        >>> @timed()
        >>> def my_function():
        >>>     pass
    """
    timer = get_timer()
    return timer.timed(name=name, module=module, log_result=log_result)

@contextmanager
def time_block(
    name: str,
    module: Optional[str] = None,
    log_result: bool = True
):
    """
    Context manager global para timing.

    Example:
        >>> from app.profiling.execution_timer import time_block
        >>> 
        >>> with time_block("my_operation"):
        >>>     process_data()
    """
    timer = get_timer()
    with timer.time(name, module=module, log_result=log_result) as result:
        yield result