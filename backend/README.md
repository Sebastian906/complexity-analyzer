# Analizador de Complejidades Algorítmicas

Sistema inteligente de análisis automático de complejidad computacional asistido por LLMs (Large Language Models).

## Descripción

Este proyecto implementa un analizador avanzado que, dado un algoritmo en pseudocódigo, determina automáticamente:

- **Complejidad Temporal**: Notaciones O (peor caso), Ω (mejor caso), Θ (caso promedio)
- **Complejidad Espacial**: Análisis de uso de memoria S(n)
- **Ecuaciones de Recurrencia**: T(n) y S(n) con simplificación automática
- **Detección de Patrones**: Identificación de técnicas algorítmicas (Divide y Vencerás, DP, Greedy, etc.)
- **Análisis Línea por Línea**: Conteo de ejecuciones por instrucción
- **Visualización**: Árboles de recursión y grafos de ejecución
- **Validación con IA**: Verificación cruzada usando Claude y Gemini
- **Validación con IA**: Verificación cruzada usando Claude, Gemini y adaptadores locales (p. ej. Ollama)

## Arquitectura

El sistema sigue una **Arquitectura Hexagonal (Ports & Adapters)** con separación clara de capas:

```
┌─────────────────────────────────────────┐
│         API Layer (FastAPI)             │
├─────────────────────────────────────────┤
│         Application Services            │
├─────────────────────────────────────────┤
│  Domain Core (Parser, Analyzer, etc.)   │
├─────────────────────────────────────────┤
│  Infrastructure (DB, LLM, Export)       │
└─────────────────────────────────────────┘
```

## Tecnologías

### Backend
- **Framework**: FastAPI 0.109+
- **Lenguaje**: Python 3.11+
- **Parser**: Lark Parser
- **Análisis Simbólico**: SymPy
- **Grafos**: NetworkX

### LLMs
- **Claude** (Anthropic) - Análisis y validación
- **Gemini** (Google) - Validación alternativa
- **LangGraph** - Orquestación multiagente
- **Ollama** (local/embebido) - Adaptador disponible en `app/infrastructure/llm/ollama_adapter.py` (uso opcional, útil en entornos offline)

### Bases de Datos
- **MongoDB**: Almacenamiento principal (algoritmos y análisis)
- **PostgreSQL**: Datos relacionales (usuarios, métricas)
- **Redis**: Caché de resultados

### Visualización
- **Graphviz**: Árboles de recursión
- **Matplotlib/Plotly**: Gráficos y diagramas

## Instalación

### Prerrequisitos

- Python 3.11 o superior
- Docker y Docker Compose (opcional pero recomendado)
- MongoDB 7.0+
- Redis 7+

### Instalación Local
```bash
# 1. Clonar el repositorio
git clone https://github.com/Sebastian906/complexity-analyzer.git
cd complexity-analyzer
cd backend

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp env/.env.example .env
# Editar .env con tus credenciales

# 5. Inicializar base de datos
python scripts/init_db.py

# 6. Ejecutar la aplicación
uvicorn app.main:app --reload
```

### Instalación con Docker
```bash
# 1. Configurar variables de entorno
cp env/.env.example .env
# Editar .env con tus credenciales

# 2. Levantar servicios
docker-compose up -d

# 3. Ver logs
docker-compose logs -f api

# Asegúrate de que los workers de Celery y Redis estén activos (si usas ejecución asíncrona)
# docker-compose incluye `celery-worker` y `redis`; verifica con `docker-compose ps`.

# La API estará disponible en: http://localhost:8000
```

## Uso Rápido

### API REST
```bash
# Health Check
curl http://localhost:8000/api/v1/health

# Analizar un algoritmo (sin validaciones LLM pesadas)
curl -X POST http://localhost:8000/api/v1/analysis/analyze-complete \
  -H "Content-Type: application/json" \
  -d '{
    "algorithm_code": "algorithm test(n)\nbegin\n  for i ← 1 to n do\n    x ← x + 1\nend"
  }'

# Para análisis pesados o pipelines que incluyan validación LLM/visualización, usa el endpoint asíncrono:
# Envío: `POST /api/v1/analysis/async` → devuelve `task_id`
# Consulta de estado: `GET /api/v1/analysis/task/{task_id}`
# Nota: si no hay workers Celery disponibles, los endpoints asíncronos responderán 503.
```

