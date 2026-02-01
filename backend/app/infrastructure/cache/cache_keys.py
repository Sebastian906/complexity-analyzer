"""
Cache Keys - Definiciones Centralizadas

Define todas las claves de caché del sistema de manera centralizada.
Proporciona funciones helper para construir claves consistentes.
"""

from typing import Optional
from hashlib import sha256

from app.core.config import settings

# PREFIJOS DE CLAVES
class CachePrefix:
    """Prefijos para diferentes tipos de caché"""
    
    # Análisis
    ANALYSIS = "analysis"
    ANALYSIS_RESULT = "analysis_result"
    COMPLEXITY = "complexity"
    RECURRENCE = "recurrence"
    
    # Patrones
    PATTERN = "pattern"
    PATTERN_DETECTION = "pattern_detection"
    PATTERN_SCORE = "pattern_score"
    
    # Estructuras de datos
    STRUCTURE = "structure"
    STRUCTURE_DETECTION = "structure_detection"
    
    # LLM
    LLM = "llm"
    LLM_CLAUDE = "llm_claude"
    LLM_GEMINI = "llm_gemini"
    LLM_VALIDATION = "llm_validation"
    
    # Visualización
    TREE = "tree"
    GRAPH = "graph"
    DIAGRAM = "diagram"
    
    # Algoritmos
    ALGORITHM = "algorithm"
    ALGORITHM_LIST = "algorithm_list"
    ALGORITHM_SEARCH = "algorithm_search"
    
    # Usuarios
    USER = "user"
    USER_SESSION = "user_session"
    USER_PERMISSIONS = "user_permissions"
    
    # Métricas
    METRICS = "metrics"
    STATS = "stats"
    
    # Generales
    TEMP = "temp"
    LOCK = "lock"

# TTL DEFAULTS
class CacheTTL:
    """Valores por defecto de TTL (Time To Live) en segundos"""
    
    # Corto (5 minutos)
    SHORT = 300
    
    # Medio (30 minutos)
    MEDIUM = 1800
    
    # Largo (1 hora)
    LONG = 3600
    
    # Muy largo (1 día)
    VERY_LONG = 86400
    
    # Específicos por tipo
    ANALYSIS = settings.CACHE_TTL_ANALYSIS  # 1 hora
    PATTERN = settings.CACHE_TTL_PATTERN    # 2 horas
    LLM = settings.CACHE_TTL_LLM            # 30 minutos
    USER_SESSION = 7200                     # 2 horas
    METRICS = 300                           # 5 minutos
    VISUALIZATION = 3600                    # 1 hora

# KEY BUILDERS - ANÁLISIS
def build_analysis_key(algorithm_id: str) -> str:
    """
    Construir clave para resultado de análisis completo.
    
    Args:
        algorithm_id: ID del algoritmo
    
    Returns:
        str: Clave de caché
    
    Example:
        >>> key = build_analysis_key("123")
        >>> print(key)  # "analysis:123"
    """
    return f"{CachePrefix.ANALYSIS}:{algorithm_id}"

def build_complexity_key(algorithm_id: str, complexity_type: str) -> str:
    """
    Construir clave para complejidad específica.
    
    Args:
        algorithm_id: ID del algoritmo
        complexity_type: Tipo (big_o, omega, theta)
    
    Returns:
        str: Clave de caché
    """
    return f"{CachePrefix.COMPLEXITY}:{algorithm_id}:{complexity_type}"

def build_recurrence_key(algorithm_id: str) -> str:
    """
    Construir clave para ecuaciones de recurrencia.
    
    Args:
        algorithm_id: ID del algoritmo
    
    Returns:
        str: Clave de caché
    """
    return f"{CachePrefix.RECURRENCE}:{algorithm_id}"

# KEY BUILDERS - PATRONES
def build_pattern_key(algorithm_id: str) -> str:
    """
    Construir clave para detección de patrones.
    
    Args:
        algorithm_id: ID del algoritmo
    
    Returns:
        str: Clave de caché
    """
    return f"{CachePrefix.PATTERN}:{algorithm_id}"

