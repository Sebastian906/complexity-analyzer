"""
Metrics Collector para Visualizaciones
Sistema de métricas, monitoring y alertas para exportación de visualizaciones
"""
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import time
import threading
import tracemalloc
import gc
from pathlib import Path
import json
from collections import defaultdict

from app.utils.logger import get_logger

logger = get_logger(__name__)


class AlertSeverity(str, Enum):
    """Niveles de severidad para alertas"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class MetricType(str, Enum):
    """Tipos de métricas"""
    EXPORT_TIME = "export_time"
    MEMORY_USAGE = "memory_usage"
    GRAPH_SIZE = "graph_size"
    FILE_SIZE = "file_size"
    OPTIMIZATION_TIME = "optimization_time"
    RENDER_TIME = "render_time"
    BATCH_THROUGHPUT = "batch_throughput"


@dataclass
class Alert:
    """Representa una alerta del sistema"""
    id: str
    severity: AlertSeverity
    message: str
    metric_type: MetricType
    value: float
    threshold: float
    timestamp: datetime = field(default_factory=datetime.now)
    task_id: Optional[str] = None
    resolved: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la alerta a diccionario"""
        return {
            'id': self.id,
            'severity': self.severity.value,
            'message': self.message,
            'metric_type': self.metric_type.value,
            'value': self.value,
            'threshold': self.threshold,
            'timestamp': self.timestamp.isoformat(),
            'task_id': self.task_id,
            'resolved': self.resolved
        }


@dataclass
class ExportMetrics:
    """Métricas de una exportación individual"""
    task_id: str
    visualization_type: str
    export_format: str
    start_time: datetime
    end_time: Optional[datetime] = None
    processing_time_ms: float = 0.0
    memory_before_bytes: int = 0
    memory_after_bytes: int = 0
    memory_peak_bytes: int = 0
    memory_delta_bytes: int = 0
    node_count: int = 0
    edge_count: int = 0
    file_size_bytes: int = 0
    optimization_applied: bool = False
    optimization_time_ms: float = 0.0
    success: bool = True
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte las métricas a diccionario"""
        return {
            'task_id': self.task_id,
            'visualization_type': self.visualization_type,
            'export_format': self.export_format,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'processing_time_ms': self.processing_time_ms,
            'memory': {
                'before_bytes': self.memory_before_bytes,
                'after_bytes': self.memory_after_bytes,
                'peak_bytes': self.memory_peak_bytes,
                'delta_bytes': self.memory_delta_bytes,
                'delta_mb': round(self.memory_delta_bytes / (1024 * 1024), 2)
            },
            'graph': {
                'node_count': self.node_count,
                'edge_count': self.edge_count
            },
            'file_size_bytes': self.file_size_bytes,
            'file_size_kb': round(self.file_size_bytes / 1024, 2),
            'optimization': {
                'applied': self.optimization_applied,
                'time_ms': self.optimization_time_ms
            },
            'success': self.success,
            'error': self.error
        }


@dataclass
class BatchMetrics:
    """Métricas de un batch de exportaciones"""
    batch_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_tasks: int = 0
    completed_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    total_processing_time_ms: float = 0.0
    avg_processing_time_ms: float = 0.0
    total_memory_used_bytes: int = 0
    peak_memory_bytes: int = 0
    total_file_size_bytes: int = 0
    throughput_tasks_per_sec: float = 0.0
    export_metrics: List[ExportMetrics] = field(default_factory=list)
    alerts_triggered: List[Alert] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte las métricas del batch a diccionario"""
        return {
            'batch_id': self.batch_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'tasks': {
                'total': self.total_tasks,
                'completed': self.completed_tasks,
                'successful': self.successful_tasks,
                'failed': self.failed_tasks,
                'success_rate': round(
                    self.successful_tasks / max(self.total_tasks, 1) * 100, 2
                )
            },
            'timing': {
                'total_processing_time_ms': self.total_processing_time_ms,
                'avg_processing_time_ms': self.avg_processing_time_ms,
                'throughput_tasks_per_sec': round(self.throughput_tasks_per_sec, 2)
            },
            'memory': {
                'total_used_bytes': self.total_memory_used_bytes,
                'peak_bytes': self.peak_memory_bytes,
                'peak_mb': round(self.peak_memory_bytes / (1024 * 1024), 2)
            },
            'output': {
                'total_file_size_bytes': self.total_file_size_bytes,
                'total_file_size_mb': round(self.total_file_size_bytes / (1024 * 1024), 2)
            },
            'alerts': [a.to_dict() for a in self.alerts_triggered],
            'export_metrics': [m.to_dict() for m in self.export_metrics]
        }


