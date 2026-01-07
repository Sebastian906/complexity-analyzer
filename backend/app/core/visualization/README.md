# Módulo de Visualización

Sistema completo de generación de visualizaciones gráficas para algoritmos y estructuras de datos.

## Contenido

- [Instalación](#instalación)
- [Inicio Rápido](#inicio-rápido)
- [Componentes](#componentes)
- [Ejemplos](#ejemplos)
- [API REST](#api-rest)

## Instalación

### Dependencias Requeridas

```bash
# Básicas (requeridas)
pip install networkx

# Graphviz (recomendado para renderizado avanzado)
pip install graphviz

# Opcionales
pip install matplotlib plotly
```

### Verificar Instalación

```python
from app.core.visualization import (
    generate_recursion_tree,
    generate_execution_flow,
    generate_graph,
    render_diagram
)

print("✓ Módulo de visualización instalado correctamente")
```

## Inicio Rápido

### Ejemplo 1: Árbol de Recursión

```python
from app.core.parser import parse_pseudocode
from app.core.visualization import generate_recursion_tree, render_diagram, RenderFormat

# Código del algoritmo
code = """
algorithm fibonacci(n)
begin
    if (n <= 1) then
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)
end
"""

# 1. Parsear
ast = parse_pseudocode(code)

# 2. Generar árbol
tree = generate_recursion_tree(ast, start_value=4)

# 3. Renderizar
svg = render_diagram(tree, format=RenderFormat.SVG)
mermaid = render_diagram(tree, format=RenderFormat.MERMAID)

print(f"Tipo de recursión: {tree.recursion_type}")
print(f"Total de llamadas: {tree.total_calls}")
print(f"Complejidad: {tree.total_work}")
```

### Ejemplo 2: Flujo de Ejecución

```python
from app.core.visualization import generate_execution_flow

code = """
algorithm bubbleSort(A[n])
begin
    for i := 1 to n - 1 do
    begin
        for j := 1 to n - i do
        begin
            if (A[j] > A[j + 1]) then
            begin
                temp := A[j]
                A[j] := A[j + 1]
                A[j + 1] := temp
            end
        end
    end
end
"""

ast = parse_pseudocode(code)
flow = generate_execution_flow(ast)

# Renderizar como diagrama de flujo Mermaid
mermaid_flow = render_diagram(flow, format=RenderFormat.MERMAID)
print(mermaid_flow.content)
```

### Ejemplo 3: Grafos de Estructuras

```python
from app.core.visualization import generate_graph, LayoutType

# Árbol binario
tree = generate_graph(
    structure_type="tree",
    values=[50, 30, 70, 20, 40, 60, 80],
    layout=LayoutType.HIERARCHICAL
)

# Grafo dirigido
graph = generate_graph(
    structure_type="graph",
    num_nodes=6,
    edges_list=[(0,1), (0,2), (1,3), (2,4), (3,5), (4,5)],
    directed=True,
    layout=LayoutType.SPRING
)

# Lista enlazada
linked_list = generate_graph(
    structure_type="linked_list",
    values=[10, 20, 30, 40, 50]
)

# Renderizar
tree_svg = render_diagram(tree, format=RenderFormat.SVG)
```

## Componentes

### 1. TreeBuilder

Constructor genérico de árboles.

```python
from app.core.visualization import TreeBuilder, NodeType

builder = TreeBuilder()

# Crear árbol manualmente
root = builder.create_node("Root", NodeType.ROOT, value=1)
child1 = builder.create_node("Child 1", NodeType.BRANCH, value=2)
child2 = builder.create_node("Child 2", NodeType.LEAF, value=3)

root.add_child(child1)
root.add_child(child2)

# Estadísticas
stats = builder.get_statistics(root)
print(f"Total nodos: {stats['total_nodes']}")
print(f"Profundidad: {stats['max_depth']}")
```

### 2. RecursionTreeGenerator

Genera árboles de recursión.

```python
from app.core.visualization import RecursionTreeGenerator

generator = RecursionTreeGenerator(
    max_depth=10,     # Profundidad máxima
    max_nodes=100     # Número máximo de nodos
)

result = generator.generate(ast, start_value=8)

print(f"Tipo: {result.recursion_type}")           # binary, linear, etc.
print(f"Llamadas: {result.total_calls}")
print(f"Trabajo total: {result.total_work}")

# Trabajo por nivel
for i, work in enumerate(result.work_per_level):
    print(f"Nivel {i}: {work}")
```

### 3. ExecutionFlowGenerator

Genera diagramas de flujo.

```python
from app.core.visualization import ExecutionFlowGenerator

generator = ExecutionFlowGenerator()
result = generator.generate(ast)

print(f"Nodos: {len(result.nodes)}")
print(f"Aristas: {len(result.edges)}")

# Tipos de nodos
for node in result.nodes:
    print(f"{node.id}: {node.label} ({node.node_type})")
```

### 4. GraphGenerator

Genera grafos de estructuras.

```python
from app.core.visualization import GraphGenerator, LayoutType

generator = GraphGenerator()

# Árbol
tree = generator.generate_tree(
    values=[1, 2, 3, 4, 5, 6, 7],
    layout=LayoutType.HIERARCHICAL
)

# Grafo personalizado
graph = generator.generate_graph(
    num_nodes=8,
    edges_list=[(0,1), (1,2), (2,3)],
    directed=True,
    layout=LayoutType.SPRING
)

# NetworkX graph disponible
if tree.networkx_graph:
    import networkx as nx
    print(f"Conectado: {nx.is_connected(tree.networkx_graph)}")
```

### 5. DiagramRenderer

Renderiza en múltiples formatos.

```python
from app.core.visualization import DiagramRenderer, RenderOptions, RenderFormat
from pathlib import Path

# Opciones personalizadas
options = RenderOptions(
    format=RenderFormat.SVG,
    engine="dot",
    node_shape="ellipse",
    node_color="#e3f2fd",
    edge_color="#1976d2",
    font_name="Arial",
    font_size=14,
    rankdir="TB"  # Top-Bottom
)

renderer = DiagramRenderer(options)

# Renderizar
result = renderer.render_tree(tree)

# Guardar en archivo
output_path = Path("output/diagram.svg")
result = renderer.render_tree(tree, output_path=output_path)
```

## Formatos de Renderizado

| Formato | Extensión | Uso | Ventajas |
|---------|-----------|-----|----------|
| **SVG** | .svg | Web, documentos | Escalable, pequeño |
| **PNG** | .png | Presentaciones | Compatible |
| **PDF** | .pdf | Reportes | Imprimible |
| **DOT** | .dot | Edición | Procesable |
| **Mermaid** | .mmd | Markdown | Simple, legible |
| **JSON** | .json | Datos | Estructurado |

### Comparación de Formatos

```python
# Probar todos los formatos
formats = [RenderFormat.DOT, RenderFormat.MERMAID, RenderFormat.JSON]

for fmt in formats:
    result = render_diagram(tree, format=fmt)
    print(f"\n{fmt.value.upper()}:")
    print(result.content[:100] + "...")
```

## Layouts de Grafos

| Layout | Mejor Para | Descripción |
|--------|------------|-------------|
| **HIERARCHICAL** | Árboles, DAGs | Jerárquico de arriba-abajo |
| **CIRCULAR** | Ciclos | Nodos en círculo |
| **SPRING** | General | Basado en fuerzas |
| **SHELL** | Capas | Concéntrico |
| **SPECTRAL** | Análisis | Eigenvalores |
| **KAMADA_KAWAI** | Estética | Optimización |

```python
# Comparar layouts
for layout in [LayoutType.HIERARCHICAL, LayoutType.CIRCULAR, LayoutType.SPRING]:
    graph = generate_graph(
        structure_type="tree",
        values=[1, 2, 3, 4, 5],
        layout=layout
    )
    print(f"Layout {layout.value}: {len(graph.nodes)} nodos posicionados")
```

## Ejemplos Avanzados

### Análisis Completo con Visualización

```python
from app.core.parser import parse_pseudocode
from app.core.analyzer import AnalyzerEngine
from app.core.visualization import (
    generate_recursion_tree,
    generate_execution_flow,
    render_diagram,
    RenderFormat
)

code = """
algorithm mergeSort(A[n])
begin
    if (n > 1) then
    begin
        mid := n / 2
        call mergeSort(A)
        call mergeSort(A)
        call merge(A, 1, mid, n)
    end
end
"""

# 1. Parsear
ast = parse_pseudocode(code)

# 2. Analizar complejidad
analyzer = AnalyzerEngine()
complexity = analyzer.analyze(ast)

# 3. Generar visualizaciones
tree = generate_recursion_tree(ast, start_value=8)
flow = generate_execution_flow(ast)

# 4. Renderizar
tree_svg = render_diagram(tree, format=RenderFormat.SVG)
flow_mermaid = render_diagram(flow, format=RenderFormat.MERMAID)

# 5. Reporte
print(f"Algoritmo: {ast.algorithm.name}")
print(f"Complejidad: {complexity.big_o}")
print(f"Tipo de recursión: {tree.recursion_type}")
print(f"Total de llamadas: {tree.total_calls}")
print(f"Nodos de flujo: {len(flow.nodes)}")
```

### Guardar Múltiples Formatos

```python
from pathlib import Path

output_dir = Path("exports/visualizations")
output_dir.mkdir(parents=True, exist_ok=True)

formats_to_save = [
    (RenderFormat.SVG, "tree.svg"),
    (RenderFormat.DOT, "tree.dot"),
    (RenderFormat.MERMAID, "tree.mmd"),
    (RenderFormat.JSON, "tree.json")
]

for fmt, filename in formats_to_save:
    output_path = output_dir / filename
    result = render_diagram(tree, format=fmt, output_path=output_path)
    print(f"✓ Guardado: {output_path}")
```

## API REST

### Endpoints Disponibles

```bash
POST /api/v1/visualization/recursion-tree
POST /api/v1/visualization/execution-flow
POST /api/v1/visualization/graph
GET  /api/v1/visualization/formats
GET  /api/v1/visualization/layouts
```

### Ejemplo: Árbol de Recursión

```bash
curl -X POST http://localhost:8000/api/v1/visualization/recursion-tree \
  -H "Content-Type: application/json" \
  -d '{
    "code": "algorithm fibonacci(n)\nbegin\n  if (n <= 1) then\n    return n\n  return fibonacci(n - 1) + fibonacci(n - 2)\nend",
    "start_value": 4,
    "max_depth": 6,
    "render_format": "mermaid"
  }'
```

### Ejemplo: Flujo de Ejecución

```bash
curl -X POST http://localhost:8000/api/v1/visualization/execution-flow \
  -H "Content-Type: application/json" \
  -d '{
    "code": "algorithm linearSearch(A[n], x)\nbegin\n  for i := 1 to n do\n    if (A[i] = x) then\n      return i\n  return -1\nend",
    "render_format": "dot"
  }'
```

### Ejemplo: Grafo

```bash
curl -X POST http://localhost:8000/api/v1/visualization/graph \
  -H "Content-Type: application/json" \
  -d '{
    "structure_type": "tree",
    "values": [10, 5, 15, 3, 7, 12, 20],
    "layout": "hierarchical",
    "render_format": "svg"
  }'
```

## Testing

### Ejecutar Tests

```bash
# Todos los tests del módulo
pytest tests/unit/test_visualization.py -v

# Tests específicos
pytest tests/unit/test_visualization.py::TestRecursionTreeGenerator -v

# Con coverage
pytest tests/unit/test_visualization.py --cov=app.core.visualization
```

### Ejemplo de Test

```python
def test_recursion_tree_generation():
    code = """
    algorithm factorial(n)
    begin
        if (n <= 1) then
            return 1
        return n * factorial(n - 1)
    end
    """
    
    ast = parse_pseudocode(code)
    result = generate_recursion_tree(ast, start_value=5)
    
    assert result.recursion_type == RecursionType.LINEAR
    assert result.total_calls > 0
    assert result.max_depth > 0
```

## Troubleshooting

### Error: Graphviz no disponible

```python
# Solución 1: Instalar graphviz
pip install graphviz

# Solución 2: Usar formatos que no requieren Graphviz
result = render_diagram(tree, format=RenderFormat.MERMAID)  # ✓
result = render_diagram(tree, format=RenderFormat.DOT)      # ✓
result = render_diagram(tree, format=RenderFormat.JSON)     # ✓
```

### Error: Max depth excedido

```python
# Incrementar límite
generator = RecursionTreeGenerator(max_depth=20, max_nodes=500)
result = generator.generate(ast, start_value=10)
```

### Error: Layout no funciona

```python
# Usar layout alternativo
try:
    graph = generate_graph(structure_type="tree", layout=LayoutType.SPRING)
except Exception:
    # Fallback a layout por defecto
    graph = generate_graph(structure_type="tree", layout=LayoutType.HIERARCHICAL)
```

## Exportación Batch

### BatchExporter

Permite exportar múltiples visualizaciones de forma eficiente.

```python
from app.core.visualization import (
    BatchExporter,
    BatchExportConfig,
    ExportTask,
    ExportFormat,
    ProcessingMode
)
from pathlib import Path

# Configuración
config = BatchExportConfig(
    mode=ProcessingMode.THREADED,  # sequential, threaded, async, multiprocess
    max_workers=4,
    chunk_size=10,
    timeout_per_task=30.0,
    retry_failed=True,
    max_retries=3
)

exporter = BatchExporter(config)

# Crear tareas
tasks = [
    ExportTask(
        id="fib-tree",
        visualization_type="recursion_tree",
        data={"recurrence": "T(n) = T(n-1) + T(n-2) + 1"},
        format=ExportFormat.SVG,
        output_path=Path("output/fib.svg"),
        priority=1
    ),
    ExportTask(
        id="sort-flow",
        visualization_type="execution_flow",
        data={"ast_node": ast},
        format=ExportFormat.PNG,
        output_path=Path("output/sort.png")
    )
]

# Exportar batch
import asyncio
results = asyncio.run(exporter.export_batch(tasks))

# Estadísticas
stats = exporter.get_stats()
print(f"Éxitos: {stats['successful']}/{stats['total_tasks']}")
```

## Optimización

### VisualizationOptimizer

Optimiza grafos grandes para mejorar rendimiento y legibilidad.

```python
from app.core.visualization import (
    VisualizationOptimizer,
    OptimizationConfig,
    OptimizationLevel
)

# Configuración
config = OptimizationConfig(
    level=OptimizationLevel.MODERATE,  # none, basic, moderate, aggressive
    max_nodes=1000,
    max_edges=5000,
    enable_clustering=True,
    enable_simplification=True,
    edge_bundling=True,
    node_aggregation=True
)

optimizer = VisualizationOptimizer(config)

# Optimizar grafo
nodes = [{"id": f"n{i}", "label": f"Node {i}"} for i in range(500)]
edges = [(f"n{i}", f"n{i+1}", {}) for i in range(499)]

opt_nodes, opt_edges, metadata = optimizer.optimize_graph(nodes, edges)

print(f"Nodos: {len(nodes)} → {len(opt_nodes)}")
print(f"Reducción: {metadata['reduction_ratio']['nodes']*100:.1f}%")
print(f"Optimizaciones: {metadata['optimizations_applied']}")
```

### Niveles de Optimización

| Nivel | Técnicas | Uso |
|-------|----------|-----|
| **NONE** | Ninguna | Debug/testing |
| **BASIC** | Duplicados, aislados | Grafos pequeños |
| **MODERATE** | + Clustering, LOD | Grafos medianos |
| **AGGRESSIVE** | + Agregación, bundling | Grafos grandes |

## Métricas y Monitoring

### MetricsCollector

Sistema de métricas y alertas para exportaciones.

```python
from app.core.visualization import (
    MetricsCollector,
    MetricsContext,
    AlertThresholds,
    AlertSeverity
)

# Configurar umbrales
thresholds = AlertThresholds(
    export_time_warning_ms=5000,
    export_time_critical_ms=30000,
    memory_warning_mb=256,
    memory_critical_mb=512,
    node_count_warning=5000,
    node_count_critical=10000
)

# Callback para alertas
def on_alert(alert):
    if alert.severity == AlertSeverity.CRITICAL:
        print(f"🚨 CRÍTICO: {alert.message}")

collector = MetricsCollector(
    thresholds=thresholds,
    alert_callback=on_alert
)

# Iniciar batch
collector.start_batch("my-batch", total_tasks=10)

# Tracking con context manager
with MetricsContext(
    collector,
    task_id="export-001",
    visualization_type="graph",
    export_format="svg",
    node_count=500,
    edge_count=800
) as metrics:
    # Tu código de exportación aquí
    pass

# Finalizar y obtener resultados
batch = collector.end_batch()
print(f"Throughput: {batch.throughput_tasks_per_sec:.2f}/s")
print(f"Alertas: {len(batch.alerts_triggered)}")

# Exportar reporte
from pathlib import Path
collector.export_report(Path("reports/metrics.json"))
```

### Tipos de Alertas

| Tipo | Descripción | Severidades |
|------|-------------|-------------|
| **Tiempo** | Exportación lenta | Warning/Critical |
| **Memoria** | Alto uso de RAM | Warning/Critical |
| **Tamaño** | Grafo muy grande | Warning/Critical |
| **Archivos** | Archivos grandes | Warning/Critical |
| **Fallos** | Tasa de errores | Warning/Critical |

### Estadísticas

```python
stats = collector.get_statistics()

print(f"Total exportaciones: {stats['total_exports']}")
print(f"Tiempo promedio: {stats['processing_time']['avg_ms']}ms")
print(f"Alertas críticas: {stats['alerts']['critical']}")
```

## Mejores Prácticas

1. **Usar límites apropiados**: No generar árboles demasiado grandes
2. **Elegir formato correcto**: SVG para web, PNG para documentos
3. **Cachear resultados**: Guardar visualizaciones generadas
4. **Manejar errores**: Try-catch para operaciones de I/O
5. **Documentar**: Agregar metadatos a las visualizaciones
6. **Optimizar**: Usar VisualizationOptimizer para grafos grandes
7. **Monitorear**: Usar MetricsCollector para tracking y alertas
8. **Batch processing**: Usar BatchExporter para exportaciones múltiples

## Contribuir

Para contribuir al módulo:

1. Fork el repositorio
2. Crear rama feature
3. Agregar tests para nuevas funcionalidades
4. Documentar en este README
5. Pull request

## Licencia

MIT License - Ver archivo LICENSE para detalles

## Soporte

- **Documentación**: [docs/modules/VISUALIZATION.md](../../docs/modules/VISUALIZATION.md)
- **Issues**: GitHub Issues
- **Email**: elsebas1912@gmail.com