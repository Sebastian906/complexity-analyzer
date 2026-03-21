# Guía de Análisis de Complejidad

Guía completa para entender cómo el sistema analiza y calcula la complejidad de algoritmos, incluyendo notaciones, ecuaciones de recurrencia y ejemplos prácticos.

---

## Tabla de Contenidos

1. [Introducción](#introducción)
2. [Notaciones de Complejidad](#notaciones-de-complejidad)
3. [Clases de Complejidad](#clases-de-complejidad)
4. [Cómo el Sistema Calcula la Complejidad](#cómo-el-sistema-calcula-la-complejidad)
5. [Complejidad Temporal](#complejidad-temporal)
6. [Complejidad Espacial](#complejidad-espacial)
7. [Análisis Línea por Línea](#análisis-línea-por-línea)
8. [Ecuaciones de Recurrencia](#ecuaciones-de-recurrencia)
9. [Métodos de Solución](#métodos-de-solución)
10. [Ejemplos de Análisis](#ejemplos-de-análisis)
11. [Patrones y su Complejidad Típica](#patrones-y-su-complejidad-típica)
12. [Limitaciones del Análisis](#limitaciones-del-análisis)

---

## Introducción

El análisis de complejidad permite predecir el comportamiento de un algoritmo cuando el tamaño de su entrada crece. En lugar de medir tiempos concretos en segundos, se estudia cómo crece el número de operaciones o la memoria utilizada en función del tamaño de la entrada `n`.

El sistema realiza el análisis directamente sobre el árbol sintáctico abstracto (AST) del algoritmo, identificando patrones estructurales como ciclos, recursión y subproblemas para derivar la complejidad de forma automática.

---

## Notaciones de Complejidad

El sistema calcula tres notaciones para cada algoritmo:

### Big O - Notación O(f(n))

Describe el **peor caso**: el máximo número de operaciones que el algoritmo ejecutará para una entrada de tamaño `n`. Es la notación más utilizada en la práctica porque garantiza que el algoritmo no superará ese límite.

Formalmente: T(n) = O(f(n)) significa que existen constantes c > 0 y n0 tal que T(n) <= c * f(n) para todo n >= n0.

**Ejemplo:** Un algoritmo con dos ciclos anidados, cada uno de n iteraciones, tiene T(n) = O(n^2).

### Omega - Notación Omega(f(n))

Describe el **mejor caso**: el mínimo número de operaciones que el algoritmo podría ejecutar. Útil para conocer cuándo el algoritmo se comporta óptimamente.

Formalmente: T(n) = Omega(f(n)) significa que existen c > 0 y n0 tal que T(n) >= c * f(n) para todo n >= n0.

**Ejemplo:** Un algoritmo de búsqueda que puede encontrar el elemento en la primera posición tiene Omega(1).

### Theta - Notación Theta(f(n))

Describe el **caso ajustado**: solo existe cuando el mejor caso y el peor caso son iguales (la misma función de crecimiento). Theta ofrece la descripción más precisa del comportamiento del algoritmo.

Formalmente: T(n) = Theta(f(n)) si y solo si T(n) = O(f(n)) Y T(n) = Omega(f(n)).

**Ejemplo:** Merge Sort siempre ejecuta en Theta(n log n), independientemente de la entrada.

### Cuándo existe Theta

Si el peor caso y el mejor caso son distintos, Theta no existe. Por ejemplo:

- Búsqueda lineal: O(n) en peor caso, Omega(1) en mejor caso. Theta no existe.
- Merge Sort: O(n log n) en peor caso, Omega(n log n) en mejor caso. Theta(n log n) existe.

---

## Clases de Complejidad

Las clases de complejidad, ordenadas de menor a mayor crecimiento:

| Notación | Nombre | Descripción |
|----------|--------|-------------|
| O(1) | Constante | El tiempo no depende de n. Acceso a un índice de array. |
| O(log n) | Logarítmica | El problema se divide en cada paso. Búsqueda binaria. |
| O(n) | Lineal | Se recorre la entrada una vez. Búsqueda lineal. |
| O(n log n) | Linealítmica | División con combinación lineal. Merge Sort, Heap Sort. |
| O(n^2) | Cuadrática | Dos ciclos anidados sobre n. Bubble Sort, Insertion Sort. |
| O(n^3) | Cúbica | Tres ciclos anidados. Multiplicación de matrices naive. |
| O(2^n) | Exponencial | Exploración de todos los subconjuntos. Fibonacci recursivo simple. |
| O(n!) | Factorial | Permutaciones. Problema del viajante por fuerza bruta. |

---

## Cómo el Sistema Calcula la Complejidad

El sistema sigue un proceso de análisis estático en tres etapas:

### Etapa 1: Análisis del AST

El árbol sintáctico abstracto (AST) es recorrido de forma recursiva. Cada tipo de nodo contribuye a la complejidad total:

- **Secuencia de sentencias:** Se suma la complejidad de cada sentencia y se toma el término dominante.
- **Asignación simple:** O(1).
- **Llamada a función conocida:** Se usa la complejidad declarada de esa función.
- **Ciclo FOR:** Se multiplica la complejidad del cuerpo por el número de iteraciones del ciclo.
- **Ciclo WHILE:** Se estima el número máximo de iteraciones basándose en las condiciones.
- **Condicional IF:** En Big O se toma la rama más costosa; en Omega se toma la rama más barata.
- **Llamada recursiva:** Se construye la ecuación de recurrencia.

### Etapa 2: Simplificación

La complejidad resultante se simplifica descartando constantes y términos de menor orden:

- O(3n^2 + 5n + 1) se simplifica a O(n^2).
- O(n + n log n) se simplifica a O(n log n).

### Etapa 3: Determinación de Theta

Se comparan el resultado de Big O y Omega. Si son funcionalmente equivalentes (misma clase de crecimiento), se calcula Theta. En caso contrario, se reporta que Theta no existe para ese algoritmo.

## Implementación y notas de ejecución

Notas sobre la implementación práctica del análisis:

- El análisis operativo está implementado por `AnalyzerEngine` y orquestado por `AnalysisOrchestrator` (ver `app/services/analysis_orchestrator.py`). El orquestador ejecuta pipelines compuestos por pasos como parseo, detección de estructuras, análisis de complejidad, detección de patrones y (opcionalmente) validación por LLM.
- Para cargas pesadas o validaciones LLM/visualizaciones, los pipelines pueden ejecutarse de forma asíncrona mediante workers Celery; los endpoints asíncronos están expuestos en `app/api/v1/endpoints/analysis_async.py` (envío y consulta de estado). Cuando no hay workers disponibles, el API devuelve 503 para las rutas que dependen de ejecución asíncrona.
- La validación asistida por modelos de lenguaje está implementada bajo `app/infrastructure/llm/` (adaptadores, `LLMFactory`, `llm_circuit_breaker`, `llm_ensemble`, `ollama_adapter.py`). Esta validación es opcional: el pipeline principal no depende de ella para calcular Big O / Omega, pero puede enriquecer explicaciones y resúmenes.
- El sistema usa caching (Redis) para evitar recomputar análisis iguales; la caché y la coordinación con Celery se encuentran en `app/infrastructure/cache/` y `app/infrastructure/tasks` respectivamente.

Estas notas son de implementación y no cambian la teoría presentada arriba; sirven para entender cómo las decisiones prácticas (timeouts, caché, LLM fallbacks, ejecución asíncrona) afectan el comportamiento en entornos reales.

---

## Complejidad Temporal

### Ciclos Simples

Un ciclo que itera exactamente `n` veces con un cuerpo de complejidad O(1):

```
for i <- 1 to n do
begin
    x <- x + 1    // O(1)
end
```

Complejidad: O(n) * O(1) = **O(n)**

### Ciclos con Límite Variable

```
for i <- 1 to n - 1 do
begin
    for j <- 1 to n - i do
    begin
        if (A[j] > A[j + 1]) then
            // O(1)
        end
    end
end
```

El ciclo externo itera n-1 veces. El ciclo interno itera n-i veces en cada paso. La suma total es: (n-1) + (n-2) + ... + 1 = n(n-1)/2, que es **O(n^2)**.

### Ciclos con División

Cuando el índice se divide en cada iteración:

```
while (n > 1) do
begin
    n <- n / 2
end
```

El número de iteraciones es log2(n). Complejidad: **O(log n)**

### Ciclos Anidados de Distinto Orden

```
for i <- 1 to n do
begin
    j <- n
    while (j > 1) do
    begin
        j <- j / 2
    end
end
```

El ciclo externo es O(n). El ciclo interno es O(log n). Complejidad total: **O(n log n)**

---

## Complejidad Espacial

La complejidad espacial S(n) mide cuánta memoria adicional requiere el algoritmo. Se compone de tres partes:

### Espacio de Entrada

La memoria que ocupa la propia entrada. Generalmente O(n) para arrays de tamaño n, O(n*m) para matrices.

### Espacio Auxiliar

La memoria adicional que el algoritmo declara internamente: variables locales, arrays temporales, estructuras intermedias. Este es el componente que más importa para comparar algoritmos con la misma entrada.

**Ejemplo:** Merge Sort crea un array temporal de tamaño n en cada nivel de recursión. Espacio auxiliar: O(n).

**Ejemplo:** Búsqueda binaria iterativa solo usa tres variables (low, high, mid). Espacio auxiliar: O(1).

### Espacio de Recursión

Para algoritmos recursivos, cada llamada ocupa espacio en la pila del sistema. La profundidad máxima de la recursión determina este componente.

**Ejemplo:** Fibonacci recursivo alcanza una profundidad de n llamadas antes de llegar al caso base. Espacio de recursión: O(n).

**Ejemplo:** Merge Sort alcanza una profundidad log n. Espacio de recursión: O(log n).

---

## Análisis Línea por Línea

Además de la complejidad global, el sistema calcula cuántas veces se ejecuta cada línea del algoritmo en función de n. Este análisis permite identificar cuáles son las líneas "calientes" que dominan el tiempo de ejecución.

### Cómo Interpretarlo

```
algorithm bubbleSort(A[n])
begin
    for i <- 1 to n - 1 do           // n-1 veces
    begin
        for j <- 1 to n - i do       // (n-i) veces por cada i
        begin
            if (A[j] > A[j + 1]) then // n(n-1)/2 veces en total
            begin
                temp <- A[j]          // 0 a n(n-1)/2 veces (depende de datos)
                A[j] <- A[j + 1]
                A[j + 1] <- temp
            end
        end
    end
end
```

El sistema reporta el número de ejecuciones de cada sentencia en términos de n, identificando el término dominante que define la complejidad total.

---

## Ecuaciones de Recurrencia

Para algoritmos recursivos, el sistema construye automáticamente la ecuación de recurrencia que describe su comportamiento.

### Qué es una Ecuación de Recurrencia

Una ecuación de recurrencia es una fórmula que define el tiempo de ejecución T(n) en términos del tiempo de ejecución para entradas más pequeñas. Por ejemplo:

```
T(n) = 2T(n/2) + O(n)   // Merge Sort
T(n) = T(n-1) + O(1)    // Factorial
T(n) = T(n-1) + T(n-2)  // Fibonacci recursivo
```

### Formas Reconocidas

El sistema reconoce y clasifica las siguientes formas:

#### F0 - División simple

```
T(n) = T(n/b) + f(n)
```

Una llamada recursiva que divide el problema por un factor b.

**Ejemplo:** Búsqueda binaria: `T(n) = T(n/2) + O(1)`

#### F1 - División múltiple uniforme

```
T(n) = a*T(n/b) + f(n)
```

Exactamente `a` llamadas recursivas, cada una con entrada de tamaño n/b.

**Ejemplo:** Merge Sort: `T(n) = 2T(n/2) + O(n)`

#### F2 - División dual no uniforme

```
T(n) = T(n/b) + T(n/c) + f(n)
```

Dos llamadas recursivas con divisores distintos.

**Ejemplo:** Quicksort en promedio: `T(n) = T(n/4) + T(3n/4) + O(n)`

#### F4 - Resta simple

```
T(n) = T(n-b) + f(n)
```

Una llamada recursiva que reduce el problema en una cantidad fija.

**Ejemplo:** Factorial: `T(n) = T(n-1) + O(1)`

#### F5 - Resta múltiple uniforme

```
T(n) = a*T(n-b) + f(n)
```

Exactamente `a` llamadas recursivas que reducen el problema en b.

**Ejemplo:** Fibonacci: `T(n) = 2T(n-1) + O(1)` (simplificación)

---

## Métodos de Solución

El sistema implementa cinco métodos para resolver ecuaciones de recurrencia:

### 1. Método de Iteración

Expande la ecuación repetidamente hasta encontrar el patrón general y luego aplica el caso base.

**Aplicable a:** F0, F1, F4, F5

**Ejemplo para T(n) = T(n-1) + 1:**

```
T(n) = T(n-1) + 1
     = T(n-2) + 1 + 1
     = T(n-3) + 1 + 1 + 1
     = T(n-k) + k
     Con k = n-1: T(1) + (n-1) = O(n)
```

### 2. Árbol de Recursión

Construye un árbol donde cada nivel representa una capa de llamadas recursivas y suma el trabajo total en cada nivel.

**Aplicable a:** F0, F1, F2, F3, F5, F6

**Ejemplo para T(n) = 2T(n/2) + n:**

```
Nivel 0: n          (trabajo: n)
Nivel 1: n/2, n/2   (trabajo: n)
Nivel 2: n/4 x4     (trabajo: n)
...
Nivel k: n/2^k x 2^k (trabajo: n)
Altura del árbol: log n
Total: n * log n = O(n log n)
```

### 3. Teorema Maestro

Aplica directamente la solución conocida para la forma `T(n) = aT(n/b) + f(n)`.

**Aplicable a:** F0, F1

**Los tres casos:**

Sea `d = log_b(a)`:

- **Caso 1:** Si f(n) = O(n^c) con c < d, entonces T(n) = Theta(n^d).
- **Caso 2:** Si f(n) = Theta(n^d), entonces T(n) = Theta(n^d * log n).
- **Caso 3:** Si f(n) = Omega(n^c) con c > d y se cumple la condición de regularidad, entonces T(n) = Theta(f(n)).

**Ejemplo:** Para T(n) = 2T(n/2) + n: a=2, b=2, d = log2(2) = 1. f(n) = n = Theta(n^1). Es Caso 2. Resultado: Theta(n log n).

### 4. Sustitución Inteligente

Hace una hipótesis educada sobre la forma de la solución y la verifica por inducción matemática.

**Aplicable a:** Todas las formas

**Ejemplo:** Para T(n) = 2T(n/2) + n, se asume T(n) = O(n log n) y se verifica que la sustitución es consistente.

### 5. Ecuación Característica

Para recurrencias lineales de la forma F4, F5, F6, resuelve la ecuación polinómica asociada para obtener la forma cerrada.

**Aplicable a:** F4, F5, F6

**Ejemplo para T(n) = 2T(n-1):**

Ecuación característica: r = 2. Raíz: r = 2. Solución: T(n) = C * 2^n = O(2^n).

---

## Ejemplos de Análisis

### Ejemplo 1: Búsqueda Lineal

```
algorithm linearSearch(A[n], x)
begin
    for i <- 1 to n do
    begin
        if (A[i] = x) then
            return i
    end
    return -1
end
```

| Métrica | Valor |
|---------|-------|
| Big O | O(n) |
| Omega | Omega(1) |
| Theta | No existe |
| S(n) | O(1) |
| Ecuación T(n) | T(n) = n operaciones iterativas |

**Justificación:** En el peor caso, el elemento no está en el array y se recorren los n elementos. En el mejor caso, el elemento está en la primera posición.

### Ejemplo 2: Merge Sort

```
algorithm mergeSort(A[1..n])
begin
    if (n > 1) then
    begin
        mid <- n / 2
        call mergeSort(A[1..mid])
        call mergeSort(A[mid+1..n])
        call merge(A, 1, mid, n)
    end
end
```

| Métrica | Valor |
|---------|-------|
| Big O | O(n log n) |
| Omega | Omega(n log n) |
| Theta | Theta(n log n) |
| S(n) | O(n) |
| T(n) | T(n) = 2T(n/2) + O(n) |

**Justificación:** Siempre divide en dos mitades y siempre fusiona en O(n). Por Teorema Maestro (Caso 2): Theta(n log n).

### Ejemplo 3: Fibonacci Recursivo

```
algorithm fibonacci(n)
begin
    if (n <= 1) then
        return n
    return call fibonacci(n - 1) + call fibonacci(n - 2)
end
```

| Métrica | Valor |
|---------|-------|
| Big O | O(2^n) |
| Omega | Omega(2^n) |
| Theta | Theta(2^n) |
| S(n) | O(n) |
| T(n) | T(n) = T(n-1) + T(n-2) + O(1) |

**Justificación:** El árbol de recursión es un árbol binario de profundidad n, con aproximadamente 2^n nodos en total. El espacio es O(n) por la profundidad máxima de la pila.

### Ejemplo 4: Búsqueda Binaria

```
algorithm binarySearch(A[n], target)
begin
    left <- 1
    right <- n
    while (left <= right) do
    begin
        mid <- floor((left + right) / 2)
        if (A[mid] = target) then return mid
        if (A[mid] < target) then left <- mid + 1
        else right <- mid - 1
    end
    return -1
end
```

| Métrica | Valor |
|---------|-------|
| Big O | O(log n) |
| Omega | Omega(1) |
| Theta | No existe |
| S(n) | O(1) |
| T(n) | T(n) = T(n/2) + O(1) |

---

## Patrones y su Complejidad Típica

| Patrón | Complejidad Temporal Típica | Complejidad Espacial Típica |
|--------|----------------------------|----------------------------|
| Fuerza Bruta | O(n^2) a O(2^n) | O(1) a O(n) |
| Recursión simple | O(n) a O(2^n) | O(n) por pila |
| Divide y Vencerás | O(n log n) | O(log n) a O(n) |
| Programación Dinámica | O(n^2) o O(n*m) | O(n^2) o O(n) |
| Greedy | O(n log n) | O(1) a O(n) |
| Backtracking | O(2^n) a O(n!) | O(n) por profundidad |
| Branch and Bound | O(2^n) con poda | O(n) |
| Ordenamiento comparativo | O(n log n) en promedio | O(1) a O(n) |
| Búsqueda binaria | O(log n) | O(1) |

---

## Limitaciones del Análisis

El sistema realiza análisis estático, lo que implica las siguientes limitaciones:

### Análisis Conservador

Para ciclos WHILE cuya condición depende de datos de entrada, el sistema estima el peor caso. Por ejemplo, un ciclo que termina antes si se encuentra un elemento en una posición temprana será analizado como si siempre recorriera toda la entrada.

### Algoritmos Probabilísticos

Algoritmos como Quicksort tienen diferentes complejidades para el promedio (O(n log n)) y el peor caso (O(n^2)). El análisis de Big O del sistema reflejará el peor caso, que puede diferir del comportamiento promedio en la práctica.

### Recursión Mutua

La recursión entre dos o más funciones que se llaman entre sí (recursión mutua) puede no ser detectada completamente. El sistema analiza cada función de forma independiente.

### Operaciones No Modeladas

El sistema asume que todas las operaciones elementales (comparaciones, asignaciones, accesos a arrays) tienen costo O(1). Para algoritmos que trabajen con números muy grandes o con operaciones de costo variable, el análisis puede ser inexacto.

### Análisis Amortizado

El análisis amortizado, que distribuye el costo de operaciones costosas sobre una secuencia de operaciones baratas, no está implementado en la versión actual.