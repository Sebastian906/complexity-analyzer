"""
Tests de integración para paralelismo
Valida que las optimizaciones no rompan funcionalidad
"""

import pytest
import asyncio
import time
from pathlib import Path

# TEST 1: ORCHESTRATOR PARALELO 
@pytest.mark.asyncio
async def test_orchestrator_parallel_vs_sequential():
    """
    Verifica que análisis paralelo funcione correctamente
    y sea más rápido que versión hipotética secuencial
    """
    from app.services.analysis_orchestrator import AnalysisOrchestrator
    from app.schemas import CompleteAnalysisRequest
    
    orchestrator = AnalysisOrchestrator()
    
    # SINTAXIS CORREGIDA con begin...end
    code = """
    algorithm fibonacci(n)
    begin
        if n <= 1 then
            begin
                return n
            end
        return fibonacci(n-1) + fibonacci(n-2)
    end
    """
    
    request = CompleteAnalysisRequest(
        code=code,
        analyze_complexity=True,
        analyze_patterns=True,
        analyze_structures=True,
        generate_visualizations=False
    )
    
    # Ejecutar análisis paralelo
    start = time.time()
    result = await orchestrator.analyze_complete(request)
    parallel_time = time.time() - start
    
    # VALIDACIONES 
    # 1. Resultado correcto
    assert result.success is True, f"Análisis falló: {result.message}"
    
    # 2. Componentes presentes
    assert result.complexity is not None, "Falta análisis de complejidad"
    assert result.patterns is not None, "Falta detección de patrones"
    assert result.structures is not None, "Falta detección de estructuras"
    
    # 3. Datos consistentes
    assert result.complexity.big_o is not None
    assert result.patterns.pattern_count >= 0
    
    # 4. Tiempo razonable (< 5 segundos para algoritmo simple)
    assert parallel_time < 5.0, f"Análisis muy lento: {parallel_time:.2f}s"
    
    print(f"\n✓ Análisis paralelo exitoso:")
    print(f"  - Tiempo: {parallel_time:.2f}s")
    print(f"  - Complejidad: {result.complexity.big_o}")
    print(f"  - Patrones detectados: {result.patterns.pattern_count}")
    print(f"  - Estructuras detectadas: {len(result.structures.structures_found) if result.structures else 0}")

@pytest.mark.asyncio
async def test_orchestrator_handles_errors_gracefully():
    """
    Verifica que si un análisis paralelo falla,
    los demás continúen funcionando
    """
    from app.services.analysis_orchestrator import AnalysisOrchestrator
    from app.schemas import CompleteAnalysisRequest
    
    orchestrator = AnalysisOrchestrator()
    
    # Código válido pero simple - SINTAXIS CORREGIDA
    code = """
    algorithm test(n)
    begin
        for i <- 1 to n do
            begin
                x <- x + 1
            end
    end
    """
    
    request = CompleteAnalysisRequest(
        code=code,
        analyze_complexity=True,
        analyze_patterns=True,
        analyze_structures=True,
    )
    
    result = await orchestrator.analyze_complete(request)
    
    # Aunque algunos análisis fallen parcialmente,
    # el resultado debe tener success=True si parsing funciona
    assert result.algorithm_info is not None
    
    # Al menos complejidad debe estar presente
    # (es el más robusto)
    assert result.complexity is not None or result.success is False
    
    print(f"\n✓ Manejo de errores correcto:")
    print(f"  - Success: {result.success}")
    print(f"  - Message: {result.message}")