def build_pattern_score_key(algorithm_id: str, pattern_type: str) -> str:
    """
    Construir clave para score de un patrón específico.
    
    Args:
        algorithm_id: ID del algoritmo
        pattern_type: Tipo de patrón
    
    Returns:
        str: Clave de caché
    """
    return f"{CachePrefix.PATTERN_SCORE}:{algorithm_id}:{pattern_type}"

# KEY BUILDERS - ESTRUCTURAS
def build_structure_key(algorithm_id: str) -> str:
    """
    Construir clave para detección de estructuras.
    
    Args:
        algorithm_id: ID del algoritmo
    
    Returns:
        str: Clave de caché
    """
    return f"{CachePrefix.STRUCTURE}:{algorithm_id}"

# KEY BUILDERS - LLM
def build_llm_key(
    prompt: str,
    llm_type: str,
    model: Optional[str] = None
) -> str:
    """
    Construir clave para respuesta de LLM.
    
    Args:
        prompt: Prompt enviado al LLM
        llm_type: Tipo de LLM (claude, gemini)
        model: Modelo específico (opcional)
    
    Returns:
        str: Clave de caché
    """
    # Hash del prompt para clave más corta
    prompt_hash = sha256(prompt.encode()).hexdigest()[:16]
    
    if model:
        return f"{CachePrefix.LLM}:{llm_type}:{model}:{prompt_hash}"
    else:
        return f"{CachePrefix.LLM}:{llm_type}:{prompt_hash}"

def build_llm_validation_key(algorithm_id: str, llm_type: str) -> str:
    """
    Construir clave para validación LLM de un algoritmo.
    
    Args:
        algorithm_id: ID del algoritmo
        llm_type: Tipo de LLM
    
    Returns:
        str: Clave de caché
    """
    return f"{CachePrefix.LLM_VALIDATION}:{algorithm_id}:{llm_type}"

# KEY BUILDERS - VISUALIZACIÓN
def build_tree_key(algorithm_id: str, tree_type: str = "recursion") -> str:
    """
    Construir clave para árbol de visualización.
    
    Args:
        algorithm_id: ID del algoritmo
        tree_type: Tipo de árbol (recursion, execution)
    
    Returns:
        str: Clave de caché
    """
    return f"{CachePrefix.TREE}:{algorithm_id}:{tree_type}"

def build_graph_key(algorithm_id: str, graph_type: str) -> str:
    """
    Construir clave para grafo.
    
    Args:
        algorithm_id: ID del algoritmo
        graph_type: Tipo de grafo
    
    Returns:
        str: Clave de caché
    """
    return f"{CachePrefix.GRAPH}:{algorithm_id}:{graph_type}"

def build_diagram_key(algorithm_id: str, diagram_format: str) -> str:
    """
    Construir clave para diagrama renderizado.
    
    Args:
        algorithm_id: ID del algoritmo
        diagram_format: Formato (svg, png, dot)
    
    Returns:
        str: Clave de caché
    """
    return f"{CachePrefix.DIAGRAM}:{algorithm_id}:{diagram_format}"

# KEY BUILDERS - ALGORITMOS
def build_algorithm_key(algorithm_id: str) -> str:
    """
    Construir clave para algoritmo.
    
    Args:
        algorithm_id: ID del algoritmo
    
    Returns:
        str: Clave de caché
    """
    return f"{CachePrefix.ALGORITHM}:{algorithm_id}"

def build_algorithm_list_key(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None
) -> str:
    """
    Construir clave para lista de algoritmos.
    
    Args:
        skip: Offset
        limit: Límite
        category: Categoría (opcional)
    
    Returns:
        str: Clave de caché
    """
    if category:
        return f"{CachePrefix.ALGORITHM_LIST}:{category}:{skip}:{limit}"
    else:
        return f"{CachePrefix.ALGORITHM_LIST}:{skip}:{limit}"

