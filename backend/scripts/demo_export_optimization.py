#!/usr/bin/env python3
"""
Demo de Exportación y Optimización de Visualizaciones
Muestra las capacidades de batch export y optimización
"""
import asyncio
from pathlib import Path
from typing import List
import time

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
from app.core.parser.pseudocode_parser import PseudocodeParser
from app.core.analyzer.recurrence.recurrence_builder import RecurrenceBuilder
from app.utils.logger import get_logger

logger = get_logger(__name__)

# === ALGORITMOS DE PRUEBA ===

FIBONACCI_CODE = """
ALGORITHM Fibonacci(n)
    IF n <= 1 THEN
        RETURN n
    ENDIF
    
    RETURN Fibonacci(n-1) + Fibonacci(n-2)
END
"""

QUICKSORT_CODE = """
ALGORITHM QuickSort(arr, low, high)
    IF low < high THEN
        pivot_index = Partition(arr, low, high)
        QuickSort(arr, low, pivot_index - 1)
        QuickSort(arr, pivot_index + 1, high)
    ENDIF
END

ALGORITHM Partition(arr, low, high)
    pivot = arr[high]
    i = low - 1
    
    FOR j = low TO high - 1 DO
        IF arr[j] < pivot THEN
            i = i + 1
            SWAP arr[i], arr[j]
        ENDIF
    ENDFOR
    
    SWAP arr[i + 1], arr[high]
    RETURN i + 1
END
"""

MERGE_SORT_CODE = """
ALGORITHM MergeSort(arr, left, right)
    IF left < right THEN
        mid = (left + right) / 2
        MergeSort(arr, left, mid)
        MergeSort(arr, mid + 1, right)
        Merge(arr, left, mid, right)
    ENDIF
END

ALGORITHM Merge(arr, left, mid, right)
    n1 = mid - left + 1
    n2 = right - mid
    
    CREATE L[n1], R[n2]
    
    FOR i = 0 TO n1 - 1 DO
        L[i] = arr[left + i]
    ENDFOR
    
    FOR j = 0 TO n2 - 1 DO
        R[j] = arr[mid + 1 + j]
    ENDFOR
    
    i = 0
    j = 0
    k = left
    
    WHILE i < n1 AND j < n2 DO
        IF L[i] <= R[j] THEN
            arr[k] = L[i]
            i = i + 1
        ELSE
            arr[k] = R[j]
            j = j + 1
        ENDIF
        k = k + 1
    ENDWHILE
END
"""

BINARY_SEARCH_TREE_CODE = """
ALGORITHM BSTInsert(root, key)
    IF root IS NULL THEN
        RETURN CreateNode(key)
    ENDIF
    
    IF key < root.key THEN
        root.left = BSTInsert(root.left, key)
    ELSE IF key > root.key THEN
        root.right = BSTInsert(root.right, key)
    ENDIF
    
    RETURN root
END

ALGORITHM BSTSearch(root, key)
    IF root IS NULL OR root.key = key THEN
        RETURN root
    ENDIF
    
    IF key < root.key THEN
        RETURN BSTSearch(root.left, key)
    ELSE
        RETURN BSTSearch(root.right, key)
    ENDIF
END
"""

GRAPH_DFS_CODE = """
ALGORITHM DFS(graph, start, visited)
    visited[start] = TRUE
    PRINT start
    
    FOR each neighbor IN graph[start] DO
        IF NOT visited[neighbor] THEN
            DFS(graph, neighbor, visited)
        ENDIF
    ENDFOR
END
"""

