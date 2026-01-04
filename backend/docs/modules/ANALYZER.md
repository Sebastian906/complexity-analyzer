# Modulo 2: Analisis de Complejidad

Documentacion completa del modulo de analisis de complejidad algoritmica.

---

## Tabla de Contenidos

1. [Descripcion General](#descripcion-general)
2. [Arquitectura](#arquitectura)
3. [Componentes](#componentes)
4. [Ecuaciones de Recurrencia](#ecuaciones-de-recurrencia)
5. [Uso](#uso)
6. [Ejemplos](#ejemplos)
7. [API Reference](#api-reference)
8. [Testing](#testing)

---

## Descripcion General

El modulo de analisis es el nucleo del sistema. Recibe un AST (del [Modulo 1 - Parser](../app/core/parser/)) y calcula:

### Analisis Temporal

| Notacion | Descripcion |
|----------|-------------|
| **Big O (O)** | Peor caso |
| **Omega (Omega)** | Mejor caso |
| **Theta (Theta)** | Caso promedio / Cota ajustada |
| **T(n)** | Ecuacion de recurrencia temporal |

### Analisis Espacial

| Componente | Descripcion |
|------------|-------------|
| **S(n)** | Complejidad espacial total |
| **Input Space** | Espacio de entrada |
| **Auxiliary Space** | Espacio auxiliar |
| **Recursion Space** | Profundidad de pila |

### Analisis Adicional

| Analisis | Descripcion |
|----------|-------------|
| **Linea por Linea** | Ejecuciones por linea de codigo |
| **Cotas Fuertes** | Verificacion de Theta |
| **Deteccion de Patrones** | Recursion, loops anidados, etc. |

---

## Arquitectura

```
analyzer/
├── complexity/                    # Analisis de complejidad temporal
│   ├── base_analyzer.py          # Clase base abstracta
│   ├── big_o_analyzer.py         # Peor caso O
│   ├── omega_analyzer.py         # Mejor caso Omega
│   ├── theta_analyzer.py         # Caso promedio Theta
│   ├── tight_bounds.py           # Cotas fuertes
│   └── complexity_calculator.py  # Orquestador
│
├── recurrence/                    # Ecuaciones de recurrencia
│   ├── recurrence_builder.py     # Constructor T(n) y S(n)
│   ├── recurrence_solver.py      # 5 metodos de solucion
│   ├── temporal_complexity.py    # Wrapper T(n)
│   └── spatial_complexity.py     # Wrapper S(n)
│
├── line_by_line_analyzer.py      # Analisis linea por linea
├── execution_counter.py          # Contador de ejecuciones
├── space_analyzer.py             # Analisis espacial
└── analyzer_engine.py            # Motor principal
```

**Archivos principales:**

- [analyzer_engine.py](../app/core/analyzer/analyzer_engine.py) - Motor principal de analisis
- [complexity_calculator.py](../app/core/analyzer/complexity/complexity_calculator.py) - Orquestador de complejidad
- [recurrence_solver.py](../app/core/analyzer/recurrence/recurrence_solver.py) - Solucionador de recurrencias

---

## Componentes

### 1. Analizadores de Complejidad Temporal

#### BigOAnalyzer (Peor Caso)

Analiza el peor escenario posible del algoritmo.

**Archivo:** [big_o_analyzer.py](../app/core/analyzer/complexity/big_o_analyzer.py)

**Estrategias:**

- **Loops:** Multiplicar iteraciones maximas x complejidad del cuerpo
- **Condicionales:** Tomar la rama mas costosa
- **Secuencial:** Sumar y tomar el termino dominante

```python
from app.core.analyzer.complexity.big_o_analyzer import BigOAnalyzer

analyzer = BigOAnalyzer()
result = analyzer.analyze(ast)
print(f"Big O: {result.complexity}")  # O(n^2)
```

#### OmegaAnalyzer (Mejor Caso)

Analiza el mejor escenario posible.

**Archivo:** [omega_analyzer.py](../app/core/analyzer/complexity/omega_analyzer.py)

**Estrategias:**

- **Loops:** Minimo de iteraciones
- **Condicionales:** Rama mas rapida
- **Early Returns:** Detectar salidas tempranas

```python
from app.core.analyzer.complexity.omega_analyzer import OmegaAnalyzer

analyzer = OmegaAnalyzer()
result = analyzer.analyze(ast)
print(f"Omega: {result.complexity}")  # Omega(1)
```

#### ThetaAnalyzer (Caso Promedio)

Calcula Theta solo si O = Omega (cota ajustada).

**Archivo:** [theta_analyzer.py](../app/core/analyzer/complexity/theta_analyzer.py)

```python
from app.core.analyzer.complexity.theta_analyzer import ThetaAnalyzer

analyzer = ThetaAnalyzer()
result = analyzer.analyze(ast)
print(f"Theta: {result.complexity}")  # Theta(n) o None
```

#### TightBoundsCalculator (Cotas Fuertes)

Verifica condiciones para Theta y calcula little-o y little-omega.

**Archivo:** [tight_bounds.py](../app/core/analyzer/complexity/tight_bounds.py)

**Condicion para Theta:**

```
Theta(f(n)) existe <=> O(f(n)) = Omega(f(n))
```

```python
from app.core.analyzer.complexity.tight_bounds import TightBoundsCalculator

calculator = TightBoundsCalculator()
result = calculator.calculate_tight_bounds("O(n^2)", "Omega(n^2)")

if result.has_tight_bound:
    print(f"Cota ajustada: {result.theta}")  # Theta(n^2)
else:
    print("No existe cota ajustada")
```

### 2. ComplexityCalculator (Orquestador)

Coordina todos los analizadores de complejidad.

**Archivo:** [complexity_calculator.py](../app/core/analyzer/complexity/complexity_calculator.py)

```python
from app.core.analyzer.complexity.complexity_calculator import ComplexityCalculator

calculator = ComplexityCalculator()
results = calculator.analyze_all(ast)

print(f"Big O:  {results['big_o']}")    # O(n^2)
print(f"Omega:  {results['omega']}")    # Omega(n^2)
print(f"Theta:  {results['theta']}")    # Theta(n^2)
```

### 3. SpaceAnalyzer (Complejidad Espacial)

Analiza el uso de memoria.

**Archivo:** [space_analyzer.py](../app/core/analyzer/space_analyzer.py)

**Componentes:**

| Componente | Descripcion |
|------------|-------------|
| Input Space | Parametros de entrada |
| Auxiliary Space | Variables locales, arrays temporales |
| Recursion Space | Profundidad de pila |

```python
from app.core.analyzer.space_analyzer import SpaceAnalyzer

analyzer = SpaceAnalyzer()
result = analyzer.analyze(ast)

print(f"S(n) = {result.space_complexity}")      # O(n)
print(f"Auxiliar: {result.auxiliary_space}")    # O(1)
print(f"Recursion: {result.recursion_space}")   # O(log n)
```

### 4. LineByLineAnalyzer

Calcula cuantas veces se ejecuta cada linea.

**Archivo:** [line_by_line_analyzer.py](../app/core/analyzer/line_by_line_analyzer.py)

```python
from app.core.analyzer.line_by_line_analyzer import LineByLineAnalyzer

analyzer = LineByLineAnalyzer()
result = analyzer.analyze(ast)

for line in result.lines:
    print(f"Linea {line.line_number}: {line.execution_count} ejecuciones")
    print(f"  Tipo: {line.statement_type}")
    print(f"  Explicacion: {line.explanation}")
```

### 5. ExecutionCounter

Cuenta ejecuciones por linea y determina complejidad dominante.

**Archivo:** [execution_counter.py](../app/core/analyzer/execution_counter.py)

```python
from app.core.analyzer.execution_counter import ExecutionCounter, count_executions

counter = ExecutionCounter()
result = counter.count(ast, source_code)

print(f"Complejidad dominante: {result['dominant']}")  # O(n^2)
for line_info in result['lines']:
    print(f"Linea {line_info['line']}: {line_info['count']} ejecuciones")
```

### 6. AnalyzerEngine (Motor Principal)

Orquesta todo el analisis completo.

**Archivo:** [analyzer_engine.py](../app/core/analyzer/analyzer_engine.py)

```python
from app.core.analyzer.analyzer_engine import AnalyzerEngine

engine = AnalyzerEngine()
result = engine.analyze(
    ast,
    analyze_line_by_line=True
)

print(f"Algoritmo: {result.algorithm_name}")
print(f"Big O: {result.big_o}")
print(f"Omega: {result.omega}")
print(f"Theta: {result.theta}")
print(f"Tiempo de analisis: {result.analysis_time}s")
```

---

## Ecuaciones de Recurrencia

### Formas de Ecuaciones

El sistema soporta 7 formas de ecuaciones de recurrencia:

#### Divide y Venceras

| Forma | Ecuacion | Descripcion |
|-------|----------|-------------|
| F0 | `T(n) = T(n/b) + f(n)` | Una division |
| F1 | `T(n) = aT(n/b) + f(n)` | Division multiple uniforme |
| F2 | `T(n) = T(n/b) + T(n/c) + f(n)` | Division dual no uniforme |
| F3 | `T(n) = T(n/b) + T(n/c) + ... + f(n)` | Division multiple |

#### Resta y Venceras

| Forma | Ecuacion | Descripcion |
|-------|----------|-------------|
| F4 | `T(n) = T(n-b) + f(n)` | Una resta |

#### Resta y seras Vencido

| Forma | Ecuacion | Descripcion |
|-------|----------|-------------|
| F5 | `T(n) = aT(n-b) + f(n)` | Resta multiple uniforme |
| F6 | `T(n) = aT(n-b) + cT(n-d) + f(n)` | Resta multiple no uniforme |

### Metodos de Solucion

El sistema implementa 5 metodos para resolver ecuaciones:

| Metodo | F0 | F1 | F2 | F3 | F4 | F5 | F6 |
|--------|----|----|----|----|----|----|-----|
| Iteracion | SI | SI | NO | NO | SI | SI | NO |
| Arbol de Recursion | SI | SI | SI | SI | NO | SI | SI |
| Teorema Maestro | SI | SI | NO | NO | NO | NO | NO |
| Sustitucion Inteligente | SI | SI | SI | SI | SI | SI | SI |
| Ecuacion Caracteristica | NO | NO | NO | NO | SI | SI | SI |

#### 1. Metodo de Iteracion

Expande la ecuacion iterativamente hasta el caso base.

```python
from app.core.analyzer.recurrence import solve_recurrence, SolutionMethod

result = solve_recurrence(
    "T(n) = T(n/2) + n",
    method=SolutionMethod.ITERATION
)
print(result.complexity)  # "n"
```

#### 2. Arbol de Recursion

Construye el arbol nivel por nivel.

```python
result = solve_recurrence(
    "T(n) = 2T(n/2) + n",
    method=SolutionMethod.RECURSION_TREE
)
print(result.complexity)  # "n log n"
```

#### 3. Teorema Maestro

Aplica uno de los 3 casos del Master Theorem.

**Forma:** `T(n) = aT(n/b) + f(n)`

**Casos:**

1. Si `f(n) = O(n^c)` donde `c < log_b(a)` entonces `T(n) = Theta(n^log_b(a))`
2. Si `f(n) = Theta(n^log_b(a))` entonces `T(n) = Theta(n^log_b(a) * log n)`
3. Si `f(n) = Omega(n^c)` donde `c > log_b(a)` entonces `T(n) = Theta(f(n))`

```python
result = solve_recurrence(
    "T(n) = 2T(n/2) + n",
    method=SolutionMethod.MASTER_THEOREM
)
print(result.complexity)  # "n log n" (Caso 2)
```

#### 4. Sustitucion Inteligente

Hace conjetura educada y verifica por induccion.

```python
result = solve_recurrence(
    "T(n) = T(n-1) + T(n-2) + 1",
    method=SolutionMethod.SMART_SUBSTITUTION
)
```

#### 5. Ecuacion Caracteristica

Para recurrencias lineales (F4, F5, F6).

```python
result = solve_recurrence(
    "T(n) = 2T(n-1) + 1",
    method=SolutionMethod.CHARACTERISTIC_EQUATION
)
print(result.complexity)  # "2^n"
```

### RecurrenceBuilder

Construye ecuaciones automaticamente del AST.

**Archivo:** [recurrence_builder.py](../app/core/analyzer/recurrence/recurrence_builder.py)

```python
from app.core.analyzer.recurrence import build_recurrence_equations

# Construir ambas ecuaciones
t_n, s_n = build_recurrence_equations(ast, "fibonacci")

print(f"T(n): {t_n.equation}")  # T(n) = 2T(n-1) + O(1)
print(f"S(n): {s_n.equation}")  # S(n) = S(n-1) + O(1)
```

### TemporalComplexityAnalyzer

Wrapper especializado para T(n).

**Archivo:** [temporal_complexity.py](../app/core/analyzer/recurrence/temporal_complexity.py)

```python
from app.core.analyzer.recurrence import analyze_temporal_complexity

result = analyze_temporal_complexity(t_n, fallback="n")

print(f"Big O: {result.big_o}")
print(f"Metodo: {result.solution.method_used.value}")
print(f"Pasos:")
for step in result.solution.steps:
    print(f"  {step}")
```

### SpatialComplexityAnalyzer

Wrapper especializado para S(n).

**Archivo:** [spatial_complexity.py](../app/core/analyzer/recurrence/spatial_complexity.py)

```python
from app.core.analyzer.recurrence import analyze_spatial_complexity

result = analyze_spatial_complexity(
    s_n,
    input_space="n",
    auxiliary_space="1"
)

print(f"S(n): {result.space_complexity}")
print(f"Desglose:")
print(f"  Input: {result.input_space}")
print(f"  Auxiliar: {result.auxiliary_space}")
print(f"  Recursion: {result.recursion_space}")
```

---

## Uso

### Flujo Completo

```python
from app.core.parser import parse_pseudocode
from app.core.analyzer.analyzer_engine import AnalyzerEngine
from app.core.analyzer.recurrence import build_recurrence_equations

# 1. Parsear codigo
code = """
algorithm mergeSort(A[n])
begin
    if n > 1 then
    begin
        mid <- n / 2
        call mergeSort(A[1..mid])
        call mergeSort(A[mid+1..n])
        call merge(A, mid)
    end
end
"""

ast = parse_pseudocode(code)

# 2. Analisis basico
engine = AnalyzerEngine()
result = engine.analyze(ast, analyze_line_by_line=True)

print(f"Big O: {result.big_o}")        # O(n log n)
print(f"Omega: {result.omega}")        # Omega(n log n)
print(f"Theta: {result.theta}")        # Theta(n log n)

# 3. Ecuaciones de recurrencia
t_n, s_n = build_recurrence_equations(ast, "mergeSort")

if t_n:
    print(f"T(n): {t_n.equation}")      # T(n) = 2T(n/2) + O(n)
    print(f"Patron: {t_n.recursion_pattern}")  # "binary"

if s_n:
    print(f"S(n): {s_n.equation}")      # S(n) = S(n/2) + O(1)

# 4. Analisis linea por linea
for line in result.line_by_line.lines[:5]:
    print(f"Linea {line.line_number}: {line.execution_count}")
```

### Via API REST

```bash
curl -X POST http://localhost:8000/api/v1/analysis/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "code": "algorithm test(n)\nbegin\n  for i <- 1 to n do\n    x <- x + 1\nend",
    "analyze_temporal": true,
    "analyze_spatial": true,
    "analyze_line_by_line": true,
    "analyze_recurrence": true
  }'
```

**Endpoints relacionados:**

- Ver [router.py](../app/api/v1/router.py) para rutas disponibles
- Ver [analysis.py](../app/api/v1/endpoints/analysis.py) para implementacion

---

## Ejemplos

### Ejemplo 1: Busqueda Lineal

```python
code = """
algorithm linearSearch(A[n], x)
begin
    for i <- 1 to n do
    begin
        if A[i] = x then
            return i
    end
    return -1
end
"""

# Resultados:
# Big O: O(n)      <- recorre todo el array
# Omega: Omega(1)  <- encuentra en primera posicion
# Theta: No existe <- O != Omega
# S(n): O(1)       <- solo variable i
```

### Ejemplo 2: Merge Sort

```python
code = """
algorithm mergeSort(A[n])
begin
    if n > 1 then
    begin
        mid <- n / 2
        call mergeSort(A[1..mid])
        call mergeSort(A[mid+1..n])
        call merge(A, mid)
    end
end
"""

# Resultados:
# Big O: O(n log n)
# Omega: Omega(n log n)
# Theta: Theta(n log n)  <- Cota ajustada
# T(n) = 2T(n/2) + O(n)
# S(n) = O(log n)        <- profundidad de pila
```

### Ejemplo 3: Fibonacci Recursivo

```python
code = """
algorithm fibonacci(n)
begin
    if n <= 1 then
        return n
    
    return fibonacci(n - 1) + fibonacci(n - 2)
end
"""

# Resultados:
# Big O: O(2^n)      <- arbol binario completo
# Omega: Omega(2^n)  <- siempre expande todo
# Theta: Theta(2^n)  <- cota ajustada
# T(n) = T(n-1) + T(n-2) + O(1)
# S(n) = O(n)        <- profundidad maxima n
```

---

## API Reference

### AnalyzerEngine

**Archivo:** [analyzer_engine.py](../app/core/analyzer/analyzer_engine.py)

```python
class AnalyzerEngine:
    def analyze(
        self,
        ast: ProgramNode,
        analyze_line_by_line: bool = True,
        analyze_space: bool = True,
        analyze_recurrence: bool = True,
        analyze_tight_bounds: bool = True
    ) -> AnalysisResult
```

### ComplexityCalculator

**Archivo:** [complexity_calculator.py](../app/core/analyzer/complexity/complexity_calculator.py)

```python
class ComplexityCalculator:
    def analyze_all(self, ast: ProgramNode) -> Dict[str, str]
```

### RecurrenceSolver

**Archivo:** [recurrence_solver.py](../app/core/analyzer/recurrence/recurrence_solver.py)

```python
class RecurrenceSolver:
    def solve(
        self,
        equation: str,
        base_case: Optional[str] = None,
        preferred_method: Optional[SolutionMethod] = None
    ) -> SolutionResult
```

### Helper Functions

```python
# Resolver ecuacion
from app.core.analyzer.recurrence import solve_recurrence

result = solve_recurrence("T(n) = 2T(n/2) + n")

# Construir ecuaciones
from app.core.analyzer.recurrence import build_recurrence_equations

t_n, s_n = build_recurrence_equations(ast, "algorithm_name")

# Analisis temporal
from app.core.analyzer.recurrence import analyze_temporal_complexity

temporal_result = analyze_temporal_complexity(t_n)

# Analisis espacial
from app.core.analyzer.recurrence import analyze_spatial_complexity

spatial_result = analyze_spatial_complexity(s_n)
```

---

## Testing

### Ejecutar Tests

```bash
# Todos los tests del modulo
pytest tests/unit/test_recurrence.py -v

# Tests especificos
pytest tests/unit/test_recurrence.py::TestRecurrenceSolver -v

# Con coverage
pytest tests/unit/test_recurrence.py --cov=app.core.analyzer.recurrence --cov-report=html

# Tests del execution counter
pytest tests/unit/test_execution_counter.py -v
```

### Tests Importantes

**Archivo:** [test_recurrence.py](../tests/unit/test_recurrence.py)

```python
def test_build_linear_recursion()
def test_build_binary_recursion()
def test_master_theorem_case1()
def test_master_theorem_case2()
def test_iteration_method()
def test_characteristic_equation()
```

**Archivo:** [test_execution_counter.py](../tests/unit/test_execution_counter.py)

```python
def test_simple_assignment()
def test_single_for_loop()
def test_nested_for_loops()
def test_triple_nested_loops()
def test_while_with_division()
```

---

## Limitaciones Actuales

| Limitacion | Estado |
|------------|--------|
| Analisis Amortizado | No implementado |
| Estructuras Complejas | Solo arrays basicos |
| Punteros | No disponible |
| Casos promedio probabilisticos | Simplificado |

---

## Proximos Pasos

1. Implementar analisis amortizado
2. Mejorar deteccion de estructuras de datos
3. Agregar mas patrones de recurrencia
4. Optimizar precision del analisis espacial
5. Soporte para algoritmos probabilisticos

---

## Referencias

- **CLRS:** Introduction to Algorithms (3rd Edition)
- **Cormen et al.:** Capitulos 3, 4 (Recurrencias)
- **Algorithm Design Manual:** Steven Skiena
- **Master Theorem:** Casos y aplicaciones
- **Ecuaciones Caracteristicas:** Teoria de recurrencias lineales

---

**Ultima actualizacion:** 2025-01-03

**Version del modulo:** 1.0.0

---

**Documentos relacionados:**

- [GETTING_STARTED.md](GETTING_STARTED.md) - Guia de inicio
- [QUICKSTART.md](QUICKSTART.md) - Inicio rapido
- [DEBUGGING.md](DEBUGGING.md) - Guia de depuracion
