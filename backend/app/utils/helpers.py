"""
Helpers - Funciones de Utilidad General

Proporciona funciones helper de uso común en todo el sistema:
- Conversión de datos
- Formateo
- Timing
- Serialización
- Etc.
"""

import time
import hashlib
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable, TypeVar, Union
from functools import wraps
from pathlib import Path

from app.utils.logger import get_logger

logger = get_logger(__name__)

T = TypeVar('T')

# CONVERSIÓN DE DATOS
def to_snake_case(text: str) -> str:
    """
    Convertir texto a snake_case.
    
    Args:
        text: Texto a convertir
    
    Returns:
        str: Texto en snake_case
    
    Example:
        >>> to_snake_case("HelloWorld")
        'hello_world'
        >>> to_snake_case("someCamelCase")
        'some_camel_case'
    """
    import re
    
    # Insertar underscore antes de mayúsculas
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
    # Insertar underscore antes de mayúsculas seguidas de minúsculas
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
    
    return s2.lower()

def to_camel_case(text: str) -> str:
    """
    Convertir texto a camelCase.
    
    Args:
        text: Texto a convertir (puede estar en snake_case)
    
    Returns:
        str: Texto en camelCase
    
    Example:
        >>> to_camel_case("hello_world")
        'helloWorld'
    """
    components = text.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])

def to_pascal_case(text: str) -> str:
    """
    Convertir texto a PascalCase.
    
    Args:
        text: Texto a convertir
    
    Returns:
        str: Texto en PascalCase
    
    Example:
        >>> to_pascal_case("hello_world")
        'HelloWorld'
    """
    return ''.join(x.title() for x in text.split('_'))