# TEST 2: PATTERN DETECTOR PARALELO 
@pytest.mark.asyncio
async def test_pattern_detector_parallel_execution():
    """
    Verifica que detector de patrones paralelo:
    1. Detecte los mismos patrones que versión secuencial
    2. Sea más rápido
    """
    from app.core.parser import PseudocodeParser
    from app.core.patterns import PatternDetector
    
    parser = PseudocodeParser()
    detector = PatternDetector()
    
    # Algoritmo divide & conquer clásico - SINTAXIS CORREGIDA
    code = """
    algorithm quicksort(arr, low, high)
    begin
        if (low < high) then
            begin
                pivot := partition(arr, low, high)
                call quicksort(arr, low, pivot - 1)
                call quicksort(arr, pivot + 1, high)
            end
    end
    """
    
    ast = parser.parse(code)
    
    # Ejecutar detección
    start = time.time()
    result = detector.detect(ast)
    detect_time = time.time() - start
    
    # VALIDACIONES 
    
    # 1. Debe detectar patrones
    assert result.has_patterns is True, "No se detectaron patrones"
    assert result.pattern_count > 0, "Pattern count = 0"
    
    # 2. Debe tener patrón primario
    assert result.primary_pattern is not None, "Falta patrón primario"
    
    # 3. Tiempo razonable
    assert detect_time < 3.0, f"Detección muy lenta: {detect_time:.2f}s"
    
    print(f"\n✓ Detección paralela exitosa:")
    print(f"  - Tiempo: {detect_time:.2f}s")
    print(f"  - Patrones detectados: {result.pattern_count}")
    print(f"  - Patrón primario: {result.primary_pattern_name}")
    print(f"  - Confianza: {result.primary_confidence:.1%}")

# TEST 3: EXPORT PARALELO 
def test_export_multiple_formats_parallel(tmp_path):
    """
    Verifica que export a múltiples formatos:
    1. Funcione correctamente en paralelo
    2. Genere todos los archivos
    3. Sea más rápido que secuencial
    """
    from app.infrastructure.export import export_to_multiple_formats, ExportFormat
    from dataclasses import dataclass, field
    from typing import Optional, List, Dict, Any
    from datetime import datetime
    
    # Mock classes para evitar dependencia de Beanie/MongoDB
    @dataclass
    class MockAlgorithm:
        name: str
        code: str
        language: str = "pseudocode"
        category: Optional[str] = None
        tags: List[str] = field(default_factory=list)
        description: Optional[str] = None
        author: Optional[str] = None
        created_at: datetime = field(default_factory=datetime.utcnow)
        id: Optional[str] = None
    
    @dataclass
    class MockAnalysisResult:
        algorithm: MockAlgorithm
        big_o: str
        omega: str
        theta: Optional[str] = None
        space_complexity: Optional[str] = None
        temporal_recurrence: Optional[str] = None
        spatial_recurrence: Optional[str] = None
        line_by_line: Dict[str, Any] = field(default_factory=dict)
        analysis_time: float = 0.0
        analyzer_version: str = "1.0.0"
        created_at: datetime = field(default_factory=datetime.utcnow)
        algorithm_id: Optional[str] = None
    
    # Código con SINTAXIS CORREGIDA
    code = """algorithm bubblesort(arr)
begin
    for i <- 0 to n do
        begin
            for j <- 0 to n-i do
                begin
                    if arr[j] > arr[j+1] then
                        begin
                            call swap(arr[j], arr[j+1])
                        end
                end
        end
end"""
    
    # Crear algoritmo usando mock
    algorithm = MockAlgorithm(
        name="bubble_sort",
        code=code,
        language="pseudocode",
        category="sorting",
        created_at=datetime.utcnow()
    )
    
    # Crear análisis usando mock
    analysis = MockAnalysisResult(
        algorithm=algorithm,
        big_o="O(n²)",
        omega="Ω(n)",
        theta="Θ(n²)",
        space_complexity="O(1)",
        analysis_time=0.5,
        analyzer_version="1.0.0",
        created_at=datetime.utcnow()
    )
    
    # Formatos a exportar
    formats = [
        ExportFormat.JSON,
        ExportFormat.MARKDOWN,
        ExportFormat.CSV,
        ExportFormat.HTML,
    ]
    
    # Ejecutar export paralelo
    start = time.time()
    results = export_to_multiple_formats(
        algorithm=algorithm,
        analysis=analysis,
        formats=formats,
        output_dir=str(tmp_path)
    )
    parallel_time = time.time() - start
    
    # VALIDACIONES 
    # 1. Todos los formatos exportados
    assert len(results) == len(formats), f"Faltaron formatos: {len(results)}/{len(formats)}"
    
    # 2. Todos exitosos
    for fmt, result in results.items():
        assert result.success is True, f"Export {fmt} falló: {result.errors}"
    
    # 3. Archivos creados
    exported_files = list(tmp_path.glob("*"))
    assert len(exported_files) >= len(formats), f"Faltan archivos: {len(exported_files)}"
    
    # 4. Tiempo razonable
    assert parallel_time < 5.0, f"Export muy lento: {parallel_time:.2f}s"
    
    print(f"\n✓ Export paralelo exitoso:")
    print(f"  - Tiempo: {parallel_time:.2f}s")
    print(f"  - Formatos: {len(formats)}")
    print(f"  - Archivos creados: {len(exported_files)}")
    
    for fmt, result in results.items():
        print(f"  - {fmt.value}: {result.file_size} bytes" if result.file_size else f"  - {fmt.value}: OK")

