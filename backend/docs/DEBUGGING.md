# Guía de Debugging Profesional

Esta guía establece el proceso sistemático para identificar y resolver bugs en el proyecto.

## Principios Fundamentales

1. **Nunca adivinar** - Siempre investigar sistemáticamente
2. **Reproducir primero** - No se puede arreglar lo que no se puede reproducir
3. **Entender la causa raíz** - Arreglar el problema, no los síntomas
4. **Agregar tests** - Prevenir regresiones futuras
5. **Documentar el proceso** - Ayudar al equipo a aprender

---

## Proceso de Debugging (7 Pasos)

### 1. Usar un Debugger para Ahorrar Tiempo

**Herramientas:**
- Python Debugger (pdb): `python -m pdb script.py`
- IPython Debugger (ipdb): `ipdb.set_trace()`
- VSCode Debugger: Breakpoints visuales
- PyCharm Debugger: Debugging avanzado

**Comandos pdb básicos:**
```python
import pdb; pdb.set_trace()  # Breakpoint manual

# Comandos dentro del debugger:
# n (next)       - Ejecutar siguiente línea
# s (step)       - Entrar en función
# c (continue)   - Continuar hasta siguiente breakpoint
# l (list)       - Mostrar código alrededor
# p variable     - Imprimir valor de variable
# pp variable    - Pretty print
# w (where)      - Stack trace
# u (up)         - Subir en stack
# d (down)       - Bajar en stack
# q (quit)       - Salir del debugger
```

**Ejemplo de uso en tests:**
```python
def test_parser_bug():
    parser = PseudocodeParser()
    code = "algorithm test(n)\nbegin\n  x ← 1\nend"
    
    import ipdb; ipdb.set_trace()  # Breakpoint aquí
    ast = parser.parse(code)
    
    assert ast.algorithm.name == "test"
```

**Configuración VSCode** (`.vscode/launch.json`):
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Debug Tests",
            "type": "python",
            "request": "launch",
            "module": "pytest",
            "args": [
                "tests/unit/test_parser.py::test_for_loop",
                "-v",
                "-s"
            ],
            "console": "integratedTerminal",
            "justMyCode": false
        }
    ]
}
```

---

### 2. Usar Git Bisect para Hallar el Bug Rápido

Git bisect realiza búsqueda binaria en el historial de commits para encontrar cuándo se introdujo el bug.

**Proceso:**
```bash
# 1. Iniciar bisect
git bisect start

# 2. Marcar commit actual como malo
git bisect bad

# 3. Marcar último commit bueno conocido
git bisect good abc123

# 4. Git checkoutea commit medio - probar si funciona
pytest tests/unit/test_parser.py

# 5. Marcar como bueno o malo
git bisect good   # si funciona
git bisect bad    # si falla

# 6. Repetir hasta encontrar el commit culpable

# 7. Terminar bisect
git bisect reset
```

**Automatizar con script:**
```bash
# Crear script test-parser.sh
#!/bin/bash
pytest tests/unit/test_parser.py::test_for_loop
exit $?

# Hacer ejecutable
chmod +x test-parser.sh

# Ejecutar bisect automático
git bisect start
git bisect bad
git bisect good abc123
git bisect run ./test-parser.sh
```

**Ejemplo de output:**
```
Bisecting: 6 revisions left to test after this (roughly 3 steps)
[commit_hash] Commit message
running ./test-parser.sh
...
abc123 is the first bad commit
```

---

### 3. Preguntarle a un Rubber Duck sobre el Bug

El "rubber duck debugging" es explicar el problema en voz alta (a un pato de goma, colega, o a ti mismo).

**Template de conversación:**
```markdown
# Rubber Duck Debugging Session

## El Bug
Descripción: El parser falla al parsear ciclos FOR anidados
Error: SyntaxErrorException en línea 5

## Lo que Espero
El parser debería reconocer:
```
for i ← 1 to n do
    for j ← 1 to n do
        ...
```

## Lo que Sucede
El parser lanza SyntaxErrorException al encontrar el segundo FOR

## Mi Código Hace
1. Tokeniza el código
2. Construye parse tree con Lark
3. Transforma parse tree a AST

## Hipótesis
1. ¿La gramática no permite FOR anidados?
2. ¿El ASTBuilder no maneja bloques correctamente?
3. ¿Hay un problema con indentación?