def build_algorithm_search_key(query: str, limit: int = 50) -> str:
    """
    Construir clave para búsqueda de algoritmos.
    
    Args:
        query: Query de búsqueda
        limit: Límite de resultados
    
    Returns:
        str: Clave de caché
    """
    query_hash = sha256(query.encode()).hexdigest()[:16]
    return f"{CachePrefix.ALGORITHM_SEARCH}:{query_hash}:{limit}"

# KEY BUILDERS - USUARIOS
def build_user_key(user_id: str) -> str:
    """
    Construir clave para usuario.
    
    Args:
        user_id: ID del usuario
    
    Returns:
        str: Clave de caché
    """
    return f"{CachePrefix.USER}:{user_id}"

def build_user_session_key(session_id: str) -> str:
    """
    Construir clave para sesión de usuario.
    
    Args:
        session_id: ID de la sesión
    
    Returns:
        str: Clave de caché
    """
    return f"{CachePrefix.USER_SESSION}:{session_id}"

def build_user_permissions_key(user_id: str) -> str:
    """
    Construir clave para permisos de usuario.
    
    Args:
        user_id: ID del usuario
    
    Returns:
        str: Clave de caché
    """
    return f"{CachePrefix.USER_PERMISSIONS}:{user_id}"

# KEY BUILDERS - MÉTRICAS
def build_metrics_key(metric_name: str, period: str = "hour") -> str:
    """
    Construir clave para métricas agregadas.
    
    Args:
        metric_name: Nombre de la métrica
        period: Período de agregación
    
    Returns:
        str: Clave de caché
    """
    return f"{CachePrefix.METRICS}:{metric_name}:{period}"

def build_stats_key(stats_type: str) -> str:
    """
    Construir clave para estadísticas.
    
    Args:
        stats_type: Tipo de estadísticas
    
    Returns:
        str: Clave de caché
    """
    return f"{CachePrefix.STATS}:{stats_type}"

# KEY BUILDERS - UTILIDADES
def build_temp_key(identifier: str) -> str:
    """
    Construir clave temporal.
    
    Args:
        identifier: Identificador único
    
    Returns:
        str: Clave de caché
    """
    return f"{CachePrefix.TEMP}:{identifier}"

def build_lock_key(resource: str) -> str:
    """
    Construir clave para lock distribuido.
    
    Args:
        resource: Recurso a lockear
    
    Returns:
        str: Clave de caché
    """
    return f"{CachePrefix.LOCK}:{resource}"

# HELPERS
def hash_content(content: str, length: int = 16) -> str:
    """
    Hashear contenido para usar en claves.
    
    Args:
        content: Contenido a hashear
        length: Longitud del hash (default 16)
    
    Returns:
        str: Hash hexadecimal
    """
    return sha256(content.encode()).hexdigest()[:length]

def build_composite_key(*parts: str) -> str:
    """
    Construir clave compuesta desde múltiples partes.
    
    Args:
        *parts: Partes de la clave
    
    Returns:
        str: Clave compuesta separada por ':'
    
    Example:
        >>> key = build_composite_key("user", "123", "algorithms", "favorites")
        >>> print(key)  # "user:123:algorithms:favorites"
    """
    return ":".join(str(part) for part in parts)

def parse_key(key: str) -> list[str]:
    """
    Parsear clave compuesta en sus partes.
    
    Args:
        key: Clave a parsear
    
    Returns:
        list: Partes de la clave
    
    Example:
        >>> parts = parse_key("user:123:algorithms:favorites")
        >>> print(parts)  # ["user", "123", "algorithms", "favorites"]
    """
    return key.split(":")

def get_key_prefix(key: str) -> str:
    """
    Obtener el prefijo de una clave.
    
    Args:
        key: Clave completa
    
    Returns:
        str: Prefijo de la clave
    
    Example:
        >>> prefix = get_key_prefix("analysis:123:big_o")
        >>> print(prefix)  # "analysis"
    """
    return key.split(":")[0] if ":" in key else key