def dict_to_flat(
    nested_dict: Dict[str, Any],
    parent_key: str = '',
    sep: str = '.'
) -> Dict[str, Any]:
    """
    Aplanar diccionario anidado.
    
    Args:
        nested_dict: Diccionario anidado
        parent_key: Clave padre (para recursión)
        sep: Separador de claves
    
    Returns:
        Dict aplanado
    
    Example:
        >>> nested = {"a": {"b": {"c": 1}}}
        >>> dict_to_flat(nested)
        {'a.b.c': 1}
    """
    items = []
    
    for k, v in nested_dict.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        
        if isinstance(v, dict):
            items.extend(dict_to_flat(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    
    return dict(items)

def flat_to_dict(flat_dict: Dict[str, Any], sep: str = '.') -> Dict[str, Any]:
    """
    Convertir diccionario aplanado a anidado.
    
    Args:
        flat_dict: Diccionario aplanado
        sep: Separador de claves
    
    Returns:
        Dict anidado
    
    Example:
        >>> flat = {'a.b.c': 1}
        >>> flat_to_dict(flat)
        {'a': {'b': {'c': 1}}}
    """
    result = {}
    
    for key, value in flat_dict.items():
        parts = key.split(sep)
        d = result
        
        for part in parts[:-1]:
            if part not in d:
                d[part] = {}
            d = d[part]
        
        d[parts[-1]] = value
    
    return result

# HASHING Y ENCODING
def generate_hash(text: str, algorithm: str = 'sha256') -> str:
    """
    Generar hash de un texto.
    
    Args:
        text: Texto a hashear
        algorithm: Algoritmo (md5, sha1, sha256, sha512)
    
    Returns:
        str: Hash hexadecimal
    
    Example:
        >>> generate_hash("hello world")
        'b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9'
    """
    hash_func = getattr(hashlib, algorithm)()
    hash_func.update(text.encode('utf-8'))
    return hash_func.hexdigest()

def generate_short_hash(text: str, length: int = 8) -> str:
    """
    Generar hash corto de un texto.
    
    Args:
        text: Texto a hashear
        length: Longitud del hash
    
    Returns:
        str: Hash hexadecimal corto
    """
    full_hash = generate_hash(text)
    return full_hash[:length]

def generate_unique_id(prefix: str = '') -> str:
    """
    Generar ID único basado en timestamp y hash.
    
    Args:
        prefix: Prefijo opcional
    
    Returns:
        str: ID único
    
    Example:
        >>> generate_unique_id("algo")
        'algo_1234567890_a1b2c3d4'
    """
    import uuid
    
    timestamp = int(time.time())
    unique = str(uuid.uuid4())[:8]
    
    if prefix:
        return f"{prefix}_{timestamp}_{unique}"
    else:
        return f"{timestamp}_{unique}"

# FORMATEO
def format_bytes(bytes_value: int) -> str:
    """
    Formatear bytes a unidad legible.
    
    Args:
        bytes_value: Bytes a formatear
    
    Returns:
        str: Bytes formateados (ej: "1.5 MB")
    
    Example:
        >>> format_bytes(1536)
        '1.5 KB'
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    
    return f"{bytes_value:.1f} PB"

def format_duration(seconds: float) -> str:
    """
    Formatear duración en segundos a formato legible.
    
    Args:
        seconds: Segundos
    
    Returns:
        str: Duración formateada
    
    Example:
        >>> format_duration(125.5)
        '2m 5.5s'
        >>> format_duration(3665)
        '1h 1m 5s'
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    
    minutes = int(seconds // 60)
    secs = seconds % 60
    
    if minutes < 60:
        return f"{minutes}m {secs:.1f}s"
    
    hours = minutes // 60
    mins = minutes % 60
    
    return f"{hours}h {mins}m {secs:.0f}s"

def format_number(number: Union[int, float], decimals: int = 2) -> str:
    """
    Formatear número con separadores de miles.
    
    Args:
        number: Número a formatear
        decimals: Decimales (para floats)
    
    Returns:
        str: Número formateado
    
    Example:
        >>> format_number(1234567)
        '1,234,567'
        >>> format_number(1234.567, decimals=2)
        '1,234.57'
    """
    if isinstance(number, int):
        return f"{number:,}"
    else:
        return f"{number:,.{decimals}f}"

def truncate_string(text: str, max_length: int, suffix: str = '...') -> str:
    """
    Truncar string a longitud máxima.
    
    Args:
        text: Texto a truncar
        max_length: Longitud máxima
        suffix: Sufijo a agregar si se trunca
    
    Returns:
        str: Texto truncado
    
    Example:
        >>> truncate_string("Hello World", 8)
        'Hello...'
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

# TIMING Y PERFORMANCE
class Timer:
    """
    Context manager para medir tiempo de ejecución.
    
    Example:
        >>> with Timer() as t:
        ...     # código a medir
        ...     time.sleep(1)
        >>> print(f"Duración: {t.duration:.2f}s")
    """
    
    def __init__(self, name: Optional[str] = None):
        self.name = name
        self.start_time = None
        self.end_time = None
        self.duration = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, *args):
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        
        if self.name:
            logger.debug(f"Timer [{self.name}]: {self.duration:.4f}s")

def timeit(func: Callable) -> Callable:
    """
    Decorador para medir tiempo de ejecución de funciones.
    
    Example:
        >>> @timeit
        >>> def slow_function():
        ...     time.sleep(1)
        ...     return "Done"
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        duration = time.time() - start
        
        logger.debug(f"Function {func.__name__} took {duration:.4f}s")
        return result
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        
        logger.debug(f"Function {func.__name__} took {duration:.4f}s")
        return result
    
    # Detectar si es async
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper

# SERIALIZACIÓN
def safe_json_dumps(obj: Any, indent: Optional[int] = None) -> str:
    """
    JSON dumps con manejo seguro de tipos no serializables.
    
    Args:
        obj: Objeto a serializar
        indent: Indentación (opcional)
    
    Returns:
        str: JSON string
    """
    def default_handler(o):
        if isinstance(o, datetime):
            return o.isoformat()
        elif isinstance(o, Path):
            return str(o)
        elif hasattr(o, '__dict__'):
            return o.__dict__
        else:
            return str(o)
    
    return json.dumps(obj, default=default_handler, indent=indent)

def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """
    JSON loads con manejo de errores.
    
    Args:
        json_str: String JSON
        default: Valor por defecto si falla
    
    Returns:
        Objeto deserializado o default
    """
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f"Error deserializando JSON: {e}")
        return default

# LISTAS Y COLECCIONES
def chunk_list(lst: List[T], chunk_size: int) -> List[List[T]]:
    """
    Dividir lista en chunks de tamaño específico.
    
    Args:
        lst: Lista a dividir
        chunk_size: Tamaño de cada chunk
    
    Returns:
        Lista de chunks
    
    Example:
        >>> chunk_list([1, 2, 3, 4, 5], 2)
        [[1, 2], [3, 4], [5]]
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def deduplicate_list(lst: List[T]) -> List[T]:
    """
    Eliminar duplicados de lista manteniendo orden.
    
    Args:
        lst: Lista con posibles duplicados
    
    Returns:
        Lista sin duplicados
    """
    seen = set()
    result = []
    
    for item in lst:
        # Para items hashables
        try:
            if item not in seen:
                seen.add(item)
                result.append(item)
        except TypeError:
            # Para items no hashables
            if item not in result:
                result.append(item)
    
    return result

def safe_get(dictionary: Dict, *keys, default=None) -> Any:
    """
    Obtener valor de diccionario anidado de forma segura.
    
    Args:
        dictionary: Diccionario
        *keys: Claves anidadas
        default: Valor por defecto
    
    Returns:
        Valor o default
    
    Example:
        >>> data = {"a": {"b": {"c": 1}}}
        >>> safe_get(data, "a", "b", "c")
        1
        >>> safe_get(data, "a", "x", "y", default=0)
        0
    """
    result = dictionary
    
    for key in keys:
        try:
            result = result[key]
        except (KeyError, TypeError, AttributeError):
            return default
    
    return result

# RETRY LOGIC
def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Decorador para reintentar función en caso de error.
    
    Args:
        max_attempts: Máximo de intentos
        delay: Delay inicial en segundos
        backoff: Factor de backoff exponencial
        exceptions: Tupla de excepciones a capturar
    
    Example:
        >>> @retry(max_attempts=3, delay=1.0)
        >>> def unstable_function():
        ...     # código que puede fallar
        ...     pass
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            current_delay = delay
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        logger.error(
                            f"Function {func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        raise
                    
                    logger.warning(
                        f"Function {func.__name__} failed (attempt {attempt}/{max_attempts}): {e}. "
                        f"Retrying in {current_delay}s..."
                    )
                    
                    import asyncio
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            current_delay = delay
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        logger.error(
                            f"Function {func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        raise
                    
                    logger.warning(
                        f"Function {func.__name__} failed (attempt {attempt}/{max_attempts}): {e}. "
                        f"Retrying in {current_delay}s..."
                    )
                    
                    time.sleep(current_delay)
                    current_delay *= backoff
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

# FECHAS Y TIEMPO
def get_timestamp() -> int:
    """
    Obtener timestamp actual en segundos.
    
    Returns:
        int: Timestamp Unix
    """
    return int(time.time())

def get_timestamp_ms() -> int:
    """
    Obtener timestamp actual en milisegundos.
    
    Returns:
        int: Timestamp en ms
    """
    return int(time.time() * 1000)

def format_datetime(dt: datetime, format_str: str = '%Y-%m-%d %H:%M:%S') -> str:
    """
    Formatear datetime a string.
    
    Args:
        dt: Datetime a formatear
        format_str: Formato
    
    Returns:
        str: Datetime formateado
    """
    return dt.strftime(format_str)

def parse_datetime(dt_str: str, format_str: str = '%Y-%m-%d %H:%M:%S') -> Optional[datetime]:
    """
    Parsear string a datetime.
    
    Args:
        dt_str: String a parsear
        format_str: Formato esperado
    
    Returns:
        datetime o None si falla
    """
    try:
        return datetime.strptime(dt_str, format_str)
    except ValueError as e:
        logger.error(f"Error parseando datetime: {e}")
        return None

def get_relative_time(dt: datetime) -> str:
    """
    Obtener tiempo relativo (ej: "hace 5 minutos").
    
    Args:
        dt: Datetime
    
    Returns:
        str: Tiempo relativo
    """
    now = datetime.utcnow()
    diff = now - dt
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "hace unos segundos"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"hace {minutes} minuto{'s' if minutes != 1 else ''}"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"hace {hours} hora{'s' if hours != 1 else ''}"
    else:
        days = int(seconds / 86400)
        return f"hace {days} día{'s' if days != 1 else ''}"

# MISCELÁNEOS
def is_production() -> bool:
    """
    Verificar si está en entorno de producción.
    
    Returns:
        bool: True si es producción
    """
    from app.core.config import settings
    return settings.APP_ENV == "production"

def is_development() -> bool:
    """
    Verificar si está en entorno de desarrollo.
    
    Returns:
        bool: True si es desarrollo
    """
    from app.core.config import settings
    return settings.APP_ENV == "development"