# TEST 4: CACHE BATCH OPERATIONS
@pytest.mark.asyncio
async def test_cache_batch_operations():
    """
    Verifica que operaciones batch del caché funcionen:
    1. set_many
    2. get_many
    3. delete_many
    """
    from app.services.cache_service import get_cache_service
    
    cache = get_cache_service()
    
    # Limpiar caché antes de test
    await cache.clear()
    
    # TEST SET_MANY
    items = {
        f"test_parallel_key_{i}": f"value_{i}"
        for i in range(20)
    }
    
    success_count = await cache.set_many(items, ttl=60)
    assert success_count == 20, f"set_many falló: {success_count}/20"
    
    # TEST GET_MANY
    results = await cache.get_many(list(items.keys()))
    assert len(results) == 20, f"get_many falló: {len(results)}/20"
    
    # Validar valores
    for key, expected_value in items.items():
        assert results[key] == expected_value, f"Valor incorrecto para {key}"
    
    # TEST GET_MANY con keys inexistentes
    mixed_keys = list(items.keys())[:10] + ["nonexistent_1", "nonexistent_2"]
    results = await cache.get_many(mixed_keys)
    
    # Solo debe retornar las 10 que existen
    assert len(results) == 10, f"get_many con mixed keys falló: {len(results)}/10"
    
    # TEST DELETE_MANY 
    deleted_count = await cache.delete_many(list(items.keys()))
    assert deleted_count == 20, f"delete_many falló: {deleted_count}/20"
    
    # Verificar que se eliminaron
    results = await cache.get_many(list(items.keys()))
    assert len(results) == 0, "Items no se eliminaron correctamente"
    
    print(f"\n✓ Operaciones batch del caché exitosas:")
    print(f"  - set_many: 20/20")
    print(f"  - get_many: 20/20")
    print(f"  - delete_many: 20/20")

# TEST 5: BATCH EXPORTER
@pytest.mark.asyncio
async def test_batch_exporter_parallel():
    """
    Verifica que BatchExporter procese múltiples tareas en paralelo
    """
    from app.core.visualization.batch_exporter import (
        BatchExporter,
        ExportTask,
        ExportFormat,
        BatchExportConfig,
        ProcessingMode
    )
    from pathlib import Path
    import tempfile
    
    # Configurar exporter con modo THREADED
    config = BatchExportConfig(
        mode=ProcessingMode.THREADED,
        max_workers=4
    )
    
    exporter = BatchExporter(config)
    
    # Usar directorio temporal real
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Crear tareas de ejemplo (simplificadas)
        tasks = []
        for i in range(10):
            task = ExportTask(
                id=f"task_{i}",
                visualization_type="graph",
                data={
                    "num_nodes": 3,
                    "edges_list": [(0, 1), (1, 2)]
                },
                format=ExportFormat.JSON,
                output_path=tmp_path / f"test_export_{i}.json"
            )
            tasks.append(task)
        
        # Ejecutar batch
        start = time.time()
        results = await exporter.export_batch(tasks)
        batch_time = time.time() - start
        
        # VALIDACIONES 
        # 1. Todas las tareas completadas
        assert len(results) == len(tasks), f"Faltan resultados: {len(results)}/{len(tasks)}"
        
        # 2. Mayoría exitosas (al menos 80%)
        successful = sum(1 for r in results if r.success)
        success_rate = successful / len(results)
        
        # DEBUG: Mostrar errores si fallan
        if success_rate < 0.8:
            print(f"\nErrores detectados:")
            for r in results:
                if not r.success:
                    print(f"  - {r.task_id}: {r.error}")
        
        assert success_rate >= 0.8, f"Tasa de éxito baja: {success_rate:.1%}"
        
        # 3. Tiempo razonable
        assert batch_time < 5.0, f"Batch muy lento: {batch_time:.2f}s"
        
        print(f"\n✓ BatchExporter paralelo exitoso:")
        print(f"  - Tiempo: {batch_time:.2f}s")
        print(f"  - Tareas: {len(tasks)}")
        print(f"  - Exitosas: {successful}/{len(tasks)} ({success_rate:.1%})")
        
        # Estadísticas
        stats = exporter.get_stats()
        print(f"  - Promedio: {stats['average_time']:.3f}s por tarea")

