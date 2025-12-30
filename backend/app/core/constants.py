
"""
Constantes del Sistema

Define todas las constantes utilizadas en el sistema para mantener
consistencia y facilitar el mantenimiento.
"""

from enum import Enum
from typing import Final

# Notaciones de Complejidad

class ComplexityNotation(str, Enum):
    """Notaciones de complejidad soportadas"""
    BIG_O = "O"      # Peor caso
    OMEGA = "Ω"      # Mejor caso
    THETA = "Θ"      # Caso promedio

class ComplexityClass(str, Enum):
    """Clases de complejidad comunes"""
    CONSTANT = "O(1)"
    LOGARITHMIC = "O(log n)"
    LINEAR = "O(n)"
    LINEARITHMIC = "O(n log n)"
    QUADRATIC = "O(n²)"
    CUBIC = "O(n³)"
    POLYNOMIAL = "O(n^k)"
    EXPONENTIAL = "O(2^n)"
    FACTORIAL = "O(n!)"

# Patrones Algorítmicos

class AlgorithmPattern(str, Enum):
    """Patrones/técnicas algorítmicas detectables"""
    RECURSION = "recursion"
    DIVIDE_AND_CONQUER = "divide_and_conquer"
    DYNAMIC_PROGRAMMING = "dynamic_programming"
    GREEDY = "greedy"
    BACKTRACKING = "backtracking"
    BRANCH_AND_BOUND = "branch_and_bound"
    SORTING = "sorting"
    SEARCHING = "searching"
    GRAPH_TRAVERSAL = "graph_traversal"
    APPROXIMATION = "approximation"
    BRUTE_FORCE = "brute_force"
    ITERATIVE = "iterative"

# Estructuras de Datos

class DataStructure(str, Enum):
    """Estructuras de datos detectables"""
    ARRAY = "array"
    LINKED_LIST = "linked_list"
    STACK = "stack"
    QUEUE = "queue"
    PRIORITY_QUEUE = "priority_queue"
    HASH_TABLE = "hash_table"
    BINARY_TREE = "binary_tree"
    BST = "binary_search_tree"
    AVL_TREE = "avl_tree"
    RED_BLACK_TREE = "red_black_tree"
    HEAP = "heap"
    GRAPH = "graph"
    TRIE = "trie"
    DISJOINT_SET = "disjoint_set"

# Tipos de Análisis

class AnalysisType(str, Enum):
    """Tipos de análisis disponibles"""
    TEMPORAL = "temporal"        # Complejidad temporal
    SPATIAL = "spatial"          # Complejidad espacial
    AMORTIZED = "amortized"      # Análisis amortizado
    BEST_CASE = "best_case"      # Mejor caso
    WORST_CASE = "worst_case"    # Peor caso
    AVERAGE_CASE = "average_case"  # Caso promedio

# Tipos de Tokens del Parser

class TokenType(str, Enum):
    """Tipos de tokens del lexer"""
    # Palabras clave
    ALGORITHM = "algorithm"
    BEGIN = "begin"
    END = "end"
    FOR = "for"
    TO = "to"
    DO = "do"
    WHILE = "while"
    REPEAT = "repeat"
    UNTIL = "until"
    IF = "if"
    THEN = "then"
    ELSE = "else"
    CALL = "call"
    RETURN = "return"
    
    # Operadores
    ASSIGN = "assign"           # ←
    PLUS = "plus"               # +
    MINUS = "minus"             # -
    MULTIPLY = "multiply"       # *
    DIVIDE = "divide"           # /
    MOD = "mod"
    DIV = "div"
    
    # Comparadores
    LESS_THAN = "less_than"     # <
    GREATER_THAN = "greater_than"  # >
    LESS_EQUAL = "less_equal"   # ≤
    GREATER_EQUAL = "greater_equal"  # ≥
    EQUAL = "equal"             # =
    NOT_EQUAL = "not_equal"     # ≠
    
    # Lógicos
    AND = "and"
    OR = "or"
    NOT = "not"
    
    # Delimitadores
    LPAREN = "lparen"           # (
    RPAREN = "rparen"           # )
    LBRACKET = "lbracket"       # [
    RBRACKET = "rbracket"       # ]
    LBRACE = "lbrace"           # {
    RBRACE = "rbrace"           # }
    COMMA = "comma"             # ,
    DOT = "dot"                 # .
    
    # Literales
    NUMBER = "number"
    IDENTIFIER = "identifier"
    STRING = "string"
    BOOLEAN = "boolean"
    
    # Especiales
    COMMENT = "comment"         # ►
    NEWLINE = "newline"
    EOF = "eof"

# Tipos de Nodos AST

