# Arquitectura del Sistema

Descripción completa de la arquitectura del sistema de análisis de complejidad algorítmica, sus componentes, flujos de datos y decisiones de diseño.

---

## Tabla de Contenidos

1. [Visión General](#visión-general)
2. [Arquitectura Hexagonal](#arquitectura-hexagonal)
3. [Estructura de Módulos](#estructura-de-módulos)
4. [Flujo de Datos Principal](#flujo-de-datos-principal)
5. [Capa de API](#capa-de-api)
6. [Capa de Dominio](#capa-de-dominio)
7. [Capa de Servicios](#capa-de-servicios)
8. [Capa de Infraestructura](#capa-de-infraestructura)
9. [Bases de Datos](#bases-de-datos)
10. [Sistema Multiagente](#sistema-multiagente)
11. [Decisiones de Diseño](#decisiones-de-diseño)
12. [Diagrama de Componentes](#diagrama-de-componentes)

---

## Visión General

El sistema es un backend de análisis de complejidad algorítmica construido como una API REST en Python. Dado un algoritmo en pseudocódigo, el sistema determina automáticamente:

- Complejidades temporal y espacial (notaciones O, Omega, Theta)
- Ecuaciones de recurrencia T(n) y S(n)
- Patrones y técnicas algorítmicas utilizadas
- Estructuras de datos involucradas
- Visualizaciones gráficas de la estructura del algoritmo

El sistema complementa el análisis estático con validación cruzada usando modelos de lenguaje (Claude de Anthropic, Gemini de Google y adaptadores locales como Ollama). La integración de LLMs está abstraída mediante adaptadores (`app/infrastructure/llm/`) y una `LLMFactory` que permite estrategias de conmutación por error, ensemble y enrutamiento.

---

## Arquitectura Hexagonal

El sistema sigue el patrón de **Arquitectura Hexagonal (Ports & Adapters)**, también conocida como Arquitectura Limpia. Este patrón garantiza que la lógica de negocio sea independiente de los detalles de infraestructura.

```
+----------------------------------------------------------+
|                      API REST (FastAPI)                   |
|                    (Adaptador de entrada)                 |
+---------------------------+------------------------------+
                            |
+---------------------------v------------------------------+
|                   Capa de Servicios                       |
|  AlgorithmService, AnalysisOrchestrator, ExportService    |
+---+----------+----------+-----------+-------------------+
    |          |          |           |
+---v---+  +--v---+  +---v---+  +----v----+
|Parser |  |Analiz|  |Patron.|  |Visualiz.|
|Mod. 1 |  |Mod. 2|  |Mod.3  |  |Mod. 4   |
+---+---+  +--+---+  +---+---+  +----+----+
    |         |          |            |
+---v---------v----------v------------v------------------+
|              Capa de Infraestructura                   |
|   MongoDB  PostgreSQL  Redis  Claude  Gemini  Ollama  |
|   (Adaptadores de salida, exportadores y adaptadores LLM)|
+--------------------------------------------------------+
```

### Principios aplicados

- **Independencia de frameworks:** La lógica de análisis no depende de FastAPI ni de la base de datos.
- **Independencia de la UI:** Los módulos de dominio pueden usarse sin la API REST.
- **Independencia de la base de datos:** Los repositorios abstraen el acceso a MongoDB o PostgreSQL.
- **Testabilidad:** Cada capa puede probarse de forma independiente con mocks.

---

## Estructura de Módulos

El sistema está organizado en siete módulos principales, cada uno con una responsabilidad clara:

| Módulo | Directorio | Responsabilidad |
|--------|-----------|-----------------|
| **1 - Parser** | `app/core/parser/` | Convertir pseudocódigo a AST |
| **2 - Analyzer** | `app/core/analyzer/` | Calcular complejidades y resolver recurrencias |
| **3 - Patterns** | `app/core/patterns/` | Detectar patrones algorítmicos |
| **3.5 - Data Structures** | `app/core/data_structures/` | Detectar estructuras de datos |
| **4 - Visualization** | `app/core/visualization/` | Generar visualizaciones gráficas |
| **5 - Services** | `app/services/` | Orquestar flujos de negocio complejos |
| **6 - Infrastructure** | `app/infrastructure/` | Bases de datos, LLMs, exportadores, agentes, tasks y telemetría |

Además, existen dos módulos opcionales:

| Módulo | Directorio | Responsabilidad |
|--------|-----------|-----------------|
| **Profiling** | `app/profiling/` | Métricas de rendimiento del sistema |
| **Parallel** | `app/parallel/` | Utilidades y pools para ejecución concurrente/async |
| **Dataset Generator** | `dataset_generator/` | Generar datasets para ML y testing |

---

## Flujo de Datos Principal

El flujo estándar para analizar un algoritmo es:

```
1. El cliente envía pseudocódigo via HTTP POST

2. FastAPI recibe la solicitud y la delega al servicio correspondiente

3. AnalysisOrchestrator coordina el pipeline:

   a. Parser (Módulo 1)
      - Lark tokeniza y parsea el pseudocódigo
      - ASTBuilder construye el AST tipado
      - SemanticAnalyzer valida reglas semánticas
      - Se produce: ProgramNode (AST)

   b. AnalyzerEngine (Módulo 2)
      - BigOAnalyzer recorre el AST para peor caso
      - OmegaAnalyzer recorre el AST para mejor caso
      - ThetaAnalyzer determina la cota ajustada
      - SpaceAnalyzer calcula S(n)
      - RecurrenceBuilder construye T(n) y S(n)
      - RecurrenceSolver resuelve las ecuaciones
      - Se produce: AnalysisResult

   c. PatternDetector (Módulo 3)
      - 12 detectores especializados analizan el AST
      - PatternScorer calcula y rankea resultados
      - Se produce: PatternDetectionResult

   d. StructureIdentifier (Módulo 3.5)
      - 8+ detectores buscan estructuras de datos
      - UsageAnalyzer analiza cómo se usan
      - Se produce: StructureDetectionResult

   e. Visualization (Módulo 4)
      - RecursionTreeGenerator para algoritmos recursivos
      - ExecutionFlowGenerator para flujos de control
      - DiagramRenderer produce el output final
      - Se produce: SVG, DOT, Mermaid, etc.

4. El resultado se serializa con Pydantic y se devuelve al cliente

5. Opcionalmente: CacheService guarda el resultado en Redis
   para evitar recalcular el mismo algoritmo

6. Opcionalmente: ExportService genera el resultado
   en el formato solicitado (PDF, Excel, etc.)
```

---

## Capa de API

### Framework

El sistema usa **FastAPI** como framework web. FastAPI provee:

- Validación automática de esquemas con Pydantic
- Documentación interactiva (Swagger y ReDoc) generada automáticamente
- Soporte nativo para operaciones asíncronas
- Serialización y deserialización automática de JSON

### Organización de Endpoints

Los endpoints están organizados bajo el prefijo `/api/v1/` y agrupados por módulo:

```
/api/v1/
├── health/          -> Verificación del estado del sistema
├── algorithms/      -> Parsing y gestión de algoritmos
├── analysis/        -> Análisis de complejidad
├── patterns/        -> Detección de patrones
├── structures/      -> Detección de estructuras de datos
├── visualization/   -> Generación de visualizaciones
├── export/          -> Exportación de resultados
└── validation/      -> Validación de código
```

### Middlewares

El sistema incluye middlewares para:

- CORS: Permite solicitudes desde el frontend (configurable por entorno)
- Rate Limiting: Limita solicitudes por IP para proteger el servicio
- Logging: Registra todas las solicitudes con timing
- Error Handling: Convierte excepciones internas a respuestas HTTP estándar

---

## Capa de Dominio

La capa de dominio (`app/core/`) contiene la lógica pura de negocio. Es completamente independiente de FastAPI, bases de datos y servicios externos.

### Módulo 1: Parser

El parser usa la librería **Lark** con una gramática LALR formal definida en `pseudocode.lark`. El proceso tiene tres etapas:

```
Código fuente (str)
      |
      v
Lark Parser
(tokenización + análisis sintáctico)
      |
      v
Parse Tree (árbol de Lark)
      |
      v
ASTBuilder (Transformer)
(construye nodos tipados)
      |
      v
ProgramNode (AST tipado)
      |
      v
SemanticAnalyzer
(valida uso de variables, tipos, etc.)
```

### Módulo 2: Analyzer

El analizador trabaja directamente sobre el AST mediante el patrón Visitor. Cada tipo de nodo AST tiene una lógica de análisis diferente:

- **ForLoopNode:** Multiplica la complejidad del cuerpo por el rango del ciclo
- **WhileLoopNode:** Estima iteraciones desde la condición
- **IfStatementNode:** En Big O toma la rama más costosa
- **CallStatementNode con recursión:** Construye la ecuación de recurrencia

### Módulo 3: Patterns

Cada detector implementa la interfaz `BasePatternDetector` y es completamente independiente. El `PatternDetector` ejecuta todos los detectores y el `PatternScorer` unifica y rankea los resultados.

### Módulo 4: Visualization

La generación de visualizaciones usa **NetworkX** para construir los grafos internamente y **Graphviz** para renderizarlos en formatos de salida. El `DiagramRenderer` soporta múltiples formatos de salida sin acoplar la representación interna al formato final.

---

## Capa de Servicios

Los servicios (`app/services/`) coordinan múltiples módulos del dominio para implementar casos de uso complejos. Actúan como orquestadores.

### Pipelines y `AnalysisOrchestrator`

El `AnalysisOrchestrator` actúa como orquestador central y materializa pipelines configurables ubicados en `app/services/pipelines/`. Un pipeline típico encadena pasos (`parse_step.py`, `complexity_step.py`, `pattern_step.py`, `structure_step.py`, `llm_validation_step.py`, `summarize_step.py`) permitiendo manejo fino de errores, retries y ejecución parcial. El orquestador soporta:

- Ejecución síncrona y asíncrona del pipeline.
- Paralelización de tareas independientes (por ejemplo, exportadores en paralelo).
- Integración con `CacheService`, `ExportService` y el sistema de agentes.

Recibe un `CompleteAnalysisRequest` y devuelve `AnalysisResult`, aplicando políticas de resiliencia (timeouts, circuit-breaker para llamadas a LLMs, fallbacks a modelos de respaldo).

### CacheService

Usa un hash del código fuente como clave de caché. Si el mismo código se analiza dos veces, el segundo análisis retorna en microsegundos desde caché en lugar de ejecutar el pipeline completo.

### ExportService

Delega en los exportadores de la capa de infraestructura. Soporta exportar el resultado de un análisis completo en cualquier formato registrado.

---

## Capa de Infraestructura

La infraestructura (`app/infrastructure/`) contiene todos los adaptadores hacia servicios externos.

### Patrón Repository

Todas las operaciones de base de datos se encapsulan en repositorios que implementan una interfaz común:

```python
class BaseRepository(ABC, Generic[T]):
    async def create(entity: T) -> T
    async def get_by_id(id: str) -> Optional[T]
    async def update(id: str, data: Dict) -> Optional[T]
    async def delete(id: str) -> bool
    async def list(skip: int, limit: int) -> List[T]
```

Esto permite cambiar la base de datos subyacente sin modificar la lógica de negocio.

### Patrón Adapter para LLMs

Cada LLM (Claude, Gemini, Ollama, etc.) implementa la misma interfaz `BaseLLM` ubicada en `app/infrastructure/llm/`. Componentes concretos detectados en el código:

- `llm_factory.py`: seleccionado dinámicamente según configuración y flags de runtime.
- `llm_circuit_breaker.py`: aplica timeouts, límites y fallbacks.
- `llm_ensemble.py` / `llm_evaluator.py`: estrategias para combinar respuestas y validar consistencia entre modelos.
- `llm_router.py` y `prompt_templates.py`: ruteo y plantillas de prompt reutilizables.
- `response_parser.py`: normaliza la salida de distintos proveedores.

El `LLMFactory` y el `llm_circuit_breaker` permiten políticas de conmutación por error y degradación controlada; cuando el LLM primario falla, se intenta un modelo de respaldo o se marca la validación como degradada, manteniendo la respuesta principal del análisis.

### Exportadores

Cada formato de exportación implementa `BaseExporter` (por ejemplo `pdf_exporter.py`, `json_exporter.py`, `mermaid_exporter.py`, `dot_exporter.py`, `svg_exporter.py`). El `ExporterFactory` los registra y los crea bajo demanda. Las exportaciones se pueden ejecutar en paralelo mediante `ThreadPoolExecutor` o colas de tareas cuando se delega a workers (Celery).

---

## Bases de Datos

El sistema usa tres tecnologías de persistencia con responsabilidades distintas:

### MongoDB (Motor + Beanie)

Almacena datos no estructurados o semi-estructurados que cambian frecuentemente:

- **algorithms**: Algoritmos registrados y su código fuente
- **analysis_results**: Resultados completos de análisis
- **pattern_detections**: Detecciones de patrones con toda su metadata

MongoDB se eligió porque los resultados de análisis son documentos JSON complejos con estructura variable, que no encajan bien en tablas relacionales. En el repositorio se observan modelos Beanie en `app/infrastructure/database/models/mongo/` (por ejemplo `algorithm.py`, `analysis_result.py`) y repositorios específicos en `app/infrastructure/database/repositories/`, que encapsulan el acceso a la capa de persistencia.

### PostgreSQL (SQLAlchemy + Asyncpg)

Almacena datos estructurados con relaciones fuertes:

- **users**: Cuentas de usuario
- **sessions**: Sesiones y tokens de autenticación
- **audit_logs**: Registro completo de eventos del sistema

PostgreSQL se eligió para datos que requieren integridad transaccional y consultas relacionales. Los modelos SQLAlchemy y adaptadores se encuentran en `app/infrastructure/database/models/postgres/` y el cliente/aspectos de conexión en `postgresql_client.py`.

### Redis

Caché de resultados de análisis. Las claves tienen un TTL configurable (por defecto 1 hora para análisis, 2 horas para patrones). Esto evita recalcular análisis idénticos y reduce la carga sobre los módulos de dominio.

---

## Sistema Multiagente

El sistema incluye un pipeline multiagente opcional basado en **LangGraph** para análisis asistido por IA:

```
Usuario (código)
      |
      v
CoordinatorAgent
      |
    +--+------------------+
    |                     |
    v                     v
ParserAgent          (En paralelo)
    |
    v
ComplexityAgent
    |
    v
PatternAgent
    |
    v
ValidationAgent
(Claude o Gemini)
    |
    v
Resultado validado por IA
```

Cada agente recibe el estado compartido (`AgentState`), realiza su tarea y pasa el estado enriquecido al siguiente agente. Componentes detectados en el repositorio incluyen `coordinator_agent.py`, `parser_agent.py`, `complexity_agent.py`, `pattern_agent.py`, `validation_agent.py` y utilidades para orquestación (`agent_graph.py`). El `ValidationAgent` puede combinar salidas vía `llm_ensemble` y utiliza `llm_router`/`prompt_templates` para controlar costos y precisión.

---

## Decisiones de Diseño

### Por qué Lark para el parser

Lark es una librería de parsing LALR para Python que permite definir gramáticas formales en notación BNF extendida. Se eligió sobre alternativas como ANTLR o PLY porque:

- La gramática se define en un archivo `.lark` separado, fácil de modificar
- Soporta español e inglés como palabras clave de forma natural
- Genera árboles de parse que se transforman fácilmente con el patrón Transformer

### Por qué análisis estático en lugar de dinámico

El análisis estático (sobre el AST) permite analizar cualquier algoritmo sin ejecutarlo. El análisis dinámico requeriría ejecutar el algoritmo con entradas de distintos tamaños, lo que es más lento, menos predecible y potencialmente inseguro para código arbitrario.

### Por qué separar MongoDB y PostgreSQL

Los resultados de análisis son documentos JSON con estructura variable (la presencia o ausencia de ecuaciones de recurrencia, número de patrones detectados, etc.). MongoDB encaja mejor para esto. Los usuarios, sesiones y logs tienen estructura fija y relaciones bien definidas, donde PostgreSQL y su integridad transaccional son superiores.

### Por qué Redis para caché

El análisis de un algoritmo puede tardar entre 50 y 500 ms. Si el mismo algoritmo se analiza múltiples veces (por distintos usuarios o en desarrollo), Redis evita ejecutar el pipeline completo. La clave de caché es un hash SHA-256 del código fuente, garantizando que cambios mínimos generen análisis frescos.

### Por qué Arquitectura Hexagonal

Permite que los módulos de dominio sean completamente independientes de FastAPI, MongoDB y cualquier servicio externo. Esto facilita:

- Probar los módulos con tests unitarios sin necesidad de base de datos
- Cambiar FastAPI por otro framework sin tocar la lógica de análisis
- Migrar de MongoDB a otra base de datos sin modificar los módulos de dominio

---

## Testing y Calidad

El repositorio incluye una suite de pruebas amplia bajo `tests/` (unit, integration, e2e, smoke, load). Cada módulo crítico (parser, analyzer, patterns, infrastructure adapters, services y agentes) cuenta con tests asociados. La separación por capas facilita:

- Tests unitarios con mocks para adaptadores externos (BD, LLMs, exporters).
- Tests de integración que validan el pipeline completo y la interacción con MongoDB/Postgres/Redis (configurables mediante fixtures y Docker Compose).
- Tests E2E para el flujo de análisis completo y exportación.

La CI (cuando esté configurada) debe ejecutar primero los tests unitarios, luego los integration/e2e en entornos controlados.

## Diagrama de Componentes

```
+----------------------------------------------+
|                   CLIENTE                    |
| (navegador, curl, Python httpx, etc.)        |
+-------------------+------------------------------+
                    | HTTP
                    v
+-------------------+------------------------------+
|              FastAPI Application               |
|  +-------------+  +--------+  +-------------+  |
|  | Middlewares |  | Routes |  | Pydantic DTOs|  |
|  +-------------+  +--------+  +-------------+  |
+------------------+--+----------------------------+
                   |
        +----------+----------+
        |                     |
+-------v------+    +--------v--------+
| Services     |    | Dependencies   |
| (Mod. 5)     |    | (DI Container) |
+-------+------+    +----------------+
        |
+-------v-----------------------------------------+
|              DOMAIN CORE                        |
|  +--------+ +----------+ +----------+ +------+  |
|  |Parser  | |Analyzer  | |Patterns  | |Data  |  |
|  |Mod. 1  | |Mod. 2    | |Mod. 3    | |Struct|  |
|  +--------+ +----------+ +----------+ |Mod.3.5|  |
|                                        +------+  |
|  +---------------------------------------------+  |
|  |     Visualization (Mod. 4)                  |  |
|  +---------------------------------------------+  |
+------------------+------------------------------+
                   |
+------------------v------------------------------+
|           INFRASTRUCTURE (Mod. 6)               |
|  +-------+ +----------+ +------+ +-----------+  |
|  |MongoDB| |PostgreSQL| |Redis | |LLMs       |  |
|  |Beanie | |SQLAlchemy| |Cache | |Claude     |  |
|  +-------+ +----------+ +------+ |Gemini     |  |
|                                   +-----------+  |
|  +---------------------------------------------+  |
|  |   Exporters: JSON, MD, PDF, Excel, HTML...  |  |
|  +---------------------------------------------+  |
|  +---------------------------------------------+  |
|  |   Agents: LangGraph Multiagent Pipeline     |  |
|  +---------------------------------------------+  |
+-------------------------------------------------+
```