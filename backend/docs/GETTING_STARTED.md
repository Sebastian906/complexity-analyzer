# Getting Started - Complexity Analyzer

Guía completa para configurar, ejecutar y desarrollar el proyecto.

## Tabla de Contenidos

- [Instalación](#instalación)
- [Configuración](#configuración)
- [Ejecutar el Servidor](#ejecutar-el-servidor)
- [Probar la API](#probar-la-api)
- [Desarrollo](#desarrollo)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

---

## Instalación

### Requisitos

- **Python 3.11+** (Recomendado: 3.11 o 3.12)
- **pip** (gestor de paquetes)
- **Git**
- (Opcional) **MongoDB** para persistencia
- (Opcional) **Redis** para caché

### Paso 1: Clonar Repositorio

```bash
git clone https://github.com/Sebastian906/complexity-analyzer.git
cd complexity-analyzer/backend
```

### Paso 2: Crear Entorno Virtual

```bash
# Crear venv
python -m venv venv

# Activar venv
# En Linux/Mac:
source venv/bin/activate

# En Windows:
venv\Scripts\activate

# Verificar que estás en el venv
which python  # Linux/Mac
where python  # Windows
# Debe apuntar a ./venv/bin/python
```

### Paso 3: Actualizar pip

```bash
python -m pip install --upgrade pip setuptools wheel
```

### Paso 4: Instalar Dependencias

```bash
# Dependencias principales
pip install -r requirements.txt

# Si vas a desarrollar, instala también:
pip install -r requirements-dev.txt
```

**Nota sobre Python 3.14:** Algunas dependencias opcionales están comentadas en `requirements-dev.txt` porque aún no tienen soporte para Python 3.14. El proyecto funciona perfectamente con Python 3.11-3.12.

---

## Configuración

### Paso 1: Copiar .env

```bash
cp .env.example .env
```

### Paso 2: Editar .env

Abre `.env` y configura:

#### Configuración Mínima (para empezar)

```bash
# Application
APP_ENV=development
DEBUG=true
LOG_LEVEL=DEBUG

# Server
HOST=0.0.0.0
PORT=8000
RELOAD=true
```

#### Configuración Completa (opcional)

```bash
# LLMs (si quieres usar validación con IA)
ANTHROPIC_API_KEY=sk-ant-tu-key-aqui
GOOGLE_API_KEY=AIzaSy-tu-key-aqui

# MongoDB (si quieres persistencia)
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=complexity_analyzer

# Redis (si quieres caché)
REDIS_HOST=localhost
REDIS_PORT=6379
```

### Paso 3: Crear Directorios

```bash
mkdir -p logs data/algorithms data/exports data/cache
```

---

## Ejecutar el Servidor

### Método 1: Script de Desarrollo (Recomendado)

```bash
python scripts/run_dev.py
```

### Método 2: Uvicorn Directo

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Método 3: Python Module

```bash
python -m app.main
```

### Salida Esperada

```
INFO:     Will watch for changes in these directories: ['/path/to/backend']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

---

## Probar la API

### 1. Verificar que el Servidor Está Corriendo

```bash
curl http://localhost:8000/api/v1/health/
```

**Respuesta esperada:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "development",
  "services": {
    "api": "healthy",
    "parser": "healthy"
  }
}
```

### 2. Abrir Swagger UI

Abre en tu navegador:

**http://localhost:8000/docs**

Aquí verás la documentación interactiva con todos los endpoints.

### 3. Probar el Parser

#### Método A: Swagger UI

1. En Swagger, expande `/api/v1/algorithms/parse`
2. Click en **"Try it out"**
3. Pega este código en el campo `code`:

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

4. Click **"Execute"**
5. Verás el AST en la respuesta

#### Método B: cURL

```bash
curl -X POST http://localhost:8000/api/v1/algorithms/parse \
  -H "Content-Type: application/json" \
  -d '{
    "code": "algorithm test(n)\nbegin\n  for i ← 1 to n do\n  begin\n    x ← x + 1\n  end\nend",
    "validate": true
  }'
```

#### Método C: Script Python

```bash
# Si instalaste requirements-dev.txt
python scripts/test_api.py
```

### 4. Obtener Ejemplos

```bash
curl http://localhost:8000/api/v1/algorithms/examples
```

---

## Desarrollo

### Estructura del Proyecto

```
backend/
├── app/                    # Código fuente
│   ├── api/               # Endpoints FastAPI
│   ├── core/              # Lógica de dominio
│   ├── services/          # Servicios
│   ├── infrastructure/    # Adaptadores externos
│   └── utils/             # Utilidades
├── tests/                 # Tests
├── docs/                  # Documentación
├── config/                # Configuraciones YAML
└── scripts/               # Scripts de utilidad
```

### Workflow de Desarrollo

1. **Crear rama para feature:**
   ```bash
   git checkout -b feature/nombre-feature
   ```

2. **Hacer cambios**

3. **Ejecutar tests:**
   ```bash
   pytest tests/unit/test_parser.py -v
   ```

4. **Verificar code style:**
   ```bash
   black app/
   flake8 app/
   mypy app/
   ```

5. **Commit y push:**
   ```bash
   git add .
   git commit -m "feat: descripción del cambio"
   git push origin feature/nombre-feature
   ```

### Hot Reload

Con `--reload`, los cambios en el código se aplican automáticamente:

1. Modifica un archivo en `app/`
2. Guarda
3. El servidor se recarga automáticamente
4. Refresca Swagger o vuelve a hacer el request

### Ver Logs en Tiempo Real

```bash
# En otra terminal
tail -f logs/app.log
```

---

## Testing

### Ejecutar Todos los Tests

```bash
pytest
```

### Tests Específicos

```bash
# Solo tests unitarios
pytest tests/unit/ -v

# Solo tests de integración
pytest tests/integration/ -v

# Test específico
pytest tests/unit/test_parser.py::TestParserBasic::test_simple_algorithm -v

# Con markers
pytest -m unit
pytest -m integration
```

### Coverage

```bash
# Generar reporte
pytest --cov=app --cov-report=html

# Ver en navegador
open htmlcov/index.html  # Mac/Linux
start htmlcov\index.html  # Windows
```

### Tests Continuos (Watch Mode)

```bash
# Requiere pytest-watch
pip install pytest-watch

# Ejecutar
ptw tests/
```

---

## Troubleshooting

### Error: "No module named 'app'"

**Causa:** No estás en el directorio correcto o el venv no está activado.

**Solución:**
```bash
cd backend
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate      # Windows
```

### Error: "Address already in use"

**Causa:** El puerto 8000 ya está en uso.

**Solución:**
```bash
# Opción 1: Cambiar puerto en .env
PORT=8001

# Opción 2: Matar proceso
# Linux/Mac
lsof -ti:8000 | xargs kill -9

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Error: "ModuleNotFoundError: lark"

**Causa:** Dependencias no instaladas.

**Solución:**
```bash
pip install -r requirements.txt
```

### Error: Logs no se crean

**Causa:** Directorio de logs no existe.

**Solución:**
```bash
mkdir -p logs
```

### Parser Falla al Parsear

**Debug:**
1. Usa el endpoint `/parse-tree` para ver el parse tree
2. Revisa los logs en `logs/app.log`
3. Verifica la sintaxis del pseudocódigo
4. Revisa los tests en `tests/unit/test_parser.py` para ejemplos

### Tests Fallan

**Debug:**
```bash
# Ejecutar con más verbosidad
pytest -vv

# Ver output completo
pytest -s

# Ver solo el test que falla
pytest tests/unit/test_parser.py::test_name -vv
```

---

## Documentación Adicional

- [Quick Start](QUICKSTART.md) - Guía rápida de 5 minutos
- [README](README.md) - Documentación completa del proyecto
- [DEBUGGING](docs/DEBUGGING.md) - Guía profesional de debugging
- [Grammar Specification](docs/grammar_specification.md) - Especificación de la gramática

---

## Próximos Pasos

1. Parser implementado
2. API funcionando
3. Tests del parser
4. **SIGUIENTE: Implementar MÓDULO 2 (Análisis de Complejidad)**

Para implementar el MÓDULO 2, revisa [MODULE_2_GUIDE.md](docs/MODULE_2_GUIDE.md).

---

## Contribuir

1. Fork el proyecto
2. Crea tu feature branch
3. Commit tus cambios
4. Push a la branch
5. Abre un Pull Request

---

## Soporte

- **Issues:** https://github.com/Sebastian906/complexity-analyzer/issues
- **Email:** elsebas1912@gmail.com
- **LinkedIn:** [Sebastián Salazar Güiza](https://www.linkedin.com/in/sebasti%C3%A1n-salazar-g%C3%BCiza-756b40210/)

---