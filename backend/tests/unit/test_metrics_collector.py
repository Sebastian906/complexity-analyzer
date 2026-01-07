"""
Tests Unitarios - Módulo de Métricas y Monitoring

Tests para validar el sistema de métricas, alertas y monitoring
para exportación de visualizaciones.
"""

import pytest
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
import tempfile
import json

from app.core.visualization.metrics_collector import (
    MetricsCollector,
    MetricsContext,
    ExportMetrics,
    BatchMetrics,
    Alert,
    AlertThresholds,
    AlertSeverity,
    MetricType,
    track_export
)


# === Fixtures ===

@pytest.fixture
def collector():
    """Crea un colector de métricas con umbrales por defecto"""
    return MetricsCollector()


@pytest.fixture
def custom_thresholds():
    """Umbrales personalizados para tests"""
    return AlertThresholds(
        export_time_warning_ms=100.0,
        export_time_critical_ms=500.0,
        memory_warning_mb=10.0,
        memory_critical_mb=50.0,
        node_count_warning=50,
        node_count_critical=100,
        edge_count_warning=100,
        edge_count_critical=200,
        file_size_warning_mb=1.0,
        file_size_critical_mb=5.0,
        failure_rate_warning=5.0,
        failure_rate_critical=10.0
    )


@pytest.fixture
def collector_with_thresholds(custom_thresholds):
    """Colector con umbrales personalizados"""
    return MetricsCollector(thresholds=custom_thresholds)


