# Guía de Uso - API de Detección de Patrones

Documentación completa para usar la API de detección de patrones algorítmicos.

## Tabla de Contenidos

- [Introducción](#introducción)
- [Endpoints Disponibles](#endpoints-disponibles)
- [Uso con Swagger](#uso-con-swagger)
- [Ejemplos con cURL](#ejemplos-con-curl)
- [Ejemplos con Python](#ejemplos-con-python)
- [Patrones Detectables](#patrones-detectables)
- [Respuestas de la API](#respuestas-de-la-api)

---

## Introducción

La API de detección de patrones permite identificar automáticamente técnicas y patrones algorítmicos en pseudocódigo. Detecta patrones como:

- **Fuerza Bruta**
- **Recursión**
- **Divide y Vencerás**
- **Programación Dinámica**
- **Greedy (Voraz)**
- **Backtracking**
- **Branch and Bound**
- **Ordenamiento**
- **Búsqueda**
- Y más...

> Nota: la detección puede opcionalmente usar validación asistida por LLMs cuando está habilitado en la configuración. En ese caso la validación puede formar parte del pipeline (síncrono o asíncrono) y estar delegada a agentes/LLMs.

---

## Endpoints Disponibles

### Base URL

```
http://localhost:8000/api/v1/patterns
```

### Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/detect` | Detecta todos los patrones |
| POST | `/detect-specific` | Detecta un patrón específico |
| GET | `/available` | Lista patrones disponibles |
| GET | `/types` | Lista tipos de patrones |

---

## Uso con Swagger

### 1. Acceder a Swagger UI

Abre tu navegador en:

```
http://localhost:8000/docs
```

### 2. Expandir el Tag "Patterns"

Verás todos los endpoints relacionados con patrones.

### 3. Probar `/patterns/detect`

1. Click en **POST /api/v1/patterns/detect**
2. Click en **"Try it out"**
3. Pega este código de ejemplo:

```json
{
  "code": "algorithm bubbleSort(A[n])\nbegin\n    for i ← 1 to n - 1 do\n    begin\n        for j ← 1 to n - i do\n        begin\n            if (A[j] > A[j + 1]) then\n            begin\n                temp ← A[j]\n                A[j] ← A[j + 1]\n                A[j + 1] ← temp\n            end\n        end\n    end\nend",
  "min_confidence": 0.3
}
```

4. Click **"Execute"**
5. Verás el resultado en la sección **"Response body"**

### 4. Probar `/patterns/available`

1. Click en **GET /api/v1/patterns/available**
2. Click en **"Try it out"**
3. Click **"Execute"**
4. Verás lista de todos los patrones disponibles

---

## Ejemplos con cURL

### 1. Detectar Todos los Patrones

```bash
curl -X POST http://localhost:8000/api/v1/patterns/detect \
  -H "Content-Type: application/json" \
  -d '{
    "code": "algorithm fibonacci(n)\nbegin\n    if (n <= 1) then\n    begin\n        return n\n    end\n    return call fibonacci(n - 1) + call fibonacci(n - 2)\nend",
    "min_confidence": 0.3
  }'
```

**Respuesta esperada:**

```json
{
  "success": true,
  "algorithm_name": "fibonacci",
  "primary_pattern": {
    "pattern_type": "recursive",
    "pattern_name": "Recursión",
    "confidence": 0.85,
    "confidence_level": "high",
    "reasoning": "El algoritmo usa recursión simple: 2 llamada(s) recursivas, con caso base definido..."
  },
  "all_patterns": [...],
  "summary": "Patrón principal detectado: Recursión (confianza: 85.00% - Alta)...",
  "metadata": {...}
}
```

### 2. Detectar Patrón Específico

```bash
curl -X POST http://localhost:8000/api/v1/patterns/detect-specific \
  -H "Content-Type: application/json" \
  -d '{
    "code": "algorithm mergeSort(A[n])\nbegin\n    if (n > 1) then\n    begin\n        mid ← n / 2\n        call mergeSort(A[1..mid])\n        call mergeSort(A[mid+1..n])\n    end\nend",
    "pattern_type": "divide_and_conquer"
  }'
```

### 3. Listar Patrones Disponibles

```bash
curl -X GET http://localhost:8000/api/v1/patterns/available
```

**Respuesta:**

```json
{
  "success": true,
  "patterns": [
    {
      "type": "brute_force",
      "name": "Fuerza Bruta",
      "description": "Exploración exhaustiva sin optimización",
      "typical_complexity": "O(n²) a O(2^n)"
    },
    {
      "type": "recursive",
      "name": "Recursión",
      "description": "Función que se invoca a sí misma",
      "typical_complexity": "Variable (depende del patrón)"
    },
    ...
  ],
  "total": 12
}
```

### 4. Obtener Tipos de Patrones

```bash
curl -X GET http://localhost:8000/api/v1/patterns/types
```

---

## Ejemplos con Python

### Ejemplo 1: Detección Completa

```python
import httpx

# Cliente HTTP
client = httpx.Client(base_url="http://localhost:8000")

# Código del algoritmo
code = """
algorithm bubbleSort(A[n])
begin
    for i ← 1 to n - 1 do
    begin
        for j ← 1 to n - i do
        begin
            if (A[j] > A[j + 1]) then
            begin
                temp ← A[j]
                A[j] ← A[j + 1]
                A[j + 1] ← temp
            end
        end
    end
end
"""

# Detectar patrones
response = client.post("/api/v1/patterns/detect", json={
    "code": code,
    "min_confidence": 0.3
})

# Procesar resultado
if response.status_code == 200:
    data = response.json()
    
    print(f"Algoritmo: {data['algorithm_name']}")
    print(f"Patrón principal: {data['primary_pattern']['pattern_name']}")
    print(f"Confianza: {data['primary_pattern']['confidence']:.2%}")
    print(f"\nResumen:\n{data['summary']}")
    
    print("\nTodos los patrones:")
    for pattern in data['all_patterns']:
        print(f"  - {pattern['pattern_name']}: {pattern['confidence']:.2%}")
else:
    print(f"Error: {response.status_code}")
```

### Ejemplo 2: Detección Específica

```python
import httpx

client = httpx.Client(base_url="http://localhost:8000")

# Detectar solo recursión
response = client.post("/api/v1/patterns/detect-specific", json={
    "code": "algorithm fib(n)\nbegin\n    if (n <= 1) then return n\n    return call fib(n-1) + call fib(n-2)\nend",
    "pattern_type": "recursive"
})

data = response.json()

if data["pattern_detected"]:
    pattern = data["pattern_info"]
    print(f"✓ Patrón detectado: {pattern['pattern_name']}")
    print(f"  Confianza: {pattern['confidence']:.2%}")
    print(f"  {pattern['reasoning']}")
else:
    print("✗ Patrón no detectado")
```

### Ejemplo 3: Comparar Algoritmos

```python
import httpx
from rich.console import Console
from rich.table import Table

console = Console()
client = httpx.Client(base_url="http://localhost:8000")

algorithms = {
    "Bubble Sort": "algorithm bubbleSort...",
    "Merge Sort": "algorithm mergeSort...",
    "Fibonacci DP": "algorithm fibDP..."
}

# Tabla de resultados
table = Table(title="Comparación de Algoritmos")
table.add_column("Algoritmo")
table.add_column("Patrón Principal")
table.add_column("Confianza")

for name, code in algorithms.items():
    response = client.post("/api/v1/patterns/detect", json={
        "code": code,
        "min_confidence": 0.3
    })
    
    if response.status_code == 200:
        data = response.json()
        primary = data['primary_pattern']
        
        table.add_row(
            name,
            primary['pattern_name'],
            f"{primary['confidence']:.2%}"
        )

console.print(table)
```

---

## Patrones Detectables

### Patrones Principales

| Tipo | Nombre | Descripción | Complejidad |
|------|--------|-------------|-------------|
| `brute_force` | Fuerza Bruta | Exploración exhaustiva | O(n²) - O(2^n) |
| `recursive` | Recursión | Llamadas recursivas | Variable |
| `divide_and_conquer` | Divide y Vencerás | División y combinación | O(n log n) |
| `dynamic_programming` | Programación Dinámica | Memoización/Tabulación | O(n²), O(n*m) |
| `greedy` | Greedy (Voraz) | Elección localmente óptima | O(n log n) |
| `backtracking` | Backtracking | Exploración con retroceso | O(2^n), O(n!) |
| `branch_and_bound` | Branch and Bound | Poda por cotas | Variable |
| `sorting` | Ordenamiento | Algoritmo de ordenamiento | O(n²) - O(n log n) |
| `searching` | Búsqueda | Algoritmo de búsqueda | O(log n) - O(n) |

### Patrones Avanzados

| Tipo | Nombre | Descripción |
|------|--------|-------------|
| `quantum` | Algoritmo Cuántico | Algoritmos cuánticos |
| `bio_inspired` | Bio-inspirado | Algoritmos evolutivos |
| `approximation` | Aproximación | Algoritmos de aproximación |

---

## Respuestas de la API

### Estructura de Response - `/detect`

```json
{
  "success": true,
  "algorithm_name": "bubbleSort",
  "primary_pattern": {
    "pattern_type": "brute_force",
    "pattern_name": "Fuerza Bruta",
    "confidence": 0.75,
    "confidence_level": "high",
    "typical_complexity": "O(n²) a O(2^n)",
    "reasoning": "El algoritmo presenta características de fuerza bruta...",
    "indicators_found": [
      {
        "name": "nested_loops",
        "description": "Múltiples loops anidados",
        "found": true,
        "weight": 3.0,
        "evidence": "Profundidad de anidación: 2"
      }
    ],
    "indicators_missing": [...],
    "rank": 1,
    "is_primary": true,
    "final_score": 0.75,
    "conflicts": []
  },
  "all_patterns": [...],
  "confident_patterns": [...],
  "summary": "Patrón principal detectado: Fuerza Bruta...",
  "metadata": {
    "total_patterns_detected": 5,
    "patterns_by_type": {...},
    "highest_confidence": 0.75,
    "detection_complete": true
  },
  "message": "Detección de patrones completada exitosamente"
}
```

### Niveles de Confianza

| Nivel | Rango | Descripción |
|-------|-------|-------------|
| `very_high` | ≥ 90% | Muy alta confianza |
| `high` | 70-89% | Alta confianza |
| `medium` | 50-69% | Confianza media |
| `low` | 30-49% | Baja confianza |
| `very_low` | < 30% | Muy baja confianza |

### Códigos de Estado HTTP

| Código | Significado |
|--------|-------------|
| 200 | Éxito |
| 400 | Request inválido |
| 422 | Error de validación |
| 500 | Error del servidor |

---

## Testing

### Ejecutar Tests

```bash
# Tests unitarios
pytest tests/unit/test_patterns.py -v

# Tests de integración (API)
pytest tests/integration/test_patterns_api.py -v

# Todos los tests
pytest tests/ -v
```

### Demo Script

```bash
# Ejecutar demo interactiva
python scripts/demo_patterns_api.py
```

---

## Troubleshooting

### Error: "Connection refused"

**Problema:** No se puede conectar a la API.

**Solución:**
```bash
# Asegúrate de que el servidor esté corriendo
uvicorn app.main:app --reload
```

### Error: "pattern_type inválido"

**Problema:** Tipo de patrón no reconocido.

**Solución:** Usa `/patterns/types` para ver los tipos válidos:
```bash
curl http://localhost:8000/api/v1/patterns/types
```

### Confianza muy baja en todos los patrones

**Problema:** Ningún patrón tiene confianza alta.

**Posibles causas:**
- El algoritmo es muy simple
- El algoritmo usa técnica no implementada
- Sintaxis incorrecta en el pseudocódigo

**Solución:**
- Reducir `min_confidence` a 0.1 para ver todos los patrones
- Verificar la sintaxis del pseudocódigo
- Revisar los indicadores faltantes en la respuesta

---

## Mejores Prácticas

### 1. Usar min_confidence apropiado

```python
# Para análisis exploratorio
response = client.post("/api/v1/patterns/detect", json={
    "code": code,
    "min_confidence": 0.1  # Ver todos los patrones
})

# Para producción
response = client.post("/api/v1/patterns/detect", json={
    "code": code,
    "min_confidence": 0.5  # Solo patrones confiables
})
```

### 2. Verificar indicadores

Siempre revisa `indicators_found` e `indicators_missing` para entender por qué se detectó (o no) un patrón:

```python
primary = data['primary_pattern']

print("Indicadores encontrados:")
for ind in primary['indicators_found']:
    print(f"  ✓ {ind['name']}: {ind['evidence']}")

print("\nIndicadores faltantes:")
for ind in primary['indicators_missing']:
    print(f"  ✗ {ind['name']}")
```

### 3. Usar detección específica para validación

Si sospechas que un algoritmo usa cierto patrón, usa `/detect-specific` para confirmarlo:

```python
# Validar si es Divide y Vencerás
response = client.post("/api/v1/patterns/detect-specific", json={
    "code": code,
    "pattern_type": "divide_and_conquer"
})

if response.json()["pattern_detected"]:
    print("✓ Confirmado: Divide y Vencerás")
```

---

## Referencias

- [Documentación Swagger](http://localhost:8000/docs)
- [Código fuente](https://github.com/Sebastian906/complexity-analyzer)
- [Tests](../tests/unit/test_patterns.py)

---

**¿Preguntas?** Abre un issue en GitHub o consulta la documentación en Swagger.