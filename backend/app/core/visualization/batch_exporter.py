"""
Batch Exporter para Visualizaciones
Procesa múltiples visualizaciones de forma eficiente
"""
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import time
from datetime import datetime

from app.core.visualization.recursion_tree_generator import RecursionTreeGenerator
from app.core.visualization.execution_flow_generator import ExecutionFlowGenerator
from app.core.visualization.graph_generator import GraphGenerator
from app.core.visualization.diagram_renderer import DiagramRenderer
from app.utils.logger import get_logger

logger = get_logger(__name__)

class ExportFormat(str, Enum):
    """Formatos de exportación disponibles"""
    PNG = "png"
    SVG = "svg"
    PDF = "pdf"
    DOT = "dot"
    MERMAID = "mermaid"
    JSON = "json"
    HTML = "html"

class ProcessingMode(str, Enum):
    """Modos de procesamiento"""
    SEQUENTIAL = "sequential"
    THREADED = "threaded"
    ASYNC = "async"
    MULTIPROCESS = "multiprocess"

@dataclass
class ExportTask:
    """Tarea de exportación individual"""
    id: str
    visualization_type: str  # 'recursion_tree', 'execution_flow', 'graph'
    data: Dict[str, Any]
    format: ExportFormat
    output_path: Path
    options: Optional[Dict[str, Any]] = None
    priority: int = 0  # Mayor número = mayor prioridad

@dataclass
class ExportResult:
    """Resultado de una exportación"""
    task_id: str
    success: bool
    output_path: Optional[Path] = None
    error: Optional[str] = None
    processing_time: float = 0.0
    file_size: Optional[int] = None

@dataclass
class BatchExportConfig:
    """Configuración para exportación batch"""
    mode: ProcessingMode = ProcessingMode.THREADED
    max_workers: int = 4
    chunk_size: int = 10
    timeout_per_task: float = 30.0
    retry_failed: bool = True
    max_retries: int = 3
    compression: bool = False
    optimize_output: bool = True