async def demo_basic_batch_export():
    """Demo 1: Exportación batch básica"""
    print("DEMO 1: Exportación Batch Básica")
    
    parser = PseudocodeParser()
    recurrence_builder = RecurrenceBuilder()
    
    # Parsear algoritmos
    algorithms = {
        'fibonacci': FIBONACCI_CODE,
        'quicksort': QUICKSORT_CODE,
        'merge_sort': MERGE_SORT_CODE
    }
    
    tasks: List[ExportTask] = []
    output_dir = Path("data/exports/demo_batch")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Crear tareas de exportación
    for name, code in algorithms.items():
        try:
            ast = parser.parse(code)
            recurrence = recurrence_builder.build_recurrence(ast)
            
            # Tarea para árbol de recursión
            tasks.append(ExportTask(
                id=f"{name}_tree",
                visualization_type='recursion_tree',
                data={
                    'recurrence': recurrence,
                    'base_cases': {'n <= 1': 'O(1)'}
                },
                format=ExportFormat.SVG,
                output_path=output_dir / f"{name}_tree.svg",
                priority=1
            ))
            
            # Tarea para flujo de ejecución
            tasks.append(ExportTask(
                id=f"{name}_flow",
                visualization_type='execution_flow',
                data={'ast_node': ast},
                format=ExportFormat.PNG,
                output_path=output_dir / f"{name}_flow.png",
                priority=2
            ))
            
        except Exception as e:
            logger.error(f"Error parseando {name}: {e}")
    
    # Configurar batch exporter
    config = BatchExportConfig(
        mode=ProcessingMode.THREADED,
        max_workers=4,
        chunk_size=5
    )
    
    exporter = BatchExporter(config)
    
    # Callback de progreso
    def progress_callback(current: int, total: int):
        percent = (current / total) * 100
        print(f"Progreso: {current}/{total} ({percent:.1f}%)")
    
    # Exportar batch
    start_time = time.time()
    results = await exporter.export_batch(tasks, progress_callback)
    elapsed = time.time() - start_time
    
    # Mostrar resultados
    print(f"\nExportación completada en {elapsed:.2f}s")
    print(f"Exitosas: {sum(1 for r in results if r.success)}/{len(results)}")
    print(f"Fallidas: {sum(1 for r in results if not r.success)}/{len(results)}")
    
    # Estadísticas
    stats = exporter.get_stats()
    print(f"\nEstadísticas:")
    print(f"  - Tiempo promedio por tarea: {stats['average_time']:.2f}s")
    print(f"  - Tasa de éxito: {stats['success_rate']:.1f}%")
    print(f"  - Tamaño total generado: {stats['total_size'] / 1024:.1f} KB")
    
    # Listar archivos generados
    print(f"\nArchivos generados en: {output_dir}")
    for result in results:
        if result.success:
            print(f"  ✓ {result.output_path.name}")
        else:
            print(f"  ✗ {result.task_id}: {result.error}")


async def demo_optimization():
    """Demo 2: Optimización de grafos grandes"""
    print("DEMO 2: Optimización de Grafos Grandes")
    
    # Crear un grafo grande sintético
    print("Generando grafo grande (1000 nodos)...")
    
    nodes = []
    edges = []
    
    # Árbol binario grande
    for i in range(1000):
        nodes.append({
            'id': f'node_{i}',
            'label': f'N{i}',
            'level': i // 100,
            'is_root': i == 0
        })
        
        # Crear aristas (árbol binario)
        if i > 0:
            parent = (i - 1) // 2
            edges.append((f'node_{parent}', f'node_{i}', {'type': 'tree_edge'}))
        
        # Añadir algunas aristas adicionales para densidad
        if i > 5 and i % 7 == 0:
            target = i - 5
            edges.append((f'node_{i}', f'node_{target}', {'type': 'cross_edge'}))
    
    print(f"Grafo original: {len(nodes)} nodos, {len(edges)} aristas")
    
    # Probar diferentes niveles de optimización
    levels = [
        OptimizationLevel.NONE,
        OptimizationLevel.BASIC,
        OptimizationLevel.MODERATE,
        OptimizationLevel.AGGRESSIVE
    ]
    
    for level in levels:
        print(f"Optimización: {level.value.upper()}")
        
        config = OptimizationConfig(
            level=level,
            max_nodes=500,
            max_edges=1500,
            enable_clustering=True,
            enable_simplification=True
        )
        
        optimizer = VisualizationOptimizer(config)
        
        start_time = time.time()
        opt_nodes, opt_edges, metadata = optimizer.optimize_graph(
            nodes, edges
        )
        elapsed = time.time() - start_time
        
        print(f"Tiempo: {elapsed*1000:.1f}ms")
        print(f"Nodos: {len(nodes)} → {len(opt_nodes)} "
              f"({metadata['reduction_ratio']['nodes']*100:.1f}% reducción)")
        print(f"Aristas: {len(edges)} → {len(opt_edges)} "
              f"({metadata['reduction_ratio']['edges']*100:.1f}% reducción)")
        print(f"Optimizaciones aplicadas: {', '.join(metadata['optimizations_applied'])}")
        
        # Métricas del grafo optimizado
        opt_metrics = metadata['optimized_metrics']
        print(f"\nMétricas optimizadas:")
        print(f"  - Densidad: {opt_metrics.density:.3f}")
        print(f"  - Grado promedio: {opt_metrics.avg_degree:.1f}")
        print(f"  - Complejidad estimada: {opt_metrics.estimated_complexity}")
        
        # Recomendaciones
        recommendations = optimizer.get_optimization_recommendations(opt_metrics)
        if recommendations:
            print(f"\nRecomendaciones:")
            for rec in recommendations:
                print(f"  • {rec}")