### Ejemplo con Python
```python
import httpx

# Cliente API
client = httpx.Client(base_url="http://localhost:8000")

# Analizar algoritmo
response = client.post("/api/v1/analysis/analyze-complete", json={
    "algorithm_code": """
    quicksort(A[1..n])
    begin
        if n > 1 then
        begin
            q ← partition(A, 1, n)
            call quicksort(A[1..q-1])
            call quicksort(A[q+1..n])
        end
    end
    """
})

result = response.json()
print(f"Big O: {result['big_o']}")
print(f"Omega: {result['omega']}")
print(f"Theta: {result['theta']}")
```

## Documentación

- [Documentación de la API](docs/api_reference.md)
- [Especificación de Gramática](docs/grammar_specification.md)
- [Guía de Análisis de Complejidad](docs/complexity_analysis_guide.md)
- [Arquitectura del Sistema](docs/architecture.md)
- [Guía de Despliegue](docs/deployment.md)

## Testing
```bash
# Ejecutar todos los tests
pytest

# Con coverage
pytest --cov=app --cov-report=html

# Solo tests unitarios
pytest tests/unit/

# Solo tests de integración
pytest tests/integration/

# Ver reporte de coverage
open htmlcov/index.html
```

## Estructura del Proyecto
```
complexity-analyzer-backend/
├── app/                    # Código fuente principal
│   ├── api/               # Endpoints REST
│   ├── core/              # Lógica de dominio
│   ├── services/          # Servicios de aplicación
│   ├── infrastructure/    # Adaptadores externos
│   ├── schemas/           # Schemas Pydantic
│   └── utils/             # Utilidades
├── tests/                 # Tests
├── config/                # Configuraciones YAML
├── notebooks/             # Jupyter notebooks
├── docs/                  # Documentación
├── data/                  # Datos persistentes
└── scripts/               # Scripts de utilidad
```

## Configuración

### Variables de Entorno Principales
```bash
# LLM APIs
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...

# Base de Datos
MONGODB_URL=mongodb://localhost:27017
REDIS_HOST=localhost

# Configuración
APP_ENV=development
DEBUG=true
```

Ver `env/.env.example` para la lista completa.

## Features Implementadas

- Parser de pseudocódigo con gramática formal
- Análisis de complejidad (O, Ω, Θ)
- Análisis línea por línea
- Ecuaciones de recurrencia T(n) y S(n)
- Detección de 10+ patrones algorítmicos
- Validación cruzada con Claude y Gemini
- Visualización de árboles de recursión
- Exportación en PDF, JSON, Markdown, Excel
- Sistema de caché con Redis
- API REST con documentación automática

## Features Planificadas

- Sistema multiagente con LangGraph
- Generador de datasets sintéticos
- Profiling avanzado de performance
- Detección de estructuras de datos
- Análisis de complejidad amortizada
- Interfaz web (Frontend Astro)

## Contribución

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

### Guías de Estilo

- Seguir PEP 8 para código Python
- Usar Black para formateo automático
- Cobertura de tests > 80%
- Documentar todas las funciones públicas

## Licencia

Este proyecto está bajo la Licencia MIT. Ver archivo `LICENSE` para más detalles.

## Autores

- **Sebastián Salazar Güiza** - *Trabajo Inicial* - [Sebastian906](https://github.com/Sebastian906)

## Agradecimientos

- Proyecto académico de Análisis y Diseño de Algoritmos
- Anthropic por la API de Claude
- Google por la API de Gemini
- Comunidad de FastAPI y Python

## Contacto

- Email: elsebas1912@gmail.com
- GitHub: [@Sebastian906](https://github.com/Sebastian906)
- LinkedIn: [Sebastián Salazar Güiza](https://www.linkedin.com/in/sebasti%C3%A1n-salazar-g%C3%BCiza-756b40210/)

---

Si este proyecto te ha sido útil, considera darle una estrella en GitHub