# Referencia de API REST

Documentación completa de todos los endpoints de la API REST del sistema de análisis de complejidad algorítmica.

---

## Tabla de Contenidos

1. [Información General](#información-general)
2. [Autenticación](#autenticación)
3. [Formato de Respuestas](#formato-de-respuestas)
4. [Endpoints: Health](#endpoints-health)
5. [Endpoints: Algoritmos](#endpoints-algoritmos)
6. [Endpoints: Análisis](#endpoints-análisis)
7. [Endpoints: Patrones](#endpoints-patrones)
8. [Endpoints: Estructuras de Datos](#endpoints-estructuras-de-datos)
9. [Endpoints: Visualización](#endpoints-visualización)
10. [Endpoints: Exportación](#endpoints-exportación)
11. [Endpoints: Validación](#endpoints-validación)
12. [Códigos de Error](#códigos-de-error)
13. [Ejemplos de Uso](#ejemplos-de-uso)

---

## Información General

### URL Base

```
http://localhost:8000/api/v1
```

En producción, reemplazar con el dominio correspondiente.

### Documentación Interactiva

El sistema genera documentación interactiva automáticamente:

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **OpenAPI JSON:** `http://localhost:8000/openapi.json`

### Versión de la API

La versión actual es `v1`. Todos los endpoints tienen el prefijo `/api/v1/`.

### Formato de Solicitud

Todas las solicitudes `POST` y `PUT` deben enviar el cuerpo en formato JSON con el header:

```
Content-Type: application/json
```

---

## Autenticación

La versión actual de la API no requiere autenticación para uso local. En entornos de producción, se contempla autenticación mediante API Keys en el header:

```
X-API-Key: tu-api-key
```

---

## Formato de Respuestas

### Respuesta Exitosa

```json
{
  "success": true,
  "data": { ... },
  "message": "Operación completada",
  "metadata": {
    "processing_time_ms": 245,
    "timestamp": "2025-01-15T10:30:00Z"
  }
}
```

### Respuesta de Error

```json
{
  "success": false,
  "error": {
    "code": "PARSE_ERROR",
    "message": "Error de sintaxis en línea 5",
    "details": "Se esperaba 'end' pero se encontró 'return'"
  }
}
```

---

## Endpoints: Health

### GET /health

Verifica el estado general del sistema.

**Respuesta:**

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "development",
  "services": {
    "api": "healthy",
    "parser": "healthy",
    "database": "unavailable",
    "cache": "unavailable"
  }
}
```

### GET /health/ready

Readiness probe para orquestadores de contenedores. Responde 200 si la API está lista para recibir tráfico.

### GET /health/live

Liveness probe. Responde 200 si el proceso está corriendo.

---

## Endpoints: Algoritmos

### POST /algorithms/parse

Parsea un algoritmo en pseudocódigo y devuelve el AST.

**Cuerpo de la solicitud:**

```json
{
  "code": "algorithm test(n)\nbegin\n  for i <- 1 to n do\n    x <- x + 1\n  end\nend",
  "validate": true
}
```

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `code` | string | Sí | Código en pseudocódigo |
| `validate` | boolean | No | Si se deben ejecutar validaciones semánticas (default: true) |

**Respuesta exitosa (200):**

```json
{
  "success": true,
  "algorithm_name": "test",
  "ast": {
    "node_type": "ProgramNode",
    "algorithm": {
      "node_type": "AlgorithmNode",
      "name": "test",
      "parameters": [{"name": "n", "is_array": false}],
      "body": { ... }
    }
  },
  "validation": {
    "is_valid": true,
    "errors": [],
    "warnings": []
  }
}
```

### POST /algorithms/parse-tree

Devuelve el parse tree crudo de Lark (útil para debugging).

**Cuerpo de la solicitud:** Igual que `/algorithms/parse`.

### POST /algorithms/validate

Valida la sintaxis y semántica de un algoritmo sin generar el AST completo.

**Cuerpo de la solicitud:**

```json
{
  "code": "algorithm test(n)\nbegin\n  x <- 1\nend"
}
```

**Respuesta:**

```json
{
  "is_valid": true,
  "errors": [],
  "warnings": ["Variable 'x' usada antes de declaración explícita"]
}
```

### GET /algorithms/examples

Devuelve una lista de algoritmos de ejemplo listos para probar.

**Respuesta:**

```json
{
  "examples": [
    {
      "name": "Bubble Sort",
      "category": "sorting",
      "code": "algorithm bubbleSort(A[n])\nbegin\n..."
    },
    {
      "name": "Binary Search",
      "category": "searching",
      "code": "algorithm binarySearch(A[n], target)\nbegin\n..."
    }
  ]
}
```

---

## Endpoints: Análisis

### POST /analysis/analyze-complete

Realiza el análisis completo de complejidad de un algoritmo. (Ruta real en el código: `/api/v1/analysis/analyze-complete`)

**Cuerpo de la solicitud:**

```json
{
  "algorithm_code": "algorithm test(n)\nbegin\n  for i <- 1 to n do\n    x <- x + 1\n  end\nend",
  "analyze_temporal": true,
  "analyze_spatial": true,
  "analyze_line_by_line": true,
  "analyze_recurrence": true
}
```

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `algorithm_code` | string | Sí | Código del algoritmo |
| `analyze_temporal` | boolean | No | Calcular O, Omega, Theta (default: true) |
| `analyze_spatial` | boolean | No | Calcular S(n) (default: true) |
| `analyze_line_by_line` | boolean | No | Ejecuciones por línea (default: false) |
| `analyze_recurrence` | boolean | No | Ecuaciones T(n) y S(n) (default: true) |

**Respuesta exitosa (200):**

```json
{
  "success": true,
  "algorithm_name": "test",
  "big_o": "O(n)",
  "omega": "Omega(n)",
  "theta": "Theta(n)",
  "space_complexity": "O(1)",
  "temporal_recurrence": {
    "equation": "T(n) = n * O(1)",
    "solution": "O(n)",
    "method": "iteracion"
  },
  "spatial_recurrence": {
    "equation": "S(n) = O(1)",
    "input_space": "O(n)",
    "auxiliary_space": "O(1)"
  },
  "line_by_line": [
    {"line": 1, "code": "for i <- 1 to n do", "executions": "n", "complexity": "O(n)"},
    {"line": 2, "code": "x <- x + 1", "executions": "n", "complexity": "O(1)"}
  ],
  "analysis_time_ms": 45
}
```

### POST /analysis/complexity

Calcula solo la complejidad temporal (sin análisis completo).

**Cuerpo de la solicitud:**

```json
{
  "algorithm_code": "...",
  "notation": "big_o"
}
```

| Campo `notation` | Descripción |
|-----------------|-------------|
| `big_o` | Solo peor caso |
| `omega` | Solo mejor caso |
| `theta` | Solo caso ajustado |
| `all` | Todas las notaciones |

### POST /analysis/recurrence

Resuelve una ecuación de recurrencia dada.

**Cuerpo de la solicitud:**

```json
{
  "equation": "T(n) = 2T(n/2) + n",
  "method": "master_theorem"
}
```

| Campo `method` | Descripción |
|---------------|-------------|
| `iteration` | Método de iteración |
| `recursion_tree` | Árbol de recursión |
| `master_theorem` | Teorema Maestro |
| `substitution` | Sustitución inteligente |
| `characteristic` | Ecuación característica |
| `auto` | Selección automática |

**Respuesta:**

```json
{
  "equation": "T(n) = 2T(n/2) + n",
  "solution": "Theta(n log n)",
  "method_used": "master_theorem",
  "case": 2,
  "steps": [
    "a=2, b=2, f(n)=n",
    "log_b(a) = log_2(2) = 1",
    "f(n) = n = Theta(n^1) -> Caso 2",
    "Resultado: Theta(n^1 * log n) = Theta(n log n)"
  ]
}

### Asíncrono (Celery)

El proyecto expone endpoints para análisis asíncrono que delegan en workers Celery cuando está configurado (ver `docker-compose.yml`):

- `POST /analysis/async` → Enviar análisis individual a Celery, retorna 202 + `task_id`.
- `POST /analysis/batch-async` → Enviar batch de análisis (máx 100) a Celery, retorna 202 + `task_id`.
- `GET /analysis/task/{task_id}` → Consultar estado/resultado de la tarea.

Nota: Estos endpoints devuelven 503 si Celery o el broker (Redis) no están disponibles.
```

---

## Endpoints: Patrones

### POST /patterns/detect

Detecta todos los patrones algorítmicos presentes en el código.

**Cuerpo de la solicitud:**

```json
{
  "code": "algorithm mergeSort(A[n])\nbegin\n  ...\nend",
  "min_confidence": 0.3
}
```

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `code` | string | Sí | Código del algoritmo |
| `min_confidence` | float | No | Umbral mínimo de confianza (default: 0.3) |

**Respuesta exitosa (200):**

```json
{
  "success": true,
  "algorithm_name": "mergeSort",
  "primary_pattern": {
    "pattern_type": "divide_and_conquer",
    "pattern_name": "Divide y Venceras",
    "confidence": 0.92,
    "confidence_level": "very_high",
    "reasoning": "División binaria con dos llamadas recursivas y función de combinación",
    "indicators_found": [
      {"name": "recursive_calls", "found": true, "weight": 3.0, "evidence": "2 llamadas recursivas"},
      {"name": "problem_division", "found": true, "weight": 2.5, "evidence": "División n/2"}
    ]
  },
  "all_patterns": [
    {
      "pattern_type": "divide_and_conquer",
      "confidence": 0.92,
      "rank": 1
    },
    {
      "pattern_type": "recursive",
      "confidence": 0.78,
      "rank": 2
    }
  ],
  "summary": "Patron principal detectado: Divide y Venceras (confianza: 92%)",
  "metadata": {
    "total_patterns_detected": 3,
    "highest_confidence": 0.92
  }
}
```

### POST /patterns/detect-specific

Detecta si un patrón específico está presente en el código.

**Cuerpo de la solicitud:**

```json
{
  "code": "...",
  "pattern_type": "dynamic_programming"
}
```

**Valores válidos para `pattern_type`:**

| Valor | Patrón |
|-------|--------|
| `brute_force` | Fuerza Bruta |
| `recursive` | Recursion |
| `divide_and_conquer` | Divide y Venceras |
| `dynamic_programming` | Programacion Dinamica |
| `greedy` | Algoritmos Greedy |
| `backtracking` | Backtracking |
| `branch_and_bound` | Branch and Bound |
| `sorting` | Algoritmos de Ordenamiento |
| `searching` | Algoritmos de Busqueda |

**Respuesta:**

```json
{
  "pattern_detected": true,
  "pattern_info": {
    "pattern_type": "dynamic_programming",
    "confidence": 0.85,
    "reasoning": "Se detecta tabla de memoización con accesos a dp[i][j]"
  }
}
```

### GET /patterns/available

Lista todos los patrones disponibles para detección.

**Respuesta:**

```json
{
  "patterns": [
    {
      "type": "brute_force",
      "name": "Fuerza Bruta",
      "description": "Exploracion exhaustiva sin optimizacion",
      "typical_complexity": "O(n^2) a O(2^n)"
    }
  ],
  "total": 12
}
```

### GET /patterns/types

Devuelve solo la lista de tipos de patrones como strings.

---

## Endpoints: Estructuras de Datos

### POST /structures/detect

Detecta las estructuras de datos utilizadas en el algoritmo.

**Cuerpo de la solicitud:**

```json
{
  "code": "algorithm bfs(graph[n], start)\nbegin\n  queue <- createQueue()\n  ...\nend",
  "min_confidence": 0.3,
  "analyze_usage": true
}
```

**Respuesta exitosa (200):**

```json
{
  "success": true,
  "algorithm_name": "bfs",
  "primary_structure": {
    "structure_type": "queue",
    "structure_name": "Cola",
    "confidence": 0.90,
    "confidence_level": "very_high",
    "variables": ["queue"],
    "operations": ["enqueue", "dequeue", "isEmpty"],
    "reasoning": "Se detectan operaciones FIFO con enqueue/dequeue"
  },
  "primary_usage": {
    "operation_frequencies": [
      {"operation": "enqueue", "count": 2, "complexity": "O(1)"},
      {"operation": "dequeue", "count": 1, "complexity": "O(1)"}
    ],
    "most_frequent_operation": "enqueue",
    "access_pattern": "sequential_fifo",
    "total_operations": 3
  },
  "all_structures": [...],
  "summary": "Estructura principal: Cola (confianza: 90%)"
}
```

### POST /structures/detect-specific

Detecta si una estructura de datos específica está presente.

**Cuerpo de la solicitud:**

```json
{
  "code": "...",
  "structure_type": "tree"
}
```

**Valores válidos para `structure_type`:**

`array`, `stack`, `queue`, `linked_list`, `dictionary`, `tree`, `graph`, `hash_table`, `heap`, `set`

### GET /structures/available

Lista todas las estructuras de datos detectables.

---

## Endpoints: Visualización

### POST /visualization/recursion-tree

Genera el árbol de recursión para un algoritmo recursivo.

**Cuerpo de la solicitud:**

```json
{
  "code": "algorithm fibonacci(n)\nbegin\n  ...\nend",
  "start_value": 5,
  "max_depth": 6,
  "format": "svg"
}
```

| Campo `format` | Descripción |
|---------------|-------------|
| `svg` | SVG (recomendado para web) |
| `dot` | DOT para Graphviz |
| `mermaid` | Mermaid Markdown |
| `json` | Datos estructurados |

**Respuesta exitosa (200):**

```json
{
  "success": true,
  "recursion_type": "binary",
  "total_calls": 15,
  "max_depth": 5,
  "total_work": "O(2^n)",
  "content": "<svg>...</svg>",
  "format": "svg"
}
```

### POST /visualization/execution-flow

Genera el diagrama de flujo de ejecución.

**Cuerpo de la solicitud:**

```json
{
  "code": "...",
  "format": "mermaid"
}
```

**Respuesta:**

```json
{
  "success": true,
  "content": "flowchart TD\n  A[Inicio] --> B{n > 1?}\n  ...",
  "format": "mermaid",
  "statistics": {
    "total_nodes": 8,
    "total_edges": 10,
    "has_loops": true
  }
}
```

### POST /visualization/graph

Genera la visualización de una estructura de datos.

**Cuerpo de la solicitud:**

```json
{
  "structure_type": "tree",
  "values": [50, 30, 70, 20, 40],
  "layout": "hierarchical",
  "format": "svg"
}
```

---

## Endpoints: Exportación

### POST /export

Exporta los resultados de un análisis en el formato especificado.

**Cuerpo de la solicitud:**

```json
{
  "algorithm_code": "...",
  "format": "pdf",
  "options": {
    "include_visualizations": true,
    "include_line_by_line": true,
    "include_metadata": true
  }
}
```

**Valores válidos para `format`:**

| Valor | Descripción |
|-------|-------------|
| `json` | JSON estructurado |
| `markdown` | Documento Markdown |
| `html` | Página HTML |
| `pdf` | PDF profesional |
| `excel` | Hoja de cálculo Excel |
| `csv` | CSV tabular |
| `dot` | Graphviz DOT |
| `mermaid` | Diagramas Mermaid |
| `svg` | Gráficos vectoriales SVG |
| `txt` | Texto plano |

**Respuesta exitosa (200):**

La respuesta devuelve el archivo generado como `application/octet-stream` con el header:

```
Content-Disposition: attachment; filename="analysis_report.pdf"
```

### GET /export/formats

Lista todos los formatos de exportación disponibles.

**Respuesta:**

```json
{
  "formats": [
    {"format": "json", "available": true, "description": "JSON estructurado"},
    {"format": "pdf", "available": true, "description": "Reporte PDF profesional"},
    {"format": "excel", "available": true, "description": "Hoja Excel"}
  ]
}
```

---

## Endpoints: Validación

### POST /validation/validate

Valida un algoritmo con múltiples niveles de rigor.

**Cuerpo de la solicitud:**

```json
{
  "code": "algorithm test(n)\nbegin\n  x <- 1\nend",
  "level": "complete"
}
```

| Valor `level` | Descripción |
|--------------|-------------|
| `syntax` | Solo validación sintáctica |
| `semantic` | Sintaxis y semántica |
| `structural` | + límites estructurales |
| `complete` | + mejores prácticas |

**Respuesta:**

```json
{
  "is_valid": true,
  "level": "complete",
  "syntax": {
    "valid": true,
    "errors": []
  },
  "semantic": {
    "valid": true,
    "warnings": ["Variable 'x' no está declarada explícitamente"]
  },
  "structural": {
    "valid": true,
    "nesting_depth": 1,
    "max_allowed": 20
  },
  "best_practices": [
    {
      "check": "variable_naming",
      "passed": false,
      "message": "Usar nombres descriptivos en lugar de 'x'"
    }
  ]
}
```

---

## Códigos de Error

| Código HTTP | Código de Error | Descripción |
|-------------|----------------|-------------|
| 400 | `INVALID_REQUEST` | La solicitud está mal formada |
| 400 | `MISSING_FIELD` | Falta un campo requerido |
| 422 | `PARSE_ERROR` | Error de sintaxis en el pseudocódigo |
| 422 | `SEMANTIC_ERROR` | Error semántico en el algoritmo |
| 422 | `VALIDATION_ERROR` | Error de validación de Pydantic |
| 404 | `NOT_FOUND` | Recurso no encontrado |
| 429 | `RATE_LIMIT` | Demasiadas solicitudes |
| 500 | `INTERNAL_ERROR` | Error interno del servidor |
| 503 | `SERVICE_UNAVAILABLE` | Servicio no disponible |

---

## Ejemplos de Uso

### Análisis completo con cURL

```bash
curl -X POST http://localhost:8000/api/v1/analysis/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "algorithm_code": "algorithm bubbleSort(A[n])\nbegin\n    for i <- 1 to n-1 do\n    begin\n        for j <- 1 to n-i do\n        begin\n            if (A[j] > A[j+1]) then\n            begin\n                temp <- A[j]\n                A[j] <- A[j+1]\n                A[j+1] <- temp\n            end\n        end\n    end\nend",
    "analyze_temporal": true,
    "analyze_spatial": true,
    "analyze_line_by_line": true
  }'
```

### Análisis completo con Python

```python
import httpx

client = httpx.Client(base_url="http://localhost:8000")

code = """
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
"""

response = client.post("/api/v1/analysis/analyze", json={
    "algorithm_code": code,
    "analyze_temporal": True,
    "analyze_recurrence": True
})

result = response.json()
print(f"Big O: {result['big_o']}")
print(f"T(n): {result['temporal_recurrence']['equation']}")
```

### Detección de patrones con Python

```python
response = client.post("/api/v1/patterns/detect", json={
    "code": code,
    "min_confidence": 0.5
})

data = response.json()
primary = data["primary_pattern"]
print(f"Patron: {primary['pattern_name']}")
print(f"Confianza: {primary['confidence']:.2%}")
```

---

## Nota sobre PATTERNS_API_GUIDE.md

El archivo `docs/PATTERNS_API_GUIDE.md` documenta exclusivamente la API de patrones con ejemplos adicionales y casos de uso específicos. Este documento (`api_reference.md`) es la referencia completa y unificada de todos los endpoints. Se recomienda usar `api_reference.md` como fuente principal y mantener `PATTERNS_API_GUIDE.md` como referencia rápida orientada a desarrolladores que trabajan específicamente con el módulo de patrones.