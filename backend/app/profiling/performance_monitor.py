"""
Performance Monitor - Monitor Integral de Performance

Combina timing y memoria profiling para análisis completo de performance.
Proporciona métricas agregadas y reportes detallados.
"""

import sys
from typing import Any, Callable, Dict, List, Optional, TypeVar
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from enum import Enum

from app.profiling.execution_timer import ExecutionTimer, TimingResult
from app.profiling.memory_profiler import MemoryProfiler, MemoryDiff
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

F = TypeVar('F', bound=Callable[..., Any])

class PerformanceLevel(str, Enum):
    """Niveles de performance"""
    EXCELLENT = "excellent"      # < 100ms y < 10MB
    GOOD = "good"                # < 500ms y < 50MB
    ACCEPTABLE = "acceptable"    # < 2s y < 200MB
    SLOW = "slow"                # < 10s y < 500MB
    CRITICAL = "critical"        # >= 10s o >= 500MB

@dataclass
class PerformanceMetrics:
    """Métricas de performance combinadas"""
    operation: str
    module: Optional[str] = None
    
    # Timing
    timing_result: Optional[TimingResult] = None
    execution_time_ms: float = 0.0
    
    # Memory
    memory_diff: Optional[MemoryDiff] = None
    memory_delta_mb: float = 0.0
    
    # Nivel de performance
    performance_level: PerformanceLevel = PerformanceLevel.ACCEPTABLE
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    warnings: List[str] = field(default_factory=list)
    
    @property
    def is_performant(self) -> bool:
        """Indica si la performance es aceptable"""
        return self.performance_level in [
            PerformanceLevel.EXCELLENT,
            PerformanceLevel.GOOD,
            PerformanceLevel.ACCEPTABLE
        ]
    
    @property
    def has_memory_leak(self) -> bool:
        """Indica si hay posible memory leak"""
        return (
            self.memory_diff is not None
            and self.memory_diff.has_leak
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario"""
        return {
            "operation": self.operation,
            "module": self.module,
            "timestamp": self.timestamp.isoformat(),
            "execution_time_ms": self.execution_time_ms,
            "memory_delta_mb": self.memory_delta_mb,
            "performance_level": self.performance_level.value,
            "is_performant": self.is_performant,
            "has_memory_leak": self.has_memory_leak,
            "warnings": self.warnings,
            "timing": self.timing_result.to_dict() if self.timing_result else None,
            "memory": self.memory_diff.to_dict() if self.memory_diff else None,
        }

@dataclass
class ModulePerformance:
    """Performance agregada por módulo"""
    module_name: str
    operations: List[PerformanceMetrics] = field(default_factory=list)
    
    @property
    def total_operations(self) -> int:
        """Total de operaciones"""
        return len(self.operations)
    
    @property
    def avg_execution_time_ms(self) -> float:
        """Tiempo de ejecución promedio"""
        if not self.operations:
            return 0.0
        return sum(op.execution_time_ms for op in self.operations) / len(self.operations)
    
    @property
    def avg_memory_delta_mb(self) -> float:
        """Delta de memoria promedio"""
        if not self.operations:
            return 0.0
        return sum(op.memory_delta_mb for op in self.operations) / len(self.operations)
    
    @property
    def slow_operations_count(self) -> int:
        """Número de operaciones lentas"""
        return sum(
            1 for op in self.operations
            if op.performance_level in [PerformanceLevel.SLOW, PerformanceLevel.CRITICAL]
        )
    
    @property
    def memory_leaks_count(self) -> int:
        """Número de operaciones con posibles leaks"""
        return sum(1 for op in self.operations if op.has_memory_leak)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario"""
        return {
            "module_name": self.module_name,
            "total_operations": self.total_operations,
            "avg_execution_time_ms": self.avg_execution_time_ms,
            "avg_memory_delta_mb": self.avg_memory_delta_mb,
            "slow_operations_count": self.slow_operations_count,
            "memory_leaks_count": self.memory_leaks_count,
            "operations": [op.to_dict() for op in self.operations],
        }

class PerformanceMonitor:
    """
    Monitor integral de performance.
    
    Combina ExecutionTimer y MemoryProfiler para análisis completo.
    
    Example:
        >>> monitor = PerformanceMonitor(enable_memory=True)
        >>> 
        >>> # Context manager
        >>> with monitor.monitor("parse_algorithm", module="parser") as metrics:
        >>>     ast = parser.parse(code)
        >>> 
        >>> print(f"Tiempo: {metrics.execution_time_ms:.2f}ms")
        >>> print(f"Memoria: {metrics.memory_delta_mb:.2f}MB")
        >>> 
        >>> # Decorador
        >>> @monitor.monitored()
        >>> def my_function():
        >>>     pass
        >>> 
        >>> # Generar reporte
        >>> monitor.generate_report(Path("performance_report.json"))
    """
    
    def __init__(
        self,
        enabled: bool = True,
        enable_timing: bool = True,
        enable_memory: bool = False,
        use_tracemalloc: bool = False
    ):
        """
        Inicializa el monitor.
        
        Args:
            enabled: Si False, el monitor no hace nada
            enable_timing: Si True, habilita timing
            enable_memory: Si True, habilita memory profiling
            use_tracemalloc: Si True, usa tracemalloc (más detallado pero más lento)
        """
        self.enabled = enabled
        self.enable_timing = enable_timing
        self.enable_memory = enable_memory
        
        # Inicializar timers y profilers
        self.timer = ExecutionTimer(enabled=enabled and enable_timing)
        self.memory_profiler = MemoryProfiler(
            enabled=enabled and enable_memory,
            use_tracemalloc=use_tracemalloc
        )
        
        # Almacenar métricas
        self._metrics: List[PerformanceMetrics] = []
        self._module_metrics: Dict[str, ModulePerformance] = {}
    
    @contextmanager
    def monitor(
        self,
        operation: str,
        module: Optional[str] = None,
        log_result: bool = True
    ):
        """
        Context manager para monitorear performance.
        
        Args:
            operation: Nombre de la operación
            module: Nombre del módulo
            log_result: Si True, loggea el resultado
        
        Yields:
            PerformanceMetrics: Métricas de performance
        
        Example:
            >>> monitor = PerformanceMonitor(enable_memory=True)
            >>> with monitor.monitor("parse_code", "parser") as metrics:
            >>>     ast = parser.parse(code)
            >>> print(f"Nivel: {metrics.performance_level.value}")
        """
        if not self.enabled:
            yield PerformanceMetrics(operation=operation, module=module)
            return
        
        metrics = PerformanceMetrics(
            operation=operation,
            module=module,
        )
        
        # Contextos anidados para timing y memoria
        timing_ctx = self.timer.time(operation, module=module, log_result=False)
        memory_ctx = self.memory_profiler.profile(operation, module=module, log_result=False)

        # Usar with anidado y actualizar métricas después de que ambos contexts hayan cerrado
        with timing_ctx as timing_result:
            with memory_ctx as memory_diff:
                try:
                    yield metrics
                finally:
                    # No actualizar todavía: timing/ memory todavía no han cerrado completamente
                    pass

        # Aquí ambos contextos ya han ejecutado sus bloques de salida y están poblados
        if timing_result:
            metrics.timing_result = timing_result
            metrics.execution_time_ms = getattr(timing_result, "duration_ms", 0.0)

        if memory_diff:
            metrics.memory_diff = memory_diff
            metrics.memory_delta_mb = getattr(memory_diff, "current_diff_mb", 0.0)

        # Calcular nivel de performance
        metrics.performance_level = self._calculate_performance_level(metrics)

        # Generar warnings
        metrics.warnings = self._generate_warnings(metrics)

        # Almacenar métricas
        self._metrics.append(metrics)

        # Almacenar por módulo
        if module:
            if module not in self._module_metrics:
                self._module_metrics[module] = ModulePerformance(module_name=module)
            self._module_metrics[module].operations.append(metrics)

        # Loggear si corresponde
        if log_result:
            self._log_metrics(metrics)
    
    def monitored(
        self,
        operation: Optional[str] = None,
        module: Optional[str] = None,
        log_result: bool = True
    ) -> Callable[[F], F]:
        """
        Decorador para monitorear funciones.
        
        Args:
            operation: Nombre de la operación (default: nombre función)
            module: Nombre del módulo (default: módulo de la función)
            log_result: Si True, loggea el resultado
        
        Returns:
            Decorador que monitorea performance
        
        Example:
            >>> monitor = PerformanceMonitor()
            >>> 
            >>> @monitor.monitored()
            >>> def process_data(data):
            >>>     return analyze(data)
        """
        def decorator(func: F) -> F:
            if not self.enabled:
                return func
            
            op_name = operation or func.__name__
            op_module = module or func.__module__
            
            def wrapper(*args, **kwargs):
                with self.monitor(
                    op_name,
                    module=op_module,
                    log_result=log_result
                ):
                    return func(*args, **kwargs)
            
            return wrapper
        
        return decorator
    
    def get_metrics(
        self,
        operation: Optional[str] = None,
        module: Optional[str] = None
    ) -> List[PerformanceMetrics]:
        """
        Obtiene métricas filtradas.
        
        Args:
            operation: Filtrar por operación
            module: Filtrar por módulo
        
        Returns:
            Lista de métricas
        """
        metrics = self._metrics
        
        if operation:
            metrics = [m for m in metrics if m.operation == operation]
        
        if module:
            metrics = [m for m in metrics if m.module == module]
        
        return metrics
    
    def get_module_performance(self, module: str) -> Optional[ModulePerformance]:
        """
        Obtiene performance agregada de un módulo.
        
        Args:
            module: Nombre del módulo
        
        Returns:
            ModulePerformance o None
        """
        return self._module_metrics.get(module)
    
    def get_all_module_performance(self) -> Dict[str, ModulePerformance]:
        """Obtiene performance de todos los módulos"""
        return self._module_metrics.copy()
    
    def get_slow_operations(
        self,
        threshold_ms: Optional[float] = None
    ) -> List[PerformanceMetrics]:
        """
        Obtiene operaciones lentas.
        
        Args:
            threshold_ms: Umbral en ms (default: automático basado en nivel)
        
        Returns:
            Lista de operaciones lentas
        """
        if threshold_ms is not None:
            return [
                m for m in self._metrics
                if m.execution_time_ms > threshold_ms
            ]
        
        return [
            m for m in self._metrics
            if m.performance_level in [PerformanceLevel.SLOW, PerformanceLevel.CRITICAL]
        ]
    
    def get_memory_intensive_operations(
        self,
        threshold_mb: float = 50.0
    ) -> List[PerformanceMetrics]:
        """
        Obtiene operaciones con alto consumo de memoria.
        
        Args:
            threshold_mb: Umbral en MB
        
        Returns:
            Lista de operaciones
        """
        return [
            m for m in self._metrics
            if m.memory_delta_mb > threshold_mb
        ]
    
    def print_summary(self):
        """Imprime resumen completo de performance"""
        if not self._metrics:
            print("No hay métricas de performance.")
            return
        
        print("\n" + "="*90)
        print("RESUMEN DE PERFORMANCE")
        print("="*90)
        
        # Resumen general
        total_ops = len(self._metrics)
        avg_time = sum(m.execution_time_ms for m in self._metrics) / total_ops
        avg_memory = sum(m.memory_delta_mb for m in self._metrics) / total_ops
        slow_ops = len(self.get_slow_operations())
        memory_leaks = sum(1 for m in self._metrics if m.has_memory_leak)
        
        print(f"\nOperaciones totales: {total_ops}")
        print(f"Tiempo promedio: {avg_time:.2f}ms")
        print(f"Memoria promedio: {avg_memory:.2f}MB")
        print(f"Operaciones lentas: {slow_ops} ({slow_ops/total_ops*100:.1f}%)")
        if self.enable_memory:
            print(f"Posibles memory leaks: {memory_leaks}")
        
        # Por módulo
        print("\nPERFORMANCE POR MÓDULO:")
        print(f"{'Módulo':<20} {'Ops':>8} {'Tiempo Avg':>12} {'Memoria Avg':>12} {'Lentas':>8} {'Leaks':>8}")
        print("-"*90)
        
        for module, module_perf in sorted(
            self._module_metrics.items(),
            key=lambda x: x[1].avg_execution_time_ms,
            reverse=True
        ):
            print(
                f"{module:<20} "
                f"{module_perf.total_operations:>8} "
                f"{module_perf.avg_execution_time_ms:>11.2f}ms "
                f"{module_perf.avg_memory_delta_mb:>11.2f}MB "
                f"{module_perf.slow_operations_count:>8} "
                f"{module_perf.memory_leaks_count:>8}"
            )
        
        # Top operaciones lentas
        slow_ops = sorted(
            self.get_slow_operations(),
            key=lambda x: x.execution_time_ms,
            reverse=True
        )[:10]
        
        if slow_ops:
            print("\nTOP 10 OPERACIONES MÁS LENTAS:")
            print(f"{'Operación':<30} {'Módulo':<15} {'Tiempo':>12} {'Nivel':<12}")
            print("-"*90)
            
            for op in slow_ops:
                print(
                    f"{op.operation:<30} "
                    f"{op.module or 'N/A':<15} "
                    f"{op.execution_time_ms:>11.2f}ms "
                    f"{op.performance_level.value:<12}"
                )
        
        print("="*90 + "\n")
    
    def generate_report(self, output_path: Path):
        """
        Genera reporte completo en JSON.
        
        Args:
            output_path: Ruta del archivo de salida
        """
        import json
        
        report = {
            "summary": {
                "total_operations": len(self._metrics),
                "avg_execution_time_ms": (
                    sum(m.execution_time_ms for m in self._metrics) / len(self._metrics)
                    if self._metrics else 0
                ),
                "avg_memory_delta_mb": (
                    sum(m.memory_delta_mb for m in self._metrics) / len(self._metrics)
                    if self._metrics else 0
                ),
                "slow_operations_count": len(self.get_slow_operations()),
                "memory_leaks_count": sum(1 for m in self._metrics if m.has_memory_leak),
            },
            "modules": {
                module: module_perf.to_dict()
                for module, module_perf in self._module_metrics.items()
            },
            "operations": [m.to_dict() for m in self._metrics],
            "slow_operations": [
                m.to_dict() for m in self.get_slow_operations()
            ],
            "memory_intensive": [
                m.to_dict() for m in self.get_memory_intensive_operations()
            ],
        }
        
        output_path.write_text(
            json.dumps(report, indent=2),
            encoding='utf-8'
        )
        
        logger.info(f"Reporte de performance generado: {output_path}")
    
    def reset(self):
        """Resetea todas las métricas"""
        self._metrics.clear()
        self._module_metrics.clear()
        self.timer.reset_stats()
        self.memory_profiler.reset()
    
    def stop(self):
        """Detiene profiling y libera recursos"""
        self.memory_profiler.stop()
    
    # Métodos privados
    def _calculate_performance_level(
        self,
        metrics: PerformanceMetrics
    ) -> PerformanceLevel:
        """Calcula nivel de performance basado en métricas"""
        time_ms = metrics.execution_time_ms
        memory_mb = metrics.memory_delta_mb
        
        # CRITICAL: >= 10s o >= 500MB
        if time_ms >= 10000 or memory_mb >= 500:
            return PerformanceLevel.CRITICAL
        
        # SLOW: >= 500ms o >= 200MB
        if time_ms >= 500 or memory_mb >= 200:
            return PerformanceLevel.SLOW

        # ACCEPTABLE: >= 100ms o >= 50MB
        if time_ms >= 100 or memory_mb >= 50:
            return PerformanceLevel.ACCEPTABLE

        # GOOD: >= 50ms o >= 10MB
        if time_ms >= 50 or memory_mb >= 10:
            return PerformanceLevel.GOOD

        # EXCELLENT: < 50ms y < 10MB
        return PerformanceLevel.EXCELLENT
    
    def _generate_warnings(self, metrics: PerformanceMetrics) -> List[str]:
        """Genera warnings basados en métricas"""
        warnings = []
        
        # Warning por tiempo
        if metrics.execution_time_ms >= 5000:
            warnings.append(f"Tiempo de ejecución muy alto: {metrics.execution_time_ms:.0f}ms")
        
        # Warning por memoria
        if metrics.memory_delta_mb >= 100:
            warnings.append(f"Alto consumo de memoria: {metrics.memory_delta_mb:.1f}MB")
        
        # Warning por leak
        if metrics.has_memory_leak:
            warnings.append("Posible memory leak detectado")
        
        return warnings
    
    def _log_metrics(self, metrics: PerformanceMetrics):
        """Loggea métricas"""
        level_label = {
            PerformanceLevel.EXCELLENT: "EXCELLENT",
            PerformanceLevel.GOOD: "GOOD",
            PerformanceLevel.ACCEPTABLE: "ACCEPTABLE",
            PerformanceLevel.SLOW: "SLOW",
            PerformanceLevel.CRITICAL: "CRITICAL",
        }
        
        label = level_label.get(metrics.performance_level, "UNKNOWN")
        
        msg = (
            f"{label} {metrics.operation}: "
            f"{metrics.execution_time_ms:.2f}ms"
        )
        
        if self.enable_memory:
            msg += f", {metrics.memory_delta_mb:.2f}MB"
        
        if metrics.module:
            msg += f" ({metrics.module})"
        
        if metrics.warnings:
            msg += f"{'; '.join(metrics.warnings)}"
        
        logger.debug(msg)

# Instancia global
_global_monitor: Optional[PerformanceMonitor] = None

def get_performance_monitor(
    enabled: bool = True,
    enable_memory: bool = False
) -> PerformanceMonitor:
    """
    Obtiene instancia global del monitor.
    
    Args:
        enabled: Si el monitor está habilitado
        enable_memory: Si el memory profiling está habilitado
    
    Returns:
        PerformanceMonitor: Instancia global
    """
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = PerformanceMonitor(
            enabled=enabled,
            enable_memory=enable_memory
        )
    return _global_monitor