@pytest.fixture
def temp_output_dir():
    """Directorio temporal para outputs"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


# === Tests de ExportMetrics ===

class TestExportMetrics:
    """Tests para la clase ExportMetrics"""
    
    def test_create_export_metrics(self):
        """Test creación de métricas de exportación"""
        metrics = ExportMetrics(
            task_id="test-001",
            visualization_type="recursion_tree",
            export_format="svg",
            start_time=datetime.now()
        )
        
        assert metrics.task_id == "test-001"
        assert metrics.visualization_type == "recursion_tree"
        assert metrics.export_format == "svg"
        assert metrics.success is True
        assert metrics.error is None
    
    def test_export_metrics_to_dict(self):
        """Test conversión a diccionario"""
        start = datetime.now()
        end = start + timedelta(milliseconds=500)
        
        metrics = ExportMetrics(
            task_id="test-002",
            visualization_type="graph",
            export_format="png",
            start_time=start,
            end_time=end,
            processing_time_ms=500.0,
            memory_before_bytes=1024,
            memory_after_bytes=2048,
            memory_delta_bytes=1024,
            node_count=100,
            edge_count=200,
            file_size_bytes=5120
        )
        
        result = metrics.to_dict()
        
        assert result['task_id'] == "test-002"
        assert result['visualization_type'] == "graph"
        assert result['processing_time_ms'] == 500.0
        assert result['memory']['delta_bytes'] == 1024
        assert result['graph']['node_count'] == 100
        assert result['file_size_kb'] == 5.0


# === Tests de BatchMetrics ===

class TestBatchMetrics:
    """Tests para la clase BatchMetrics"""
    
    def test_create_batch_metrics(self):
        """Test creación de métricas de batch"""
        batch = BatchMetrics(
            batch_id="batch-001",
            start_time=datetime.now(),
            total_tasks=10
        )
        
        assert batch.batch_id == "batch-001"
        assert batch.total_tasks == 10
        assert batch.completed_tasks == 0
        assert batch.successful_tasks == 0
        assert batch.failed_tasks == 0
    
    def test_batch_metrics_to_dict(self):
        """Test conversión a diccionario"""
        start = datetime.now()
        end = start + timedelta(seconds=10)
        
        batch = BatchMetrics(
            batch_id="batch-002",
            start_time=start,
            end_time=end,
            total_tasks=10,
            completed_tasks=10,
            successful_tasks=8,
            failed_tasks=2,
            throughput_tasks_per_sec=1.0
        )
        
        result = batch.to_dict()
        
        assert result['batch_id'] == "batch-002"
        assert result['tasks']['total'] == 10
        assert result['tasks']['success_rate'] == 80.0
        assert result['timing']['throughput_tasks_per_sec'] == 1.0


# === Tests de Alert ===

class TestAlert:
    """Tests para la clase Alert"""
    
    def test_create_alert(self):
        """Test creación de alerta"""
        alert = Alert(
            id="ALERT-0001",
            severity=AlertSeverity.WARNING,
            message="Test alert",
            metric_type=MetricType.EXPORT_TIME,
            value=6000.0,
            threshold=5000.0,
            task_id="task-001"
        )
        
        assert alert.id == "ALERT-0001"
        assert alert.severity == AlertSeverity.WARNING
        assert alert.resolved is False
    
    def test_alert_to_dict(self):
        """Test conversión a diccionario"""
        alert = Alert(
            id="ALERT-0002",
            severity=AlertSeverity.CRITICAL,
            message="Critical alert",
            metric_type=MetricType.MEMORY_USAGE,
            value=600.0,
            threshold=512.0
        )
        
        result = alert.to_dict()
        
        assert result['severity'] == "critical"
        assert result['metric_type'] == "memory_usage"
        assert result['resolved'] is False


# === Tests de MetricsCollector ===

class TestMetricsCollector:
    """Tests para el colector de métricas"""
    
    def test_initialization(self, collector):
        """Test inicialización del colector"""
        assert collector.thresholds is not None
        assert collector._current_batch is None
        assert len(collector._alerts) == 0
    
    def test_start_batch(self, collector):
        """Test inicio de batch"""
        batch = collector.start_batch("batch-test", 5)
        
        assert batch.batch_id == "batch-test"
        assert batch.total_tasks == 5
        assert collector._current_batch is batch
    
    def test_end_batch(self, collector):
        """Test finalización de batch"""
        collector.start_batch("batch-test", 3)
        
        # Simular algunas exportaciones
        for i in range(3):
            metrics = collector.start_export(
                f"task-{i}",
                "graph",
                "svg"
            )
            collector.end_export(metrics, success=True)
        
        batch = collector.end_batch()
        
        assert batch is not None
        assert batch.completed_tasks == 3
        assert batch.successful_tasks == 3
        assert collector._current_batch is None
    
    def test_start_export(self, collector):
        """Test inicio de tracking de exportación"""
        metrics = collector.start_export(
            task_id="export-001",
            visualization_type="recursion_tree",
            export_format="svg",
            node_count=50,
            edge_count=75
        )
        
        assert metrics.task_id == "export-001"
        assert metrics.visualization_type == "recursion_tree"
        assert metrics.node_count == 50
        assert metrics.edge_count == 75
    
    def test_end_export_success(self, collector):
        """Test finalización exitosa de exportación"""
        metrics = collector.start_export(
            task_id="export-002",
            visualization_type="graph",
            export_format="png"
        )
        
        result = collector.end_export(metrics, success=True)
        
        assert result.success is True
        assert result.error is None
        assert result.processing_time_ms > 0
    
    def test_end_export_failure(self, collector):
        """Test finalización con error de exportación"""
        metrics = collector.start_export(
            task_id="export-003",
            visualization_type="flow",
            export_format="dot"
        )
        
        result = collector.end_export(
            metrics,
            success=False,
            error="Render failed"
        )
        
        assert result.success is False
        assert result.error == "Render failed"
    
    def test_track_optimization(self, collector):
        """Test registro de optimización"""
        metrics = collector.start_export(
            task_id="export-004",
            visualization_type="graph",
            export_format="svg"
        )
        
        collector.track_optimization(metrics, 150.5)
        
        assert metrics.optimization_applied is True
        assert metrics.optimization_time_ms == 150.5
    
    def test_export_in_batch_updates_batch(self, collector):
        """Test que exportaciones actualizan el batch"""
        collector.start_batch("batch-update", 2)
        
        metrics1 = collector.start_export("task-1", "graph", "svg")
        collector.end_export(metrics1, success=True)
        
        metrics2 = collector.start_export("task-2", "graph", "png")
        collector.end_export(metrics2, success=False, error="Failed")
        
        batch = collector.end_batch()
        
        assert batch.completed_tasks == 2
        assert batch.successful_tasks == 1
        assert batch.failed_tasks == 1


# === Tests de Alertas ===

class TestAlertSystem:
    """Tests para el sistema de alertas"""
    
    def test_graph_size_warning_alert(self, collector_with_thresholds):
        """Test alerta de warning por tamaño de grafo"""
        # Umbral de warning: 50 nodos
        collector_with_thresholds.start_export(
            task_id="large-graph",
            visualization_type="graph",
            export_format="svg",
            node_count=75,  # > 50
            edge_count=50
        )
        
        alerts = collector_with_thresholds.get_alerts(AlertSeverity.WARNING)
        
        assert len(alerts) >= 1
        assert any("nodos" in a.message for a in alerts)
    
    def test_graph_size_critical_alert(self, collector_with_thresholds):
        """Test alerta crítica por tamaño de grafo"""
        # Umbral crítico: 100 nodos
        collector_with_thresholds.start_export(
            task_id="huge-graph",
            visualization_type="graph",
            export_format="svg",
            node_count=150,  # > 100
            edge_count=50
        )
        
        alerts = collector_with_thresholds.get_alerts(AlertSeverity.CRITICAL)
        
        assert len(alerts) >= 1
        assert any("nodos" in a.message for a in alerts)
    
    def test_edge_count_alert(self, collector_with_thresholds):
        """Test alerta por cantidad de aristas"""
        collector_with_thresholds.start_export(
            task_id="dense-graph",
            visualization_type="graph",
            export_format="svg",
            node_count=20,
            edge_count=250  # > 200 crítico
        )
        
        alerts = collector_with_thresholds.get_alerts(AlertSeverity.CRITICAL)
        
        assert len(alerts) >= 1
        assert any("aristas" in a.message for a in alerts)
    
    def test_alert_callback(self):
        """Test callback de alertas"""
        callback_calls = []
        
        def alert_callback(alert):
            callback_calls.append(alert)
        
        thresholds = AlertThresholds(node_count_warning=10)
        collector = MetricsCollector(
            thresholds=thresholds,
            alert_callback=alert_callback
        )
        
        collector.start_export(
            task_id="callback-test",
            visualization_type="graph",
            export_format="svg",
            node_count=20  # > 10
        )
        
        assert len(callback_calls) >= 1
    
    def test_resolve_alert(self, collector_with_thresholds):
        """Test resolución de alertas"""
        collector_with_thresholds.start_export(
            task_id="resolvable",
            visualization_type="graph",
            export_format="svg",
            node_count=75
        )
        
        alerts = collector_with_thresholds.get_alerts()
        assert len(alerts) > 0
        
        alert_id = alerts[0].id
        result = collector_with_thresholds.resolve_alert(alert_id)
        
        assert result is True
        
        unresolved = collector_with_thresholds.get_alerts(unresolved_only=True)
        resolved_ids = [a.id for a in unresolved]
        assert alert_id not in resolved_ids
    
    def test_get_alerts_by_severity(self, collector_with_thresholds):
        """Test filtrado de alertas por severidad"""
        # Generar alertas de diferentes severidades
        collector_with_thresholds.start_export(
            "warning-task", "graph", "svg", node_count=75
        )
        collector_with_thresholds.start_export(
            "critical-task", "graph", "svg", node_count=150
        )
        
        warnings = collector_with_thresholds.get_alerts(AlertSeverity.WARNING)
        criticals = collector_with_thresholds.get_alerts(AlertSeverity.CRITICAL)
        
        assert all(a.severity == AlertSeverity.WARNING for a in warnings)
        assert all(a.severity == AlertSeverity.CRITICAL for a in criticals)


# === Tests de Estadísticas y Reportes ===

class TestStatisticsAndReports:
    """Tests para estadísticas y reportes"""
    
    def test_get_statistics(self, collector):
        """Test obtención de estadísticas"""
        # Ejecutar algunas exportaciones
        for i in range(3):
            metrics = collector.start_export(f"stat-{i}", "graph", "svg")
            collector.end_export(metrics, success=True)
        
        stats = collector.get_statistics()
        
        assert stats['total_exports'] == 3
        assert 'processing_time' in stats
        assert 'memory_usage' in stats
        assert 'alerts' in stats
    
    def test_get_batch_history(self, collector):
        """Test historial de batches"""
        # Ejecutar dos batches
        collector.start_batch("batch-1", 2)
        m1 = collector.start_export("t1", "graph", "svg")
        collector.end_export(m1)
        m2 = collector.start_export("t2", "graph", "svg")
        collector.end_export(m2)
        collector.end_batch()
        
        collector.start_batch("batch-2", 1)
        m3 = collector.start_export("t3", "graph", "svg")
        collector.end_export(m3)
        collector.end_batch()
        
        history = collector.get_batch_history()
        
        assert len(history) == 2
        assert history[0].batch_id == "batch-1"
        assert history[1].batch_id == "batch-2"
    
    def test_export_report(self, collector, temp_output_dir):
        """Test exportación de reporte"""
        # Generar datos
        collector.start_batch("report-batch", 2)
        m1 = collector.start_export("r1", "graph", "svg", node_count=10)
        collector.end_export(m1, success=True)
        m2 = collector.start_export("r2", "tree", "png", node_count=5)
        collector.end_export(m2, success=True)
        collector.end_batch()
        
        # Exportar reporte
        report_path = temp_output_dir / "report.json"
        collector.export_report(report_path)
        
        assert report_path.exists()
        
        with open(report_path) as f:
            report = json.load(f)
        
        assert 'generated_at' in report
        assert 'statistics' in report
        assert 'alerts' in report
        assert 'batches' in report
        assert len(report['batches']) == 1
    
    def test_export_report_without_raw_metrics(self, collector, temp_output_dir):
        """Test exportación sin métricas detalladas"""
        collector.start_batch("compact-batch", 1)
        m = collector.start_export("c1", "graph", "svg")
        collector.end_export(m)
        collector.end_batch()
        
        report_path = temp_output_dir / "compact_report.json"
        collector.export_report(report_path, include_raw_metrics=False)
        
        with open(report_path) as f:
            report = json.load(f)
        
        assert 'export_metrics' not in report['batches'][0]
    
    def test_clear_history(self, collector):
        """Test limpieza de historial"""
        # Generar datos
        collector.start_batch("clear-batch", 1)
        m = collector.start_export("cl1", "graph", "svg", node_count=100)
        collector.end_export(m)
        collector.end_batch()
        
        # Verificar que hay datos
        assert len(collector.get_batch_history()) > 0
        
        # Limpiar
        collector.clear_history()
        
        # Verificar limpieza
        assert len(collector.get_batch_history()) == 0
        assert len(collector.get_alerts()) == 0


# === Tests de MetricsContext ===

class TestMetricsContext:
    """Tests para el context manager"""
    
    def test_context_manager_success(self, collector):
        """Test context manager con éxito"""
        collector.start_batch("ctx-batch", 1)
        
        with MetricsContext(
            collector,
            task_id="ctx-task",
            visualization_type="graph",
            export_format="svg",
            node_count=10
        ) as metrics:
            # Simular trabajo
            pass
        
        batch = collector.end_batch()
        
        assert batch.successful_tasks == 1
        assert batch.failed_tasks == 0
    
    def test_context_manager_with_exception(self, collector):
        """Test context manager con excepción"""
        collector.start_batch("ctx-error-batch", 1)
        
        try:
            with MetricsContext(
                collector,
                task_id="ctx-error-task",
                visualization_type="graph",
                export_format="svg"
            ) as metrics:
                raise ValueError("Test error")
        except ValueError:
            pass
        
        batch = collector.end_batch()
        
        assert batch.failed_tasks == 1
        assert batch.export_metrics[0].error == "Test error"


# === Tests de AlertThresholds ===

class TestAlertThresholds:
    """Tests para configuración de umbrales"""
    
    def test_default_thresholds(self):
        """Test umbrales por defecto"""
        thresholds = AlertThresholds()
        
        assert thresholds.export_time_warning_ms == 5000.0
        assert thresholds.export_time_critical_ms == 30000.0
        assert thresholds.memory_warning_mb == 256.0
        assert thresholds.node_count_warning == 5000
        assert thresholds.node_count_critical == 10000
    
    def test_custom_thresholds(self, custom_thresholds):
        """Test umbrales personalizados"""
        assert custom_thresholds.export_time_warning_ms == 100.0
        assert custom_thresholds.node_count_warning == 50
        assert custom_thresholds.failure_rate_critical == 10.0


# === Tests de Rendimiento ===

class TestPerformance:
    """Tests de rendimiento del colector"""
    
    def test_high_volume_tracking(self, collector):
        """Test tracking de alto volumen"""
        collector.start_batch("high-volume", 100)
        
        for i in range(100):
            metrics = collector.start_export(
                f"hv-{i}",
                "graph",
                "svg",
                node_count=10,
                edge_count=15
            )
            collector.end_export(metrics, success=True)
        
        batch = collector.end_batch()
        
        assert batch.completed_tasks == 100
        assert batch.successful_tasks == 100
        assert len(batch.export_metrics) == 100
    
    def test_concurrent_safe(self, collector):
        """Test seguridad en concurrencia"""
        import threading
        
        collector.start_batch("concurrent", 10)
        threads = []
        
        def track_export(task_id):
            metrics = collector.start_export(task_id, "graph", "svg")
            collector.end_export(metrics, success=True)
        
        for i in range(10):
            t = threading.Thread(target=track_export, args=(f"t-{i}",))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        batch = collector.end_batch()
        
        assert batch.completed_tasks == 10


# === Integration Tests ===

class TestIntegration:
    """Tests de integración"""
    
    def test_full_workflow(self, collector_with_thresholds, temp_output_dir):
        """Test flujo completo de trabajo"""
        collector = collector_with_thresholds
        
        # Iniciar batch
        batch = collector.start_batch("integration-batch", 4)
        
        # Exportación normal
        m1 = collector.start_export("normal", "graph", "svg", node_count=20)
        collector.end_export(m1, success=True)
        
        # Exportación con warning
        m2 = collector.start_export("warning", "graph", "png", node_count=75)
        collector.track_optimization(m2, 50.0)
        collector.end_export(m2, success=True)
        
        # Exportación con error
        m3 = collector.start_export("error", "tree", "dot")
        collector.end_export(m3, success=False, error="Render failed")
        
        # Exportación crítica
        m4 = collector.start_export("critical", "graph", "svg", node_count=150)
        collector.end_export(m4, success=True)
        
        # Finalizar batch
        result = collector.end_batch()
        
        # Verificaciones
        assert result.completed_tasks == 4
        assert result.successful_tasks == 3
        assert result.failed_tasks == 1
        
        # Verificar alertas
        warnings = collector.get_alerts(AlertSeverity.WARNING)
        criticals = collector.get_alerts(AlertSeverity.CRITICAL)
        assert len(warnings) >= 1
        assert len(criticals) >= 1
        
        # Exportar reporte
        report_path = temp_output_dir / "integration_report.json"
        collector.export_report(report_path)
        assert report_path.exists()
        
        # Verificar estadísticas
        stats = collector.get_statistics()
        assert stats['total_exports'] == 4
        assert stats['alerts']['total'] >= 2
