# Modulo 3: Deteccion de Patrones Algoritmicos

Documentacion completa del modulo de deteccion automatica de patrones y tecnicas algoritmicas.

---

## Tabla de Contenidos

1. [Descripcion General](#descripcion-general)
2. [Arquitectura](#arquitectura)
3. [Patrones Soportados](#patrones-soportados)
4. [Componentes](#componentes)
5. [Sistema de Scoring](#sistema-de-scoring)
6. [Uso](#uso)
7. [API Reference](#api-reference)
8. [Ejemplos](#ejemplos)
9. [Testing](#testing)
10. [Integracion con Modulos](#integracion-con-modulos)

---

## Descripcion General

El modulo de patrones identifica automaticamente las tecnicas algoritmicas utilizadas en un algoritmo mediante analisis estatico del AST.

### Funcionalidades Principales

| Funcionalidad | Descripcion |
|---------------|-------------|
| **Deteccion Automatica** | Identifica 12+ patrones algoritmicos |
| **Nivel de Confianza** | Score de 0.0 a 1.0 por cada patron detectado |
| **Indicadores** | Lista de evidencias encontradas por patron |
| **Ranking** | Ordena patrones por confianza |
| **Resolucion de Conflictos** | Maneja patrones mutuamente excluyentes |

### Patrones Detectables

| Categoria | Patrones |
|-----------|----------|
| **Basicos** | Fuerza Bruta, Recursion |
| **Divide y Venceras** | Division, Combinacion, Caso Base |
| **Optimizacion** | Programacion Dinamica, Greedy |
| **Busqueda** | Backtracking, Branch and Bound |
| **Ordenamiento** | Sorting, Searching |
| **Avanzados** | Quantico, Bio-inspirado, Aproximacion |

---

## Arquitectura

```
patterns/
├── __init__.py                     # Exports principales
├── base_pattern.py                 # Clases base y tipos
├── pattern_detector.py             # Detector principal (orquestador)
├── pattern_matcher.py              # Utilidades de matching en AST
├── pattern_scorer.py               # Sistema de scoring y ranking
│
└── detectors/                      # Detectores especificos
    ├── __init__.py
    ├── brute_force.py              # Fuerza Bruta
    ├── recursive_detector.py       # Recursion
    ├── divide_conquer_detector.py  # Divide y Venceras
    ├── dynamic_programming_detector.py  # Programacion Dinamica
    ├── greedy_detector.py          # Algoritmos Greedy
    ├── backtracking_detector.py    # Backtracking
    ├── branch_bound_detector.py    # Branch and Bound
    ├── sorting_and_searching.py    # Ordenamiento y Busqueda
    └── advanced_patterns.py        # Patrones Avanzados
```

**Archivos principales:**

- [pattern_detector.py](../app/core/patterns/pattern_detector.py) - Orquestador principal
- [base_pattern.py](../app/core/patterns/base_pattern.py) - Clases base y tipos
- [pattern_scorer.py](../app/core/patterns/pattern_scorer.py) - Sistema de scoring

---

## Patrones Soportados

### 1. Fuerza Bruta

**Indicadores clave:**
- Multiples loops anidados (profundidad >= 2)
- Exploracion exhaustiva sin poda
- Ausencia de memorizacion
- Patron de swap (intercambio)

**Complejidad tipica:** O(n^2) a O(2^n)

```
algorithm bruteForceSearch(A[n], target)
begin
    for i <- 1 to n do
        for j <- 1 to n do
            if (A[i] + A[j] = target) then
                return true
            end
        end
    end
    return false
end
```

### 2. Recursion

**Indicadores clave:**
- Llamadas recursivas al mismo algoritmo
- Caso base para terminar recursion
- Reduccion del problema en cada llamada
- Posible recursion de cola

**Complejidad tipica:** Variable (depende del patron)

```
algorithm factorial(n)
begin
    if (n <= 1) then
        return 1
    end
    return n * factorial(n - 1)
end
```

### 3. Divide y Venceras

**Indicadores clave:**
- Division del problema en partes (n/2)
- Multiples llamadas recursivas (>= 2)
- Combinacion de soluciones parciales
- Caso base para problemas pequenos

**Complejidad tipica:** O(n log n)

```
algorithm mergeSort(A[n], low, high)
begin
    if (low < high) then
        mid <- floor((low + high) / 2)
        call mergeSort(A, low, mid)
        call mergeSort(A, mid + 1, high)
        call merge(A, low, mid, high)
    end
end
```

### 4. Programacion Dinamica

**Indicadores clave:**
- Uso de tabla de memorizacion
- Subproblemas superpuestos
- Estructura optima de subproblemas
- Acceso a valores previamente calculados

**Complejidad tipica:** O(n^2) o O(n*m)

```
algorithm fibonacci(n)
begin
    dp[1] <- 1
    dp[2] <- 1
    for i <- 3 to n do
        dp[i] <- dp[i-1] + dp[i-2]
    end
    return dp[n]
end
```

### 5. Greedy (Voraz)

**Indicadores clave:**
- Seleccion del optimo local
- Ordenamiento previo (frecuentemente)
- Sin reconsideracion de decisiones
- Construccion incremental de solucion

**Complejidad tipica:** O(n log n) o O(n)

```
algorithm coinChange(coins[n], amount)
begin
    call sort(coins)  // Ordenar descendente
    count <- 0
    for i <- n to 1 do
        while (amount >= coins[i]) do
            amount <- amount - coins[i]
            count <- count + 1
        end
    end
    return count
end
```

### 6. Backtracking

**Indicadores clave:**
- Exploracion de espacio de soluciones
- Condiciones de poda (pruning)
- Retroceso cuando no hay solucion
- Construccion incremental con validacion

**Complejidad tipica:** O(2^n) o O(n!)

```
algorithm nQueens(board[n][n], col)
begin
    if (col > n) then
        return true
    end
    for row <- 1 to n do
        if (isSafe(board, row, col)) then
            board[row][col] <- 1
            if (nQueens(board, col + 1)) then
                return true
            end
            board[row][col] <- 0  // Backtrack
        end
    end
    return false
end
```

### 7. Branch and Bound

**Indicadores clave:**
- Calculo de cotas (bounds)
- Poda basada en cotas
- Cola de prioridad o heap
- Exploracion selectiva

**Complejidad tipica:** Exponencial con poda

```
algorithm branchAndBound(nodes)
begin
    queue <- createPriorityQueue()
    call enqueue(queue, root)
    while (not isEmpty(queue)) do
        node <- dequeue(queue)
        if (bound(node) < bestSolution) then
            if (isComplete(node)) then
                bestSolution <- node.value
            else
                call expandNode(node, queue)
            end
        end
    end
end
```

### 8. Ordenamiento

**Indicadores clave:**
- Comparaciones entre elementos
- Operaciones de intercambio (swap)
- Nombre del algoritmo (sort, ordenar)
- Patrones tipicos de sorting

**Complejidad tipica:** O(n log n) o O(n^2)

### 9. Busqueda

**Indicadores clave:**
- Comparacion con valor objetivo
- Division del espacio de busqueda
- Retorno al encontrar elemento
- Variable target/objetivo

**Complejidad tipica:** O(log n) o O(n)

### 10. Patrones Avanzados

**Quantico:**
- Operaciones de superposicion
- Medicion cuantica
- Puertas cuanticas

**Bio-inspirado:**
- Poblaciones de soluciones
- Operadores geneticos (mutacion, cruce)
- Fitness y seleccion

**Aproximacion:**
- Soluciones aproximadas
- Garantias de ratio
- Heuristicas

---

## Componentes

### 1. PatternDetector (Orquestador)

Coordina la ejecucion de todos los detectores y proporciona resultados unificados.

**Archivo:** [pattern_detector.py](../app/core/patterns/pattern_detector.py)

```python
from app.core.patterns import PatternDetector

detector = PatternDetector()
result = detector.detect(ast, min_confidence=0.3)

print(f"Patron primario: {result.primary_pattern_name}")
print(f"Confianza: {result.primary_confidence:.2%}")
print(f"Total patrones: {result.pattern_count}")
```

**Metodos principales:**

| Metodo | Descripcion |
|--------|-------------|
| `detect(ast, min_confidence)` | Detecta todos los patrones |
| `detect_specific(ast, pattern_type)` | Detecta un patron especifico |
| `get_available_patterns()` | Lista patrones disponibles |

### 2. BasePatternDetector (Clase Base)

Interfaz abstracta para todos los detectores especificos.

**Archivo:** [base_pattern.py](../app/core/patterns/base_pattern.py)

**Metodos abstractos:**

```python
class BasePatternDetector(ABC):
    @abstractmethod
    def detect(self, ast: ASTNode) -> PatternMatch:
        """Detecta si el patron esta presente"""
        pass

    @abstractmethod
    def _analyze_structure(self, ast: ASTNode) -> Dict[str, Any]:
        """Analiza estructura buscando caracteristicas"""
        pass
```

**Metodos heredados:**

| Metodo | Descripcion |
|--------|-------------|
| `_calculate_confidence()` | Calcula score basado en indicadores |
| `_create_match()` | Crea objeto PatternMatch |

### 3. PatternMatch (Resultado)

Encapsula el resultado de deteccion de un patron.

```python
@dataclass
class PatternMatch:
    pattern_type: PatternType
    pattern_name: str
    confidence: float
    confidence_level: ConfidenceLevel
    indicators_found: List[PatternIndicator]
    indicators_missing: List[PatternIndicator]
    reasoning: str
    typical_complexity: Optional[str]
    metadata: Dict[str, Any]
```

**Propiedades utiles:**

| Propiedad | Descripcion |
|-----------|-------------|
| `is_confident` | True si confianza >= 0.7 |
| `total_indicators` | Total de indicadores evaluados |
| `found_ratio` | Proporcion de indicadores encontrados |

### 4. PatternIndicator

Representa una evidencia individual de un patron.

```python
@dataclass
class PatternIndicator:
    name: str           # Identificador del indicador
    description: str    # Descripcion legible
    found: bool         # Si fue encontrado
    weight: float       # Peso en el calculo de confianza
    evidence: str       # Evidencia encontrada
    location: str       # Ubicacion en el AST
```

### 5. PatternScorer

Sistema de scoring y resolucion de conflictos.

**Archivo:** [pattern_scorer.py](../app/core/patterns/pattern_scorer.py)

```python
from app.core.patterns import PatternScorer

scorer = PatternScorer()
scored_patterns = scorer.score_patterns(raw_patterns)
primary = scorer.get_primary_pattern(scored_patterns)
```

---

## Sistema de Scoring

### Calculo de Confianza

La confianza se calcula como:

```
confianza = suma(pesos_indicadores_encontrados) / suma(pesos_totales)
```

### Ajustes de Score

| Ajuste | Valor | Condicion |
|--------|-------|-----------|
| Bonus alta confianza | +10% | confianza >= 0.80 |
| Penalizacion indicadores faltantes | -10% | ratio_faltantes > 0.5 |
| Penalizacion conflictos | -15% | patrones en conflicto |

### Patrones Mutuamente Excluyentes

Algunos patrones no pueden coexistir con alta confianza:

| Patron | Conflictos |
|--------|------------|
| Fuerza Bruta | Programacion Dinamica, Greedy |
| Programacion Dinamica | Fuerza Bruta |
| Greedy | Fuerza Bruta, Backtracking |

### Niveles de Confianza

| Nivel | Rango | Descripcion |
|-------|-------|-------------|
| `VERY_HIGH` | >= 0.9 | Deteccion muy segura |
| `HIGH` | 0.7 - 0.9 | Deteccion confiable |
| `MEDIUM` | 0.5 - 0.7 | Deteccion probable |
| `LOW` | 0.3 - 0.5 | Deteccion posible |
| `VERY_LOW` | < 0.3 | Deteccion debil |

---

## Uso

### Uso Basico - Python

```python
from app.core.parser import parse_pseudocode
from app.core.patterns import PatternDetector

code = """
algorithm mergeSort(A[n], low, high)
begin
    if (low < high) then
        mid <- floor((low + high) / 2)
        call mergeSort(A, low, mid)
        call mergeSort(A, mid + 1, high)
        call merge(A, low, mid, high)
    end
end
"""

# Parsear codigo
ast = parse_pseudocode(code)

# Detectar patrones
detector = PatternDetector()
result = detector.detect(ast)

# Resultados
print(f"Patron principal: {result.primary_pattern_name}")
print(f"Confianza: {result.primary_confidence:.2%}")
```

### Deteccion con Umbral Personalizado

```python
# Solo patrones con alta confianza
result = detector.detect(ast, min_confidence=0.7)

for pattern in result.confident_patterns:
    print(f"{pattern.pattern.pattern_name}: {pattern.final_score:.2%}")
```

### Deteccion de Patron Especifico

```python
from app.core.patterns import PatternType

# Buscar solo recursion
match = detector.detect_specific(ast, PatternType.RECURSIVE)

if match and match.confidence >= 0.7:
    print("Algoritmo recursivo detectado")
    print(f"Tipo: {match.metadata.get('recursion_type')}")
```

### Acceso a Indicadores

```python
result = detector.detect(ast)

if result.primary_pattern:
    pattern = result.primary_pattern.pattern
    
    print("Indicadores encontrados:")
    for ind in pattern.indicators_found:
        print(f"  + {ind.name}: {ind.evidence}")
    
    print("Indicadores faltantes:")
    for ind in pattern.indicators_missing:
        print(f"  - {ind.name}: {ind.description}")
```

### Manejo de Conflictos

```python
result = detector.detect(ast)

for scored in result.all_patterns:
    if scored.conflicts:
        print(f"{scored.pattern.pattern_name} conflicta con: {scored.conflicts}")
```

---

## API Reference

### Tipos y Enums

```python
class PatternType(str, Enum):
    BRUTE_FORCE = "brute_force"
    RECURSIVE = "recursive"
    DIVIDE_AND_CONQUER = "divide_and_conquer"
    DYNAMIC_PROGRAMMING = "dynamic_programming"
    GREEDY = "greedy"
    BACKTRACKING = "backtracking"
    BRANCH_AND_BOUND = "branch_and_bound"
    SORTING = "sorting"
    SEARCHING = "searching"
    QUANTUM = "quantum"
    BIO_INSPIRED = "bio_inspired"
    APPROXIMATION = "approximation"

class ConfidenceLevel(str, Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"
```

### PatternDetector

```python
class PatternDetector:
    def detect(
        self,
        ast: ASTNode,
        min_confidence: Optional[float] = None
    ) -> PatternDetectionResult:
        """Detecta todos los patrones presentes"""

    def detect_specific(
        self,
        ast: ASTNode,
        pattern_type: PatternType
    ) -> Optional[PatternMatch]:
        """Detecta un patron especifico"""

    def get_available_patterns(self) -> List[str]:
        """Retorna lista de patrones disponibles"""
```

### PatternDetectionResult

```python
@dataclass
class PatternDetectionResult:
    primary_pattern: Optional[ScoredPattern]
    all_patterns: List[ScoredPattern]
    confident_patterns: List[ScoredPattern]
    summary: str
    metadata: Dict[str, Any]

    @property
    def has_patterns(self) -> bool: ...
    @property
    def pattern_count(self) -> int: ...
    @property
    def primary_pattern_name(self) -> Optional[str]: ...
    @property
    def primary_confidence(self) -> float: ...
```

### PatternScorer

```python
class PatternScorer:
    def score_patterns(
        self,
        patterns: List[PatternMatch]
    ) -> List[ScoredPattern]:
        """Asigna scores finales y rankea"""

    def filter_by_confidence(
        self,
        patterns: List[ScoredPattern],
        min_confidence: float
    ) -> List[ScoredPattern]:
        """Filtra por umbral de confianza"""

    def get_primary_pattern(
        self,
        patterns: List[ScoredPattern]
    ) -> Optional[ScoredPattern]:
        """Obtiene el patron con mayor score"""
```

---

## Ejemplos

### Deteccion de Fuerza Bruta

```python
code = """
algorithm bubbleSort(A[n])
begin
    for i <- 1 to n-1 do
        for j <- 1 to n-i do
            if (A[j] > A[j+1]) then
                temp <- A[j]
                A[j] <- A[j+1]
                A[j+1] <- temp
            end
        end
    end
end
"""

ast = parse_pseudocode(code)
result = detector.detect(ast)

# Esperado: Fuerza Bruta con alta confianza
# Indicadores: nested_loops, swap_pattern, no_memoization
```

### Deteccion de Divide y Venceras

```python
code = """
algorithm binarySearch(A[n], target, low, high)
begin
    if (low > high) then
        return -1
    end
    
    mid <- floor((low + high) / 2)
    
    if (A[mid] = target) then
        return mid
    end
    
    if (A[mid] > target) then
        return binarySearch(A, target, low, mid - 1)
    else
        return binarySearch(A, target, mid + 1, high)
    end
end
"""

# Esperado: Divide y Venceras + Busqueda
# Indicadores: problem_division, recursive_solution, base_case
```

### Deteccion de Programacion Dinamica

```python
code = """
algorithm longestCommonSubsequence(X[m], Y[n])
begin
    for i <- 0 to m do
        dp[i][0] <- 0
    end
    for j <- 0 to n do
        dp[0][j] <- 0
    end
    
    for i <- 1 to m do
        for j <- 1 to n do
            if (X[i] = Y[j]) then
                dp[i][j] <- dp[i-1][j-1] + 1
            else
                dp[i][j] <- max(dp[i-1][j], dp[i][j-1])
            end
        end
    end
    
    return dp[m][n]
end
"""

# Esperado: Programacion Dinamica
# Indicadores: memoization_table, overlapping_subproblems
```

---

## Testing

### Ejecutar Tests

```bash
# Tests del modulo patterns
pytest tests/unit/test_patterns.py -v

# Tests de detectores especificos
pytest tests/unit/test_detectors.py -v

# Cobertura
pytest tests/unit/test_patterns.py --cov=app/core/patterns
```

### Tests Unitarios Incluidos

| Test | Descripcion |
|------|-------------|
| `test_brute_force_detection` | Deteccion de fuerza bruta |
| `test_recursive_detection` | Deteccion de recursion |
| `test_divide_conquer_detection` | Deteccion de divide y venceras |
| `test_dp_detection` | Deteccion de programacion dinamica |
| `test_greedy_detection` | Deteccion de algoritmos greedy |
| `test_pattern_ranking` | Ranking de patrones |
| `test_conflict_resolution` | Resolucion de conflictos |

---

## Integracion con Modulos

El modulo de patrones se integra con otros modulos del sistema:

```
   ┌─────────────────┐
   │     Parser      │  Modulo 1
   │   (Genera AST)  │
   └────────┬────────┘
            │ AST
            ▼
   ┌─────────────────┐
   │    Analyzer     │  Modulo 2
   │  (Complejidad)  │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │    Patterns     │  Modulo 3 (Este modulo)
   │  (Deteccion)    │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ Data Structures │  Modulo 3.5
   │  (Estructuras)  │
   └─────────────────┘
```

**Dependencias:**

- Requiere AST del [Parser](PARSER.md)
- Complementa el analisis de [Analyzer](ANALYZER.md)
- Trabaja junto con [Data Structures](DATA_STRUCTURES.md)

### Uso Combinado

```python
from app.core.parser import parse_pseudocode
from app.core.analyzer import AnalyzerEngine
from app.core.patterns import PatternDetector

# 1. Parsear
ast = parse_pseudocode(code)

# 2. Analizar complejidad
analyzer = AnalyzerEngine()
complexity = analyzer.analyze(ast)

# 3. Detectar patrones
detector = PatternDetector()
patterns = detector.detect(ast)

# 4. Resultado combinado
print(f"Algoritmo: {ast.algorithm.name}")
print(f"Complejidad: {complexity.big_o}")
print(f"Patron: {patterns.primary_pattern_name}")
```