async def demo_advanced_batch():
    """Demo 3: Batch avanzado con múltiples formatos"""
    print("DEMO 3: Batch Avanzado - Múltiples Formatos")

    parser = PseudocodeParser()
    
    # Parsear algoritmo complejo
    ast = parser.parse(QUICKSORT_CODE)
    
    output_dir = Path("data/exports/demo_advanced")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Crear tareas para todos los formatos
    formats = [
        ExportFormat.SVG,
        ExportFormat.PNG,
        ExportFormat.DOT,
        ExportFormat.MERMAID,
        ExportFormat.JSON
    ]
    
    tasks = []
    for fmt in formats:
        tasks.append(ExportTask(
            id=f"quicksort_{fmt.value}",
            visualization_type='execution_flow',
            data={'ast_node': ast},
            format=fmt,
            output_path=output_dir / f"quicksort.{fmt.value}"
        ))
    
    # Configurar para procesamiento asíncrono
    config = BatchExportConfig(
        mode=ProcessingMode.ASYNC,
        max_workers=3,
        optimize_output=True
    )
    
    exporter = BatchExporter(config)
    
    print(f"Exportando QuickSort en {len(formats)} formatos...")
    
    results = await exporter.export_batch(tasks)
    
    print(f"\nExportación completada")
    for result in results:
        if result.success:
            size_kb = result.file_size / 1024 if result.file_size else 0
            print(f"  ✓ {result.output_path.name} "
                  f"({size_kb:.1f} KB, {result.processing_time:.2f}s)")
        else:
            print(f"  ✗ {result.task_id}: {result.error}")

async def demo_recursion_tree_optimization():
    """Demo 4: Optimización específica para árboles de recursión"""
    print("DEMO 4: Optimización de Árboles de Recursión")
    
    # Crear árbol de recursión grande (Fibonacci)
    def create_fib_tree(n: int, depth: int = 0) -> dict:
        """Crea árbol de recursión de Fibonacci"""
        if n <= 1 or depth > 15:
            return {
                'id': f'fib_{n}_{depth}',
                'value': n,
                'depth': depth,
                'children': []
            }
        
        return {
            'id': f'fib_{n}_{depth}',
            'value': n,
            'depth': depth,
            'children': [
                create_fib_tree(n-1, depth+1),
                create_fib_tree(n-2, depth+1)
            ]
        }
    
    print("Generando árbol de recursión Fibonacci(10)...")
    tree_data = {'root': create_fib_tree(10)}
    
    # Contar nodos
    def count_nodes(node):
        if not node.get('children'):
            return 1
        return 1 + sum(count_nodes(child) for child in node['children'])
    
    original_size = count_nodes(tree_data['root'])
    print(f"Árbol original: {original_size} nodos")
    
    # Optimizar con diferentes profundidades máximas
    optimizer = VisualizationOptimizer(
        OptimizationConfig(level=OptimizationLevel.AGGRESSIVE)
    )
    
    for max_depth in [5, 8, 10]:
        print(f"Max Depth: {max_depth}")
        
        optimized = optimizer.optimize_recursion_tree(
            tree_data.copy(),
            max_depth=max_depth
        )
        
        optimized_size = count_nodes(optimized['root'])
        reduction = (1 - optimized_size / original_size) * 100
        
        print(f"Nodos: {original_size} → {optimized_size} ({reduction:.1f}% reducción)")