## Pasos para Verificar
[ ] Revisar gramática Lark
[ ] Probar parse tree directamente
[ ] Verificar otros ciclos anidados
[ ] Comparar con algoritmo que funciona
```

**Escribir en docs/debugging-sessions/YYYYMMDD-issue-name.md**

---

### 4. Chequear los Logs para Hallar el Bug

Los logs son tu mejor amigo. El sistema usa Loguru para logging estructurado.

**Niveles de log:**
- DEBUG: Información detallada para debugging
- INFO: Confirmación de operaciones normales
- WARNING: Algo inesperado pero no crítico
- ERROR: Error que impide una operación
- CRITICAL: Error que puede causar fallo del sistema

**Ver logs:**
```bash
# Ver todos los logs
cat logs/app.log

# Ver solo errores
cat logs/errors.log

# Seguir logs en tiempo real
tail -f logs/app.log

# Buscar patrón específico
grep "ParserException" logs/app.log

# Ver logs con contexto (3 líneas antes y después)
grep -C 3 "error" logs/app.log
```

**Agregar logging temporal:**
```python
from app.utils.logger import setup_logger
logger = setup_logger(__name__)

def parse_for_loop(items):
    logger.debug(f"Parsing FOR loop with items: {items}")
    logger.debug(f"Item types: {[type(i).__name__ for i in items]}")
    
    variable = str(items[0])
    logger.debug(f"Variable: {variable}")
    
    start = items[1]
    logger.debug(f"Start expression: {start}")
    
    # ... resto del código
```

**Ejemplo de log estructurado:**
```python
logger.bind(
    operation="parse_for_loop",
    variable="i",
    line_number=5
).debug("Processing FOR loop")
```

---

### 5. Reproducir la Falla para Asegurar que el Bug sea Arreglado

**Crear test de reproducción:**
```python
# tests/unit/test_parser_regression.py

def test_regression_nested_for_loops_issue_42():
    """
    Regression test para Issue #42
    
    Bug: El parser fallaba al parsear ciclos FOR anidados
    Causa: ASTBuilder no procesaba correctamente bloques dentro de loops
    Fix: Commit abc123
    """
    parser = PseudocodeParser()
    
    # Este código causaba SyntaxErrorException antes del fix
    code = """
    algorithm test(n)
    begin
        for i ← 1 to n do
        begin
            for j ← 1 to n do
            begin
                x ← x + 1
            end
        end
    end
    """
    
    # Ahora debe funcionar
    ast = parser.parse(code)
    
    assert ast is not None
    outer_loop = ast.algorithm.body.statements[0]
    assert isinstance(outer_loop, ForLoopNode)
    
    inner_loop = outer_loop.body.statements[0]
    assert isinstance(inner_loop, ForLoopNode)
```

**Verificar en múltiples escenarios:**
```python
@pytest.mark.parametrize("nesting_level", [2, 3, 4])
def test_nested_loops_various_depths(nesting_level):
    """Verificar que funciona con diferentes niveles de anidación"""
    parser = PseudocodeParser()
    
    # Generar código con anidación dinámica
    code = generate_nested_loops(nesting_level)
    
    ast = parser.parse(code)
    assert ast is not None
```

---

### 6. Entender la Raíz que Causa el Bug Antes de Arreglarlo

No arregles síntomas, arregla causas.

**Template de análisis:**
```markdown
# Root Cause Analysis (RCA)

## Síntoma
Parser falla con SyntaxErrorException en ciclos FOR anidados

## Investigación

### Hipótesis 1: Gramática incorrecta
- Verificado: La gramática Lark permite bloques dentro de for_loop
- Resultado: ✓ Gramática correcta

### Hipótesis 2: ASTBuilder no procesa bloques
- Código relevante:
```python
  def for_loop(self, items):
      # items[3] debería ser BlockNode pero es List
      body = items[3]
```
- Verificado: items[3] es lista, no BlockNode
- Resultado: ✗ Bug encontrado

### Hipótesis 3: Transformer no llama block()
- Lark llama block() correctamente
- Pero for_loop() recibe resultado incorrecto
- Resultado: ✓ Confirmado

## Causa Raíz
El método `block()` retorna lista en lugar de BlockNode cuando está vacío.

