# Módulo 6: Infraestructura

Capa de infraestructura que proporciona servicios externos, persistencia, caché y adaptadores para LLMs.

---

## Tabla de Contenidos

1. [Descripción General](#descripción-general)
2. [Arquitectura](#arquitectura)
3. [Submódulos](#submódulos)
   - [Agents](#agents---sistema-multiagente)
   - [Cache](#cache---sistema-de-caché)
   - [Database](#database---bases-de-datos)
   - [Export](#export---exportadores)
   - [LLM](#llm---large-language-models)
4. [Patrones de Diseño](#patrones-de-diseño)
5. [Configuración](#configuración)
6. [API Reference](#api-reference)
7. [Ejemplos](#ejemplos)
8. [Testing](#testing)

---

## Descripción General

El módulo `infrastructure` implementa la capa de infraestructura de la aplicación, siguiendo los principios de Clean Architecture. Proporciona:

- **Sistema multiagente** con LangGraph para análisis distribuido
- **Clientes de base de datos** para MongoDB y PostgreSQL
- **Sistema de caché** con Redis para optimización de rendimiento
- **Adaptadores para LLMs** (Claude y Gemini)
- **Exportadores** para generación de reportes en múltiples formatos

### Funcionalidades Principales

| Submódulo | Responsabilidad | Dependencias Externas |
|-----------|-----------------|----------------------|
| **Agents** | Pipeline multiagente | LangGraph |
| **Cache** | Caché distribuido | Redis |
| **Database** | Persistencia | MongoDB, PostgreSQL |
| **Export** | Generación de reportes | reportlab, openpyxl |
| **LLM** | Integración con IA | Anthropic, Google AI |

---

## Arquitectura

```
infrastructure/
    __init__.py              # Exportaciones publicas
    agents/                  # Sistema multiagente
        __init__.py
        base_agent.py        # Agente base abstracto
        parser_agent.py      # Agente de parsing
        complexity_agent.py  # Agente de complejidad
        pattern_agent.py     # Agente de patrones
        validation_agent.py  # Agente de validacion
        coordinator_agent.py # Coordinador de agentes
        agent_graph.py       # Orquestador con LangGraph
    cache/                   # Sistema de cache
        __init__.py
        redis_cache.py       # Cliente Redis
        cache_keys.py        # Builders de claves
    database/                # Bases de datos
        __init__.py
        connection.py        # Gestor de conexiones
        database_factory.py  # Factory de clientes
        mongodb_client.py    # Cliente MongoDB
        postgresql_client.py # Cliente PostgreSQL
        models/              # Modelos de datos
            mongo/           # Modelos MongoDB
            postgres/        # Modelos PostgreSQL
        repositories/        # Repositorios
            base_repository.py
            algorithm_repository.py
            analysis_repository.py
            user_repository.py
            metrics_repository.py
            cache_repository.py
    export/                  # Exportadores
        __init__.py
        base_exporter.py     # Exportador base
        json_exporter.py
        markdown_exporter.py
        csv_exporter.py
        html_exporter.py
        pdf_exporter.py
        excel_exporter.py
        dot_exporter.py
        mermaid_exporter.py
        svg_exporter.py
    llm/                     # Large Language Models
        __init__.py
        base_llm.py          # Interface base
        claude_adapter.py    # Adaptador Anthropic
        gemini_adapter.py    # Adaptador Google
        ollama_adapter.py    # Adaptador Ollama
        llm_factory.py       # Factory de LLMs
        prompt_templates.py  # Plantillas de prompts
        response_parser.py   # Parser de respuestas
```

**Dependencias:**

```
Infrastructure Layer
     │
     ├─→ Services Layer (Módulo 5)
     ├─→ External: Redis
     ├─→ External: MongoDB
     ├─→ External: PostgreSQL
     ├─→ External: Anthropic API
     └─→ External: Google AI API
```

---

## Submódulos

### Agents - Sistema Multiagente

Sistema de agentes especializados que trabajan en conjunto para analizar algoritmos.

#### Clases Principales

| Clase | Descripción |
|-------|-------------|
| `BaseAgent` | Clase base abstracta para todos los agentes |
| `AgentState` | Estado compartido entre agentes durante el pipeline |
| `ParserAgent` | Parsea el código y genera el AST |
| `ComplexityAgent` | Analiza la complejidad temporal y espacial |
| `PatternAgent` | Detecta patrones algorítmicos |
| `ValidationAgent` | Valida resultados con LLM |
| `CoordinatorAgent` | Coordina la ejecución del pipeline |
| `AgentGraphOrchestrator` | Orquestador basado en LangGraph |

#### AgentState

```python
@dataclass
class AgentState:
    algorithm_code: str
    algorithm_name: Optional[str] = None
    ast: Optional[Any] = None
    complexity_result: Optional[Dict[str, Any]] = None
    pattern_result: Optional[Dict[str, Any]] = None
    structure_result: Optional[Dict[str, Any]] = None
    validation_result: Optional[Dict[str, Any]] = None
    errors: list = None
```

#### Uso del Coordinador

```python
from app.infrastructure import CoordinatorAgent

coordinator = CoordinatorAgent(use_llm=True)
result = await coordinator.execute_pipeline(algorithm_code)
```

---

### Cache - Sistema de Caché

Sistema de caché distribuido con Redis para optimizar el rendimiento.

#### Clases Principales

| Clase/Función | Descripción |
|---------------|-------------|
| `RedisCache` | Cliente Redis asíncrono |
| `CachePrefix` | Prefijos para claves de caché |
| `CacheTTL` | Tiempos de vida predefinidos |

#### Builders de Claves

El módulo proporciona funciones para construir claves de caché de forma consistente:

```python
from app.infrastructure import (
    build_analysis_key,
    build_complexity_key,
    build_pattern_key,
    build_algorithm_key,
    build_user_session_key,
)

# Ejemplos
key = build_analysis_key(algorithm_hash="abc123")
key = build_user_session_key(user_id="user_001")
```

#### Uso del Caché

```python
from app.infrastructure import get_redis_client

redis = get_redis_client()
await redis.connect()

# Guardar
await redis.set("key", {"data": "value"}, ttl=3600)

# Obtener
data = await redis.get("key")

# Eliminar
await redis.delete("key")
```

---

### Database - Bases de Datos

Capa de persistencia con soporte para MongoDB y PostgreSQL.

#### Clientes

| Cliente | Descripción |
|---------|-------------|
| `MongoDBClient` | Cliente para MongoDB (datos de análisis) |
| `PostgreSQLClient` | Cliente para PostgreSQL (usuarios, sesiones) |
| `DatabaseConnectionManager` | Gestor unificado de conexiones |

#### Modelos MongoDB

```python
from app.infrastructure import Algorithm, AnalysisResult, PatternDetection

# Modelo de algoritmo
algorithm = Algorithm(
    name="bubbleSort",
    code="algorithm bubbleSort...",
    category="sorting"
)
```

#### Modelos PostgreSQL

```python
from app.infrastructure import User, Session, AuditLog

# Modelo de usuario
user = User(
    username="admin",
    email="admin@example.com"
)
```

#### Repositorios

Implementan el patrón Repository para acceso a datos:

| Repositorio | Descripción |
|-------------|-------------|
| `BaseRepository` | Repositorio base abstracto |
| `AlgorithmRepository` | CRUD de algoritmos (MongoDB) |
| `AnalysisRepository` | CRUD de análisis (MongoDB) |
| `UserRepository` | CRUD de usuarios (PostgreSQL) |
| `MetricsRepository` | Métricas de rendimiento |
| `CacheRepository` | Repositorio con caché integrado |

#### Interface del Repositorio Base

```python
class BaseRepository(ABC, Generic[T]):
    async def create(self, entity: T) -> T
    async def get_by_id(self, id: str) -> Optional[T]
    async def update(self, id: str, data: Dict) -> Optional[T]
    async def delete(self, id: str) -> bool
    async def list(self, skip: int, limit: int) -> List[T]
```

#### Inicialización de Bases de Datos

```python
from app.infrastructure import init_databases, close_databases

# Al iniciar la aplicación
await init_databases()

# Al cerrar la aplicación
await close_databases()
```

---

### Export - Exportadores

Sistema de exportación de resultados a múltiples formatos.

#### Formatos Soportados

| Formato | Clase | Descripción |
|---------|-------|-------------|
| JSON | `JSONExporter` | Datos estructurados |
| Markdown | `MarkdownExporter` | Documentación |
| CSV | `CSVExporter` | Hojas de cálculo |
| HTML | `HTMLExporter` | Reportes web |
| DOT | `DOTExporter` | Grafos GraphViz |
| Mermaid | `MermaidExporter` | Diagramas Mermaid |
| SVG | `SVGExporter` | Gráficos vectoriales |
| PDF | `PDFExporter` | Reportes formales |
| Excel | `ExcelExporter` | Hojas Excel |

#### Configuración de Exportación

```python
from app.infrastructure import ExportConfig, ExportFormat

config = ExportConfig(
    format=ExportFormat.PDF,
    output_path=Path("output/report.pdf"),
    include_metadata=True,
    include_code=True,
    include_visualizations=True,
    include_statistics=True,
    pretty_print=True
)
```

#### Uso de Exportadores

```python
from app.infrastructure import export_analysis, ExportFormat

# Exportar a un formato
result = export_analysis(
    algorithm=algorithm,
    analysis=analysis_result,
    format=ExportFormat.PDF
)

# Exportar a múltiples formatos
from app.infrastructure import export_to_multiple_formats

results = export_to_multiple_formats(
    data=export_data,
    formats=[ExportFormat.JSON, ExportFormat.PDF, ExportFormat.MARKDOWN]
)
```

---

### LLM - Large Language Models

Integración con modelos de lenguaje para validación y análisis avanzado.

#### Adaptadores Soportados

| Adaptador | Proveedor | Modelo |
|-----------|-----------|--------|
| `ClaudeAdapter` | Anthropic | Claude 3/3.5 |
| `GeminiAdapter` | Google | Gemini Pro |
| `OllamaAdapter` | Ollama | Ollama |

El paquete `llm` incluye utilidades para creación y manejo de modelos: además de los adaptadores, contiene `llm_factory.py`, `prompt_templates.py` y `response_parser.py`. La `LLMFactory` permite configurar un LLM primario y un LLM de respaldo (fallback) y devolver objetos `BaseLLM` listos para uso en agentes y servicios.

Nota: la integración está preparada para ampliar su catálogo de adaptadores y añadir utilidades de orquestación (por ejemplo, circuit-breakers o ensembles) dentro de `app/infrastructure/llm/` si se incorporan en el repositorio.

#### Interface Base

```python
class BaseLLM(ABC):
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> LLMResponse

    async def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]
```

#### Respuesta del LLM

```python
@dataclass
class LLMResponse:
    content: str
    model: str
    tokens_used: int
    finish_reason: str
    metadata: Dict[str, Any]
```

#### Uso del Factory

```python
from app.infrastructure import LLMFactory

# Crear LLM primario (Claude)
llm = LLMFactory.create_primary()

# Crear LLM de respaldo (Gemini)
fallback = LLMFactory.create_fallback()

# Generar respuesta
response = await llm.generate(
    prompt="Analiza la complejidad de este algoritmo...",
    system_prompt="Eres un experto en algoritmos."
)
```

---

## Patrones de Diseño

El módulo implementa los siguientes patrones:

| Patrón | Uso |
|--------|-----|
| **Repository** | Acceso a datos desacoplado |
| **Factory** | Creación de clientes de BD y LLMs |
| **Adapter** | Integración de diferentes LLMs |
| **Strategy** | Exportadores intercambiables |
| **Singleton** | Clientes de caché y BD |
| **Pipeline** | Sistema multiagente |

---

## Configuración

Las configuraciones se manejan a través de variables de entorno:

### Redis
```
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
REDIS_MAX_CONNECTIONS=10
```

### MongoDB
```
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=complexity_analyzer
```

### PostgreSQL
```
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=
POSTGRES_DATABASE=complexity_analyzer
```

### LLMs
```
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
PRIMARY_LLM=claude
FALLBACK_LLM=gemini
```

---

## API Reference

### Exports Principales

```python
from app.infrastructure import (
    # Agents
    BaseAgent, AgentState,
    ParserAgent, ComplexityAgent, PatternAgent,
    ValidationAgent, CoordinatorAgent,
    AgentGraphOrchestrator,
    
    # Cache
    RedisCache, get_redis_client,
    CachePrefix, CacheTTL,
    build_analysis_key, build_pattern_key,
    
    # Database
    MongoDBClient, PostgreSQLClient,
    DatabaseConnectionManager,
    init_databases, close_databases,
    
    # Repositories
    BaseRepository, AlgorithmRepository,
    AnalysisRepository, UserRepository,
    MetricsRepository, CacheRepository,
    
    # Export
    ExportFormat, ExportConfig,
    export_analysis, export_to_multiple_formats,
    JSONExporter, MarkdownExporter, PDFExporter,
    
    # LLM
    BaseLLM, LLMResponse, LLMFactory,
    ClaudeAdapter, GeminiAdapter, OllamaAdapter,
)
```

---

## Ejemplos

### Pipeline Completo de Análisis

```python
from app.infrastructure import (
    CoordinatorAgent,
    export_analysis,
    ExportFormat,
    get_redis_client,
)

# 1. Ejecutar análisis con agentes
coordinator = CoordinatorAgent(use_llm=True)
result = await coordinator.execute_pipeline(code)

# 2. Cachear resultado
cache = get_redis_client()
await cache.set(f"analysis:{algorithm_id}", result, ttl=3600)

# 3. Exportar a PDF
export_result = export_analysis(
    algorithm=result["algorithm"],
    analysis=result["analysis"],
    format=ExportFormat.PDF
)
```

### Repositorio con Caché

```python
from app.infrastructure import (
    AlgorithmRepository,
    CacheRepository,
    get_mongodb_client,
)

# Crear repositorio con caché
mongo = await get_mongodb_client()
base_repo = AlgorithmRepository(mongo)
repo = CacheRepository(base_repo, cache_ttl=1800)

# Las operaciones se cachean automáticamente
algorithm = await repo.get_by_id("algo_001")
```

### Exportación Múltiple

```python
from app.infrastructure import (
    ExportData,
    export_to_multiple_formats,
    ExportFormat,
)

data = ExportData(
    algorithm=algorithm,
    analysis=analysis_result,
    patterns=pattern_detection
)

results = export_to_multiple_formats(
    data=data,
    formats=[
        ExportFormat.JSON,
        ExportFormat.MARKDOWN,
        ExportFormat.PDF,
        ExportFormat.EXCEL
    ],
    output_dir=Path("exports/")
)

for result in results:
    print(f"{result.format}: {result.output_path}")
```

---

## Testing

### Ejecutar Tests del Módulo

```bash
# Tests de infraestructura completos
pytest tests/infrastructure/ -v

# Tests por submódulo
pytest tests/infrastructure/test_exports.py -v
pytest tests/infrastructure/test_metrics_collector.py -v

# Con cobertura
pytest tests/infrastructure/ --cov=app/infrastructure --cov-report=html
```

### Estructura de Tests

```
tests/infrastructure/
├── test_exports.py           # Tests de exportadores
├── test_metrics_collector.py # Tests de métricas y alertas
└── conftest.py               # Fixtures compartidas
```

### Consideraciones de Testing

- **Mocks**: Los tests usan mocks para servicios externos (Redis, MongoDB, LLMs)
- **Async**: Usar `pytest-asyncio` para tests asíncronos
- **Threading**: El `MetricsCollector` usa `RLock` para evitar deadlocks

---

## Referencias

- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Repository Pattern](https://martinfowler.com/eaaCatalog/repository.html)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Redis Documentation](https://redis.io/docs/)
- [MongoDB Documentation](https://www.mongodb.com/docs/)
