# Módulo 5: Servicios (Services)

Sistema de servicios de aplicación que orquestan operaciones complejas combinando múltiples módulos del dominio.

---

## Tabla de Contenidos

1. [Descripción General](#descripción-general)
2. [Arquitectura](#arquitectura)
3. [Servicios Implementados](#servicios-implementados)
4. [Flujos de Trabajo](#flujos-de-trabajo)
5. [Uso](#uso)
6. [API Reference](#api-reference)
7. [Ejemplos](#ejemplos)
8. [Integración](#integración)
9. [Testing](#testing)

---

## Descripción General

El módulo de servicios actúa como capa de orquestación entre la API REST y los módulos de dominio. Proporciona servicios de alto nivel que combinan múltiples operaciones para casos de uso específicos.

### Funcionalidades Principales

| Servicio | Responsabilidad | Módulos Utilizados |
|----------|----------------|-------------------|
| **AlgorithmService** | CRUD de algoritmos | Parser |
| **AnalysisOrchestrator** | Análisis completo | Parser, Analyzer, Patterns, Structures, Visualization |
| **ValidationService** | Validación multi-nivel | Parser, Validator, SemanticAnalyzer |
| **ExportService** | Exportación multi-formato | Todos los módulos |
| **CacheService** | Optimización de rendimiento | - |

### Características

- **Orquestación**: Coordina múltiples módulos en flujos complejos
- **Transaccionalidad**: Maneja errores y rollback cuando es necesario
- **Optimización**: Caché inteligente para análisis repetidos
- **Flexibilidad**: Configuración granular de cada operación
- **Extensibilidad**: Preparado para integrar LLMs y bases de datos (Módulo 6)

---

## Arquitectura

```
services/
├── __init__.py                  # Exports principales
├── algorithm_service.py         # Gestión de algoritmos
├── analysis_orchestrator.py     # Orquestación de análisis completo
├── validation_service.py        # Validación de código
├── export_service.py           # Exportación de resultados
└── cache_service.py            # Servicio de caché
```

**Dependencias:**

```
Services Layer
     │
     ├─→ Parser Module (Módulo 1)
     ├─→ Analyzer Module (Módulo 2)
     ├─→ Patterns Module (Módulo 3)
     ├─→ Structures Module (Módulo 3.5)
     └─→ Visualization Module (Módulo 4)
```

---

## Servicios Implementados

### 1. AlgorithmService - Gestión de Algoritmos

**Responsabilidad:** CRUD completo de algoritmos con almacenamiento en disco.

**Características:**
- Creación y almacenamiento de algoritmos
- Búsqueda y filtrado avanzado
- Versionado de algoritmos
- Metadata y estadísticas
- Validación de tamaño y sintaxis

**Casos de uso:**
- Biblioteca de algoritmos
- Gestión de versiones
- Búsqueda por categoría/tags
- Tracking de análisis

**Limitaciones actuales:**
- Índice en memoria (migrar a base de datos en Módulo 6)
- No soporta concurrencia multi-usuario

### 2. AnalysisOrchestrator - Análisis Completo

**Responsabilidad:** Coordina análisis integral de algoritmos.

**Pipeline de análisis:**
```
Código → Parse → Complexity → Patterns → Structures → Visualization → Resultado
```

**Características:**
- Análisis paso a paso con tracking
- Manejo de errores parciales
- Configuración granular por módulo
- Generación de resumen ejecutivo
- Metadata de rendimiento

**Opciones configurables:**
- Análisis de complejidad (temporal/espacial)
- Detección de patrones (umbral de confianza)
- Detección de estructuras
- Generación de visualizaciones
- Análisis línea por línea

### 3. ValidationService - Validación Multi-Nivel

**Responsabilidad:** Validación exhaustiva de código pseudocódigo.

**Niveles de validación:**

| Nivel | Validaciones | Uso |
|-------|-------------|-----|
| **SYNTAX** | Solo sintaxis | Pre-parsing rápido |
| **SEMANTIC** | Sintaxis + semántica | Validación estándar |
| **STRUCTURAL** | + límites estructurales | Validación completa |
| **COMPLETE** | + best practices | QA detallado |

**Validaciones semánticas:**
- Variables no declaradas
- Tipos incompatibles
- Accesos inválidos a arrays
- Llamadas a funciones inexistentes

**Best Practices (heurísticas):**
- Longitud de líneas
- Nombres de variables descriptivos
- Complejidad ciclomática
- Profundidad de anidación

### 4. ExportService - Exportación Multi-Formato

**Responsabilidad:** Exporta resultados en múltiples formatos.

**Formatos soportados:**

| Formato | Uso | Estado |
|---------|-----|--------|
| **JSON** | API, procesamiento | ✓ Completo |
| **Markdown** | Documentación | ✓ Completo |
| **TXT** | Plain text | ✓ Completo |
| **HTML** | Web, reportes | ✓ Completo |
| **PDF** | Reportes formales | ⏳ Pendiente (Módulo 6) |

**Opciones configurables:**
- Incluir/excluir visualizaciones
- Incluir/excluir metadata
- Pretty print
- Nombres de archivo personalizados

### 5. CacheService - Caché de Resultados

**Responsabilidad:** Optimiza análisis repetidos.

**Estrategia actual:**
- Caché en memoria (Python dict)
- TTL configurable por tipo
- Limpieza automática de entradas expiradas
- Generación de claves por hash de código

**TTL por defecto:**
- Análisis completo: 1 hora
- Patrones: 2 horas
- Visualizaciones: 1 hora

**Preparado para migración a Redis (Módulo 6):**
- Interfaz abstracta
- Métodos async
- Soporte para distributed cache

---

## Flujos de Trabajo

### Flujo 1: Análisis Completo

```python
from app.services import AnalysisOrchestrator, CompleteAnalysisRequest

orchestrator = AnalysisOrchestrator()
request = CompleteAnalysisRequest(
    code="algorithm test(n)\nbegin\n  for i <- 1 to n do\n    x <- x + 1\nend",
    analyze_complexity=True,
    analyze_patterns=True,
    analyze_structures=True,
    generate_visualizations=True
)

result = await orchestrator.analyze_complete(request)
```

**Pasos ejecutados:**
1. **Parse**: Convierte código a AST
2. **Complexity**: Calcula O, Ω, Θ, S(n), T(n)
3. **Patterns**: Detecta técnicas algorítmicas
4. **Structures**: Identifica estructuras de datos
5. **Visualization**: Genera árbol recursión y flujo

### Flujo 2: Almacenar y Buscar Algoritmos

```python
from app.services import AlgorithmService, AlgorithmCreateRequest

service = AlgorithmService()

# Crear
create_req = AlgorithmCreateRequest(
    code="algorithm bubbleSort(A[n])\nbegin\n...\nend",
    name="Bubble Sort",
    category=AlgorithmCategory.SORTING,
    tags=["sorting", "quadratic"]
)
algorithm = await service.create(create_req)

# Buscar
criteria = AlgorithmSearchCriteria(
    category=AlgorithmCategory.SORTING,
    tags=["quadratic"]
)
results = await service.search(criteria)
```

### Flujo 3: Validar y Exportar

```python
from app.services import ValidationService, ExportService

# Validar
validator = ValidationService()
val_result = await validator.validate(
    ValidationRequest(code=code, level=ValidationLevel.COMPLETE)
)

if val_result.is_valid:
    # Exportar
    exporter = ExportService()
    export_result = await exporter.export(
        ExportRequest(
            data=analysis_result,
            format=ExportFormat.MARKDOWN,
            filename="reporte.md"
        )
    )
```

---

## Uso

### Ejemplo Completo: Pipeline Típico

```python
from app.services import (
    AlgorithmService,
    AnalysisOrchestrator,
    ValidationService,
    ExportService,
    CacheService,
    get_cache_service,
)

# 1. Validar código
validator = ValidationService()
validation = await validator.validate(
    ValidationRequest(code=code, level=ValidationLevel.COMPLETE)
)

if not validation.is_valid:
    print("Errores de validación:")
    for error in validation.errors:
        print(f"  - {error.message}")
    return

# 2. Verificar caché
cache = get_cache_service()
cache_key = generate_cache_key(CacheKey.ANALYSIS, code)
cached_result = await cache.get(cache_key)

if cached_result:
    print("Usando resultado cacheado")
    return cached_result

# 3. Ejecutar análisis completo
orchestrator = AnalysisOrchestrator()
result = await orchestrator.analyze_complete(
    CompleteAnalysisRequest(
        code=code,
        analyze_complexity=True,
        analyze_patterns=True,
        analyze_structures=True,
        generate_visualizations=True
    )
)

# 4. Guardar en caché
await cache.set(cache_key, result, cache_type=CacheKey.ANALYSIS)

# 5. Almacenar algoritmo
algo_service = AlgorithmService()
stored = await algo_service.create(
    AlgorithmCreateRequest(
        code=code,
        name=result.algorithm_name,
        category=AlgorithmCategory.OTHER
    )
)

# 6. Exportar resultado
exporter = ExportService()
await exporter.export(
    ExportRequest(
        data=result,
        format=ExportFormat.MARKDOWN,
        filename=f"{result.algorithm_name}_report.md"
    )
)

print(result.summary)
```

---

## API Reference

### AlgorithmService

```python
class AlgorithmService:
    async def create(request: AlgorithmCreateRequest) -> StoredAlgorithm
    async def get(algorithm_id: str) -> Optional[StoredAlgorithm]
    async def update(algorithm_id: str, request: AlgorithmUpdateRequest) -> Optional[StoredAlgorithm]
    async def delete(algorithm_id: str) -> bool
    async def search(criteria: AlgorithmSearchCriteria) -> List[AlgorithmMetadata]
    async def validate_code(code: str) -> bool
```

### AnalysisOrchestrator

```python
class AnalysisOrchestrator:
    async def analyze_complete(request: CompleteAnalysisRequest) -> CompleteAnalysisResult
```

### ValidationService

```python
class ValidationService:
    async def validate(request: ValidationRequest) -> ValidationResult
    async def quick_validate(code: str) -> bool
```

### ExportService

```python
class ExportService:
    async def export(request: ExportRequest) -> ExportResult
```

### CacheService

```python
class CacheService:
    async def get(key: str) -> Optional[Any]
    async def set(key: str, value: Any, ttl: Optional[int]) -> bool
    async def delete(key: str) -> bool
    async def clear(prefix: Optional[str]) -> int
```

---

## Ejemplos

Ver notebooks de Jupyter en `notebooks/09_services/`:
- `algorithm_management.ipynb`: Gestión de algoritmos
- `complete_analysis.ipynb`: Análisis completo
- `validation_workflow.ipynb`: Validación de código
- `export_examples.ipynb`: Exportación de resultados
- `caching_demo.ipynb`: Uso de caché

---

## Integración

### Con API REST

```python
# api/v1/endpoints/algorithms.py
from app.services import AlgorithmService

@router.post("/algorithms")
async def create_algorithm(request: AlgorithmCreateRequest):
    service = AlgorithmService()
    result = await service.create(request)
    return result.metadata

@router.post("/analyze")
async def analyze_algorithm(request: CompleteAnalysisRequest):
    orchestrator = AnalysisOrchestrator()
    result = await orchestrator.analyze_complete(request)
    return result
```

### Con Base de Datos (Futuro - Módulo 6)

El diseño actual está preparado para migrar a persistencia real:
- AlgorithmService → MongoDB/PostgreSQL
- CacheService → Redis
- Análisis histórico → TimeSeries DB

---

## Testing

### Ejecutar Tests

```bash
# Tests del módulo services
pytest tests/unit/test_services.py -v

# Tests de integración
pytest tests/integration/test_services_integration.py -v

# Coverage
pytest tests/unit/test_services.py --cov=app/services
```

### Tests Unitarios Importantes

```python
def test_algorithm_service_create()
def test_algorithm_service_search()
def test_analysis_orchestrator_complete()
def test_validation_service_levels()
def test_export_service_formats()
def test_cache_service_operations()
```

---

## Próximos Pasos (Módulo 6)

1. **Integrar bases de datos:**
   - MongoDB para algoritmos y análisis
   - PostgreSQL para usuarios y métricas
   - Redis para caché distribuido

2. **Integrar LLMs:**
   - ValidationService → validación con Claude/Gemini
   - Análisis de calidad de código con IA
   - Sugerencias de optimización

3. **Implementar sistema multiagente:**
   - LangGraph para orquestación
   - Agentes especializados por módulo

4. **Completar exportadores:**
   - PDF con reportlab
   - Excel avanzado con gráficos

5. **Optimizaciones:**
   - Análisis en background
   - Rate limiting
   - Métricas de rendimiento

---

## Limitaciones Actuales

| Limitación | Impacto | Solución Futura |
|------------|---------|-----------------|
| Caché en memoria | No persistente | Migrar a Redis |
| Almacenamiento en disco | No escalable | MongoDB/PostgreSQL |
| Sin autenticación | No multi-user | Auth en Módulo 6 |
| Exportación PDF limitada | Reportes incompletos | Implementar con reportlab |

---

## Referencias

- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)
- [Hexagonal Architecture](https://en.wikipedia.org/wiki/Hexagonal_architecture_(software))
- [Service Layer Pattern](https://www.martinfowler.com/eaaCatalog/serviceLayer.html)

---

**Última actualización:** 2025-01-11

**Versión del módulo:** 1.0.0

---

**Documentos relacionados:**

- [PARSER.md](PARSER.md) - Módulo de parsing
- [ANALYZER.md](ANALYZER.md) - Módulo de análisis
- [PATTERNS.md](PATTERNS.md) - Módulo de patrones
- [DATA_STRUCTURES.md](DATA_STRUCTURES.md) - Módulo de estructuras
- [VISUALIZATION.md](VISUALIZATION.md) - Módulo de visualización
