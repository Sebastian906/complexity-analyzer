# Quick Start - Complexity Analyzer

Guía rápida para poner el proyecto en funcionamiento en 5 minutos.

## Prerrequisitos

- Python 3.11+
- pip
- (Opcional) MongoDB, Redis para funcionalidades avanzadas

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/Sebastian906/complexity-analyzer.git
cd complexity-analyzer/backend
```

### 2. Crear entorno virtual

```bash
python -m venv venv

# En Linux/Mac
source venv/bin/activate

# En Windows
venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
# Dependencias principales
pip install -r requirements.txt

# Dependencias de desarrollo (opcional)
pip install -r requirements-dev.txt
```

### 4. Configurar variables de entorno

```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar .env con tus configuraciones
# Para empezar, solo necesitas ajustar:
# - APP_ENV=development
# - DEBUG=true
# Las demás pueden quedarse por defecto
```

## Ejecutar el Servidor

### Opción 1: Script de desarrollo (Recomendado)

```bash
python scripts/run_dev.py
```

### Opción 2: Uvicorn directo

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Opción 3: Desde el módulo

```bash
python -m app.main
```

El servidor estará corriendo en: **http://localhost:8000**

## Documentación Interactiva (Swagger)

Una vez que el servidor esté corriendo, abre tu navegador:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Probar la API

### Opción 1: Swagger UI (Interfaz Visual)

1. Abre http://localhost:8000/docs
2. Expande el endpoint `/api/v1/algorithms/parse`
3. Click en "Try it out"
4. Pega este código de ejemplo:

```
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
```

5. Click "Execute"
6. Verás el AST generado en la respuesta

### Opción 2: Script de Pruebas

```bash
# Instalar rich para output bonito
pip install rich

# Ejecutar tests
python scripts/test_api.py
```

### Opción 3: cURL

```bash
# Health check
curl http://localhost:8000/api/v1/health/

# Parsear algoritmo
curl -X POST http://localhost:8000/api/v1/algorithms/parse \
  -H "Content-Type: application/json" \
  -d '{
    "code": "algorithm test(n)\nbegin\n  x ← 1\nend",
    "validate": true
  }'

# Ver ejemplos
curl http://localhost:8000/api/v1/algorithms/examples
```

### Opción 4: Python httpx

```python
import httpx

# Cliente
client = httpx.Client(base_url="http://localhost:8000")

# Parsear algoritmo
response = client.post("/api/v1/algorithms/parse", json={
    "code": """
    algorithm test(n)
    begin
        for i ← 1 to n do
        begin
            x ← x + 1
        end
    end
    """,
    "validate": True
})

# Ver resultado
print(response.json())
```

## Ejecutar Tests

```bash
# Todos los tests
pytest

# Solo tests unitarios
pytest tests/unit/

# Con coverage
pytest --cov=app --cov-report=html

# Ver coverage en navegador
open htmlcov/index.html  # Linux/Mac
start htmlcov/index.html  # Windows
```

## Endpoints Disponibles

### Health Check
- `GET /api/v1/health/` - Estado del sistema
- `GET /api/v1/health/ready` - Readiness probe
- `GET /api/v1/health/live` - Liveness probe

### Algorithms
- `POST /api/v1/algorithms/parse` - Parsear algoritmo
- `POST /api/v1/algorithms/parse-tree` - Ver parse tree (debug)
- `POST /api/v1/algorithms/validate` - Validar sintaxis
- `GET /api/v1/algorithms/examples` - Algoritmos de ejemplo

### Analysis (Próximamente)
- `POST /api/v1/analysis/analyze` - Analizar complejidad

## Troubleshooting

### Error: "ModuleNotFoundError"

```bash
# Asegúrate de estar en el directorio correcto
cd backend

# Y que el venv esté activado
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate      # Windows
```

### Error: "Port already in use"

```bash
# Cambiar puerto en .env
PORT=8001

# O matar proceso en puerto 8000
# Linux/Mac
lsof -ti:8000 | xargs kill -9

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Error: Logs no se crean

```bash
# Crear directorio de logs manualmente
mkdir -p logs
```

## Próximos Pasos

1. **Explorar la API**: Prueba todos los endpoints en Swagger
2. **Leer la documentación**: Revisa `docs/` para más detalles
3. **Revisar tests**: Mira `tests/unit/test_parser.py` para ejemplos
4. **Implementar MÓDULO 2**: Análisis de complejidad (siguiente fase)

## Recursos

- [Documentación Completa](README.md)
- [Guía de Debugging](docs/DEBUGGING.md)
- [Especificación de Gramática](docs/grammar_specification.md)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Lark Parser](https://lark-parser.readthedocs.io/)

## Tips

- **Swagger es tu mejor amigo**: Úsalo para probar todos los endpoints
- **Hot reload**: Los cambios se aplican automáticamente con `--reload`
- **Logs en tiempo real**: `tail -f logs/app.log`
- **Debug mode**: Activa `DEBUG=true` en `.env` para más información

## Contribuir

¿Encontraste un bug? ¿Tienes una idea? Abre un issue o PR en GitHub.

---

**¿Listo para empezar?**

```bash
python scripts/run_dev.py
```

Luego abre http://localhost:8000/docs y explora la API.