## Solución
```python
def block(self, items):
    statements = items[0] if items else []
    return BlockNode(statements=statements)  # Siempre retornar BlockNode
```

## Tests Agregados
- test_nested_for_loops
- test_empty_block_in_loop
- test_multiple_statements_in_loop

## Prevención
- Agregar type hints en ASTBuilder
- Agregar assertions en métodos críticos
- Mejorar coverage de tests
```

---

### 7. Sistemáticamente Arreglar el Bug

**Proceso paso a paso:**

#### Paso 7.1: Crear rama de bug fix
```bash
git checkout develop
git pull origin develop
git checkout -b bugfix/nested-loops-parser-error
```

#### Paso 7.2: Escribir test que falla
```python
# tests/unit/test_parser.py

def test_nested_for_loops():
    """Test para verificar el bug antes del fix"""
    parser = PseudocodeParser()
    code = """
    algorithm test(n)
    begin
        for i ← 1 to n do
        begin
            for j ← 1 to n do
            begin
                x ← x + 1
            end
        end
    end
    """
    
    # Este test debe FALLAR antes del fix
    ast = parser.parse(code)
    assert ast is not None
```

Ejecutar: `pytest tests/unit/test_parser.py::test_nested_for_loops -v`

Resultado esperado: **FAIL**

#### Paso 7.3: Implementar el fix
```python
# app/core/parser/ast_builder.py

def block(self, items: List[Any]) -> BlockNode:
    """
    Regla block: BEGIN statement_list END
    
    IMPORTANTE: Siempre retorna BlockNode, nunca lista
    """
    statements = items[0] if items else []
    
    # FIX: Siempre retornar BlockNode
    return BlockNode(statements=statements)
```

#### Paso 7.4: Verificar que el test pasa
```bash
pytest tests/unit/test_parser.py::test_nested_for_loops -v
```

Resultado esperado: **PASS**

#### Paso 7.5: Ejecutar toda la suite
```bash
pytest tests/unit/test_parser.py -v
pytest tests/ -v  # Todos los tests
```

Asegurar que no rompimos nada más.

#### Paso 7.6: Commit con mensaje descriptivo
```bash
git add app/core/parser/ast_builder.py
git add tests/unit/test_parser.py
git commit -m "fix(parser): Fix nested loop parsing in ASTBuilder

- Fixed block() method to always return BlockNode instead of list
- Added regression test for nested FOR loops
- Root cause: for_loop() expected BlockNode but received list

Fixes #42"
```

#### Paso 7.7: Push y crear Pull Request
```bash
git push origin bugfix/nested-loops-parser-error
```

Crear PR en GitHub con:
- Descripción del bug
- Root cause analysis
- Solución implementada
- Tests agregados
- Screenshots/logs si aplica

---

## Herramientas Adicionales

### Profiling
```bash
# Time profiling
python -m cProfile -o profile.stats app/core/parser/pseudocode_parser.py

# Ver resultados
python -m pstats profile.stats
> sort cumtime
> stats 20

# Memory profiling
python -m memory_profiler script.py
```

### Coverage
```bash
# Generar reporte de coverage
pytest --cov=app/core/parser --cov-report=html

# Ver en navegador
open htmlcov/index.html
```

### Linting
```bash
# Verificar código
flake8 app/core/parser/
mypy app/core/parser/
black --check app/core/parser/

# Autofix
black app/core/parser/
isort app/core/parser/
```

---

## Checklist de Debugging

- [ ] Reproduje el bug localmente
- [ ] Usé debugger para inspeccionar estado
- [ ] Revisé logs relevantes
- [ ] Identifiqué la causa raíz (no solo síntomas)
- [ ] Escribí test que reproduce el bug
- [ ] Implementé el fix mínimo necesario
- [ ] Verifiqué que el test pasa
- [ ] Ejecuté suite completa de tests
- [ ] Agregué regression test
- [ ] Documenté el RCA
- [ ] Hice commit descriptivo
- [ ] Actualicé documentación si necesario

---

## Recursos

- [Python Debugger Docs](https://docs.python.org/3/library/pdb.html)
- [Git Bisect Tutorial](https://git-scm.com/docs/git-bisect)
- [Rubber Duck Debugging](https://en.wikipedia.org/wiki/Rubber_duck_debugging)
- [Root Cause Analysis](https://en.wikipedia.org/wiki/Root_cause_analysis)