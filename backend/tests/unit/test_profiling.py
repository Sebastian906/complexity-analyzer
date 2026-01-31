"""
Tests Unitarios - Módulo de Profiling

Tests para ExecutionTimer, MemoryProfiler y PerformanceMonitor.
"""

import pytest
from time import sleep
from pathlib import Path

from app.profiling import (
    ExecutionTimer,
    MemoryProfiler,
    PerformanceMonitor,
    PerformanceLevel,
    get_timer,
    get_memory_profiler,
    get_performance_monitor,
)

class TestExecutionTimer:
    """Tests para ExecutionTimer"""
    
    def test_timer_initialization(self):
        """Test: Inicialización del timer"""
        timer = ExecutionTimer(enabled=True)
        assert timer.enabled is True
        assert len(timer._stats) == 0
    
    def test_timer_disabled(self):
        """Test: Timer deshabilitado no hace nada"""
        timer = ExecutionTimer(enabled=False)
        
        with timer.time("test_operation"):
            sleep(0.1)
        
        assert len(timer._stats) == 0
    
    def test_time_context_manager(self):
        """Test: Context manager de timing"""
        timer = ExecutionTimer()
        
        with timer.time("sleep_test") as result:
            sleep(0.1)
        
        assert result is not None
        assert result.name == "sleep_test"
        assert result.duration_ms >= 100  # Al menos 100ms
        assert result.duration_seconds >= 0.1
    
    def test_timed_decorator(self):
        """Test: Decorador timed"""
        timer = ExecutionTimer()
        
        @timer.timed()
        def slow_function():
            sleep(0.05)
            return 42
        
        result = slow_function()
        
        assert result == 42
        stats = timer.get_stats("slow_function")
        assert stats is not None
        assert stats.total_executions == 1
    
    def test_multiple_executions(self):
        """Test: Múltiples ejecuciones de la misma operación"""
        timer = ExecutionTimer()
        
        for i in range(5):
            with timer.time("repeated_op"):
                sleep(0.01)
        
        stats = timer.get_stats("repeated_op")
        assert stats is not None
        assert stats.total_executions == 5
        assert stats.avg_time > 0
        assert stats.min_time <= stats.avg_time <= stats.max_time
    
    def test_reset_stats(self):
        """Test: Resetear estadísticas"""
        timer = ExecutionTimer()
        
        with timer.time("test"):
            pass
        
        assert len(timer._stats) == 1
        
        timer.reset_stats()
        assert len(timer._stats) == 0
    
    def test_get_all_stats(self):
        """Test: Obtener todas las estadísticas"""
        timer = ExecutionTimer()
        
        with timer.time("op1"):
            pass
        with timer.time("op2"):
            pass
        
        all_stats = timer.get_all_stats()
        assert len(all_stats) == 2
        assert "op1" in all_stats
        assert "op2" in all_stats

class TestMemoryProfiler:
    """Tests para MemoryProfiler"""
    
    def test_profiler_initialization(self):
        """Test: Inicialización del profiler"""
        profiler = MemoryProfiler(enabled=True)
        assert profiler.enabled is True
        assert len(profiler._snapshots) == 0
    
    def test_profiler_disabled(self):
        """Test: Profiler deshabilitado no hace nada"""
        profiler = MemoryProfiler(enabled=False)
        
        with profiler.profile("test_operation"):
            large_list = [i for i in range(100000)]
        
        assert len(profiler._snapshots) == 0
    
    def test_take_snapshot(self):
        """Test: Tomar snapshot de memoria"""
        profiler = MemoryProfiler(enabled=True)
        
        snapshot = profiler.take_snapshot(operation="test_snapshot")
        
        assert snapshot is not None
        assert snapshot.operation == "test_snapshot"
        assert snapshot.current_mb >= 0
        assert snapshot.peak_mb >= 0
    
    def test_profile_context_manager(self):
        """Test: Context manager de profiling"""
        profiler = MemoryProfiler(enabled=True)
        
        with profiler.profile("allocate_list") as diff:
            large_list = [i for i in range(1000000)]
        
        assert diff is not None
        # La memoria debería haber incrementado
        # (aunque puede variar dependiendo del GC)
        assert diff.current_diff_mb is not None
    
    def test_profile_function_decorator(self):
        """Test: Decorador de profiling de funciones"""
        profiler = MemoryProfiler(enabled=True)
        
        @profiler.profile_function()
        def allocate_memory():
            return [i for i in range(100000)]
        
        result = allocate_memory()
        
        assert len(result) == 100000
        diffs = profiler.get_diffs("allocate_memory")
        assert len(diffs) == 1
    
    def test_reset(self):
        """Test: Resetear profiler"""
        profiler = MemoryProfiler(enabled=True)
        
        with profiler.profile("test"):
            pass
        
        assert len(profiler._snapshots) > 0
        
        profiler.reset()
        assert len(profiler._snapshots) == 0
        assert len(profiler._diffs) == 0

