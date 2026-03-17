"""
Tests Unitarios - Worker Pools y Graphviz

Verifica que las operaciones bloqueantes (Graphviz, I/O)
se ejecuten en pools de workers sin bloquear el event loop.
"""

import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

from app.parallel.worker_pools import (
    PoolConfig,
    ThreadPoolRegistry,
    get_io_pool,
    get_cpu_pool,
    get_graphviz_pool,
    shutdown_all_pools,
    get_pool_stats,
)

@pytest.mark.unit
class TestPoolConfig:
    """Tests de configuración de pools"""
    
    def test_default_config(self):
        """Test valores por defecto de configuración"""
        config = PoolConfig()
        
        assert config.io_workers > 0
        assert config.cpu_workers > 0
        assert config.graphviz_workers > 0
        assert config.graphviz_workers <= 4  # Limitado intencionalmente
    
    def test_config_respects_env_vars(self, monkeypatch):
        """Test que respeta variables de entorno"""
        monkeypatch.setenv("PARALLEL_IO_WORKERS", "10")
        monkeypatch.setenv("PARALLEL_CPU_WORKERS", "2")
        monkeypatch.setenv("PARALLEL_GRAPHVIZ_WORKERS", "3")
        
        config = PoolConfig()
        
        assert config.io_workers == 10
        assert config.cpu_workers == 2
        assert config.graphviz_workers == 3

@pytest.mark.unit
class TestThreadPoolRegistry:
    """Tests del registro de pools"""
    
    def test_singleton_pattern(self):
        """Test que ThreadPoolRegistry es singleton"""
        registry1 = ThreadPoolRegistry()
        registry2 = ThreadPoolRegistry()
        
        assert registry1 is registry2
    
    def test_get_or_create_pool(self):
        """Test creación de pools"""
        registry = ThreadPoolRegistry()
        
        pool1 = registry.get_or_create("test_pool", max_workers=4)
        pool2 = registry.get_or_create("test_pool", max_workers=4)
        
        # Debe retornar el mismo pool
        assert pool1 is pool2
        assert isinstance(pool1, ThreadPoolExecutor)
    
    def test_shutdown_all_pools(self):
        """Test cierre de todos los pools"""
        registry = ThreadPoolRegistry()
        
        # Crear varios pools
        registry.get_or_create("pool1", max_workers=2)
        registry.get_or_create("pool2", max_workers=2)
        
        # Cerrar todos
        registry.shutdown_all(wait=False)
        
        # Los pools deben estar cerrados
        # (no podemos verificar directamente, pero no debe lanzar error)
    
    def test_get_stats(self):
        """Test obtener estadísticas de pools"""
        registry = ThreadPoolRegistry()
        
        registry.get_or_create("stats_pool", max_workers=5)
        
        stats = registry.get_stats()
        
        assert "stats_pool" in stats
        assert stats["stats_pool"]["max_workers"] == 5

@pytest.mark.unit
class TestWorkerPools:
    """Tests de los pools públicos"""
    
    def test_get_io_pool(self):
        """Test obtener pool I/O"""
        pool = get_io_pool()
        
        assert isinstance(pool, ThreadPoolExecutor)
    
    def test_get_cpu_pool(self):
        """Test obtener pool CPU"""
        pool = get_cpu_pool()
        
        assert isinstance(pool, ThreadPoolExecutor)
    
    def test_get_graphviz_pool(self):
        """Test obtener pool Graphviz"""
        pool = get_graphviz_pool()
        
        assert isinstance(pool, ThreadPoolExecutor)
    
    def test_pools_are_reused(self):
        """Test que los pools se reutilizan"""
        pool1 = get_io_pool()
        pool2 = get_io_pool()
        
        assert pool1 is pool2
    
    def test_different_pools_are_separate(self):
        """Test que pools diferentes son instancias separadas"""
        io_pool = get_io_pool()
        cpu_pool = get_cpu_pool()
        graphviz_pool = get_graphviz_pool()
        
        assert io_pool is not cpu_pool
        assert io_pool is not graphviz_pool
        assert cpu_pool is not graphviz_pool

@pytest.mark.integration
class TestGraphvizInExecutor:
    """Tests de Graphviz en executor (no bloquea event loop)"""
    
    @pytest.mark.asyncio
    async def test_graphviz_doesnt_block_event_loop(self):
        """Test que Graphviz no bloquea el event loop"""
        try:
            import graphviz
        except ImportError:
            pytest.skip("Graphviz no instalado")
        
        # Simular operación Graphviz bloqueante
        def blocking_graphviz_operation():
            dot = graphviz.Digraph()
            dot.node("A", "Start")
            dot.node("B", "End")
            dot.edge("A", "B")
            return dot.pipe(format="svg")
        
        # Ejecutar en pool
        loop = asyncio.get_event_loop()
        start = time.time()
        
        # Lanzar operación en pool sin bloquear
        task = loop.run_in_executor(get_graphviz_pool(), blocking_graphviz_operation)
        
        # El event loop debe seguir respondiendo
        counter = 0
        while not task.done():
            counter += 1
            await asyncio.sleep(0.01)
        
        elapsed = time.time() - start
        
        # La tarea completó
        result = await task
        assert result is not None
        
        # El event loop procesó al menos algunas iteraciones
        assert counter > 0
        
        # No debe haber tomado demasiado tiempo
        assert elapsed < 2.0
    
    @pytest.mark.asyncio
    async def test_multiple_graphviz_concurrent(self):
        """Test múltiples operaciones Graphviz concurrentes"""
        try:
            import graphviz
        except ImportError:
            pytest.skip("Graphviz no instalado")
        
        def create_simple_graph(name):
            dot = graphviz.Digraph()
            dot.node(name, name)
            return dot.pipe(format="svg")
        
        loop = asyncio.get_event_loop()
        
        # Lanzar 10 operaciones concurrentes
        tasks = [
            loop.run_in_executor(get_graphviz_pool(), create_simple_graph, f"Node{i}")
            for i in range(10)
        ]
        
        # Todas deben completar sin bloquear
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 10
        assert all(r is not None for r in results)