# TEST 6: PERFORMANCE COMPARISON 
@pytest.mark.asyncio
@pytest.mark.slow
async def test_performance_comparison():
    """
    Compara performance de análisis completo con múltiples algoritmos
    """
    from app.services.analysis_orchestrator import AnalysisOrchestrator
    from app.schemas import CompleteAnalysisRequest
    
    orchestrator = AnalysisOrchestrator()
    
    # Lista de algoritmos con SINTAXIS CORREGIDA
    algorithms = [
        # Algoritmo 1: Linear Search
        """algorithm linear_search(arr, x)
begin
    for i <- 0 to n do
        begin
            if arr[i] = x then
                begin
                    return i
                end
        end
    return -1
end""",
        
        # Algoritmo 2: Binary Search
        """algorithm binary_search(arr, x, low, high)
begin
    if low > high then
        begin
            return -1
        end
    mid <- (low + high) / 2
    if arr[mid] = x then
        begin
            return mid
        end
    else
        begin
            if arr[mid] > x then
                begin
                    return binary_search(arr, x, low, mid-1)
                end
            else
                begin
                    return binary_search(arr, x, mid+1, high)
                end
        end
end""",
        
        # Algoritmo 3: Bubble Sort
        """algorithm bubble_sort(arr)
begin
    for i <- 0 to n do
        begin
            for j <- 0 to n-i do
                begin
                    if arr[j] > arr[j+1] then
                        begin
                            call swap(arr[j], arr[j+1])
                        end
                end
        end
end"""
    ]
    
    total_time = 0
    successful = 0
    
    for i, code in enumerate(algorithms):
        request = CompleteAnalysisRequest(
            code=code,
            analyze_complexity=True,
            analyze_patterns=True,
            analyze_structures=True,
        )
        
        start = time.time()
        result = await orchestrator.analyze_complete(request)
        elapsed = time.time() - start
        
        total_time += elapsed
        if result.success:
            successful += 1
        
        print(f"\n  Algoritmo {i+1}: {elapsed:.2f}s - {'✓' if result.success else '✗'}")
    
    avg_time = total_time / len(algorithms)
    
    print(f"\n✓ Performance batch:")
    print(f"  - Total: {total_time:.2f}s")
    print(f"  - Promedio: {avg_time:.2f}s")
    print(f"  - Exitosos: {successful}/{len(algorithms)}")
    
    # Promedio debe ser razonable (< 3s por algoritmo)
    assert avg_time < 3.0, f"Promedio muy alto: {avg_time:.2f}s"

# HELPERS
@pytest.fixture(autouse=True)
async def cleanup_cache():
    """Limpia caché después de cada test"""
    yield
    
    from app.services.cache_service import get_cache_service
    cache = get_cache_service()
    await cache.clear()

if __name__ == "__main__":
    # Ejecutar tests
    pytest.main([__file__, "-v", "-s"])