async def demo_comparison():
    """Demo 5: Comparación de rendimiento"""
    print("DEMO 5: Comparación de Modos de Procesamiento")
    
    parser = PseudocodeParser()
    
    # Preparar 20 tareas
    algorithms = [
        ('fib', FIBONACCI_CODE),
        ('quick', QUICKSORT_CODE),
        ('merge', MERGE_SORT_CODE),
        ('bst', BINARY_SEARCH_TREE_CODE),
        ('dfs', GRAPH_DFS_CODE)
    ]
    
    output_dir = Path("data/exports/demo_comparison")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    tasks = []
    for i, (name, code) in enumerate(algorithms * 4):  # 20 tareas
        try:
            ast = parser.parse(code)
            tasks.append(ExportTask(
                id=f"{name}_{i}",
                visualization_type='execution_flow',
                data={'ast_node': ast},
                format=ExportFormat.SVG,
                output_path=output_dir / f"{name}_{i}.svg"
            ))
        except:
            pass
    
    # Probar diferentes modos
    modes = [
        ProcessingMode.SEQUENTIAL,
        ProcessingMode.THREADED,
        ProcessingMode.ASYNC
    ]
    
    results_comparison = {}
    
    for mode in modes:
        print(f"Modo: {mode.value.upper()}")
        
        config = BatchExportConfig(
            mode=mode,
            max_workers=4
        )
        
        exporter = BatchExporter(config)
        
        start_time = time.time()
        results = await exporter.export_batch(tasks)
        elapsed = time.time() - start_time
        
        successful = sum(1 for r in results if r.success)
        
        results_comparison[mode.value] = {
            'time': elapsed,
            'successful': successful,
            'avg_time': elapsed / len(tasks)
        }
        
        print(f"Tiempo total: {elapsed:.2f}s")
        print(f"Tiempo promedio: {elapsed/len(tasks)*1000:.1f}ms/tarea")
        print(f"Exitosas: {successful}/{len(tasks)}")
    
    # Comparación final
    print("COMPARACIÓN FINAL")
    
    baseline = results_comparison['sequential']['time']
    
    for mode, data in results_comparison.items():
        speedup = baseline / data['time']
        print(f"\n{mode.upper()}")
        print(f"  Tiempo: {data['time']:.2f}s")
        print(f"  Speedup: {speedup:.2f}x")
        print(f"  Tasa éxito: {data['successful']}/{len(tasks)}")

async def main():
    """Ejecuta todos los demos"""
    print("DEMO: EXPORTACIÓN Y OPTIMIZACIÓN DE VISUALIZACIONES")
    
    demos = [
        ("Exportación Batch Básica", demo_basic_batch_export),
        ("Optimización de Grafos", demo_optimization),
        ("Batch Avanzado", demo_advanced_batch),
        ("Optimización de Árboles", demo_recursion_tree_optimization),
        ("Comparación de Rendimiento", demo_comparison)
    ]
    
    for i, (name, demo_func) in enumerate(demos, 1):
        try:
            await demo_func()
        except Exception as e:
            logger.error(f"Error en demo {name}: {e}", exc_info=True)
        
        if i < len(demos):
            input("Presiona Enter para continuar al siguiente demo...")

if __name__ == "__main__":
    asyncio.run(main())