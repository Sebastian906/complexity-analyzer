# Módulo 3.5: Detección de Estructuras de Datos

Sistema automático de detección de estructuras de datos utilizadas en algoritmos mediante análisis estático del AST.

---

## Tabla de Contenidos

1. [Descripción General](#descripción-general)
2. [Arquitectura](#arquitectura)
3. [Estructuras Soportadas](#estructuras-soportadas)
4. [Uso](#uso)
5. [API Reference](#api-reference)
6. [Ejemplos](#ejemplos)
7. [Testing](#testing)
8. [Integración con Módulos](#integración-con-módulos)

---

## Descripción General

El módulo de detección de estructuras de datos identifica automáticamente qué estructuras están siendo utilizadas en un algoritmo y proporciona:

### Funcionalidades Principales

| Funcionalidad | Descripción |
|---------------|-------------|
| **Detección Automática** | Identifica 8+ estructuras mediante análisis del AST |
| **Nivel de Confianza** | Score de 0.0 a 1.0 por cada estructura detectada |
| **Análisis de Uso** | Frecuencia de operaciones y patrones de acceso |
| **Complejidades** | Complejidad de cada operación sobre la estructura |
| **Recomendaciones** | Sugerencias de optimización basadas en uso |

### Estructuras Detectables

- **Arrays/Listas**: Acceso por índice
- **Pilas (Stack)**: LIFO - Last In First Out
- **Colas (Queue)**: FIFO - First In First Out
- **Listas Enlazadas**: Nodos con punteros next/prev
- **Diccionarios/Maps**: Clave-valor
- **Árboles**: Estructura jerárquica
- **Grafos**: Nodos y aristas
- **Tablas Hash**: Función hash y buckets

---

## Arquitectura

```
data_structures/
├── __init__.py                     # Exports principales
├── base_structure.py               # Clases base y tipos
├── structure_identifier.py         # Identificador principal
├── usage_analyzer.py               # Análisis de uso
│
└── detectors/                      # Detectores específicos
    ├── __init__.py
    ├── array_detector.py           # Arrays/Listas
    ├── stack_detector.py           # Pilas
    ├── queue_detector.py           # Colas
    ├── linked_list_detector.py     # Listas enlazadas
    ├── dictionary_detector.py      # Diccionarios
    ├── tree_detector.py            # Árboles
    ├── graph_detector.py           # Grafos
    └── hash_table_detector.py      # Tablas Hash
```

**Archivos principales:**

- [base_structure.py](../app/core/data_structures/base_structure.py) - Clase base y tipos
- [structure_identifier.py](../app/core/data_structures/structure_identifier.py) - Identificador principal
- [usage_analyzer.py](../app/core/data_structures/usage_analyzer.py) - Análisis de uso

---

## Estructuras Soportadas

### 1. Arrays/Listas

**Indicadores clave:**
- Parámetros con notación `A[n]` o `A[]`
- Accesos indexados `A[i]`
- Iteraciones `for i ← 1 to n`

**Complejidades:**
- Acceso: O(1)
- Búsqueda: O(n)
- Inserción al final: O(1)
- Inserción en medio: O(n)

```python
algorithm example(A[n])
begin
    for i ← 1 to n do
        print(A[i])
end
```

### 2. Pilas (Stacks)

**Indicadores clave:**
- Operaciones `push()`, `pop()`
- Variables con nombres `stack`, `pila`
- Recursión (pila implícita)

**Complejidades:**
- push: O(1)
- pop: O(1)
- top/peek: O(1)

```python
algorithm reverse(text)
begin
    stack ← createStack()
    for char in text do
        call push(stack, char)
    
    while not isEmpty(stack) do
        call pop(stack)
end
```

### 3. Colas (Queues)

**Indicadores clave:**
- Operaciones `enqueue()`, `dequeue()`
- Variables `queue`, `cola`
- Acceso a frente y final

**Complejidades:**
- enqueue: O(1)
- dequeue: O(1)
- front: O(1)

```python
algorithm bfs(graph, start)
begin
    queue ← createQueue()
    call enqueue(queue, start)
    
    while not isEmpty(queue) do
        node ← dequeue(queue)
        process(node)
end
```

### 4. Listas Enlazadas

**Indicadores clave:**
- Accesos `.next`, `.prev`
- Clase `Node` definida
- Travesía `while node != null`

**Complejidades:**
- Inserción inicio: O(1)
- Búsqueda: O(n)
- Eliminación: O(n)

```python
algorithm traverse(head)
begin
    node ← head
    while node != null do
        process(node.data)
        node ← node.next
end
```

### 5. Diccionarios/Maps

**Indicadores clave:**
- Acceso por clave `map[key]`
- Operaciones `put()`, `get()`
- Variables `dict`, `map`

**Complejidades:**
- Inserción: O(1) promedio
- Búsqueda: O(1) promedio
- Eliminación: O(1) promedio

### 6. Árboles

**Indicadores clave:**
- Accesos `.left`, `.right`
- Recursión binaria
- Variables `tree`, `root`

**Complejidades:**
- Búsqueda: O(log n) - O(n)
- Inserción: O(log n) - O(n)
- Travesía: O(n)

```python
algorithm inorder(node)
begin
    if node != null then
    begin
        call inorder(node.left)
        process(node.data)
        call inorder(node.right)
    end
end
```

### 7. Grafos

**Indicadores clave:**
- Lista/matriz de adyacencia
- Variables `graph`, `adj`
- Array `visited[]`

**Complejidades:**
- Agregar vértice: O(1)
- Agregar arista: O(1)
- BFS/DFS: O(V + E)

### 8. Tablas Hash

**Indicadores clave:**
- Función `hash()`
- Variables `hash_table`, `bucket`
- Manejo de colisiones

**Complejidades:**
- Inserción: O(1) promedio
- Búsqueda: O(1) promedio
- Eliminación: O(1) promedio

---

## Uso

### Uso Básico - Python

```python
from app.core.parser import parse_pseudocode
from app.core.data_structures import identify_structures

# Parsear código
code = """
algorithm bubbleSort(A[n])
begin
    for i ← 1 to n-1 do
        for j ← 1 to n-i do
            if A[j] > A[j+1] then
                swap(A[j], A[j+1])
end
"""

ast = parse_pseudocode(code)

# Identificar estructuras
result = identify_structures(ast, min_confidence=0.3)

print(result.summary)
# Output: Estructura principal: Array/Lista (confianza: 85%)

# Estructura principal
primary = result.primary_structure
print(f"Tipo: {primary.structure_name}")
print(f"Variables: {primary.variables}")
print(f"Operaciones: {primary.operations}")
```

### Análisis de Uso

```python
from app.core.data_structures import analyze_structure_usage

# Analizar cómo se usa la estructura
usage = analyze_structure_usage(ast, primary)

print(f"Total operaciones: {usage.total_operations}")
print(f"Operación dominante: {usage.most_frequent_operation}")
print(f"Patrón de acceso: {usage.access_pattern}")

# Recomendaciones
for rec in usage.recommendations:
    print(f"💡 {rec}")
```

### Detección Específica

```python
from app.core.data_structures import StructureIdentifier, StructureType

identifier = StructureIdentifier()

# Buscar solo pilas
stack_match = identifier.identify_specific(ast, StructureType.STACK)

if stack_match:
    print(f"Pila detectada: {stack_match.confidence:.2%}")
else:
    print("No se detectó uso de pila")
```

### Estructuras Disponibles

```python
identifier = StructureIdentifier()
available = identifier.get_available_structures()

for struct in available:
    print(f"{struct['name']}: {struct['description']}")
```

---

## API Reference

### StructureIdentifier

```python
class StructureIdentifier:
    def identify(
        self,
        ast: ProgramNode,
        min_confidence: float = 0.3
    ) -> StructureDetectionResult
    
    def identify_specific(
        self,
        ast: ProgramNode,
        structure_type: StructureType
    ) -> Optional[StructureMatch]
    
    def get_available_structures(self) -> List[Dict]
```

### StructureMatch

```python
@dataclass
class StructureMatch:
    structure_type: StructureType
    structure_name: str
    confidence: float
    confidence_level: ConfidenceLevel
    
    variables: List[str]
    indicators_found: List[StructureIndicator]
    indicators_missing: List[StructureIndicator]
    
    operations: List[str]
    operation_complexities: List[OperationComplexity]
    
    reasoning: str
    properties: Dict[str, Any]
    code_evidence: List[str]
```

### UsageAnalyzer

```python
class UsageAnalyzer:
    def analyze(
        self,
        ast: ProgramNode,
        structure_match: StructureMatch
    ) -> StructureUsage
```

### Helper Functions

```python
# Identificar estructuras
from app.core.data_structures import identify_structures
result = identify_structures(ast)

# Analizar uso
from app.core.data_structures import analyze_structure_usage
usage = analyze_structure_usage(ast, structure_match)
```

---

## Ejemplos

### Ejemplo 1: Búsqueda Binaria (Array)

```python
code = """
algorithm binarySearch(A[n], x)
begin
    left ← 1
    right ← n
    
    while left <= right do
    begin
        mid ← (left + right) / 2
        
        if A[mid] = x then
            return mid
        else if A[mid] < x then
            left ← mid + 1
        else
            right ← mid - 1
    end
    
    return -1
end
"""

result = identify_structures(ast)

# Output:
# Estructura principal: Array/Lista (confianza: 92%)
# Variables: A
# Operaciones: Acceso por índice
# Patrón: random_access
```

### Ejemplo 2: DFS con Pila

```python
code = """
algorithm dfs(graph, start)
begin
    stack ← createStack()
    visited ← createSet()
    
    call push(stack, start)
    
    while not isEmpty(stack) do
    begin
        node ← pop(stack)
        
        if node not in visited then
        begin
            call add(visited, node)
            process(node)
            
            for neighbor in graph[node] do
                call push(stack, neighbor)
        end
    end
end
"""

result = identify_structures(ast)

# Output:
# Estructura principal: Pila (confianza: 88%)
# Variables: stack
# Operaciones: push, pop
# Patrón: sequential_lifo
```

### Ejemplo 3: BFS con Cola

```python
code = """
algorithm bfs(graph, start)
begin
    queue ← createQueue()
    visited ← createSet()
    
    call enqueue(queue, start)
    
    while not isEmpty(queue) do
    begin
        node ← dequeue(queue)
        
        if node not in visited then
        begin
            call add(visited, node)
            process(node)
            
            for neighbor in graph[node] do
                call enqueue(queue, neighbor)
        end
    end
end
"""

result = identify_structures(ast)

# Output:
# Estructura principal: Cola (confianza: 90%)
# Variables: queue, graph
# Operaciones: enqueue, dequeue
# Patrón: sequential_fifo
```

---

## API REST

### Detectar Estructuras

```bash
POST /api/v1/structures/detect

{
  "code": "algorithm test(A[n])\nbegin\n  for i ← 1 to n do\n    x ← A[i]\nend",
  "min_confidence": 0.3,
  "analyze_usage": true
}
```

**Response:**

```json
{
  "success": true,
  "algorithm_name": "test",
  "primary_structure": {
    "structure_type": "array",
    "structure_name": "Array/Lista",
    "confidence": 0.85,
    "confidence_level": "high",
    "variables": ["A"],
    "operations": ["Acceso: A[i]", "Iteración sobre A"],
    "reasoning": "Se encontraron 3 indicadores clave: Parámetro con corchetes, Acceso indexado, Iteración secuencial"
  },
  "primary_usage": {
    "operation_frequencies": [
      {
        "operation": "Acceso",
        "count": 5,
        "complexity": "O(1)"
      }
    ],
    "most_frequent_operation": "Acceso",
    "access_pattern": "sequential",
    "total_operations": 5,
    "recommendations": ["Acceso secuencial óptimo para arrays"]
  },
  "all_structures": [...],
  "summary": "Estructura principal: Array/Lista (confianza: 85%)",
  "message": "Detección de estructuras completada exitosamente"
}
```

### Detectar Estructura Específica

```bash
POST /api/v1/structures/detect-specific

{
  "code": "...",
  "structure_type": "stack"
}
```

### Listar Estructuras Disponibles

```bash
GET /api/v1/structures/available
```

---

## Testing

### Ejecutar Tests

```bash
# Todos los tests del módulo
pytest tests/unit/test_data_structures.py -v

# Tests específicos
pytest tests/unit/test_data_structures.py::TestArrayDetector -v

# Con coverage
pytest tests/unit/test_data_structures.py --cov=app.core.data_structures --cov-report=html
```

### Tests Importantes

```python
def test_array_detection()
def test_stack_detection()
def test_queue_detection()
def test_tree_detection()
def test_usage_analysis()
def test_confidence_calculation()
```

---

## Integración con Módulos

### Con Módulo de Análisis

```python
from app.core.parser import parse_pseudocode
from app.core.analyzer.analyzer_engine import AnalyzerEngine
from app.core.data_structures import identify_structures

ast = parse_pseudocode(code)

# Análisis de complejidad
engine = AnalyzerEngine()
complexity_result = engine.analyze(ast)

# Detección de estructuras
structures_result = identify_structures(ast)

print(f"Big O: {complexity_result.big_o}")
print(f"Estructuras: {structures_result.summary}")
```

### Con Módulo de Patrones

```python
from app.core.patterns import detect_patterns
from app.core.data_structures import identify_structures

# Detectar patrones y estructuras
patterns = detect_patterns(ast)
structures = identify_structures(ast)

print(f"Patrón: {patterns.primary_pattern_name}")
print(f"Estructura: {structures.primary_structure.structure_name}")
```

### Análisis Completo

```python
def analyze_algorithm_complete(code: str):
    """Análisis completo: parsing, complejidad, patrones y estructuras"""
    
    # 1. Parse
    ast = parse_pseudocode(code)
    
    # 2. Complejidad
    engine = AnalyzerEngine()
    complexity = engine.analyze(ast)
    
    # 3. Patrones
    patterns = detect_patterns(ast)
    
    # 4. Estructuras
    structures = identify_structures(ast)
    
    return {
        "complexity": {
            "big_o": complexity.big_o,
            "omega": complexity.omega,
            "theta": complexity.theta
        },
        "pattern": patterns.primary_pattern_name,
        "structures": [
            s.structure_name for s in structures.structures_found
        ]
    }
```

---

## Limitaciones Actuales

| Limitación | Estado |
|------------|--------|
| Estructuras Complejas | Solo básicas implementadas |
| Detección de Punteros | Limitada en pseudocódigo |
| Estructuras Anidadas | Detección simplificada |
| Sets/Multisets | No implementado |
| Heaps | No implementado |

---

## Próximos Pasos

1. Implementar detectores de Set y Heap
2. Mejorar detección de estructuras anidadas
3. Agregar análisis de complejidad específico por estructura
4. Integrar con sistema de recomendaciones de optimización
5. Soporte para estructuras personalizadas

---

## Referencias

- **CLRS:** Introduction to Algorithms - Capítulos sobre estructuras de datos
- **Data Structures and Algorithms in Python:** Goodrich, Tamassia, Goldwasser
- **Algorithm Design Manual:** Steven Skiena - Capítulo 3

---

**Última actualización:** 2025-01-04

**Versión del módulo:** 1.0.0

---

**Documentos relacionados:**

- [ANALYZER.md](ANALYZER.md) - Módulo de análisis
- [PATTERNS.md](../patterns/README.md) - Módulo de patrones
- [GETTING_STARTED.md](GETTING_STARTED.md) - Guía de inicio