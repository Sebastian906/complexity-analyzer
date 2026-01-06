# Módulo 4: Visualización

Sistema de generación de visualizaciones gráficas para algoritmos, árboles de recursión, grafos y diagramas de flujo.

---

## Tabla de Contenidos

1. [Descripción General](#descripción-general)
2. [Arquitectura](#arquitectura)
3. [Componentes](#componentes)
4. [Formatos Soportados](#formatos-soportados)
5. [Uso](#uso)
6. [API Reference](#api-reference)
7. [Ejemplos](#ejemplos)
8. [Testing](#testing)
9. [Integración con Módulos](#integración-con-módulos)

---

## Descripción General

El módulo de visualización genera representaciones gráficas de estructuras de datos y algoritmos para facilitar su comprensión y análisis.

### Funcionalidades Principales

| Funcionalidad | Descripción |
|---------------|-------------|
| **Árboles de Recursión** | Visualiza llamadas recursivas y análisis de complejidad |
| **Flujos de Ejecución** | Diagramas de flujo paso a paso |
| **Grafos** | Representación de estructuras de datos (árboles, grafos, listas) |
| **Múltiples Formatos** | SVG, PNG, PDF, DOT, Mermaid, JSON |
| **Layouts** | Diferentes distribuciones (jerárquico, circular, spring, etc.) |

### Tipos de Visualización

| Tipo | Descripción | Uso Principal |
|------|-------------|---------------|
| **Recursion Tree** | Árbol de llamadas recursivas | Análisis de ecuaciones de recurrencia |
| **Execution Flow** | Diagrama de flujo de ejecución | Entender lógica del algoritmo |
| **Data Structure Graph** | Grafo de estructura de datos | Visualizar árboles, grafos, listas |
| **Generic Tree** | Árbol genérico | Base para otros tipos |

---

## Arquitectura

```
visualization/
├── __init__.py                     # Exports principales
├── tree_builder.py                 # Constructor árboles genéricos
├── recursion_tree_generator.py     # Árboles de recursión
├── execution_flow_generator.py     # Flujos de ejecución
├── graph_generator.py              # Generador de grafos
└── diagram_renderer.py             # Renderizador universal
```

**Archivos principales:**

- [tree_builder.py](../../app/core/visualization/tree_builder.py) - Constructor de árboles
- [recursion_tree_generator.py](../../app/core/visualization/recursion_tree_generator.py) - Árboles de recursión
- [execution_flow_generator.py](../../app/core/visualization/execution_flow_generator.py) - Flujos
- [graph_generator.py](../../app/core/visualization/graph_generator.py) - Grafos
- [diagram_renderer.py](../../app/core/visualization/diagram_renderer.py) - Renderizador

---

## Componentes

### 1. TreeBuilder (Constructor de Árboles)

Constructor genérico de árboles que sirve como base para otros componentes.

**Archivo:** [tree_builder.py](../../app/core/visualization/tree_builder.py)

```python
from app.core.visualization import TreeBuilder, TreeNode, NodeType

builder = TreeBuilder()

# Crear árbol manualmente
root = builder.create_node("Root", NodeType.ROOT)
child1 = builder.create_node("Child 1", NodeType.BRANCH)
child2 = builder.create_node("Child 2", NodeType.LEAF)

root.add_child(child1)
root.add_child(child2)

# Estadísticas
stats = builder.get_statistics(root)
print(f"Total nodos: {stats['total_nodes']}")
print(f"Profundidad: {stats['max_depth']}")
```

**Tipos de nodos:**
- `ROOT`: Nodo raíz
- `BRANCH`: Nodo intermedio
- `LEAF`: Nodo hoja
- `CALL`: Llamada recursiva
- `RETURN`: Retorno
- `OPERATION`: Operación
- `CONDITION`: Condición

### 2. RecursionTreeGenerator (Árboles de Recursión)

Genera árboles que muestran las llamadas recursivas de un algoritmo.

**Archivo:** [recursion_tree_generator.py](../../app/core/visualization/recursion_tree_generator.py)

```python
from app.core.parser import parse_pseudocode
from app.core.visualization import generate_recursion_tree

code = """
algorithm fibonacci(n)
begin
    if (n <= 1) then
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)
end
"""

ast = parse_pseudocode(code)

# Generar árbol
result = generate_recursion_tree(ast, start_value=4, max_depth=6)

print(f"Tipo: {result.recursion_type}")           # binary
print(f"Total llamadas: {result.total_calls}")    # 9
print(f"Profundidad: {result.max_depth}")         # 4
print(f"Trabajo total: {result.total_work}")      # O(2^n)
```

**Tipos de recursión detectados:**
- `LINEAR`: T(n) = T(n-1) + f(n)
- `BINARY`: T(n) = 2T(n/2) + f(n)
- `MULTIPLE`: T(n) = aT(n/b) + f(n)
- `NESTED`: Recursión anidada
- `TAIL`: Recursión de cola

### 3. ExecutionFlowGenerator (Flujos de Ejecución)

Genera diagramas de flujo que muestran la ejecución paso a paso.

**Archivo:** [execution_flow_generator.py](../../app/core/visualization/execution_flow_generator.py)

```python
from app.core.visualization import generate_execution_flow

code = """
algorithm linearSearch(A[n], x)
begin
    for i := 1 to n do
    begin
        if (A[i] = x) then
            return i
    end
    return -1
end
"""

ast = parse_pseudocode(code)
result = generate_execution_flow(ast)

print(f"Nodos: {result.statistics['total_nodes']}")
print(f"Aristas: {result.statistics['total_edges']}")
print(f"Tiene loops: {result.statistics['has_loops']}")
```

**Tipos de nodos de flujo:**
- `START`: Inicio
- `END`: Fin
- `PROCESS`: Proceso/operación
- `DECISION`: Decisión/condición
- `LOOP_START`: Inicio de ciclo
- `LOOP_END`: Fin de ciclo
- `CALL`: Llamada a función
- `RETURN`: Retorno

### 4. GraphGenerator (Generador de Grafos)

Genera representaciones gráficas de estructuras de datos.

**Archivo:** [graph_generator.py](../../app/core/visualization/graph_generator.py)

```python
from app.core.visualization import generate_graph, LayoutType

# Árbol binario
tree = generate_graph(
    structure_type="tree",
    values=[10, 5, 15, 3, 7, 12, 20],
    layout=LayoutType.HIERARCHICAL
)

# Grafo dirigido
graph = generate_graph(
    structure_type="graph",
    num_nodes=6,
    edges_list=[(0,1), (0,2), (1,3), (2,4)],
    directed=True,
    layout=LayoutType.SPRING
)

# Lista enlazada
linked_list = generate_graph(
    structure_type="linked_list",
    values=[1, 2, 3, 4, 5],
    layout=LayoutType.HIERARCHICAL
)
```

**Tipos de grafos:**
- `DIRECTED`: Grafo dirigido
- `UNDIRECTED`: Grafo no dirigido
- `TREE`: Árbol
- `DAG`: Grafo acíclico dirigido
- `WEIGHTED`: Grafo ponderado

**Tipos de layout:**
- `HIERARCHICAL`: Jerárquico (árboles)
- `CIRCULAR`: Circular
- `SPRING`: Basado en fuerzas
- `SHELL`: Capas concéntricas
- `SPECTRAL`: Espectral
- `KAMADA_KAWAI`: Kamada-Kawai

### 5. DiagramRenderer (Renderizador Universal)

Renderiza cualquier tipo de diagrama en múltiples formatos.

**Archivo:** [diagram_renderer.py](../../app/core/visualization/diagram_renderer.py)

```python
from app.core.visualization import render_diagram, RenderFormat, RenderOptions
from pathlib import Path

# Renderizar en SVG
svg_result = render_diagram(
    result,
    format=RenderFormat.SVG,
    rankdir="TB",
    node_color="#e3f2fd"
)

# Renderizar en DOT
dot_result = render_diagram(result, format=RenderFormat.DOT)
print(dot_result.content)

# Renderizar en Mermaid
mermaid_result = render_diagram(result, format=RenderFormat.MERMAID)

# Guardar en archivo
output_path = Path("output/diagram.svg")
svg_result = render_diagram(
    result,
    format=RenderFormat.SVG,
    output_path=output_path
)
```

---

## Formatos Soportados

### Formatos de Renderizado

| Formato | Extensión | Descripción | Uso |
|---------|-----------|-------------|-----|
| **SVG** | .svg | Scalable Vector Graphics | Web, escalable |
| **PNG** | .png | Imagen rasterizada | Documentos, presentaciones |
| **PDF** | .pdf | Portable Document Format | Reportes, impresión |
| **DOT** | .dot | Graphviz DOT | Edición, procesamiento |
| **Mermaid** | .mmd | Mermaid diagram | Markdown, documentación |
| **JSON** | .json | JavaScript Object Notation | Datos estructurados |

### Comparación de Formatos

| Característica | SVG | PNG | DOT | Mermaid |
|---------------|-----|-----|-----|---------|
| Escalable | ✓ | ✗ | ✓ | ✓ |
| Tamaño archivo | Pequeño | Grande | Pequeño | Pequeño |
| Editable | ✓ | ✗ | ✓ | ✓ |
| Web-friendly | ✓ | ✓ | ✗ | ✓ |
| Calidad | Alta | Variable | Alta | Alta |

---

## Uso

### Flujo Completo

```python
from app.core.parser import parse_pseudocode
from app.core.visualization import (
    generate_recursion_tree,
    generate_execution_flow,
    render_diagram,
    RenderFormat
)

# 1. Parsear algoritmo
code = """
algorithm quicksort(A[n], low, high)
begin
    if (low < high) then
    begin
        pivot := partition(A, low, high)
        call quicksort(A, low, pivot - 1)
        call quicksort(A, pivot + 1, high)
    end
end
"""

ast = parse_pseudocode(code)

# 2. Generar árbol de recursión
tree_result = generate_recursion_tree(ast, start_value=8)

# 3. Generar flujo de ejecución
flow_result = generate_execution_flow(ast)

# 4. Renderizar
svg_tree = render_diagram(tree_result, format=RenderFormat.SVG)
dot_flow = render_diagram(flow_result, format=RenderFormat.DOT)
mermaid_tree = render_diagram(tree_result, format=RenderFormat.MERMAID)

# 5. Guardar
from pathlib import Path

tree_path = Path("exports/quicksort_tree.svg")
flow_path = Path("exports/quicksort_flow.dot")

render_diagram(tree_result, format=RenderFormat.SVG, output_path=tree_path)
render_diagram(flow_result, format=RenderFormat.DOT, output_path=flow_path)
```

### Uso Avanzado

```python
from app.core.visualization import (
    RecursionTreeGenerator,
    DiagramRenderer,
    RenderOptions
)

# Generador con configuración personalizada
generator = RecursionTreeGenerator(max_depth=8, max_nodes=200)
result = generator.generate(ast, start_value=16)

# Renderizador con opciones
options = RenderOptions(
    format=RenderFormat.SVG,
    engine="dot",
    node_shape="ellipse",
    node_color="#bbdefb",
    edge_color="#1976d2",
    font_name="Arial",
    font_size=14,
    rankdir="LR"  # Left to Right
)

renderer = DiagramRenderer(options)
svg_result = renderer.render_tree(result)
```

---

## API Reference

### RecursionTreeGenerator

```python
class RecursionTreeGenerator:
    def __init__(
        self,
        max_depth: int = 10,
        max_nodes: int = 100
    )
    
    def generate(
        self,
        ast: ProgramNode,
        start_value: Optional[int] = None
    ) -> RecursionTreeResult
```

### ExecutionFlowGenerator

```python
class ExecutionFlowGenerator:
    def generate(
        self,
        ast: ProgramNode
    ) -> ExecutionFlowResult
```

### GraphGenerator

```python
class GraphGenerator:
    def generate_tree(
        self,
        values: Optional[List[Any]] = None,
        layout: LayoutType = LayoutType.HIERARCHICAL
    ) -> GraphResult
    
    def generate_graph(
        self,
        num_nodes: int = 6,
        edges_list: Optional[List[Tuple[int, int]]] = None,
        directed: bool = True,
        layout: LayoutType = LayoutType.SPRING
    ) -> GraphResult
    
    def generate_linked_list(
        self,
        values: Optional[List[Any]] = None,
        layout: LayoutType = LayoutType.HIERARCHICAL
    ) -> GraphResult
```

### DiagramRenderer

```python
class DiagramRenderer:
    def __init__(
        self,
        options: Optional[RenderOptions] = None
    )
    
    def render_tree(
        self,
        tree: Union[TreeNode, RecursionTreeResult],
        output_path: Optional[Path] = None
    ) -> RenderResult
    
    def render_graph(
        self,
        graph: GraphResult,
        output_path: Optional[Path] = None
    ) -> RenderResult
    
    def render_flow(
        self,
        flow: ExecutionFlowResult,
        output_path: Optional[Path] = None
    ) -> RenderResult
```

### Helper Functions

```python
# Generar árbol de recursión
from app.core.visualization import generate_recursion_tree
result = generate_recursion_tree(ast, start_value=8)

# Generar flujo de ejecución
from app.core.visualization import generate_execution_flow
result = generate_execution_flow(ast)

# Generar grafo
from app.core.visualization import generate_graph
result = generate_graph(structure_type="tree", values=[1,2,3])

# Renderizar diagrama
from app.core.visualization import render_diagram, RenderFormat
result = render_diagram(diagram, format=RenderFormat.SVG)
```

---

## Ejemplos

### Ejemplo 1: Fibonacci - Árbol de Recursión

```python
code = """
algorithm fibonacci(n)
begin
    if (n <= 1) then
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)
end
"""

ast = parse_pseudocode(code)
result = generate_recursion_tree(ast, start_value=5)

# Output:
# Tipo: binary
# Total llamadas: 15
# Trabajo total: O(2^n)
```

### Ejemplo 2: Merge Sort - Visualización Completa

```python
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

ast = parse_pseudocode(code)

# Árbol de recursión
tree = generate_recursion_tree(ast, start_value=8)
print(f"Trabajo: {tree.total_work}")  # O(n log n)

# Flujo de ejecución
flow = generate_execution_flow(ast)
print(f"Nodos: {flow.statistics['total_nodes']}")

# Renderizar ambos
tree_svg = render_diagram(tree, format=RenderFormat.SVG)
flow_dot = render_diagram(flow, format=RenderFormat.DOT)
```

### Ejemplo 3: Grafos - Estructura de Datos

```python
# Árbol binario de búsqueda
bst = generate_graph(
    structure_type="tree",
    values=[50, 30, 70, 20, 40, 60, 80]
)

# Renderizar
svg = render_diagram(bst, format=RenderFormat.SVG)

# Grafo de dependencias
graph = generate_graph(
    structure_type="graph",
    num_nodes=5,
    edges_list=[(0,1), (0,2), (1,3), (2,3), (3,4)],
    directed=True
)

# Mermaid
mermaid = render_diagram(graph, format=RenderFormat.MERMAID)
```

---

## Testing

### Ejecutar Tests

```bash
# Tests del módulo visualization
pytest tests/unit/test_visualization.py -v

# Tests específicos
pytest tests/unit/test_visualization.py::TestRecursionTreeGenerator -v

# Con coverage
pytest tests/unit/test_visualization.py --cov=app/core/visualization
```

### Tests Unitarios

```python
def test_tree_builder()
def test_recursion_tree_generation()
def test_execution_flow_generation()
def test_graph_generation()
def test_rendering_formats()
def test_recursion_type_detection()
```

---

## Integración con Módulos

El módulo de visualización se integra con todos los módulos anteriores:

```
   ┌─────────────────┐
   │     Parser      │  Módulo 1
   │   (Genera AST)  │
   └────────┬────────┘
            │ AST
            ▼
   ┌─────────────────┐
   │    Analyzer     │  Módulo 2
   │  (Complejidad)  │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │    Patterns     │  Módulo 3
   │  (Detección)    │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ Data Structures │  Módulo 3.5
   │  (Estructuras)  │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ Visualization   │  Módulo 4 (Este módulo)
   │    (Grafos)     │
   └─────────────────┘
```

### Uso Combinado

```python
from app.core.parser import parse_pseudocode
from app.core.analyzer import AnalyzerEngine
from app.core.patterns import PatternDetector
from app.core.data_structures import identify_structures
from app.core.visualization import (
    generate_recursion_tree,
    generate_execution_flow,
    render_diagram,
    RenderFormat
)

# 1. Parsear
ast = parse_pseudocode(code)

# 2. Analizar complejidad
analyzer = AnalyzerEngine()
complexity = analyzer.analyze(ast)

# 3. Detectar patrones
detector = PatternDetector()
patterns = detector.detect(ast)

# 4. Identificar estructuras
structures = identify_structures(ast)

# 5. Visualizar
tree = generate_recursion_tree(ast)
flow = generate_execution_flow(ast)

# 6. Renderizar
tree_svg = render_diagram(tree, format=RenderFormat.SVG)
flow_mermaid = render_diagram(flow, format=RenderFormat.MERMAID)

# 7. Reporte completo
print(f"Algoritmo: {ast.algorithm.name}")
print(f"Complejidad: {complexity.big_o}")
print(f"Patrón: {patterns.primary_pattern_name}")
print(f"Estructura: {structures.primary_structure.structure_name if structures.primary_structure else 'N/A'}")
print(f"Visualizaciones generadas: 2")
```

---

## Limitaciones Actuales

| Limitación | Estado |
|------------|--------|
| Grafos muy grandes | Limitado por max_nodes |
| Animaciones | No implementado |
| Interactividad | Solo estática |
| Formatos 3D | No soportado |

---

## Próximos Pasos

1. Agregar soporte para animaciones paso a paso
2. Implementar visualizaciones interactivas
3. Optimizar renderizado de grafos grandes
4. Agregar más tipos de layout
5. Integrar con frontend para visualización web

---

## Dependencias

### Requeridas
- `networkx`: Grafos y layouts
- `pathlib`: Manejo de rutas

### Opcionales
- `graphviz`: Renderizado SVG/PNG/PDF (recomendado)
- `matplotlib`: Visualización alternativa
- `plotly`: Visualización interactiva

### Instalación

```bash
# Dependencias básicas
pip install networkx

# Graphviz (recomendado)
pip install graphviz

# Opcional
pip install matplotlib plotly
```

---

## Referencias

- **Graphviz:** https://graphviz.org/
- **Mermaid:** https://mermaid-js.github.io/
- **NetworkX:** https://networkx.org/
- **DOT Language:** https://graphviz.org/doc/info/lang.html

---

**Última actualización:** 2025-01-06

**Versión del módulo:** 1.0.0

---

**Documentos relacionados:**

- [ANALYZER.md](ANALYZER.md) - Módulo de análisis
- [PATTERNS.md](PATTERNS.md) - Módulo de patrones
- [DATA_STRUCTURES.md](DATA_STRUCTURES.md) - Módulo de estructuras
- [GETTING_STARTED.md](../GETTING_STARTED.md) - Guía de inicio