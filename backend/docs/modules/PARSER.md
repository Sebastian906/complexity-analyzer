# Módulo 1: Parser de Pseudocódigo

Documentación completa del módulo de parsing de pseudocódigo a Abstract Syntax Tree (AST).

---

## Tabla de Contenidos

1. [Descripción General](#descripción-general)
2. [Arquitectura](#arquitectura)
3. [Componentes](#componentes)
4. [Gramática Soportada](#gramática-soportada)
5. [Nodos AST](#nodos-ast)
6. [Uso](#uso)
7. [API Reference](#api-reference)
8. [Ejemplos](#ejemplos)
9. [Testing](#testing)

---

## Descripcion General

El modulo de parser es el punto de entrada del sistema de analisis. Convierte codigo pseudocodigo en un Abstract Syntax Tree (AST) estructurado que puede ser analizado por los demas modulos.

### Funcionalidades Principales

| Funcionalidad | Descripcion |
|---------------|-------------|
| **Parsing** | Convierte pseudocodigo en parse tree usando Lark |
| **Construccion AST** | Transforma parse tree en nodos AST tipados |
| **Analisis Semantico** | Valida reglas semanticas del codigo |
| **Validacion** | Verifica restricciones estructurales y limites |

### Sintaxis Soportada

| Elemento | Variantes |
|----------|-----------|
| **Algoritmo** | `algorithm`, `algoritmo`, `proceso`, `funcion` |
| **Bloques** | `begin...end`, `inicio...fin` |
| **Ciclos** | `for...to...do`, `while...do`, `repeat...until` |
| **Condicionales** | `if...then...else` |
| **Asignacion** | `x <- valor` (flecha unicode) |
| **Llamadas** | `call funcion(args)` |
| **Retorno** | `return expresion` |

---

## Arquitectura

```
parser/
├── __init__.py              # Exports principales
├── pseudocode_parser.py     # Parser principal (Lark)
├── ast_builder.py           # Transformer de parse tree a AST
├── ast_nodes.py             # Definicion de nodos AST
├── semantic_analyzer.py     # Analizador semantico
├── validator.py             # Validador de AST
│
└── grammar/
    ├── __init__.py
    └── pseudocode.lark      # Gramatica Lark completa
```

**Archivos principales:**

- [pseudocode_parser.py](../app/core/parser/pseudocode_parser.py) - Parser principal usando Lark
- [ast_builder.py](../app/core/parser/ast_builder.py) - Constructor de AST
- [ast_nodes.py](../app/core/parser/ast_nodes.py) - Definicion de todos los nodos
- [semantic_analyzer.py](../app/core/parser/semantic_analyzer.py) - Analisis semantico
- [validator.py](../app/core/parser/validator.py) - Validacion estructural

**Integración y agentes:**

- Existe un `parser_agent.py` en `app/infrastructure/agents/` que puede ejecutar la fase de parsing como un paso de un pipeline multiagente (ver `app/infrastructure/agents/`). Esto permite reutilizar el parser tanto en flujos sincrónicos como en orquestaciones asistidas por agentes.

---

## Componentes

### 1. PseudocodeParser

Parser principal que utiliza Lark para el analisis lexico y sintactico.

**Archivo:** [pseudocode_parser.py](../app/core/parser/pseudocode_parser.py)

**Caracteristicas:**

- Parser LALR para mejor rendimiento
- Propagacion de posiciones (linea/columna)
- Cache de gramatica compilada
- Manejo detallado de errores

```python
from app.core.parser import PseudocodeParser

parser = PseudocodeParser()
ast = parser.parse(code, validate=True)
print(f"Algoritmo: {ast.algorithm.name}")
```

**Opciones de parsing:**

| Opcion | Tipo | Descripcion |
|--------|------|-------------|
| `validate` | bool | Valida el codigo antes de parsear |
| `timeout` | int | Timeout en segundos |

### 2. ASTBuilder

Transformer que convierte el parse tree de Lark en nodos AST tipados.

**Archivo:** [ast_builder.py](../app/core/parser/ast_builder.py)

**Patron:** Visitor/Transformer

**Proceso:**
1. Recibe parse tree de Lark
2. Recorre cada nodo del arbol
3. Crea nodos AST correspondientes
4. Construye arbol AST final

```python
from app.core.parser import ASTBuilder, build_ast_from_tree

# Uso directo
builder = ASTBuilder()
ast = builder.transform(parse_tree)

# Helper function
ast = build_ast_from_tree(parse_tree)
```

**Reglas transformadas:**

| Regla Lark | Nodo AST |
|------------|----------|
| `program` | `ProgramNode` |
| `algorithm` | `AlgorithmNode` |
| `block` | `BlockNode` |
| `for_loop` | `ForLoopNode` |
| `while_loop` | `WhileLoopNode` |
| `if_statement` | `IfStatementNode` |
| `assignment` | `AssignmentNode` |
| `call_statement` | `CallStatementNode` |

### 3. SemanticAnalyzer

Analizador que valida reglas semanticas sobre el AST.

**Archivo:** [semantic_analyzer.py](../app/core/parser/semantic_analyzer.py)

**Validaciones:**

| Validacion | Descripcion |
|------------|-------------|
| Variables no declaradas | Detecta uso antes de declaracion |
| Tipos incompatibles | Verifica consistencia de tipos |
| Indices de arrays | Valida accesos a arrays |
| Llamadas a funciones | Verifica existencia de funciones |

```python
from app.core.parser import SemanticAnalyzer

analyzer = SemanticAnalyzer()
is_valid = analyzer.analyze(ast)

# Acceder a tabla de simbolos
for name, info in analyzer.symbol_table.items():
    print(f"{name}: array={info.is_array}, param={info.is_parameter}")
```

**Estructuras de datos internas:**

```python
@dataclass
class VariableInfo:
    name: str
    is_array: bool = False
    is_parameter: bool = False
    dimensions: List[Optional[int]] = field(default_factory=list)
    first_use_line: Optional[int] = None

@dataclass
class FunctionInfo:
    name: str
    parameters: List[ParameterNode] = field(default_factory=list)
    is_recursive: bool = False
```

### 4. ASTValidator

Validador de restricciones estructurales del AST.

**Archivo:** [validator.py](../app/core/parser/validator.py)

**Restricciones validadas:**

| Restriccion | Limite por defecto |
|-------------|-------------------|
| Profundidad de anidacion | 20 niveles |
| Numero de nodos | 10,000 nodos |
| Tamano del codigo | Configurable en settings |

```python
from app.core.parser import ASTValidator, ValidationResult

validator = ASTValidator(max_depth=20, max_nodes=10000)
result = validator.validate(ast)

if result.is_valid:
    print("AST valido")
else:
    for error in result.errors:
        print(f"Error: {error}")
```

---

## Gramatica Soportada

### Estructura del Programa

```
program := class_definition* algorithm
algorithm := ALGORITHM_KW IDENTIFIER "(" parameter_list? ")" block
block := BEGIN statement_list END
```

### Definicion de Clases

Permite definir estructuras de datos personalizadas:

```
class_definition := CLASS_NAME "{" attribute_list "}"
```

Ejemplo:
```
Node { data, next }
```

### Parametros

**Parametro simple:**
```
algorithm test(n)
```

**Parametro array:**
```
algorithm sort(A[n])
algorithm matrix(M[n][m])
```

**Parametro objeto:**
```
algorithm traverse(Node head)
```

### Estructuras de Control

**For Loop:**
```
for i <- 1 to n do
    // cuerpo
end
```

**While Loop:**
```
while (condicion) do
    // cuerpo
end
```

**Repeat Loop:**
```
repeat
    // cuerpo
until (condicion)
```

**If Statement:**
```
if (condicion) then
    // cuerpo
else
    // alternativa
end
```

### Expresiones

**Operadores aritmeticos:**
- `+`, `-`, `*`, `/`, `^` (potencia)
- `mod`, `div`

**Operadores de comparacion:**
- `<`, `>`, `<=`, `>=`, `=`, `!=`
- Variantes unicode: `<=`, `>=`, `!=`

**Operadores logicos:**
- `and`, `or`, `not`

**Funciones especiales:**
- `ceil(x)` - Techo
- `floor(x)` - Piso
- `length(A)` - Longitud de array

---

## Nodos AST

### Jerarquia de Nodos

```
ASTNode (abstracto)
├── ProgramNode
├── ClassDefinitionNode
├── AlgorithmNode
├── ParameterNode
├── BlockNode
│
├── Statements
│   ├── AssignmentNode
│   ├── ForLoopNode
│   ├── WhileLoopNode
│   ├── RepeatLoopNode
│   ├── IfStatementNode
│   ├── CallStatementNode
│   └── ReturnStatementNode
│
└── Expressions
    ├── BinaryOpNode
    ├── UnaryOpNode
    ├── LiteralNode
    ├── VariableNode
    ├── ArrayAccessNode
    ├── ObjectAccessNode
    └── FunctionCallNode
```

### Nodos Principales

**ProgramNode:**
```python
@dataclass
class ProgramNode(ASTNode):
    classes: List[ClassDefinitionNode]
    algorithm: Optional[AlgorithmNode]
```

**AlgorithmNode:**
```python
@dataclass
class AlgorithmNode(ASTNode):
    name: str
    parameters: List[ParameterNode]
    body: Optional[BlockNode]
```

**ForLoopNode:**
```python
@dataclass
class ForLoopNode(ASTNode):
    variable: str
    start: ASTNode  # Expresion inicio
    end: ASTNode    # Expresion fin
    body: BlockNode
```

### Serializacion

Todos los nodos implementan `to_dict()` para serializacion:

```python
ast_dict = ast.to_dict()
import json
print(json.dumps(ast_dict, indent=2))
```

---

## Uso

### Uso Basico - Python

```python
from app.core.parser import parse_pseudocode

code = """
algorithm factorial(n)
begin
    if (n <= 1) then
        return 1
    end
    return n * factorial(n - 1)
end
"""

ast = parse_pseudocode(code)
print(f"Nombre: {ast.algorithm.name}")
print(f"Parametros: {len(ast.algorithm.parameters)}")
```

### Parsing con Validacion Completa

```python
from app.core.parser import (
    PseudocodeParser,
    SemanticAnalyzer,
    ASTValidator
)

# 1. Parsear
parser = PseudocodeParser()
ast = parser.parse(code)

# 2. Validar estructura
validator = ASTValidator()
result = validator.validate(ast)
if not result.is_valid:
    raise Exception(result.errors)

# 3. Analisis semantico
analyzer = SemanticAnalyzer()
analyzer.analyze(ast)

print("Codigo parseado y validado correctamente")
```

### Acceso a Informacion del AST

```python
# Recorrer statements
for stmt in ast.algorithm.body.statements:
    print(f"Tipo: {stmt.node_type}")
    print(f"Linea: {stmt.line}")
```

### Manejo de Errores

```python
from app.core.exceptions import (
    SyntaxErrorException,
    TokenizationException,
    SemanticErrorException
)

try:
    ast = parse_pseudocode(code)
except SyntaxErrorException as e:
    print(f"Error de sintaxis en linea {e.line}: {e.message}")
except TokenizationException as e:
    print(f"Caracter invalido: {e.message}")
except SemanticErrorException as e:
    print(f"Error semantico: {e.message}")
```

---

## API Reference

### Funciones Helper

```python
def parse_pseudocode(code: str) -> ProgramNode:
    """
    Parsea codigo pseudocodigo rapidamente.
    
    Args:
        code: Codigo pseudocodigo
        
    Returns:
        ProgramNode: Raiz del AST
    """
```

### Clases Principales

**PseudocodeParser:**
```python
class PseudocodeParser:
    def parse(
        self,
        code: str,
        validate: bool = True,
        timeout: Optional[int] = None
    ) -> ProgramNode:
        """Parsea codigo y retorna AST"""
```

**SemanticAnalyzer:**
```python
class SemanticAnalyzer:
    symbol_table: Dict[str, VariableInfo]
    functions: Dict[str, FunctionInfo]
    errors: List[str]
    warnings: List[str]
    
    def analyze(self, ast: ProgramNode) -> bool:
        """Analiza semanticamente el AST"""
```

**ASTValidator:**
```python
class ASTValidator:
    def validate(self, ast: ProgramNode) -> ValidationResult:
        """Valida restricciones del AST"""
```

---

## Ejemplos

### Algoritmo de Ordenamiento

```
algorithm bubbleSort(A[n])
begin
    for i <- 1 to n-1 do
        for j <- 1 to n-i do
            if (A[j] > A[j+1]) then
                temp <- A[j]
                A[j] <- A[j+1]
                A[j+1] <- temp
            end
        end
    end
end
```

### Algoritmo Recursivo

```
algorithm fibonacci(n)
begin
    if (n <= 1) then
        return n
    end
    return fibonacci(n-1) + fibonacci(n-2)
end
```

### Uso de Objetos

```
Node { data, next }

algorithm traverse(Node head)
begin
    current <- head
    while (current != null) do
        call print(current.data)
        current <- current.next
    end
end
```

### Busqueda Binaria

```
algorithm binarySearch(A[n], target)
begin
    low <- 1
    high <- n
    
    while (low <= high) do
        mid <- floor((low + high) / 2)
        
        if (A[mid] = target) then
            return mid
        end
        
        if (A[mid] < target) then
            low <- mid + 1
        else
            high <- mid - 1
        end
    end
    
    return -1
end
```

---

## Testing

### Ejecutar Tests

```bash
# Tests del modulo parser
pytest tests/unit/test_parser.py -v

# Tests de AST
pytest tests/unit/test_ast_nodes.py -v

# Tests de validacion
pytest tests/unit/test_validator.py -v

# Cobertura
pytest tests/unit/test_parser.py --cov=app/core/parser
```

### Tests Unitarios Incluidos

| Test | Descripcion |
|------|-------------|
| `test_simple_algorithm` | Parsing de algoritmo basico |
| `test_array_parameters` | Parametros tipo array |
| `test_nested_loops` | Loops anidados |
| `test_conditionals` | Estructuras condicionales |
| `test_recursive_calls` | Llamadas recursivas |
| `test_semantic_validation` | Validacion semantica |
| `test_error_handling` | Manejo de errores |

---

## Integracion con Otros Modulos

El parser es el punto de entrada para todo el sistema:

```
Codigo Pseudocodigo
        │
        ▼
   ┌─────────────────┐
   │     Parser      │  Modulo 1
   │  (Este modulo)  │
   └────────┬────────┘
            │ AST
            ▼
   ┌─────────────────┐
   │    Analyzer     │  Modulo 2
   │  (Complejidad)  │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │    Patterns     │  Modulo 3
   │  (Deteccion)    │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ Data Structures │  Modulo 3.5
   │  (Estructuras)  │
   └─────────────────┘
```

**Dependencias:**

- El modulo de analisis ([ANALYZER.md](ANALYZER.md)) consume el AST generado
- El modulo de patrones ([PATTERNS.md](PATTERNS.md)) utiliza el AST para deteccion
- El modulo de estructuras de datos ([DATA_STRUCTURES.md](DATA_STRUCTURES.md)) analiza el AST
