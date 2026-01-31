# Módulo de Profiling - Complexity Analyzer

Sistema completo de profiling de performance para monitorear y optimizar el rendimiento del backend.

---

## Tabla de Contenidos

1. [Descripción General](#descripción-general)
2. [Arquitectura](#arquitectura)
3. [Componentes](#componentes)
4. [Uso](#uso)
5. [API Reference](#api-reference)
6. [Ejemplos](#ejemplos)
7. [Integración](#integración)
8. [Testing](#testing)
9. [Best Practices](#best-practices)

---

## Descripción General

El módulo de profiling proporciona herramientas para medir y monitorear la performance del sistema en tres dimensiones:

### Componentes Principales

| Componente | Responsabilidad | Métricas |
|------------|----------------|----------|
| **ExecutionTimer** | Timing de operaciones | Tiempo de ejecución, estadísticas |
| **MemoryProfiler** | Profiling de memoria | Consumo de memoria, memory leaks |
| **PerformanceMonitor** | Monitor integral | Timing + Memoria + Niveles de performance |

### Características

- **Decoradores**: Profiling no-invasivo con `@timed()` y `@monitored()`
- **Context Managers**: Profiling de bloques de código con `with`
- **Estadísticas**: Métricas agregadas por operación y módulo
- **Reportes**: Exportación en JSON para análisis posterior
- **Niveles de Performance**: Clasificación automática (Excellent → Critical)
- **Memory Leak Detection**: Detección de posibles fugas de memoria

---

## Arquitectura

```
profiling/
├── __init__.py              # Exports principales
├── execution_timer.py       # Timer de ejecución
├── memory_profiler.py       # Profiler de memoria
└── performance_monitor.py   # Monitor integral
```

**Dependencias:**

```
PerformanceMonitor
    ├─→ ExecutionTimer
    └─→ MemoryProfiler
```

---

## Componentes

### 1. ExecutionTimer - Timer de Ejecución

Mide tiempos de ejecución y mantiene estadísticas.

**Archivo:** [execution_timer.py](../../app/profiling/execution_timer.py)

**Características:**
- Decoradores `@timed()`
- Context manager `with time_block()`
- Estadísticas acumulativas
- Exportación de resultados

```python
from app.profiling import ExecutionTimer, timed, time_block

# Opción 1: Decorador
@timed()
def process_data():
    # código a medir
    pass

# Opción 2: Context manager
timer = ExecutionTimer()
with timer.time("my_operation") as result:
    # código a medir
    pass

print(f"Tiempo: {result.duration_readable}")
```

**Métodos principales:**
- `time(name)`: Context manager para timing
- `timed()`: Decorador para funciones
- `get_stats(name)`: Obtener estadísticas
- `print_summary()`: Imprimir resumen
- `export_stats(path)`: Exportar a JSON

### 2. MemoryProfiler - Profiler de Memoria

Monitorea uso de memoria y detecta leaks.

**Archivo:** [memory_profiler.py](../../app/profiling/memory_profiler.py)

**Características:**
- Snapshots de memoria
- Diferencias entre snapshots
- Detección de memory leaks
- Soporte para `tracemalloc`

```python
from app.profiling import MemoryProfiler, profile_memory

# Opción 1: Context manager global
with profile_memory("allocate_data"):
    large_list = [i for i in range(1000000)]

# Opción 2: Profiler personalizado
profiler = MemoryProfiler(use_tracemalloc=True)

with profiler.profile("my_operation") as diff:
    # código a perfilar
    pass

print(f"Memoria: {diff.current_diff_readable}")
if diff.has_leak:
    print("⚠️ Posible memory leak detectado")
```

**Métodos principales:**
- `take_snapshot()`: Tomar snapshot de memoria
- `profile(name)`: Context manager para profiling
- `profile_function()`: Decorador
- `detect_leaks()`: Detectar memory leaks
- `print_summary()`: Imprimir resumen
- `export_report(path)`: Exportar a JSON

### 3. PerformanceMonitor - Monitor Integral

Combina timing y memoria para análisis completo.

**Archivo:** [performance_monitor.py](../../app/profiling/performance_monitor.py)

**Características:**
- Métricas combinadas (tiempo + memoria)
- Niveles de performance automáticos
- Agregación por módulo
- Detección de operaciones lentas
- Reportes completos

```python
from app.profiling import get_performance_monitor

monitor = get_performance_monitor(enable_memory=True)

with monitor.monitor("parse_algorithm", module="parser") as metrics:
    ast = parser.parse(code)

print(f"Tiempo: {metrics.execution_time_ms:.2f}ms")
print(f"Memoria: {metrics.memory_delta_mb:.2f}MB")
print(f"Nivel: {metrics.performance_level.value}")

# Generar reporte
monitor.generate_report(Path("performance_report.json"))
```

**Métodos principales:**
- `monitor(name, module)`: Context manager
- `monitored()`: Decorador
- `get_metrics()`: Obtener métricas
- `get_module_performance()`: Performance por módulo
- `get_slow_operations()`: Operaciones lentas
- `print_summary()`: Imprimir resumen
- `generate_report(path)`: Generar reporte JSON

---

## Niveles de Performance

El monitor clasifica automáticamente las operaciones:

| Nivel | Tiempo | Memoria | Descripción |
|-------|--------|---------|-------------|
| **EXCELLENT** 🟢 | < 100ms | < 10MB | Performance óptima |
| **GOOD** 🟡 | < 500ms | < 50MB | Performance aceptable |
| **ACCEPTABLE** 🟠 | < 2s | < 200MB | Aceptable pero mejorable |
| **SLOW** 🔴 | < 10s | < 500MB | Requiere optimización |
| **CRITICAL** 🚨 | >= 10s | >= 500MB | Crítico, acción inmediata |

---

## Uso

### Uso Básico - Decoradores

```python
from app.profiling import timed

@timed()
def process_algorithm(code):
    ast = parser.parse(code)
    result = analyzer.analyze(ast)
    return result
```

### Uso Básico - Context Managers

```python
from app.profiling import time_block, profile_memory

# Solo timing
with time_block("parse_code"):
    ast = parser.parse(code)

# Solo memoria
with profile_memory("analyze_complexity"):
    result = analyzer.analyze(ast)
```

### Uso Avanzado - Monitor Integral

```python
from app.profiling import get_performance_monitor

monitor = get_performance_monitor(enable_memory=True)

# Profiling completo
with monitor.monitor("full_analysis", module="orchestrator") as metrics:
    # Parse
    with monitor.monitor("parse", module="parser"):
        ast = parser.parse(code)
    
    # Analyze
    with monitor.monitor("analyze", module="analyzer"):
        result = analyzer.analyze(ast)
    
    # Patterns
    with monitor.monitor("patterns", module="patterns"):
        patterns = detector.detect(ast)

# Ver resultados
print(f"Tiempo total: {metrics.execution_time_ms:.2f}ms")
print(f"Nivel: {metrics.performance_level.value}")

# Performance por módulo
for module_name in ["parser", "analyzer", "patterns"]:
    module_perf = monitor.get_module_performance(module_name)
    print(f"{module_name}: {module_perf.avg_execution_time_ms:.2f}ms")
```

### Habilitar Profiling Global

```python
from app.profiling import enable_profiling

# Al inicio de la aplicación
enable_profiling(
    enable_timing=True,
    enable_memory=True,
    use_tracemalloc=False  # True para más detalle (más lento)
)

# Usar decoradores globales
from app.profiling import timed

@timed()
def my_function():
    pass
```

### Generar Reportes

```python
from app.profiling import (
    print_profiling_summary,
    generate_profiling_report,
)
from pathlib import Path

# Imprimir resumen en consola
print_profiling_summary()

# Exportar a JSON
generate_profiling_report(Path("logs/profiling_report.json"))
```

---

## API Reference

### ExecutionTimer

```python
class ExecutionTimer:
    def __init__(self, enabled: bool = True)
    
    @contextmanager
    def time(
        self,
        name: str,
        module: Optional[str] = None,
        log_result: bool = True
    ) -> TimingResult
    
    def timed(
        self,
        name: Optional[str] = None,
        module: Optional[str] = None,
        log_result: bool = True
    ) -> Callable
    
    def get_stats(self, name: str) -> Optional[TimingStats]
    def get_all_stats(self) -> Dict[str, TimingStats]
    def reset_stats(self, name: Optional[str] = None)
    def print_summary(self, top_n: int = 10)
    def export_stats(self, output_path: Path)
```

### MemoryProfiler

```python
class MemoryProfiler:
    def __init__(
        self,
        enabled: bool = True,
        use_tracemalloc: bool = False,
        top_allocations: int = 10
    )
    
    def take_snapshot(
        self,
        operation: Optional[str] = None,
        module: Optional[str] = None
    ) -> MemorySnapshot
    
    @contextmanager
    def profile(
        self,
        operation: str,
        module: Optional[str] = None,
        log_result: bool = True
    ) -> MemoryDiff
    
    def profile_function(
        self,
        operation: Optional[str] = None,
        module: Optional[str] = None,
        log_result: bool = True
    ) -> Callable
    
    def get_diffs(self, operation: str) -> List[MemoryDiff]
    def detect_leaks(self, threshold_mb: float = 1.0) -> Dict[str, List[MemoryDiff]]
    def print_summary()
    def export_report(self, output_path: Path)
    def reset()
    def stop()
```

### PerformanceMonitor

```python
class PerformanceMonitor:
    def __init__(
        self,
        enabled: bool = True,
        enable_timing: bool = True,
        enable_memory: bool = False,
        use_tracemalloc: bool = False
    )
    
    @contextmanager
    def monitor(
        self,
        operation: str,
        module: Optional[str] = None,
        log_result: bool = True
    ) -> PerformanceMetrics
    
    def monitored(
        self,
        operation: Optional[str] = None,
        module: Optional[str] = None,
        log_result: bool = True
    ) -> Callable
    
    def get_metrics(
        self,
        operation: Optional[str] = None,
        module: Optional[str] = None
    ) -> List[PerformanceMetrics]
    
    def get_module_performance(self, module: str) -> Optional[ModulePerformance]
    def get_slow_operations(self, threshold_ms: Optional[float] = None) -> List[PerformanceMetrics]
    def get_memory_intensive_operations(self, threshold_mb: float = 50.0) -> List[PerformanceMetrics]
    def print_summary()
    def generate_report(self, output_path: Path)
    def reset()
    def stop()
```

---

## Ejemplos

### Ejemplo 1: Profiling de Parsing

```python
from app.profiling import get_performance_monitor
from app.core.parser import parse_pseudocode

monitor = get_performance_monitor(enable_memory=True)

code = """
algorithm bubbleSort(A[1..n])
begin
    for i ← 1 to n-1 do
        for j ← 1 to n-i do
            if (A[j] > A[j+1]) then
                swap(A[j], A[j+1])
end
"""

with monitor.monitor("parse_bubble_sort", module="parser") as metrics:
    ast = parse_pseudocode(code)

print(f"Tiempo: {metrics.execution_time_ms:.2f}ms")
print(f"Memoria: {metrics.memory_delta_mb:.2f}MB")
print(f"Performance: {metrics.performance_level.value}")
```

### Ejemplo 2: Profiling de Análisis Completo

```python
from app.profiling import get_performance_monitor
from app.services import AnalysisOrchestrator

monitor = get_performance_monitor(enable_memory=True)

code = "..."  # Algoritmo

with monitor.monitor("complete_analysis", module="orchestrator") as metrics:
    orchestrator = AnalysisOrchestrator()
    result = await orchestrator.analyze_complete(code)

# Ver métricas
print(f"Tiempo total: {metrics.execution_time_ms:.2f}ms")
print(f"Nivel: {metrics.performance_level.value}")

# Ver performance por módulo
for module in ["parser", "analyzer", "patterns"]:
    perf = monitor.get_module_performance(module)
    if perf:
        print(f"{module}: {perf.avg_execution_time_ms:.2f}ms")
```

### Ejemplo 3: Detectar Operaciones Lentas

```python
from app.profiling import get_performance_monitor

monitor = get_performance_monitor()

# Ejecutar varias operaciones
# ...

# Detectar operaciones lentas
slow_ops = monitor.get_slow_operations(threshold_ms=500)

print(f"Operaciones lentas (>500ms): {len(slow_ops)}")
for op in slow_ops:
    print(f"  - {op.operation}: {op.execution_time_ms:.2f}ms")
    print(f"    Nivel: {op.performance_level.value}")
    if op.warnings:
        print(f"    Warnings: {', '.join(op.warnings)}")
```

### Ejemplo 4: Detectar Memory Leaks

```python
from app.profiling import get_memory_profiler

profiler = get_memory_profiler(use_tracemalloc=True)

# Ejecutar operación sospechosa varias veces
for i in range(10):
    with profiler.profile("potential_leak"):
        # código que puede tener leak
        data = process_large_data()

# Detectar leaks
leaks = profiler.detect_leaks(threshold_mb=1.0)

if leaks:
    print("⚠️ Memory leaks detectados:")
    for operation, diffs in leaks.items():
        print(f"  {operation}: {len(diffs)} ocurrencias")
        avg_leak = sum(d.current_diff_mb for d in diffs) / len(diffs)
        print(f"    Promedio: {avg_leak:.2f}MB por ejecución")
```

---

## Integración

### Con FastAPI

```python
from fastapi import FastAPI
from app.profiling import get_performance_monitor

app = FastAPI()
monitor = get_performance_monitor(enable_memory=True)

@app.post("/analyze")
@monitor.monitored(module="api")
async def analyze_algorithm(code: str):
    with monitor.monitor("parse", module="parser"):
        ast = parser.parse(code)
    
    with monitor.monitor("analyze", module="analyzer"):
        result = analyzer.analyze(ast)
    
    return result

@app.get("/profiling/stats")
async def get_profiling_stats():
    return {
        "modules": {
            module: perf.to_dict()
            for module, perf in monitor.get_all_module_performance().items()
        }
    }
```

### Con Servicios

```python
from app.profiling import get_performance_monitor

class AlgorithmService:
    def __init__(self):
        self.monitor = get_performance_monitor()
    
    @monitor.monitored(module="algorithm_service")
    async def create(self, request):
        with self.monitor.monitor("validate", module="algorithm_service"):
            # validación
            pass
        
        with self.monitor.monitor("save", module="algorithm_service"):
            # guardar
            pass
```

---

## Testing

### Ejecutar Tests

```bash
# Tests del módulo profiling
pytest tests/unit/test_profiling.py -v

# Con coverage
pytest tests/unit/test_profiling.py --cov=app/profiling
```

### Tests Importantes

```python
def test_timer_context_manager()
def test_timed_decorator()
def test_multiple_executions()
def test_profiler_memory_diff()
def test_monitor_performance_levels()
def test_detect_slow_operations()
def test_module_performance()
```

---

## Best Practices

### 1. Habilitar solo en desarrollo

```python
from app.core.config import settings
from app.profiling import enable_profiling

if settings.ENABLE_PROFILING:
    enable_profiling(
        enable_timing=True,
        enable_memory=settings.PROFILE_MEMORY
    )
```

### 2. Usar niveles apropiados

- **Producción**: Solo timing básico
- **Staging**: Timing + memoria (sin tracemalloc)
- **Desarrollo**: Timing + memoria + tracemalloc

### 3. Exportar reportes periódicamente

```python
import schedule

def export_profiling():
    from app.profiling import generate_profiling_report
    from datetime import datetime
    
    filename = f"profiling_{datetime.now():%Y%m%d_%H%M%S}.json"
    generate_profiling_report(Path(f"logs/{filename}"))

# Cada hora
schedule.every().hour.do(export_profiling)
```

### 4. Monitorear módulos críticos

```python
# Parser, Analyzer, Patterns son críticos
CRITICAL_MODULES = ["parser", "analyzer", "patterns"]

monitor = get_performance_monitor(enable_memory=True)

# Revisar periódicamente
for module in CRITICAL_MODULES:
    perf = monitor.get_module_performance(module)
    if perf and perf.avg_execution_time_ms > 500:
        logger.warning(f"{module} tiene performance degradada")
```

---

## Limitaciones

| Limitación | Impacto | Mitigación |
|------------|---------|------------|
| Overhead de profiling | 1-5% en timing | Deshabilitar en producción |
| tracemalloc es lento | 10-50% overhead | Usar solo en debugging |
| Memory leaks falsos positivos | GC puede no ejecutarse | Usar `gc.collect()` antes de snapshots |

---

## Próximos Pasos

1. Integrar con Prometheus para métricas en tiempo real
2. Agregar flamegraphs de CPU profiling
3. Dashboard web para visualización de métricas
4. Alertas automáticas por performance degradada
5. Profiling de queries a base de datos

---

## Referencias

- **Python profiling**: https://docs.python.org/3/library/profile.html
- **tracemalloc**: https://docs.python.org/3/library/tracemalloc.html
- **memory_profiler**: https://pypi.org/project/memory-profiler/

---

**Última actualización:** 2026-01-30

**Versión del módulo:** 1.0.0

---

**Documentos relacionados:**

- [GETTING_STARTED.md](../GETTING_STARTED.md) - Guía de inicio
- [DEBUGGING.md](../DEBUGGING.md) - Guía de debugging
- [PARSER.md](PARSER.md) - Módulo de parsing
- [ANALYZER.md](ANALYZER.md) - Módulo de análisis