class BatchExporter:
    """
    Exportador batch para visualizaciones con soporte para
    procesamiento paralelo y optimización
    """
    
    def __init__(self, config: Optional[BatchExportConfig] = None):
        self.config = config or BatchExportConfig()
        self.recursion_generator = RecursionTreeGenerator()
        self.flow_generator = ExecutionFlowGenerator()
        self.graph_generator = GraphGenerator()
        self.renderer = DiagramRenderer()
        
        self._stats = {
            'total_tasks': 0,
            'successful': 0,
            'failed': 0,
            'total_time': 0.0,
            'total_size': 0
        }
    
    async def export_batch(
        self,
        tasks: List[ExportTask],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[ExportResult]:
        """
        Exporta un batch de visualizaciones
        
        Args:
            tasks: Lista de tareas de exportación
            progress_callback: Callback para reportar progreso (current, total)
            
        Returns:
            Lista de resultados de exportación
        """
        logger.info(f"Iniciando exportación batch de {len(tasks)} tareas")
        start_time = time.time()
        
        # Ordenar por prioridad
        sorted_tasks = sorted(tasks, key=lambda t: t.priority, reverse=True)
        
        # Seleccionar modo de procesamiento
        if self.config.mode == ProcessingMode.SEQUENTIAL:
            results = await self._export_sequential(sorted_tasks, progress_callback)
        elif self.config.mode == ProcessingMode.THREADED:
            results = await self._export_threaded(sorted_tasks, progress_callback)
        elif self.config.mode == ProcessingMode.ASYNC:
            results = await self._export_async(sorted_tasks, progress_callback)
        else:  # MULTIPROCESS
            results = await self._export_multiprocess(sorted_tasks, progress_callback)
        
        # Actualizar estadísticas
        total_time = time.time() - start_time
        self._update_stats(results, total_time)
        
        logger.info(f"Batch completado en {total_time:.2f}s: "
                   f"{self._stats['successful']} exitosas, "
                   f"{self._stats['failed']} fallidas")
        
        return results
    
    async def _export_sequential(
        self,
        tasks: List[ExportTask],
        progress_callback: Optional[Callable]
    ) -> List[ExportResult]:
        """Exportación secuencial"""
        results = []
        for i, task in enumerate(tasks):
            result = await self._process_single_task(task)
            results.append(result)
            
            if progress_callback:
                progress_callback(i + 1, len(tasks))
        
        return results
    
    async def _export_threaded(
        self,
        tasks: List[ExportTask],
        progress_callback: Optional[Callable]
    ) -> List[ExportResult]:
        """Exportación con ThreadPoolExecutor"""
        from concurrent.futures import as_completed  # AGREGAR IMPORT

        results = []
        completed = 0
        
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            # Procesar con as_completed
            futures = {
                executor.submit(self._process_task_sync, task): task
                for task in tasks
            }

            # MEJORA: Usar as_completed en vez de iterar futures directamente
            for future in as_completed(futures, timeout=self.config.timeout_per_task):
                try:
                    result = future.result()
                    results.append(result)
                    completed += 1

                    if progress_callback:
                        progress_callback(completed, len(tasks))

                except TimeoutError:
                    task = futures[future]
                    logger.error(f"Timeout en tarea {task.id}")
                    results.append(ExportResult(
                        task_id=task.id,
                        success=False,
                        error="Timeout exceeded"
                    ))
                    completed += 1

                except Exception as e:
                    task = futures[future]
                    logger.error(f"Error en tarea {task.id}: {e}")
                    results.append(ExportResult(
                        task_id=task.id,
                        success=False,
                        error=str(e)
                    ))
                    completed += 1

        return results
    
    async def _export_async(
        self,
        tasks: List[ExportTask],
        progress_callback: Optional[Callable]
    ) -> List[ExportResult]:
        """Exportación asíncrona con asyncio"""
        semaphore = asyncio.Semaphore(self.config.max_workers)
        
        async def process_with_semaphore(task: ExportTask) -> ExportResult:
            async with semaphore:
                return await self._process_single_task(task)
        
        # Crear todas las tareas
        coroutines = [process_with_semaphore(task) for task in tasks]
        
        # Procesar con progreso
        results = []
        for i, coro in enumerate(asyncio.as_completed(coroutines)):
            result = await coro
            results.append(result)
            
            if progress_callback:
                progress_callback(i + 1, len(tasks))
        
        return results
    
    async def _export_multiprocess(
        self,
        tasks: List[ExportTask],
        progress_callback: Optional[Callable]
    ) -> List[ExportResult]:
        """Exportación con ProcessPoolExecutor (para CPU-bound)"""
        results = []
        completed = 0
        
        with ProcessPoolExecutor(max_workers=self.config.max_workers) as executor:
            futures = [
                executor.submit(self._process_task_sync, task)
                for task in tasks
            ]
            
            for future in futures:
                try:
                    result = future.result(timeout=self.config.timeout_per_task)
                    results.append(result)
                    completed += 1
                    
                    if progress_callback:
                        progress_callback(completed, len(tasks))
                except Exception as e:
                    logger.error(f"Error en proceso: {e}")
                    results.append(ExportResult(
                        task_id="unknown",
                        success=False,
                        error=str(e)
                    ))
        
        return results
    
    async def _process_single_task(self, task: ExportTask) -> ExportResult:
        """Procesa una tarea individual (async)"""
        start_time = time.time()
        
        try:
            # Crear directorio si no existe
            task.output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Generar visualización según tipo
            if task.visualization_type == 'recursion_tree':
                diagram = self.recursion_generator.generate_tree(
                    task.data.get('recurrence'),
                    task.data.get('base_cases', {}),
                    task.options or {}
                )
            elif task.visualization_type == 'execution_flow':
                diagram = self.flow_generator.generate_flow(
                    task.data.get('ast_node'),
                    task.options or {}
                )
            elif task.visualization_type == 'graph':
                diagram = self.graph_generator.generate_graph(
                    num_nodes=task.data.get('num_nodes', 6),
                    edges_list=task.data.get('edges_list'),
                    directed=task.data.get('directed', True),
                    layout=task.data.get('layout', None)
                )
            else:
                raise ValueError(f"Tipo desconocido: {task.visualization_type}")
            
            # Renderizar en formato solicitado
            if task.format == ExportFormat.DOT:
                output = diagram.to_dot()
            elif task.format == ExportFormat.MERMAID:
                output = diagram.to_mermaid()
            elif task.format == ExportFormat.JSON:
                output = diagram.to_json()
            else:
                # PNG, SVG, PDF requieren renderizado
                output = await self._render_diagram(diagram, task.format, task.options)
            
            # Guardar archivo
            if isinstance(output, str):
                task.output_path.write_text(output, encoding='utf-8')
            else:
                task.output_path.write_bytes(output)
            
            # Optimizar si está habilitado
            if self.config.optimize_output:
                await self._optimize_output(task.output_path, task.format)
            
            processing_time = time.time() - start_time
            file_size = task.output_path.stat().st_size
            
            return ExportResult(
                task_id=task.id,
                success=True,
                output_path=task.output_path,
                processing_time=processing_time,
                file_size=file_size
            )
            
        except Exception as e:
            logger.error(f"Error procesando tarea {task.id}: {e}")
            return ExportResult(
                task_id=task.id,
                success=False,
                error=str(e),
                processing_time=time.time() - start_time
            )
    
    def _process_task_sync(self, task: ExportTask) -> ExportResult:
        """Versión síncrona para ThreadPoolExecutor/ProcessPoolExecutor"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self._process_single_task(task))
        finally:
            loop.close()
    
    async def _render_diagram(
        self,
        diagram: Any,
        format: ExportFormat,
        options: Optional[Dict]
    ) -> bytes:
        """Renderiza diagrama en formato específico"""
        return await self.renderer.render(
            diagram,
            format.value,
            options or {}
        )
    
    async def _optimize_output(self, path: Path, format: ExportFormat):
        """Optimiza archivo de salida"""
        if format == ExportFormat.SVG:
            # Optimizar SVG (remover metadata innecesaria, etc)
            content = path.read_text()
            # Aplicar optimizaciones específicas
            optimized = self._optimize_svg(content)
            path.write_text(optimized)
        elif format == ExportFormat.PNG and self.config.compression:
            # Comprimir PNG
            await self._compress_png(path)
    
    def _optimize_svg(self, content: str) -> str:
        """Optimiza contenido SVG"""
        # Implementar optimizaciones SVG
        # Por ahora retorna tal cual
        return content
    
    async def _compress_png(self, path: Path):
        """Comprime archivo PNG"""
        # Implementar compresión PNG con PIL/Pillow
        pass
    
    def _update_stats(self, results: List[ExportResult], total_time: float):
        """Actualiza estadísticas de exportación"""
        self._stats['total_tasks'] += len(results)
        self._stats['successful'] += sum(1 for r in results if r.success)
        self._stats['failed'] += sum(1 for r in results if not r.success)
        self._stats['total_time'] += total_time
        self._stats['total_size'] += sum(
            r.file_size for r in results if r.file_size
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de exportación"""
        return {
            **self._stats,
            'average_time': (
                self._stats['total_time'] / self._stats['total_tasks']
                if self._stats['total_tasks'] > 0 else 0
            ),
            'success_rate': (
                self._stats['successful'] / self._stats['total_tasks'] * 100
                if self._stats['total_tasks'] > 0 else 0
            )
        }
    
    def reset_stats(self):
        """Reinicia estadísticas"""
        self._stats = {
            'total_tasks': 0,
            'successful': 0,
            'failed': 0,
            'total_time': 0.0,
            'total_size': 0
        }
    
    async def export_with_retry(
        self,
        task: ExportTask,
        max_retries: Optional[int] = None
    ) -> ExportResult:
        """
        Exporta con reintentos en caso de fallo
        
        Args:
            task: Tarea a exportar
            max_retries: Número máximo de reintentos (usa config si es None)
            
        Returns:
            Resultado de exportación
        """
        max_retries = max_retries or self.config.max_retries
        last_error = None
        
        for attempt in range(max_retries + 1):
            result = await self._process_single_task(task)
            
            if result.success:
                if attempt > 0:
                    logger.info(f"Tarea {task.id} exitosa en intento {attempt + 1}")
                return result
            
            last_error = result.error
            if attempt < max_retries:
                wait_time = 2 ** attempt  # Backoff exponencial
                logger.warning(
                    f"Intento {attempt + 1} fallido para {task.id}, "
                    f"reintentando en {wait_time}s..."
                )
                await asyncio.sleep(wait_time)
        
        logger.error(f"Tarea {task.id} falló después de {max_retries + 1} intentos")
        return ExportResult(
            task_id=task.id,
            success=False,
            error=f"Falló después de {max_retries + 1} intentos: {last_error}"
        )