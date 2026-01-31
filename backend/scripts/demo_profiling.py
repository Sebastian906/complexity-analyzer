"""
Demo: Módulo de Profiling

Demuestra el uso del módulo de profiling para medir performance
de las operaciones principales del sistema.
"""

import sys
from pathlib import Path
from time import sleep

# Agregar directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from app.profiling import (
    get_performance_monitor,
    timed,
    time_block,
    profile_memory,
    enable_profiling,
    print_profiling_summary,
    generate_profiling_report,
)

from app.core.parser import parse_pseudocode
from app.core.analyzer import AnalyzerEngine
from app.core.patterns import PatternDetector

def demo_basic_timing():
    """Demo 1: Timing básico con decoradores"""
    print("DEMO 1: TIMING BÁSICO")
    
    @timed()
    def slow_function():
        """Función de ejemplo lenta"""
        sleep(0.5)
        return sum(range(1000000))
    
    @timed(name="fast_operation")
    def fast_function():
        """Función de ejemplo rápida"""
        return sum(range(100))
    
    # Ejecutar funciones
    result1 = slow_function()
    result2 = fast_function()
    
    print(f"Resultados: {result1}, {result2}")

def demo_context_manager():
    """Demo 2: Context managers para timing"""
    print("DEMO 2: CONTEXT MANAGERS")
    
    # Timing básico
    with time_block("process_data"):
        data = [i**2 for i in range(100000)]
        total = sum(data)
    
    # Memory profiling
    with profile_memory("allocate_large_list"):
        large_list = [i for i in range(1000000)]
        result = len(large_list)
    
    print(f"Procesado completado: {result} elementos")


def demo_performance_monitor():
    """Demo 3: Monitor de performance integral"""
    print("DEMO 3: PERFORMANCE MONITOR")
    
    # Crear monitor con memory profiling
    monitor = get_performance_monitor(enable_memory=True)
    
    # Ejemplo con parsing
    code = """
algorithm bubbleSort(A[1..n])
begin
    for i ← 1 to n-1 do
    begin
        for j ← 1 to n-i do
        begin
            if (A[j] > A[j+1]) then
            begin
                temp ← A[j]
                A[j] ← A[j+1]
                A[j+1] ← temp
            end
        end
    end
end
    """
    
    with monitor.monitor("parse_algorithm", module="parser") as metrics:
        ast = parse_pseudocode(code)
    
    print(f"Parsing: {metrics.execution_time_ms:.2f}ms")
    print(f"Memoria: {metrics.memory_delta_mb:.2f}MB")
    print(f"Nivel: {metrics.performance_level.value}")
    
    # Ejemplo con análisis
    with monitor.monitor("analyze_complexity", module="analyzer") as metrics:
        analyzer = AnalyzerEngine()
        result = analyzer.analyze(ast, analyze_line_by_line=False)
    
    print(f"Análisis: {metrics.execution_time_ms:.2f}ms")
    print(f"Big O: {result.big_o}")
    
    # Ejemplo con patrones
    with monitor.monitor("detect_patterns", module="patterns") as metrics:
        detector = PatternDetector()
        patterns = detector.detect(ast, min_confidence=0.3)
    
    print(f"Detección: {metrics.execution_time_ms:.2f}ms")
    print(f"Patrón: {patterns.primary_pattern_name}")

def demo_module_profiling():
    """Demo 4: Profiling por módulo"""
    print("DEMO 4: PROFILING POR MÓDULO")
    
    # Habilitar profiling global
    enable_profiling(enable_timing=True, enable_memory=True)
    
    monitor = get_performance_monitor()
    
    # Algoritmo simple
    simple_code = """
algorithm simple(n)
begin
    x ← 1
    for i ← 1 to n do
    begin
        x ← x + 1
    end
end
    """
    
    # Procesar con todos los módulos
    with monitor.monitor("full_analysis", module="orchestrator"):
        # Parse
        with monitor.monitor("parse", module="parser"):
            ast = parse_pseudocode(simple_code)
        
        # Analyze
        with monitor.monitor("analyze", module="analyzer"):
            analyzer = AnalyzerEngine()
            analysis = analyzer.analyze(ast, analyze_line_by_line=False)
        
        # Patterns
        with monitor.monitor("patterns", module="patterns"):
            detector = PatternDetector()
            patterns = detector.detect(ast)
    
    # Mostrar performance por módulo
    for module_name in ["parser", "analyzer", "patterns"]:
        module_perf = monitor.get_module_performance(module_name)
        if module_perf:
            print(f"\n{module_name.upper()}:")
            print(f"  Operaciones: {module_perf.total_operations}")
            print(f"  Tiempo promedio: {module_perf.avg_execution_time_ms:.2f}ms")
            print(f"  Memoria promedio: {module_perf.avg_memory_delta_mb:.2f}MB")

def demo_detect_slow_operations():
    """Demo 5: Detectar operaciones lentas"""
    print("DEMO 5: DETECTAR OPERACIONES LENTAS")
    
    monitor = get_performance_monitor()
    
    # Simular varias operaciones
    @monitor.monitored(module="test")
    def operation_1():
        sleep(0.1)
    
    @monitor.monitored(module="test")
    def operation_2():
        sleep(0.5)
    
    @monitor.monitored(module="test")
    def operation_3():
        sleep(1.0)
    
    # Ejecutar operaciones
    operation_1()
    operation_2()
    operation_3()
    
    # Detectar operaciones lentas
    slow_ops = monitor.get_slow_operations(threshold_ms=400)
    
    print(f"Operaciones lentas (>400ms): {len(slow_ops)}")
    for op in slow_ops:
        print(f"  - {op.operation}: {op.execution_time_ms:.2f}ms ({op.performance_level.value})")


def demo_export_report():
    """Demo 6: Exportar reporte"""
    print("DEMO 6: EXPORTAR REPORTE")    
    # Ejecutar varias operaciones para generar datos
    monitor = get_performance_monitor()
    
    code = """
algorithm test(n)
begin
    for i ← 1 to n do
    begin
        x ← x + 1
    end
end
    """
    
    # Procesar varias veces
    for i in range(3):
        with monitor.monitor(f"run_{i+1}", module="demo"):
            ast = parse_pseudocode(code)
            sleep(0.1 * (i + 1))
    
    # Generar reporte
    output_path = Path("data/exports/profiling_demo_report.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    generate_profiling_report(output_path)
    
    print(f"Reporte generado: {output_path}")
    print(f"Tamaño: {output_path.stat().st_size} bytes")


def main():
    """Función principal"""
    print("DEMO: MÓDULO DE PROFILING")    
    try:
        # Ejecutar demos
        demo_basic_timing()
        demo_context_manager()
        demo_performance_monitor()
        demo_module_profiling()
        demo_detect_slow_operations()
        demo_export_report()
        
        # Mostrar resumen final
        print("RESUMEN FINAL DE PROFILING")

        print_profiling_summary()
        
        print("\nDemo completado exitosamente")
        
    except Exception as e:
        print(f"\nError durante demo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()