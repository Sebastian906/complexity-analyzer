#!/usr/bin/env python3
"""
Demo de Métricas y Monitoring para Visualizaciones
Muestra las capacidades del sistema de métricas, alertas y monitoring
"""
import sys
from pathlib import Path

# Add backend directory to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio
from datetime import datetime
import time
import random

from app.core.visualization.metrics_collector import (
    MetricsCollector,
    MetricsContext,
    AlertThresholds,
    AlertSeverity,
    MetricType
)
from app.core.visualization.batch_exporter import (
    BatchExporter,
    ExportTask,
    ExportFormat,
    ProcessingMode,
    BatchExportConfig
)
from app.core.visualization.optimizer import (
    VisualizationOptimizer,
    OptimizationConfig,
    OptimizationLevel
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


# === Configuración ===

OUTPUT_DIR = Path("data/exports/metrics_demo")
REPORTS_DIR = Path("data/exports/reports")


# === Demo 1: Tracking Básico de Métricas ===

async def demo_basic_tracking():
    """
    Demuestra el tracking básico de métricas de exportación
    """
    print("DEMO 1: Tracking Básico de Métricas")
    
    # Crear colector de métricas
    collector = MetricsCollector()
    
    # Iniciar un batch
    collector.start_batch("demo-basic-batch", total_tasks=5)
    
    # Simular exportaciones
    visualizations = [
        ("viz-001", "recursion_tree", "svg", 25, 24),
        ("viz-002", "graph", "png", 50, 75),
        ("viz-003", "execution_flow", "dot", 30, 35),
        ("viz-004", "recursion_tree", "mermaid", 15, 14),
        ("viz-005", "graph", "json", 40, 60),
    ]
    
    for task_id, viz_type, fmt, nodes, edges in visualizations:
        # Iniciar tracking
        metrics = collector.start_export(
            task_id=task_id,
            visualization_type=viz_type,
            export_format=fmt,
            node_count=nodes,
            edge_count=edges
        )
        
        # Simular trabajo de exportación
        await asyncio.sleep(random.uniform(0.1, 0.3))
        
        # Simular optimización ocasional
        if nodes > 30:
            collector.track_optimization(metrics, random.uniform(10, 50))
        
        # Finalizar tracking
        collector.end_export(
            metrics,
            success=random.random() > 0.1  # 90% éxito
        )
    
    # Finalizar batch
    batch_result = collector.end_batch()
    
    # Mostrar estadísticas
    stats = collector.get_statistics()
    
    print("\n Estadísticas del Batch:")
    print(f"   Total exportaciones: {stats['total_exports']}")
    print(f"   Tiempo promedio: {stats['processing_time']['avg_ms']:.2f}ms")
    print(f"   Tiempo total: {stats['processing_time']['total_ms']:.2f}ms")
    print(f"   Throughput: {batch_result.throughput_tasks_per_sec:.2f} tareas/seg")
    
    return collector


# === Demo 2: Sistema de Alertas ===

async def demo_alert_system():
    """
    Demuestra el sistema de alertas con diferentes umbrales
    """
    print("DEMO 2: Sistema de Alertas")
    
    # Configurar umbrales personalizados (bajos para demo)
    thresholds = AlertThresholds(
        export_time_warning_ms=200.0,
        export_time_critical_ms=500.0,
        memory_warning_mb=50.0,
        memory_critical_mb=100.0,
        node_count_warning=100,
        node_count_critical=500,
        edge_count_warning=200,
        edge_count_critical=1000,
        failure_rate_warning=10.0,
        failure_rate_critical=25.0
    )
    
    # Callback para recibir alertas en tiempo real
    alerts_received = []
    
    def alert_callback(alert):
        severity_icon = {
            AlertSeverity.INFO: "INFO",
            AlertSeverity.WARNING: "WARNING",
            AlertSeverity.CRITICAL: "CRITICAL"
        }
        icon = severity_icon.get(alert.severity, "UNKNOWN")
        print(f"   {icon} ALERTA RECIBIDA: {alert.message}")
        alerts_received.append(alert)
    
    collector = MetricsCollector(
        thresholds=thresholds,
        alert_callback=alert_callback
    )
    
    print("\n Umbrales configurados:")
    print(f"   Nodos - Warning: {thresholds.node_count_warning}, Critical: {thresholds.node_count_critical}")
    print(f"   Aristas - Warning: {thresholds.edge_count_warning}, Critical: {thresholds.edge_count_critical}")
    print(f"   Tiempo - Warning: {thresholds.export_time_warning_ms}ms, Critical: {thresholds.export_time_critical_ms}ms")
    
    collector.start_batch("demo-alerts-batch", total_tasks=4)
    
    print("\n Ejecutando exportaciones que dispararán alertas:")
    
    # Exportación normal (sin alertas)
    print("\n   1 Exportación normal (50 nodos)...")
    m1 = collector.start_export("normal", "graph", "svg", node_count=50, edge_count=80)
    await asyncio.sleep(0.05)
    collector.end_export(m1, success=True)
    
    # Exportación con warning de nodos
    print("\n   2 Exportación con grafo grande (150 nodos)...")
    m2 = collector.start_export("large", "graph", "svg", node_count=150, edge_count=200)
    await asyncio.sleep(0.1)
    collector.end_export(m2, success=True)
    
    # Exportación con alerta crítica de nodos
    print("\n   3 Exportación con grafo muy grande (600 nodos)...")
    m3 = collector.start_export("huge", "graph", "svg", node_count=600, edge_count=800)
    await asyncio.sleep(0.2)
    collector.end_export(m3, success=True)
    
    # Exportación con muchas aristas
    print("\n   4 Exportación con muchas aristas (1500)...")
    m4 = collector.start_export("dense", "graph", "svg", node_count=100, edge_count=1500)
    await asyncio.sleep(0.15)
    collector.end_export(m4, success=True)
    
    collector.end_batch()
    
    # Resumen de alertas
    print("RESUMEN DE ALERTAS:")
    
    all_alerts = collector.get_alerts()
    warnings = collector.get_alerts(AlertSeverity.WARNING)
    criticals = collector.get_alerts(AlertSeverity.CRITICAL)
    
    print(f"   Total: {len(all_alerts)}")
    print(f"   Warnings: {len(warnings)}")
    print(f"   Críticas: {len(criticals)}")
    
    # Resolver una alerta
    if all_alerts:
        alert_to_resolve = all_alerts[0]
        print(f"\n   Resolviendo alerta: {alert_to_resolve.id}")
        collector.resolve_alert(alert_to_resolve.id)
        
        unresolved = collector.get_alerts(unresolved_only=True)
        print(f"   Alertas sin resolver: {len(unresolved)}")
    
    return collector

# === Demo 3: Context Manager para Tracking ===

async def demo_context_manager():
    """
    Demuestra el uso del context manager MetricsContext
    """
    print("DEMO 3: Context Manager para Tracking")
    
    collector = MetricsCollector()
    collector.start_batch("demo-context-batch", total_tasks=3)
    
    print("\nUsando MetricsContext para tracking automático:")
    
    # Exportación exitosa con context manager
    print("\n   1 Exportación exitosa con context manager...")
    with MetricsContext(
        collector,
        task_id="ctx-success",
        visualization_type="recursion_tree",
        export_format="svg",
        node_count=30,
        edge_count=29
    ) as metrics:
        # Simular trabajo
        await asyncio.sleep(0.1)
        print(f"      Procesando {metrics.node_count} nodos...")
    print("       Completado automáticamente")
    
    # Exportación con error capturado
    print("\n   2 Exportación con error (capturado por context)...")
    try:
        with MetricsContext(
            collector,
            task_id="ctx-error",
            visualization_type="graph",
            export_format="png",
            node_count=50
        ) as metrics:
            await asyncio.sleep(0.05)
            raise ValueError("Error simulado de renderizado")
    except ValueError:
        print("      Error capturado y registrado automáticamente")
    
    # Exportación con optimización
    print("\n   3 Exportación con optimización manual...")
    with MetricsContext(
        collector,
        task_id="ctx-optimized",
        visualization_type="graph",
        export_format="svg",
        node_count=100,
        edge_count=200
    ) as metrics:
        # Registrar optimización
        collector.track_optimization(metrics, 75.5)
        await asyncio.sleep(0.08)
    print("       Completado con optimización registrada")
    
    batch = collector.end_batch()
    
    print("\nResultados del batch:")
    print(f"   Exitosas: {batch.successful_tasks}")
    print(f"   Fallidas: {batch.failed_tasks}")
    print(f"   Con optimización: {sum(1 for m in batch.export_metrics if m.optimization_applied)}")
    
    return collector


# === Demo 4: Generación de Reportes ===

async def demo_reporting():
    """
    Demuestra la generación de reportes detallados
    """
    print("DEMO 4: Generación de Reportes")
    
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Configurar umbrales bajos para generar alertas
    thresholds = AlertThresholds(
        node_count_warning=20,
        node_count_critical=50
    )
    
    collector = MetricsCollector(thresholds=thresholds)
    
    # Ejecutar múltiples batches
    for batch_num in range(2):
        batch_id = f"report-batch-{batch_num + 1}"
        print(f"\nEjecutando {batch_id}...")
        
        collector.start_batch(batch_id, total_tasks=5)
        
        for i in range(5):
            # Variar tamaño de grafos para generar alertas
            node_count = random.choice([10, 25, 40, 60, 100])
            
            metrics = collector.start_export(
                task_id=f"{batch_id}-task-{i}",
                visualization_type=random.choice(["graph", "recursion_tree", "flow"]),
                export_format=random.choice(["svg", "png", "dot"]),
                node_count=node_count,
                edge_count=node_count * 2
            )
            
            await asyncio.sleep(random.uniform(0.02, 0.1))
            
            collector.end_export(
                metrics,
                success=random.random() > 0.15  # 85% éxito
            )
        
        collector.end_batch()
    
    # Generar reporte completo
    full_report_path = REPORTS_DIR / f"full_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    collector.export_report(full_report_path, include_raw_metrics=True)
    print(f"\nReporte completo guardado en: {full_report_path}")
    
    # Generar reporte compacto
    compact_report_path = REPORTS_DIR / f"compact_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    collector.export_report(compact_report_path, include_raw_metrics=False)
    print(f"Reporte compacto guardado en: {compact_report_path}")
    
    # Mostrar estadísticas finales
    stats = collector.get_statistics()
    
    print("\nEstadísticas Globales:")
    print(f"   Total exportaciones: {stats['total_exports']}")
    print(f"   Total batches: {stats['total_batches']}")
    print(f"   Tiempo promedio: {stats['processing_time']['avg_ms']:.2f}ms")
    print(f"   Alertas totales: {stats['alerts']['total']}")
    print(f"   - Críticas: {stats['alerts']['critical']}")
    print(f"   - Warnings: {stats['alerts']['warning']}")
    
    # Mostrar historial de batches
    print("\n Historial de Batches:")
    for batch in collector.get_batch_history():
        success_rate = batch.successful_tasks / max(batch.total_tasks, 1) * 100
        print(f"   {batch.batch_id}: {batch.successful_tasks}/{batch.total_tasks} ({success_rate:.0f}%)")
    
    return collector

# === Demo 5: Integración con BatchExporter ===

async def demo_integration_with_exporter():
    """
    Demuestra la integración del MetricsCollector con BatchExporter
    """
    print("DEMO 5: Integración con BatchExporter")
    
    # Crear colector y exportador
    thresholds = AlertThresholds(
        node_count_warning=100,
        export_time_warning_ms=1000
    )
    collector = MetricsCollector(thresholds=thresholds)
    
    exporter = BatchExporter(
        BatchExportConfig(
            mode=ProcessingMode.SEQUENTIAL,
            max_workers=2
        )
    )
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Preparar tareas de exportación
    print("\n Preparando tareas de exportación...")
    
    tasks_data = [
        {"id": "fib", "type": "recursion_tree", "nodes": 31, "edges": 30},
        {"id": "qs", "type": "recursion_tree", "nodes": 63, "edges": 62},
        {"id": "binary", "type": "recursion_tree", "nodes": 15, "edges": 14},
        {"id": "dp", "type": "graph", "nodes": 50, "edges": 100},
    ]
    
    # Iniciar batch en el colector
    collector.start_batch("integrated-batch", len(tasks_data))
    
    print("\n Ejecutando exportaciones con métricas...")
    
    for task_data in tasks_data:
        # Tracking con métricas
        with MetricsContext(
            collector,
            task_id=task_data["id"],
            visualization_type=task_data["type"],
            export_format="svg",
            node_count=task_data["nodes"],
            edge_count=task_data["edges"]
        ) as metrics:
            # Simular exportación
            await asyncio.sleep(random.uniform(0.05, 0.15))
            
            # Simular optimización para grafos grandes
            if task_data["nodes"] > 50:
                collector.track_optimization(metrics, random.uniform(20, 80))
            
            print(f"    {task_data['id']}: {task_data['nodes']} nodos procesados")
    
    batch = collector.end_batch()
    
    # Mostrar resultados
    print("\n Resultados de la Integración:")
    print(f"   Tareas completadas: {batch.completed_tasks}")
    print(f"   Throughput: {batch.throughput_tasks_per_sec:.2f} tareas/seg")
    print(f"   Tiempo total: {batch.total_processing_time_ms:.2f}ms")
    print(f"   Alertas: {len(batch.alerts_triggered)}")
    
    # Exportar reporte final
    report_path = REPORTS_DIR / "integration_report.json"
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    collector.export_report(report_path)
    print(f"\n Reporte guardado en: {report_path}")
    
    return collector

# === Demo 6: Monitoreo de Memoria ===

async def demo_memory_monitoring():
    """
    Demuestra el monitoreo de uso de memoria
    """
    print("DEMO 6: Monitoreo de Memoria")
    
    # Configurar umbrales de memoria bajos para demo
    thresholds = AlertThresholds(
        memory_warning_mb=0.5,  # 0.5 MB
        memory_critical_mb=2.0  # 2 MB
    )
    
    collector = MetricsCollector(thresholds=thresholds)
    collector.start_batch("memory-demo-batch", total_tasks=3)
    
    print("\n Ejecutando exportaciones con diferentes cargas de memoria:")
    
    # Exportación ligera
    print("\n   1 Exportación ligera...")
    m1 = collector.start_export("light", "graph", "svg", node_count=10)
    # Crear datos pequeños
    small_data = [i for i in range(100)]
    await asyncio.sleep(0.05)
    collector.end_export(m1, success=True)
    del small_data
    
    print(f"      Memoria delta: {m1.memory_delta_bytes / 1024:.2f} KB")
    
    # Exportación media
    print("\n   2 Exportación media...")
    m2 = collector.start_export("medium", "graph", "svg", node_count=100)
    # Crear datos medianos
    medium_data = [{"id": i, "data": "x" * 100} for i in range(1000)]
    await asyncio.sleep(0.1)
    collector.end_export(m2, success=True)
    del medium_data
    
    print(f"      Memoria delta: {m2.memory_delta_bytes / 1024:.2f} KB")
    
    # Exportación pesada
    print("\n   3 Exportación pesada...")
    m3 = collector.start_export("heavy", "graph", "svg", node_count=500)
    # Crear datos grandes
    large_data = [{"id": i, "data": "x" * 1000} for i in range(5000)]
    await asyncio.sleep(0.15)
    collector.end_export(m3, success=True)
    del large_data
    
    print(f"      Memoria delta: {m3.memory_delta_bytes / 1024:.2f} KB")
    
    batch = collector.end_batch()
    
    # Resumen de memoria
    print("\nResumen de Uso de Memoria:")
    print(f"   Memoria pico: {batch.peak_memory_bytes / (1024 * 1024):.2f} MB")
    print(f"   Memoria total usada: {batch.total_memory_used_bytes / 1024:.2f} KB")
    
    # Alertas de memoria
    memory_alerts = [
        a for a in collector.get_alerts()
        if a.metric_type == MetricType.MEMORY_USAGE
    ]
    
    if memory_alerts:
        print(f"\n Alertas de memoria: {len(memory_alerts)}")
        for alert in memory_alerts:
            print(f"   - {alert.severity.value}: {alert.message}")
    else:
        print("\n Sin alertas de memoria")
    
    return collector

# === Demo 7: Comparación de Rendimiento ===

async def demo_performance_comparison():
    """
    Compara rendimiento entre diferentes configuraciones
    """
    print("DEMO 7: Comparación de Rendimiento")
    
    results = {}
    
    # Configuraciones a comparar
    configs = [
        ("Sin optimización", OptimizationLevel.NONE),
        ("Optimización básica", OptimizationLevel.BASIC),
        ("Optimización moderada", OptimizationLevel.MODERATE),
        ("Optimización agresiva", OptimizationLevel.AGGRESSIVE),
    ]
    
    for config_name, opt_level in configs:
        print(f"\n Probando: {config_name}...")
        
        collector = MetricsCollector()
        optimizer = VisualizationOptimizer(
            OptimizationConfig(level=opt_level)
        )
        
        collector.start_batch(f"perf-{opt_level.value}", total_tasks=10)
        
        total_opt_time = 0
        
        for i in range(10):
            # Simular grafo
            nodes = [{"id": f"n{j}", "label": f"Node {j}"} for j in range(100)]
            edges = [(f"n{j}", f"n{j+1}", {}) for j in range(99)]
            
            metrics = collector.start_export(
                f"perf-{i}",
                "graph",
                "svg",
                node_count=len(nodes),
                edge_count=len(edges)
            )
            
            # Aplicar optimización
            start = time.time()
            opt_nodes, opt_edges, _ = optimizer.optimize_graph(nodes, edges)
            opt_time = (time.time() - start) * 1000
            total_opt_time += opt_time
            
            collector.track_optimization(metrics, opt_time)
            
            # Simular renderizado
            await asyncio.sleep(0.02)
            
            collector.end_export(metrics, success=True)
        
        batch = collector.end_batch()
        
        results[config_name] = {
            'avg_time': batch.avg_processing_time_ms,
            'avg_opt_time': total_opt_time / 10,
            'throughput': batch.throughput_tasks_per_sec
        }
    
    # Mostrar comparación
    print("COMPARACIÓN DE RENDIMIENTO:")
    print(f"{'Configuración':<25} {'Tiempo Prom.':<15} {'Opt. Prom.':<15} {'Throughput':<12}")
    
    for config_name, data in results.items():
        print(
            f"{config_name:<25} "
            f"{data['avg_time']:>10.2f}ms   "
            f"{data['avg_opt_time']:>10.2f}ms   "
            f"{data['throughput']:>8.2f}/s"
        )
    
    return results

# === Main ===

async def run_all_demos():
    """Ejecuta todas las demos"""
    print("DEMOS DE MÉTRICAS Y MONITORING PARA VISUALIZACIONES")
    print(f"   Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        await demo_basic_tracking()
        await demo_alert_system()
        await demo_context_manager()
        await demo_reporting()
        await demo_integration_with_exporter()
        await demo_memory_monitoring()
        await demo_performance_comparison()
        
        print("TODAS LAS DEMOS COMPLETADAS EXITOSAMENTE")
        
    except Exception as e:
        print(f"\n Error durante las demos: {e}")
        import traceback
        traceback.print_exc()
        raise


def run_single_demo(demo_name: str):
    """Ejecuta una demo específica"""
    demos = {
        "basic": demo_basic_tracking,
        "alerts": demo_alert_system,
        "context": demo_context_manager,
        "reports": demo_reporting,
        "integration": demo_integration_with_exporter,
        "memory": demo_memory_monitoring,
        "performance": demo_performance_comparison,
    }
    
    if demo_name not in demos:
        print(f"Demo no encontrada: {demo_name}")
        print(f"Demos disponibles: {', '.join(demos.keys())}")
        return
    
    asyncio.run(demos[demo_name]())


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        demo_name = sys.argv[1].lower()
        run_single_demo(demo_name)
    else:
        asyncio.run(run_all_demos())