class ASTNodeType(str, Enum):
    """Tipos de nodos del Abstract Syntax Tree"""
    PROGRAM = "program"
    ALGORITHM = "algorithm"
    BLOCK = "block"
    FOR_LOOP = "for_loop"
    WHILE_LOOP = "while_loop"
    REPEAT_LOOP = "repeat_loop"
    IF_STATEMENT = "if_statement"
    ASSIGNMENT = "assignment"
    CALL = "call"
    RETURN = "return"
    BINARY_OP = "binary_op"
    UNARY_OP = "unary_op"
    VARIABLE = "variable"
    LITERAL = "literal"
    ARRAY_ACCESS = "array_access"
    OBJECT_ACCESS = "object_access"

# Formatos de Exportación

class ExportFormat(str, Enum):
    """Formatos de exportación soportados"""
    PDF = "pdf"
    JSON = "json"
    MARKDOWN = "markdown"
    HTML = "html"
    EXCEL = "excel"
    CSV = "csv"
    DOT = "dot"         # Graphviz
    MERMAID = "mermaid"
    SVG = "svg"

# Estados de Análisis

class AnalysisStatus(str, Enum):
    """Estados posibles de un análisis"""
    PENDING = "pending"
    PARSING = "parsing"
    ANALYZING = "analyzing"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

# Niveles de Confianza

class ConfidenceLevel(str, Enum):
    """Niveles de confianza en detección de patrones"""
    VERY_LOW = "very_low"      # < 0.3
    LOW = "low"                # 0.3 - 0.5
    MEDIUM = "medium"          # 0.5 - 0.7
    HIGH = "high"              # 0.7 - 0.9
    VERY_HIGH = "very_high"    # >= 0.9

# Constantes Matemáticas

# Símbolos de complejidad
COMPLEXITY_SYMBOLS: Final[dict] = {
    "O": "Big O",
    "Ω": "Omega",
    "Θ": "Theta",
    "o": "little o",
    "ω": "little omega"
}

# Operaciones básicas y su complejidad
BASIC_OPERATIONS_COMPLEXITY: Final[dict] = {
    "assignment": "O(1)",
    "comparison": "O(1)",
    "arithmetic": "O(1)",
    "logical": "O(1)",
    "array_access": "O(1)",
    "array_append": "O(1)",  # Amortizado
    "array_insert": "O(n)",
    "array_delete": "O(n)",
    "hash_insert": "O(1)",   # Promedio
    "hash_search": "O(1)",   # Promedio
}

# Mensajes de Error

ERROR_MESSAGES: Final[dict] = {
    "PARSE_ERROR": "Error al parsear el algoritmo",
    "SYNTAX_ERROR": "Error de sintaxis en la línea {line}",
    "SEMANTIC_ERROR": "Error semántico: {message}",
    "TIMEOUT_ERROR": "El análisis excedió el tiempo máximo permitido",
    "LLM_ERROR": "Error al comunicarse con el LLM: {message}",
    "DATABASE_ERROR": "Error de base de datos: {message}",
    "VALIDATION_ERROR": "Error de validación: {message}",
    "NOT_FOUND": "Recurso no encontrado",
    "UNAUTHORIZED": "No autorizado",
}

# Límites del Sistema

class SystemLimits:
    """Límites del sistema para prevenir abuse"""
    MAX_ALGORITHM_LENGTH: Final[int] = 10000  # caracteres
    MAX_ALGORITHM_LINES: Final[int] = 1000
    MAX_NESTING_DEPTH: Final[int] = 20
    MAX_RECURSION_CALLS: Final[int] = 1000
    MAX_LOOP_ITERATIONS: Final[int] = 10**9
    MAX_TREE_NODES: Final[int] = 10000
    MAX_EXPORT_SIZE_MB: Final[int] = 50    

# Configuración de Caché

CACHE_KEYS: Final[dict] = {
    "ANALYSIS": "analysis:{algorithm_hash}",
    "PATTERN": "pattern:{algorithm_hash}",
    "LLM_VALIDATION": "llm:{algorithm_hash}:{llm_type}",
    "TREE": "tree:{algorithm_hash}",
}

CACHE_TTL: Final[dict] = {
    "SHORT": 300,      # 5 minutos
    "MEDIUM": 1800,    # 30 minutos
    "LONG": 3600,      # 1 hora
    "VERY_LONG": 86400,  # 1 día
}

# Headers HTTP

HTTP_HEADERS: Final[dict] = {
    "X_REQUEST_ID": "X-Request-ID",
    "X_API_KEY": "X-API-Key",
    "X_RATE_LIMIT": "X-RateLimit-Limit",
    "X_RATE_REMAINING": "X-RateLimit-Remaining",
    "X_RATE_RESET": "X-RateLimit-Reset",
}

# Versiones de API

API_VERSION: Final[str] = "v1"
API_PREFIX: Final[str] = f"/api/{API_VERSION}"