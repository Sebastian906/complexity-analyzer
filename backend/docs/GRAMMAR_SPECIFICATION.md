# Especificación de la Gramática de Pseudocódigo

Referencia técnica completa de la gramática formal aceptada por el sistema de análisis de complejidad algorítmica.

---

## Tabla de Contenidos

1. [Descripción General](#descripción-general)
2. [Convenciones y Notación](#convenciones-y-notación)
3. [Estructura del Programa](#estructura-del-programa)
4. [Palabras Clave Aceptadas](#palabras-clave-aceptadas)
5. [Declaración de Algoritmos](#declaración-de-algoritmos)
6. [Parámetros](#parámetros)
7. [Tipos de Datos y Variables](#tipos-de-datos-y-variables)
8. [Operadores](#operadores)
9. [Estructuras de Control](#estructuras-de-control)
10. [Llamadas y Retorno](#llamadas-y-retorno)
11. [Expresiones y Funciones Especiales](#expresiones-y-funciones-especiales)
12. [Comentarios](#comentarios)
13. [Clases y Objetos](#clases-y-objetos)
14. [Ejemplos Completos](#ejemplos-completos)
15. [Errores Comunes](#errores-comunes)

---

## Descripción General

El sistema acepta pseudocódigo estructurado inspirado en el estilo PSeInt. La gramática es formal, procesada por el parser Lark usando análisis LALR, y está diseñada para ser legible tanto para humanos como para el análisis automático de complejidad.

El pseudocódigo acepta variantes tanto en español como en inglés para la mayoría de las palabras clave, lo que permite a los usuarios escribir en el idioma que les resulte más natural.

Nota de implementación: La gramática concreta se encuentra en `app/core/parser/grammar/pseudocode.lark` y es consumida por `PseudocodeParser` (`app/core/parser/pseudocode_parser.py`) que utiliza Lark en modo `lalr` (cacheado). El parser aplica validaciones previas (tamaño máximo, número de líneas) y soporta timeouts configurables (`settings.PARSER_TIMEOUT`). Si actualizas esta especificación, revisa también la gramática `.lark` y `ASTBuilder` para mantener la coherencia.

---

## Convenciones y Notación

| Símbolo | Significado |
|---------|-------------|
| `MAYUSCULAS` | Terminal o palabra clave |
| `minusculas` | Regla no-terminal |
| `?` | Elemento opcional |
| `*` | Cero o más repeticiones |
| `+` | Una o más repeticiones |
| `|` | Alternativa |
| `"texto"` | Literal exacto |

El parser es insensible a mayúsculas y minúsculas para todas las palabras clave. Los identificadores de variables y algoritmos sí distinguen mayúsculas de minúsculas.

---

## Estructura del Programa

Un programa completo tiene la siguiente estructura:

```
programa := definicion_clase* algoritmo
```

Un programa puede contener cero o más definiciones de clases, seguidas obligatoriamente de una definición de algoritmo principal.

**Ejemplo mínimo:**

```
algorithm suma(a, b)
begin
    result <- a + b
    return result
end
```

**Ejemplo con clases:**

```
Node { data, next }

algorithm traverse(Node head)
begin
    current <- head
    while (current != null) do
    begin
        call print(current.data)
        current <- current.next
    end
end
```

---

## Palabras Clave Aceptadas

El sistema acepta las siguientes palabras clave en inglés o en español, indistintamente:

### Declaración de Algoritmo

| Inglés | Español |
|--------|---------|
| `algorithm` | `algoritmo`, `proceso`, `subproceso`, `funcion`, `función` |

### Bloques

| Inglés | Español |
|--------|---------|
| `begin` | `inicio` |
| `end` | `fin`, `finproceso`, `finalgoritmo`, `finfuncion`, `finsubproceso` |

### Ciclos

| Inglés | Español |
|--------|---------|
| `for` | `para` |
| `to` | `hasta` |
| `do` | `hacer` |
| `while` | `mientras` |
| `repeat` | `repetir` |
| `until` | `hasta que`, `hastaque` |

### Condicionales

| Inglés | Español |
|--------|---------|
| `if` | `si` |
| `then` | `entonces` |
| `else` | `sino` |

### Llamadas y Retorno

| Inglés | Español |
|--------|---------|
| `call` | `llamar` |
| `return` | `retornar`, `devolver` |

### Operadores Lógicos

| Inglés | Español | Símbolo |
|--------|---------|---------|
| `and` | - | `&&` |
| `or` | - | `\|\|` |
| `not` | `no` | `!` |

### Funciones Matemáticas

| Inglés | Español | Símbolo Unicode |
|--------|---------|-----------------|
| `ceil` | `techo` | `⌈` |
| `floor` | `piso` | `⌊` |
| `length` | `longitud`, `tamaño` | - |
| `mod` | `módulo` | `%` |
| `div` | - | - |

---

## Declaración de Algoritmos

### Sintaxis

```
algorithm NOMBRE(parametros?)
begin
    sentencias
end
```

### Reglas

- El nombre del algoritmo debe ser un identificador válido (letras, números, guion bajo, sin espacios).
- La lista de parámetros es opcional; si se omite, los paréntesis siguen siendo requeridos.
- El bloque `begin...end` es obligatorio aunque el cuerpo esté vacío.

### Ejemplos

```
algorithm factorial(n)
begin
    if (n <= 1) then
        return 1
    end
    return n * call factorial(n - 1)
end
```

```
algorithm printHello()
begin
    call print("Hello World")
end
```

---

## Parámetros

El sistema soporta tres tipos de parámetros:

### 1. Parámetro Simple

Una variable escalar sin dimensiones.

```
algorithm test(n, m, x)
```

### 2. Parámetro Array

Una variable con notación de corchetes para indicar que es un arreglo unidimensional o bidimensional.

```
algorithm sort(A[n])
algorithm matrix(M[n][m])
algorithm range(A[1..n])
```

- La dimensión puede ser una expresión o una notación de rango `[inicio..fin]`.
- La dimensión puede omitirse: `A[]`.

### 3. Parámetro Objeto

Una variable que es instancia de una clase definida en el mismo programa.

```
Node { data, next }

algorithm traverse(Node head)
begin
    ...
end
```

El nombre de clase debe comenzar con letra mayúscula para diferenciarse de un identificador simple.

---

## Tipos de Datos y Variables

El sistema no requiere declaración explícita de tipos. Las variables se asignan directamente. Los tipos reconocidos implícitamente son:

| Tipo | Ejemplo |
|------|---------|
| Entero | `5`, `100`, `3` |
| Decimal | `3.14`, `2.0`, `0.5` |
| Notación científica | `1e6`, `2.5E-3` |
| Booleano | `TRUE`, `FALSE`, `VERDADERO`, `FALSO` |
| Cadena de texto | `"hola"`, `'mundo'` |

### Declaración Local de Variables

Se permite declarar variables locales en la forma:

```
NombreDeClase variable
```

Donde `NombreDeClase` empieza con mayúscula, o bien:

```
identificador[numero]
```

Para declarar un arreglo local de tamaño fijo.

---

## Operadores

### Asignación

El sistema acepta dos símbolos de asignación:

| Símbolo | Descripción |
|---------|-------------|
| `<-` o `←` | Flecha de asignación (recomendado) |
| `:=` | Asignación alternativa |

**Importante:** El símbolo `=` es exclusivamente un operador de comparación, no de asignación.

```
x <- 5
y := x + 1
```

### Operadores Aritméticos

| Operador | Descripción | Ejemplo |
|----------|-------------|---------|
| `+` | Suma | `a + b` |
| `-` | Resta | `a - b` |
| `*` | Multiplicación | `a * b` |
| `/` | División | `a / b` |
| `^` | Potencia | `a ^ b` |
| `%` o `mod` | Módulo/Resto | `a % b` |
| `div` | División entera | `a div b` |

### Operadores de Comparación

| Operador | Descripción | Alternativa Unicode |
|----------|-------------|---------------------|
| `<` | Menor que | - |
| `>` | Mayor que | - |
| `<=` | Menor o igual | `≤` |
| `>=` | Mayor o igual | `≥` |
| `=` | Igual a | - |
| `!=` | Diferente de | `≠` |

### Operadores Lógicos

| Operador | Descripción | Alternativa |
|----------|-------------|-------------|
| `and` | Y lógico | `&&` |
| `or` | O lógico | `\|\|` |
| `not` | Negación | `!`, `no` |

### Precedencia de Operadores

Del mayor al menor:

1. Paréntesis `()`
2. Potencia `^`
3. Negación unaria `-x`, `not x`
4. Multiplicación `*`, `/`, `%`, `div`
5. Suma `+`, `-`
6. Comparación `<`, `>`, `<=`, `>=`, `=`, `!=`
7. Negación lógica `not`
8. Y lógico `and`
9. O lógico `or`

---

## Estructuras de Control

### Ciclo FOR

Itera desde un valor inicial hasta un valor final, inclusive.

**Sintaxis:**

```
for VARIABLE <- INICIO to FIN do
begin
    sentencias
end
```

**Reglas:**
- La variable de control es asignada automáticamente en cada iteración.
- Los valores de inicio y fin pueden ser expresiones arbitrarias.
- El ciclo siempre itera en sentido ascendente.

**Ejemplo:**

```
for i <- 1 to n do
begin
    x <- x + 1
end
```

**Con expresiones en los límites:**

```
for j <- 1 to n - i do
begin
    if (A[j] > A[j + 1]) then
    begin
        temp <- A[j]
        A[j] <- A[j + 1]
        A[j + 1] <- temp
    end
end
```

### Ciclo WHILE

Repite mientras la condición sea verdadera.

**Sintaxis:**

```
while (CONDICION) do
begin
    sentencias
end
```

**Reglas:**
- La condición debe estar entre paréntesis.
- Se evalúa antes de ejecutar el cuerpo (puede no ejecutarse nunca).

**Ejemplo:**

```
while (left <= right) do
begin
    mid <- (left + right) / 2
    if (A[mid] = target) then
        return mid
    end
    if (A[mid] < target) then
        left <- mid + 1
    else
        right <- mid - 1
    end
end
```

### Ciclo REPEAT...UNTIL

Repite hasta que la condición sea verdadera.

**Sintaxis:**

```
repeat
    sentencias
until (CONDICION)
```

**Reglas:**
- La condición se evalúa al final; el cuerpo se ejecuta al menos una vez.
- La condición debe estar entre paréntesis.

**Ejemplo:**

```
repeat
    x <- x + 1
until (x >= n)
```

### Condicional IF...THEN...ELSE

**Sintaxis:**

```
if (CONDICION) then
begin
    sentencias_verdadero
end

if (CONDICION) then
begin
    sentencias_verdadero
end
else
begin
    sentencias_falso
end
```

**Reglas:**
- El bloque `else` es opcional.
- La condición puede ir con o sin paréntesis, aunque se recomienda usarlos para mayor claridad.
- Los bloques `begin...end` son necesarios si hay más de una sentencia.
- Para sentencias únicas, se puede omitir el bloque (ver ejemplo).

**Ejemplo con bloque:**

```
if (A[mid] = target) then
begin
    return mid
end
else
begin
    if (A[mid] < target) then
        left <- mid + 1
    else
        right <- mid - 1
    end
end
```

**Ejemplo sin bloque (sentencia única):**

```
if (n <= 1) then
    return n
```

---

## Llamadas y Retorno

### Llamada a Subrutina

**Sintaxis:**

```
call NOMBRE(argumentos?)
```

**Reglas:**
- La palabra clave `call` es obligatoria antes del nombre de la función.
- Los argumentos pueden ser expresiones, variables, o slices de arrays.
- La lista de argumentos puede estar vacía.

**Ejemplos:**

```
call quicksort(A, low, high)
call print("resultado")
call merge(A, 1, mid, n)
```

### Llamada como Expresión

Una llamada puede aparecer dentro de una expresión cuando se espera un valor de retorno:

```
result <- call fibonacci(n - 1) + call fibonacci(n - 2)
x <- call max(a, b)
```

### Slices como Argumentos

Se soportan dos notaciones para pasar subrangos de arrays:

```
call mergeSort(A[1:mid])
call mergeSort(A[mid+1..n])
```

### Retorno de Valores

**Sintaxis:**

```
return EXPRESION
return
```

**Reglas:**
- `return` sin expresión termina la ejecución del algoritmo sin devolver valor.
- `return` con expresión devuelve el valor calculado.

**Ejemplos:**

```
return n
return dp[n][m]
return -1
return
```

---

## Expresiones y Funciones Especiales

### Acceso a Arrays

```
A[i]
M[i][j]
```

El índice puede ser cualquier expresión aritmética.

### Acceso a Campos de Objetos

```
node.data
node.next
tree.left
```

### Función CEIL (Techo)

Redondea hacia arriba al entero más cercano.

```
mid <- ceil(n / 2)
mid <- ⌈n / 2⌉
```

### Función FLOOR (Piso)

Redondea hacia abajo al entero más cercano.

```
mid <- floor((low + high) / 2)
mid <- ⌊(low + high) / 2⌋
```

### Función LENGTH

Devuelve la longitud de un array.

```
n <- length(A)
```

---

## Comentarios

El sistema soporta dos tipos de comentarios, ambos de línea (no hay comentarios de bloque):

| Tipo | Símbolo | Ejemplo |
|------|---------|---------|
| Estilo PSeInt | `►` | `► Este es un comentario` |
| Estilo C/Java | `//` | `// Este es un comentario` |

Los comentarios son ignorados completamente por el parser y no afectan el análisis.

```
algorithm bubbleSort(A[n])
begin
    // Ordenar por comparaciones sucesivas
    for i <- 1 to n - 1 do
    begin
        for j <- 1 to n - i do     ► Ciclo interno
        begin
            if (A[j] > A[j + 1]) then
            begin
                temp <- A[j]
                A[j] <- A[j + 1]
                A[j + 1] <- temp
            end
        end
    end
end
```

---

## Clases y Objetos

Las clases se definen antes del algoritmo principal y permiten representar estructuras de datos personalizadas.

### Definición de Clase

**Sintaxis:**

```
NombreDeClase { atributo1, atributo2, ... }
```

**Reglas:**
- El nombre de la clase comienza con letra mayúscula.
- Los atributos son identificadores separados por comas.
- La clase no tiene métodos; solo encapsula datos.

### Uso en Parámetros y Variables

```
Node { data, next }

algorithm insertLinkedList(Node head, value)
begin
    Node newNode
    newNode.data <- value
    newNode.next <- head
    return newNode
end
```

### Ejemplo: Árbol Binario

```
TreeNode { data, left, right }

algorithm inorder(TreeNode node)
begin
    if (node != null) then
    begin
        call inorder(node.left)
        call print(node.data)
        call inorder(node.right)
    end
end
```

---

## Ejemplos Completos

### Ejemplo 1: Búsqueda Binaria

Algoritmo de búsqueda binaria iterativa.

```
algorithm binarySearch(A[n], target)
begin
    left <- 1
    right <- n

    while (left <= right) do
    begin
        mid <- floor((left + right) / 2)

        if (A[mid] = target) then
            return mid
        end

        if (A[mid] < target) then
            left <- mid + 1
        else
            right <- mid - 1
        end
    end

    return -1
end
```

**Complejidad esperada:** O(log n) temporal, O(1) espacial.

### Ejemplo 2: Merge Sort

Algoritmo de ordenamiento por mezcla (recursivo).

```
algorithm mergeSort(A[1..n], low, high)
begin
    if (low < high) then
    begin
        mid <- floor((low + high) / 2)
        call mergeSort(A, low, mid)
        call mergeSort(A, mid + 1, high)
        call merge(A, low, mid, high)
    end
end
```

**Complejidad esperada:** O(n log n) temporal, O(n) espacial.

**Ecuación de recurrencia:** T(n) = 2T(n/2) + O(n)

### Ejemplo 3: Fibonacci Dinámico

Cálculo de Fibonacci con programación dinámica.

```
algorithm fibonacci(n)
begin
    dp[1] <- 0
    dp[2] <- 1

    for i <- 3 to n do
    begin
        dp[i] <- dp[i - 1] + dp[i - 2]
    end

    return dp[n]
end
```

**Complejidad esperada:** O(n) temporal, O(n) espacial.

### Ejemplo 4: N-Reinas con Backtracking

```
algorithm nQueens(board[n][n], col)
begin
    if (col > n) then
        return true
    end

    for row <- 1 to n do
    begin
        if (call isSafe(board, row, col)) then
        begin
            board[row][col] <- 1
            if (call nQueens(board, col + 1)) then
                return true
            end
            board[row][col] <- 0
        end
    end

    return false
end
```

**Complejidad esperada:** O(n!) temporal.

### Ejemplo 5: Algoritmo de Prim con Clase

```
Edge { src, dest, weight }

algorithm prim(graph[n][n])
begin
    visited[1] <- true
    edges <- 0

    while (edges < n - 1) do
    begin
        minEdge <- call findMinEdge(graph, visited, n)
        call addEdge(minEdge)
        visited[minEdge.dest] <- true
        edges <- edges + 1
    end
end
```

### Ejemplo 6: Programación Dinámica 2D

Solución al problema de la mochila (Knapsack).

```
algorithm knapsack(w[n], v[n], capacity)
begin
    for i <- 0 to n do
    begin
        dp[i][0] <- 0
    end

    for j <- 0 to capacity do
    begin
        dp[0][j] <- 0
    end

    for i <- 1 to n do
    begin
        for j <- 1 to capacity do
        begin
            if (w[i] <= j) then
            begin
                dp[i][j] <- call max(v[i] + dp[i-1][j-w[i]], dp[i-1][j])
            end
            else
            begin
                dp[i][j] <- dp[i-1][j]
            end
        end
    end

    return dp[n][capacity]
end
```

**Complejidad esperada:** O(n * capacity) temporal, O(n * capacity) espacial.

---

## Errores Comunes

### Error 1: Usar `=` para asignación

**Incorrecto:**

```
x = 5       // ERROR: = es comparación, no asignación
```

**Correcto:**

```
x <- 5
```

### Error 2: Olvidar la palabra clave `call`

**Incorrecto:**

```
mergeSort(A, low, mid)     // ERROR: falta call
```

**Correcto:**

```
call mergeSort(A, low, mid)
```

**Excepción:** Cuando la llamada aparece dentro de una expresión como parte de un `return` o asignación, también debe llevar `call`:

```
return call fibonacci(n - 1) + call fibonacci(n - 2)
```

### Error 3: No incluir `begin...end` donde se requiere

Si un ciclo o condicional tiene más de una sentencia, el bloque `begin...end` es obligatorio.

**Incorrecto:**

```
for i <- 1 to n do
    x <- x + 1       // ERROR: falta begin...end con múltiples líneas
    y <- y + 1
```

**Correcto:**

```
for i <- 1 to n do
begin
    x <- x + 1
    y <- y + 1
end
```

### Error 4: Usar `=` como comparación sin contexto lógico

La gramática distingue automáticamente el contexto, pero es importante escribir expresiones claras:

```
if (A[mid] = target) then    // Correcto: comparación dentro de if
    x <- y = z               // ERROR: y = z es comparación, no puede asignarse directamente
```

### Error 5: Iniciar el nombre de clase con minúscula

La gramática distingue entre `CLASS_NAME` (empieza con mayúscula) e `IDENTIFIER` (empieza con minúscula). Si se define `node { ... }` en minúscula, el parser no lo reconocerá como clase.

**Incorrecto:**

```
node { data, next }   // ERROR: debe empezar con mayúscula
```

**Correcto:**

```
Node { data, next }
```

### Error 6: Falta de paréntesis en condiciones de WHILE y UNTIL

```
while left <= right do     // ERROR: falta paréntesis
```

```
while (left <= right) do   // Correcto
```

---

## Referencia Rápida

```
// Estructura mínima
algorithm NOMBRE(params)
begin
    // sentencias
end

// Asignación
x <- valor
x := valor

// Ciclos
for i <- 1 to n do begin ... end
while (cond) do begin ... end
repeat ... until (cond)

// Condicional
if (cond) then begin ... end
if (cond) then begin ... end else begin ... end

// Llamadas
call funcion(args)
return expresion

// Arrays
A[i]    M[i][j]    A[1..n]

// Objetos
node.campo

// Funciones matemáticas
floor(x)    ceil(x)    length(A)
```