@dataclass
class AlertThresholds:
    """Configuración de umbrales para alertas"""
    # Tiempo de exportación
    export_time_warning_ms: float = 5000.0  # 5 segundos
    export_time_critical_ms: float = 30000.0  # 30 segundos
    
    # Uso de memoria
    memory_warning_mb: float = 256.0  # 256 MB
    memory_critical_mb: float = 512.0  # 512 MB
    
    # Tamaño del grafo
    node_count_warning: int = 5000
    node_count_critical: int = 10000
    edge_count_warning: int = 20000
    edge_count_critical: int = 50000
    
    # Tamaño de archivo
    file_size_warning_mb: float = 10.0
    file_size_critical_mb: float = 50.0
    
    # Tasa de fallos
    failure_rate_warning: float = 10.0  # 10%
    failure_rate_critical: float = 25.0  # 25%


class MetricsCollector:
    """
    Colector de métricas para visualizaciones con:
    - Logs detallados de tiempo de exportación
    - Métricas de uso de memoria
    - Alertas para grafos muy grandes
    """
    
    def __init__(
        self,
        thresholds: Optional[AlertThresholds] = None,
        alert_callback: Optional[Callable[[Alert], None]] = None
    ):
        """
        Inicializa el colector de métricas
        
        Args:
            thresholds: Umbrales personalizados para alertas
            alert_callback: Callback opcional para notificar alertas
        """
        self.thresholds = thresholds or AlertThresholds()
        self.alert_callback = alert_callback
        
        self._current_batch: Optional[BatchMetrics] = None
        self._all_batches: List[BatchMetrics] = []
        self._alerts: List[Alert] = []
        self._alert_counter = 0
        self._lock = threading.RLock()  # RLock permite re-adquisición desde el mismo hilo
        
        # Estadísticas agregadas
        self._stats = defaultdict(list)
        
        logger.info("MetricsCollector inicializado")
    
    # === Gestión de Batches ===
    
    def start_batch(self, batch_id: str, total_tasks: int) -> BatchMetrics:
        """
        Inicia el tracking de un nuevo batch
        
        Args:
            batch_id: Identificador único del batch
            total_tasks: Número total de tareas
            
        Returns:
            BatchMetrics para el batch iniciado
        """
        with self._lock:
            self._current_batch = BatchMetrics(
                batch_id=batch_id,
                start_time=datetime.now(),
                total_tasks=total_tasks
            )
            
            # Iniciar tracking de memoria
            tracemalloc.start()
            
            logger.info(f"Batch {batch_id} iniciado con {total_tasks} tareas")
            
            return self._current_batch
    
    def end_batch(self) -> Optional[BatchMetrics]:
        """
        Finaliza el batch actual y calcula métricas finales
        
        Returns:
            BatchMetrics completas o None si no hay batch activo
        """
        with self._lock:
            if not self._current_batch:
                logger.warning("No hay batch activo para finalizar")
                return None
            
            batch = self._current_batch
            batch.end_time = datetime.now()
            
            # Obtener peak de memoria
            current, peak = tracemalloc.get_traced_memory()
            batch.peak_memory_bytes = peak
            tracemalloc.stop()
            
            # Calcular estadísticas agregadas
            if batch.export_metrics:
                times = [m.processing_time_ms for m in batch.export_metrics]
                batch.total_processing_time_ms = sum(times)
                batch.avg_processing_time_ms = sum(times) / len(times)
                
                batch.total_memory_used_bytes = sum(
                    m.memory_delta_bytes for m in batch.export_metrics
                )
                
                batch.total_file_size_bytes = sum(
                    m.file_size_bytes for m in batch.export_metrics
                )
            
            # Calcular throughput
            duration_sec = (batch.end_time - batch.start_time).total_seconds()
            if duration_sec > 0:
                batch.throughput_tasks_per_sec = batch.completed_tasks / duration_sec
            
            # Verificar alertas de tasa de fallos
            if batch.total_tasks > 0:
                failure_rate = (batch.failed_tasks / batch.total_tasks) * 100
                self._check_failure_rate_alert(batch.batch_id, failure_rate)
            
            # Guardar en historial
            self._all_batches.append(batch)
            
            # Log resumen
            self._log_batch_summary(batch)
            
            self._current_batch = None
            return batch
    
    # === Tracking de Exportaciones ===
    
    def start_export(
        self,
        task_id: str,
        visualization_type: str,
        export_format: str,
        node_count: int = 0,
        edge_count: int = 0
    ) -> ExportMetrics:
        """
        Inicia el tracking de una exportación
        
        Args:
            task_id: ID de la tarea
            visualization_type: Tipo de visualización
            export_format: Formato de exportación
            node_count: Número de nodos
            edge_count: Número de aristas
            
        Returns:
            ExportMetrics para la exportación
        """
        # Verificar alertas de tamaño de grafo antes de iniciar
        self._check_graph_size_alerts(task_id, node_count, edge_count)
        
        # Capturar memoria inicial
        gc.collect()  # Limpiar para medición más precisa
        memory_before = self._get_current_memory()
        
        metrics = ExportMetrics(
            task_id=task_id,
            visualization_type=visualization_type,
            export_format=export_format,
            start_time=datetime.now(),
            node_count=node_count,
            edge_count=edge_count,
            memory_before_bytes=memory_before
        )
        
        logger.debug(
            f"Exportación iniciada: {task_id} "
            f"(tipo={visualization_type}, formato={export_format}, "
            f"nodos={node_count}, aristas={edge_count})"
        )
        
        return metrics
    
    def end_export(
        self,
        metrics: ExportMetrics,
        success: bool = True,
        error: Optional[str] = None,
        file_path: Optional[Path] = None
    ) -> ExportMetrics:
        """
        Finaliza el tracking de una exportación
        
        Args:
            metrics: Métricas de la exportación
            success: Si fue exitosa
            error: Mensaje de error si falló
            file_path: Ruta del archivo generado
            
        Returns:
            ExportMetrics actualizadas
        """
        metrics.end_time = datetime.now()
        metrics.success = success
        metrics.error = error
        
        # Calcular tiempo de procesamiento
        processing_time = (metrics.end_time - metrics.start_time).total_seconds()
        metrics.processing_time_ms = processing_time * 1000
        
        # Capturar memoria final
        metrics.memory_after_bytes = self._get_current_memory()
        metrics.memory_delta_bytes = max(
            0, metrics.memory_after_bytes - metrics.memory_before_bytes
        )
        
        # Obtener tamaño de archivo
        if file_path and file_path.exists():
            metrics.file_size_bytes = file_path.stat().st_size
        
        # Verificar alertas
        self._check_export_time_alert(metrics)
        self._check_memory_alert(metrics)
        self._check_file_size_alert(metrics)
        
        # Actualizar batch si existe
        with self._lock:
            if self._current_batch:
                self._current_batch.export_metrics.append(metrics)
                self._current_batch.completed_tasks += 1
                if success:
                    self._current_batch.successful_tasks += 1
                else:
                    self._current_batch.failed_tasks += 1
        
        # Guardar en estadísticas
        self._stats['processing_times'].append(metrics.processing_time_ms)
        self._stats['memory_usage'].append(metrics.memory_delta_bytes)
        
        # Log detallado
        self._log_export_metrics(metrics)
        
        return metrics
    
    def track_optimization(
        self,
        metrics: ExportMetrics,
        optimization_time_ms: float
    ) -> None:
        """
        Registra el tiempo de optimización
        
        Args:
            metrics: Métricas de la exportación
            optimization_time_ms: Tiempo de optimización en ms
        """
        metrics.optimization_applied = True
        metrics.optimization_time_ms = optimization_time_ms
        
        logger.debug(
            f"Optimización aplicada a {metrics.task_id}: "
            f"{optimization_time_ms:.2f}ms"
        )
    
    # === Sistema de Alertas ===
    
    def _create_alert(
        self,
        severity: AlertSeverity,
        message: str,
        metric_type: MetricType,
        value: float,
        threshold: float,
        task_id: Optional[str] = None
    ) -> Alert:
        """Crea y registra una alerta"""
        with self._lock:
            self._alert_counter += 1
            alert_id = f"ALERT-{self._alert_counter:04d}"
        
        alert = Alert(
            id=alert_id,
            severity=severity,
            message=message,
            metric_type=metric_type,
            value=value,
            threshold=threshold,
            task_id=task_id
        )
        
        self._alerts.append(alert)
        
        if self._current_batch:
            self._current_batch.alerts_triggered.append(alert)
        
        # Log según severidad
        log_msg = f"[{alert_id}] {message} (valor={value:.2f}, umbral={threshold:.2f})"
        if severity == AlertSeverity.CRITICAL:
            logger.error(f"ALERTA CRÍTICA: {log_msg}")
        elif severity == AlertSeverity.WARNING:
            logger.warning(f"ALERTA: {log_msg}")
        else:
            logger.info(f"INFO: {log_msg}")
        
        # Notificar via callback
        if self.alert_callback:
            try:
                self.alert_callback(alert)
            except Exception as e:
                logger.error(f"Error en callback de alerta: {e}")
        
        return alert
    
    def _check_graph_size_alerts(
        self,
        task_id: str,
        node_count: int,
        edge_count: int
    ) -> None:
        """Verifica alertas de tamaño de grafo"""
        # Alertas de nodos
        if node_count >= self.thresholds.node_count_critical:
            self._create_alert(
                AlertSeverity.CRITICAL,
                f"Grafo muy grande detectado: {node_count} nodos",
                MetricType.GRAPH_SIZE,
                node_count,
                self.thresholds.node_count_critical,
                task_id
            )
        elif node_count >= self.thresholds.node_count_warning:
            self._create_alert(
                AlertSeverity.WARNING,
                f"Grafo grande detectado: {node_count} nodos",
                MetricType.GRAPH_SIZE,
                node_count,
                self.thresholds.node_count_warning,
                task_id
            )
        
        # Alertas de aristas
        if edge_count >= self.thresholds.edge_count_critical:
            self._create_alert(
                AlertSeverity.CRITICAL,
                f"Demasiadas aristas: {edge_count}",
                MetricType.GRAPH_SIZE,
                edge_count,
                self.thresholds.edge_count_critical,
                task_id
            )
        elif edge_count >= self.thresholds.edge_count_warning:
            self._create_alert(
                AlertSeverity.WARNING,
                f"Muchas aristas: {edge_count}",
                MetricType.GRAPH_SIZE,
                edge_count,
                self.thresholds.edge_count_warning,
                task_id
            )
    
    def _check_export_time_alert(self, metrics: ExportMetrics) -> None:
        """Verifica alertas de tiempo de exportación"""
        if metrics.processing_time_ms >= self.thresholds.export_time_critical_ms:
            self._create_alert(
                AlertSeverity.CRITICAL,
                f"Exportación extremadamente lenta: {metrics.processing_time_ms:.0f}ms",
                MetricType.EXPORT_TIME,
                metrics.processing_time_ms,
                self.thresholds.export_time_critical_ms,
                metrics.task_id
            )
        elif metrics.processing_time_ms >= self.thresholds.export_time_warning_ms:
            self._create_alert(
                AlertSeverity.WARNING,
                f"Exportación lenta: {metrics.processing_time_ms:.0f}ms",
                MetricType.EXPORT_TIME,
                metrics.processing_time_ms,
                self.thresholds.export_time_warning_ms,
                metrics.task_id
            )
    
    def _check_memory_alert(self, metrics: ExportMetrics) -> None:
        """Verifica alertas de uso de memoria"""
        memory_mb = metrics.memory_delta_bytes / (1024 * 1024)
        
        if memory_mb >= self.thresholds.memory_critical_mb:
            self._create_alert(
                AlertSeverity.CRITICAL,
                f"Uso de memoria crítico: {memory_mb:.1f} MB",
                MetricType.MEMORY_USAGE,
                memory_mb,
                self.thresholds.memory_critical_mb,
                metrics.task_id
            )
        elif memory_mb >= self.thresholds.memory_warning_mb:
            self._create_alert(
                AlertSeverity.WARNING,
                f"Alto uso de memoria: {memory_mb:.1f} MB",
                MetricType.MEMORY_USAGE,
                memory_mb,
                self.thresholds.memory_warning_mb,
                metrics.task_id
            )
    
    def _check_file_size_alert(self, metrics: ExportMetrics) -> None:
        """Verifica alertas de tamaño de archivo"""
        file_size_mb = metrics.file_size_bytes / (1024 * 1024)
        
        if file_size_mb >= self.thresholds.file_size_critical_mb:
            self._create_alert(
                AlertSeverity.CRITICAL,
                f"Archivo muy grande: {file_size_mb:.1f} MB",
                MetricType.FILE_SIZE,
                file_size_mb,
                self.thresholds.file_size_critical_mb,
                metrics.task_id
            )
        elif file_size_mb >= self.thresholds.file_size_warning_mb:
            self._create_alert(
                AlertSeverity.WARNING,
                f"Archivo grande: {file_size_mb:.1f} MB",
                MetricType.FILE_SIZE,
                file_size_mb,
                self.thresholds.file_size_warning_mb,
                metrics.task_id
            )
    
    def _check_failure_rate_alert(
        self,
        batch_id: str,
        failure_rate: float
    ) -> None:
        """Verifica alertas de tasa de fallos"""
        if failure_rate >= self.thresholds.failure_rate_critical:
            self._create_alert(
                AlertSeverity.CRITICAL,
                f"Tasa de fallos crítica en batch {batch_id}: {failure_rate:.1f}%",
                MetricType.BATCH_THROUGHPUT,
                failure_rate,
                self.thresholds.failure_rate_critical,
                batch_id
            )
        elif failure_rate >= self.thresholds.failure_rate_warning:
            self._create_alert(
                AlertSeverity.WARNING,
                f"Alta tasa de fallos en batch {batch_id}: {failure_rate:.1f}%",
                MetricType.BATCH_THROUGHPUT,
                failure_rate,
                self.thresholds.failure_rate_warning,
                batch_id
            )
    
    # === Logging ===
    
    def _log_export_metrics(self, metrics: ExportMetrics) -> None:
        """Log detallado de métricas de exportación"""
        status = "SUCCESS" if metrics.success else "FAILURE"
        memory_mb = metrics.memory_delta_bytes / (1024 * 1024)
        file_kb = metrics.file_size_bytes / 1024
        
        logger.info(
            f"{status} Exportación {metrics.task_id} completada: "
            f"tiempo={metrics.processing_time_ms:.2f}ms, "
            f"memoria={memory_mb:.2f}MB, "
            f"archivo={file_kb:.2f}KB"
        )
        
        if metrics.optimization_applied:
            logger.debug(
                f"   └─ Optimización: {metrics.optimization_time_ms:.2f}ms"
            )
    
    def _log_batch_summary(self, batch: BatchMetrics) -> None:
        """Log resumen del batch"""
        duration = (batch.end_time - batch.start_time).total_seconds()
        success_rate = (
            batch.successful_tasks / max(batch.total_tasks, 1) * 100
        )
        memory_mb = batch.peak_memory_bytes / (1024 * 1024)
        file_mb = batch.total_file_size_bytes / (1024 * 1024)
        
        logger.info(f"RESUMEN BATCH: {batch.batch_id}")
        logger.info(f"   Tareas: {batch.successful_tasks}/{batch.total_tasks} exitosas ({success_rate:.1f}%)")
        logger.info(f"   Duración: {duration:.2f}s")
        logger.info(f"   Throughput: {batch.throughput_tasks_per_sec:.2f} tareas/s")
        logger.info(f"   Tiempo promedio: {batch.avg_processing_time_ms:.2f}ms")
        logger.info(f"   Memoria pico: {memory_mb:.2f} MB")
        logger.info(f"   Archivos generados: {file_mb:.2f} MB total")
        
        if batch.alerts_triggered:
            critical = sum(1 for a in batch.alerts_triggered if a.severity == AlertSeverity.CRITICAL)
            warning = sum(1 for a in batch.alerts_triggered if a.severity == AlertSeverity.WARNING)
            logger.info(f"   Alertas: {critical} críticas, {warning} warnings")
        
        logger.info("=" * 60)
    
    # === Utilidades ===
    
    def _get_current_memory(self) -> int:
        """Obtiene el uso de memoria actual del proceso"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss
        except ImportError:
            # Fallback sin psutil
            import sys
            return sum(sys.getsizeof(obj) for obj in gc.get_objects())
    
    # === Consultas y Reportes ===
    
    def get_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        unresolved_only: bool = False
    ) -> List[Alert]:
        """
        Obtiene las alertas registradas
        
        Args:
            severity: Filtrar por severidad
            unresolved_only: Solo alertas no resueltas
            
        Returns:
            Lista de alertas
        """
        alerts = self._alerts.copy()
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        if unresolved_only:
            alerts = [a for a in alerts if not a.resolved]
        
        return alerts
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Marca una alerta como resuelta"""
        for alert in self._alerts:
            if alert.id == alert_id:
                alert.resolved = True
                logger.info(f"Alerta {alert_id} resuelta")
                return True
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas agregadas
        
        Returns:
            Diccionario con estadísticas
        """
        times = self._stats['processing_times']
        memory = self._stats['memory_usage']
        
        return {
            'total_exports': len(times),
            'total_batches': len(self._all_batches),
            'processing_time': {
                'avg_ms': sum(times) / len(times) if times else 0,
                'min_ms': min(times) if times else 0,
                'max_ms': max(times) if times else 0,
                'total_ms': sum(times)
            },
            'memory_usage': {
                'avg_bytes': sum(memory) / len(memory) if memory else 0,
                'max_bytes': max(memory) if memory else 0,
                'total_bytes': sum(memory)
            },
            'alerts': {
                'total': len(self._alerts),
                'critical': sum(1 for a in self._alerts if a.severity == AlertSeverity.CRITICAL),
                'warning': sum(1 for a in self._alerts if a.severity == AlertSeverity.WARNING),
                'unresolved': sum(1 for a in self._alerts if not a.resolved)
            }
        }
    
    def get_batch_history(self) -> List[BatchMetrics]:
        """Obtiene historial de batches"""
        return self._all_batches.copy()
    
    def export_report(
        self,
        output_path: Path,
        include_raw_metrics: bool = True
    ) -> None:
        """
        Exporta reporte completo a JSON
        
        Args:
            output_path: Ruta del archivo de salida
            include_raw_metrics: Incluir métricas detalladas de cada export
        """
        report = {
            'generated_at': datetime.now().isoformat(),
            'statistics': self.get_statistics(),
            'alerts': [a.to_dict() for a in self._alerts],
            'batches': []
        }
        
        for batch in self._all_batches:
            batch_dict = batch.to_dict()
            if not include_raw_metrics:
                del batch_dict['export_metrics']
            report['batches'].append(batch_dict)
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2, default=str))
        
        logger.info(f"Reporte exportado a {output_path}")
    
    def clear_history(self) -> None:
        """Limpia todo el historial"""
        with self._lock:
            self._all_batches.clear()
            self._alerts.clear()
            self._stats.clear()
            self._alert_counter = 0
            logger.info("Historial de métricas limpiado")


# === Decorador de conveniencia ===

def track_export(collector: MetricsCollector):
    """
    Decorador para trackear exportaciones automáticamente
    
    Usage:
        @track_export(collector)
        async def export_visualization(task):
            ...
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extraer info del task si está disponible
            task_id = kwargs.get('task_id', 'unknown')
            viz_type = kwargs.get('visualization_type', 'unknown')
            export_format = kwargs.get('export_format', 'unknown')
            
            metrics = collector.start_export(task_id, viz_type, export_format)
            
            try:
                result = await func(*args, **kwargs)
                collector.end_export(metrics, success=True)
                return result
            except Exception as e:
                collector.end_export(metrics, success=False, error=str(e))
                raise
        
        return wrapper
    return decorator


# === Context Manager ===

class MetricsContext:
    """Context manager para tracking de exportaciones"""
    
    def __init__(
        self,
        collector: MetricsCollector,
        task_id: str,
        visualization_type: str,
        export_format: str,
        node_count: int = 0,
        edge_count: int = 0
    ):
        self.collector = collector
        self.task_id = task_id
        self.visualization_type = visualization_type
        self.export_format = export_format
        self.node_count = node_count
        self.edge_count = edge_count
        self.metrics: Optional[ExportMetrics] = None
    
    def __enter__(self) -> ExportMetrics:
        self.metrics = self.collector.start_export(
            self.task_id,
            self.visualization_type,
            self.export_format,
            self.node_count,
            self.edge_count
        )
        return self.metrics
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.metrics:
            success = exc_type is None
            error = str(exc_val) if exc_val else None
            self.collector.end_export(self.metrics, success=success, error=error)