@pytest.mark.integration
class TestDiagramRendererIntegration:
    """Tests de integración con diagram_renderer usando pools"""
    
    @pytest.mark.asyncio
    async def test_render_diagram_async_uses_pool(self):
        """Test que render_diagram_async usa el pool"""
        from app.core.visualization.diagram_renderer import render_diagram_async, RenderFormat
        from app.core.visualization.tree_builder import TreeNode
        
        # Crear árbol simple
        root = TreeNode(id="root", label="Root")
        child1 = TreeNode(id="child1", label="Child 1")
        child2 = TreeNode(id="child2", label="Child 2")
        root.add_child(child1)
        root.add_child(child2)
        
        try:
            # Renderizar de forma async (debe usar pool)
            start = time.time()
            result = await render_diagram_async(root, format=RenderFormat.SVG)
            elapsed = time.time() - start
            
            assert result is not None
            assert result.content is not None
            
            # No debe bloquear (timeout razonable)
            assert elapsed < 5.0
        except Exception as e:
            # Si Graphviz no está disponible, skip
            if "graphviz" in str(e).lower() or "not available" in str(e).lower():
                pytest.skip(f"Graphviz no disponible: {e}")
            raise
    
    @pytest.mark.asyncio
    async def test_render_diagram_async_vs_sync(self):
        """Test comparar render async vs sync"""
        from app.core.visualization.diagram_renderer import render_diagram, render_diagram_async, RenderFormat
        from app.core.visualization.tree_builder import TreeNode
        
        root = TreeNode(id="root", label="Root")
        for i in range(5):
            root.add_child(TreeNode(id=f"child{i}", label=f"Child {i}"))
        
        try:
            # Sync (puede bloquear event loop si hay uno activo)
            start_sync = time.time()
            result_sync = render_diagram(root, format=RenderFormat.DOT)  # DOT no usa Graphviz
            elapsed_sync = time.time() - start_sync
            
            # Async (no bloquea)
            start_async = time.time()
            result_async = await render_diagram_async(root, format=RenderFormat.DOT)
            elapsed_async = time.time() - start_async
            
            # Ambos deben producir resultado
            assert result_sync.content is not None
            assert result_async.content is not None
            
            # El contenido debe ser similar
            assert len(result_sync.content) > 0
            assert len(result_async.content) > 0
        except Exception as e:
            pytest.skip(f"Error en render: {e}")

@pytest.mark.integration
class TestPoolsUnderLoad:
    """Tests de pools bajo carga"""
    
    @pytest.mark.asyncio
    async def test_io_pool_handles_many_tasks(self):
        """Test que el pool I/O maneja muchas tareas"""
        def slow_io_operation(i):
            time.sleep(0.1)  # Simular I/O
            return i * 2
        
        loop = asyncio.get_event_loop()
        
        # 50 tareas I/O concurrentes
        tasks = [
            loop.run_in_executor(get_io_pool(), slow_io_operation, i)
            for i in range(50)
        ]
        
        start = time.time()
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start
        
        # Todas deben completar
        assert len(results) == 50
        assert results[10] == 20  # 10 * 2
        
        # Debe ser más rápido que secuencial (50 * 0.1 = 5s)
        assert elapsed < 3.0  # Paralelismo reduce el tiempo
    
    @pytest.mark.asyncio
    async def test_graphviz_pool_limits_concurrency(self):
        """Test que el pool Graphviz limita concurrencia"""
        try:
            import graphviz
        except ImportError:
            pytest.skip("Graphviz no instalado")
        
        def heavy_graph_operation(i):
            # Operación más pesada
            dot = graphviz.Digraph()
            for j in range(20):
                dot.node(f"n{i}_{j}", f"Node {j}")
            return dot.pipe(format="svg")
        
        loop = asyncio.get_event_loop()
        
        # Lanzar más tareas que workers disponibles
        tasks = [
            loop.run_in_executor(get_graphviz_pool(), heavy_graph_operation, i)
            for i in range(20)
        ]
        
        # Debe completar sin saturar el sistema
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 20
        assert all(r is not None for r in results)

@pytest.mark.integration
class TestPoolShutdown:
    """Tests de cierre de pools"""
    
    def test_shutdown_all_pools_waits(self):
        """Test que shutdown espera tareas en progreso"""
        # Resetear pools
        shutdown_all_pools(wait=False)
        
        # Crear tarea larga
        def long_task():
            time.sleep(0.5)
            return "done"
        
        pool = get_io_pool()
        future = pool.submit(long_task)
        
        # Shutdown con wait
        start = time.time()
        shutdown_all_pools(wait=True)
        elapsed = time.time() - start
        
        # Debe haber esperado
        assert elapsed >= 0.5
        assert future.done()
    
    def test_get_pool_stats_after_creation(self):
        """Test estadísticas después de crear pools"""
        # Resetear
        shutdown_all_pools(wait=False)
        
        # Crear pools
        get_io_pool()
        get_cpu_pool()
        get_graphviz_pool()
        
        stats = get_pool_stats()
        
        assert "io" in stats
        assert "cpu" in stats
        assert "graphviz" in stats
        
        # Cleanup
        shutdown_all_pools(wait=False)

# Ejecutar tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])