class TestPerformanceMonitor:
    """Tests para PerformanceMonitor"""
    
    def test_monitor_initialization(self):
        """Test: Inicialización del monitor"""
        monitor = PerformanceMonitor(
            enabled=True,
            enable_timing=True,
            enable_memory=False
        )
        
        assert monitor.enabled is True
        assert monitor.enable_timing is True
        assert monitor.enable_memory is False
    
    def test_monitor_disabled(self):
        """Test: Monitor deshabilitado"""
        monitor = PerformanceMonitor(enabled=False)
        
        with monitor.monitor("test_op") as metrics:
            sleep(0.1)
        
        # No debería registrar métricas
        assert len(monitor._metrics) == 0
    
    def test_monitor_context_manager(self):
        """Test: Context manager del monitor"""
        monitor = PerformanceMonitor(enable_timing=True, enable_memory=False)
        
        with monitor.monitor("test_operation", module="test") as metrics:
            sleep(0.05)
        
        assert metrics is not None
        assert metrics.operation == "test_operation"
        assert metrics.module == "test"
        assert metrics.execution_time_ms >= 50
        assert metrics.performance_level is not None
    
    def test_monitored_decorator(self):
        """Test: Decorador monitored"""
        monitor = PerformanceMonitor(enable_timing=True)
        
        @monitor.monitored(module="test")
        def test_function():
            sleep(0.02)
            return 42
        
        result = test_function()
        
        assert result == 42
        metrics = monitor.get_metrics(operation="test_function")
        assert len(metrics) == 1
        assert metrics[0].module == "test"
    
    def test_performance_levels(self):
        """Test: Niveles de performance"""
        monitor = PerformanceMonitor(enable_timing=True)
        
        # EXCELLENT: < 100ms
        @monitor.monitored()
        def excellent_op():
            sleep(0.01)
        
        # SLOW: >= 500ms
        @monitor.monitored()
        def slow_op():
            sleep(0.6)
        
        excellent_op()
        slow_op()
        
        excellent_metrics = monitor.get_metrics(operation="excellent_op")[0]
        slow_metrics = monitor.get_metrics(operation="slow_op")[0]
        
        assert excellent_metrics.performance_level in [
            PerformanceLevel.EXCELLENT,
            PerformanceLevel.GOOD
        ]
        assert slow_metrics.performance_level in [
            PerformanceLevel.SLOW,
            PerformanceLevel.CRITICAL
        ]
    
    def test_get_slow_operations(self):
        """Test: Obtener operaciones lentas"""
        monitor = PerformanceMonitor(enable_timing=True)
        
        @monitor.monitored()
        def fast():
            sleep(0.01)
        
        @monitor.monitored()
        def slow():
            sleep(0.7)
        
        fast()
        slow()
        
        slow_ops = monitor.get_slow_operations()
        assert len(slow_ops) >= 1  # Al menos la operación lenta
    
    def test_module_performance(self):
        """Test: Performance por módulo"""
        monitor = PerformanceMonitor(enable_timing=True)
        
        with monitor.monitor("op1", module="module_a"):
            sleep(0.01)
        
        with monitor.monitor("op2", module="module_a"):
            sleep(0.02)
        
        with monitor.monitor("op3", module="module_b"):
            sleep(0.01)
        
        module_a_perf = monitor.get_module_performance("module_a")
        assert module_a_perf is not None
        assert module_a_perf.total_operations == 2
        
        module_b_perf = monitor.get_module_performance("module_b")
        assert module_b_perf is not None
        assert module_b_perf.total_operations == 1
    
    def test_reset(self):
        """Test: Resetear monitor"""
        monitor = PerformanceMonitor(enable_timing=True)
        
        with monitor.monitor("test"):
            pass
        
        assert len(monitor._metrics) > 0
        
        monitor.reset()
        assert len(monitor._metrics) == 0
        assert len(monitor._module_metrics) == 0
    
    def test_export_report(self, tmp_path):
        """Test: Exportar reporte"""
        monitor = PerformanceMonitor(enable_timing=True)
        
        with monitor.monitor("test_op"):
            sleep(0.01)
        
        output_path = tmp_path / "report.json"
        monitor.generate_report(output_path)
        
        assert output_path.exists()
        assert output_path.stat().st_size > 0
        
        # Verificar contenido
        import json
        report = json.loads(output_path.read_text())
        assert "summary" in report
        assert "operations" in report

class TestIntegration:
    """Tests de integración entre componentes"""
    
    def test_timer_and_profiler_together(self):
        """Test: Usar timer y profiler juntos"""
        timer = ExecutionTimer()
        profiler = MemoryProfiler(enabled=True)
        
        with timer.time("combined_op"):
            with profiler.profile("combined_op"):
                large_list = [i for i in range(100000)]
                sleep(0.05)
        
        timing_stats = timer.get_stats("combined_op")
        memory_diffs = profiler.get_diffs("combined_op")
        
        assert timing_stats is not None
        assert len(memory_diffs) > 0
    
    def test_monitor_with_real_operations(self):
        """Test: Monitor con operaciones reales del sistema"""
        from app.core.parser import parse_pseudocode
        
        monitor = PerformanceMonitor(enable_timing=True, enable_memory=True)
        
        code = """
algorithm test(n)
begin
    for i ← 1 to n do
    begin
        x ← x + 1
    end
end
        """
        
        with monitor.monitor("parse_code", module="parser") as metrics:
            ast = parse_pseudocode(code)
        
        assert metrics.operation == "parse_code"
        assert metrics.module == "parser"
        assert metrics.execution_time_ms > 0
        assert ast is not None

class TestSingletonPatterns:
    """Tests para patrones singleton"""
    
    def test_get_timer_singleton(self):
        """Test: get_timer retorna misma instancia"""
        timer1 = get_timer()
        timer2 = get_timer()
        
        assert timer1 is timer2
    
    def test_get_memory_profiler_singleton(self):
        """Test: get_memory_profiler retorna misma instancia"""
        profiler1 = get_memory_profiler()
        profiler2 = get_memory_profiler()
        
        assert profiler1 is profiler2
    
    def test_get_performance_monitor_singleton(self):
        """Test: get_performance_monitor retorna misma instancia"""
        monitor1 = get_performance_monitor()
        monitor2 = get_performance_monitor()
        
        assert monitor1 is monitor2

if __name__ == "__main__":
    pytest.main([__file__, "-v"])