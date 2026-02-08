"""
Sistema de Logging Centralizado

Configuración avanzada de logging usando Loguru para toda la aplicación.
Proporciona logging estructurado, rotación de archivos y múltiples destinos.
"""

import sys
from pathlib import Path
from typing import Optional

from loguru import logger

# Avoid importing settings at module import time to prevent circular imports.
# Import settings lazily inside `setup_logger`.


def setup_logger(name: Optional[str] = None) -> logger: # type: ignore
    """
    Configura el sistema de logging de la aplicación.
    
    Args:
        name: Nombre del logger (generalmente __name__ del módulo)
    
    Returns:
        logger: Instancia configurada de Loguru
    
    Example:
        >>> from app.utils.logger import setup_logger
        >>> logger = setup_logger(__name__)
        >>> logger.info("Mensaje de log")
    """
    
    # Import settings lazily to avoid circular imports. If importing settings
    # raises an exception (partial initialization / circular import), fall
    # back to safe defaults so logging still works during startup.
    try:
        from app.core.config import settings  # local import
        _settings = settings
    except Exception:
        class _Fallback:
            is_development = True
            is_production = False
            ENABLE_PROFILING = False
            LOG_FORMAT = "{time} | {level} | {name}:{function}:{line} - {message}"
            LOG_LEVEL = "DEBUG"
            LOG_FILE_PATH = Path("./logs/app.log")
            LOG_ROTATION = "00:00"
            LOG_RETENTION = "30 days"
            LOG_COMPRESSION = "zip"

        _settings = _Fallback()

    # Remover handlers por defecto
    logger.remove()

    # En modo desarrollo, solo log a consola para evitar conflictos de acceso concurrente a archivos
    if _settings.is_development:
        logger.add(
            sys.stdout,
            format=_settings.LOG_FORMAT,
            level=_settings.LOG_LEVEL,
            colorize=True,
            backtrace=True,
            diagnose=True,
        )
        # Nota: No se agregan handlers de archivo en desarrollo para evitar errores de acceso concurrente
    else:
        # Handler 1: Console Output (stdout)
        logger.add(
            sys.stdout,
            format=settings.LOG_FORMAT,
            level=settings.LOG_LEVEL,
            colorize=True,
            backtrace=True,
            diagnose=True,
        )
        # Handler 2: Archivo de Log General
        logger.add(
            _settings.LOG_FILE_PATH,
            format=(
                "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
                "{level: <8} | "
                "{name}:{function}:{line} | "
                "{message}"
            ),
            level="DEBUG",
            rotation=_settings.LOG_ROTATION,
            retention=_settings.LOG_RETENTION,
            compression=_settings.LOG_COMPRESSION,
            backtrace=True,
            diagnose=True,
            enqueue=True,  # Thread-safe
        )
        # Handler 3: Archivo de Errores (solo ERROR y CRITICAL)
        error_log_path = settings.LOG_FILE_PATH.parent / "errors.log"
        logger.add(
            error_log_path,
            format=(
                "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
                "{level: <8} | "
                "{name}:{function}:{line} | "
                "{message} | "
                "{extra}"
            ),
            level="ERROR",
            rotation="100 MB",
            retention="90 days",
            compression="zip",
            backtrace=True,
            diagnose=True,
            enqueue=True,
        )
        # Handler 4: Archivo de Performance (si está habilitado)
        if getattr(_settings, "ENABLE_PROFILING", False):
            performance_log_path = settings.LOG_FILE_PATH.parent / "performance.log"
            logger.add(
                performance_log_path,
                format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {message}",
                filter=lambda record: "performance" in record["extra"],
                level="INFO",
                rotation="50 MB",
                retention="30 days",
                compression="zip",
                enqueue=True,
            )
        # Handler 5: JSON Log para parseo externo (producción)
        if getattr(_settings, "is_production", False):
            json_log_path = _settings.LOG_FILE_PATH.parent / "app.json.log"
            logger.add(
                json_log_path,
                format="{message}",
                level="INFO",
                rotation="100 MB",
                retention="60 days",
                compression="zip",
                serialize=True,  # Output en JSON
                enqueue=True,
            )

    # Bind contexto si se proporciona nombre
    if name:
        return logger.bind(module=name)

    return logger

def log_function_call(func_name: str, **kwargs):
    """
    Loggea llamadas a funciones con sus argumentos.
    
    Args:
        func_name: Nombre de la función
        **kwargs: Argumentos de la función
    
    Example:
        >>> log_function_call("analyze_complexity", algorithm_id="123")
    """
    logger.opt(depth=1).debug(
        f"Llamando {func_name}",
        extra={"function": func_name, "arguments": kwargs}
    )

def log_performance(operation: str, duration: float, **metadata):
    """
    Loggea métricas de performance.
    
    Args:
        operation: Nombre de la operación
        duration: Duración en segundos
        **metadata: Metadatos adicionales
    
    Example:
        >>> log_performance("parse_algorithm", 0.123, lines=50)
    """
    logger.bind(performance=True).info(
        f"Performance: {operation} completado en {duration:.4f}s",
        extra={
            "operation": operation,
            "duration": duration,
            **metadata
        }
    )

def log_llm_call(
    provider: str,
    model: str,
    tokens_used: int,
    duration: float,
    success: bool = True
):
    """
    Loggea llamadas a LLMs.
    
    Args:
        provider: Proveedor del LLM (claude, gemini)
        model: Modelo usado
        tokens_used: Tokens consumidos
        duration: Duración de la llamada
        success: Si la llamada fue exitosa
    """
    status = "SUCCESS" if success else "FAILURE"
    logger.bind(llm=True).info(
        f"{status} LLM Call: {provider}/{model} - {tokens_used} tokens en {duration:.2f}s",
        extra={
            "provider": provider,
            "model": model,
            "tokens": tokens_used,
            "duration": duration,
            "success": success,
        }
    )

def log_database_operation(
    operation: str,
    collection: str,
    duration: float,
    affected_docs: int = 0
):
    """
    Loggea operaciones de base de datos.
    
    Args:
        operation: Tipo de operación (insert, update, delete, find)
        collection: Colección/tabla afectada
        duration: Duración de la operación
        affected_docs: Documentos afectados
    """
    logger.bind(database=True).debug(
        f"DB {operation} en {collection}: {affected_docs} docs en {duration:.3f}s",
        extra={
            "operation": operation,
            "collection": collection,
            "duration": duration,
            "affected": affected_docs,
        }
    )

def log_cache_operation(
    operation: str,
    key: str,
    hit: Optional[bool] = None,
    duration: Optional[float] = None
):
    """
    Loggea operaciones de caché.
    
    Args:
        operation: Tipo de operación (get, set, delete)
        key: Clave de caché
        hit: Si fue hit (get) o None para otras operaciones
        duration: Duración de la operación
    """
    hit_str = ""
    if hit is not None:
        hit_str = " [HIT]" if hit else " [MISS]"
    
    logger.bind(cache=True).debug(
        f"Cache {operation}{hit_str}: {key}",
        extra={
            "operation": operation,
            "key": key,
            "hit": hit,
            "duration": duration,
        }
    )

class LoggerContextManager:
    """
    Context manager para logging de bloques de código.
    
    Example:
        >>> with LoggerContextManager("parsing_algorithm"):
        ...     # código aquí
        ...     pass
    """
    
    def __init__(self, operation_name: str, **metadata):
        self.operation_name = operation_name
        self.metadata = metadata
        self.start_time = None
    
    def __enter__(self):
        import time
        self.start_time = time.time()
        logger.debug(f"Iniciando: {self.operation_name}", extra=self.metadata)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        duration = time.time() - self.start_time
        
        if exc_type is None:
            logger.debug(
                f"Completado: {self.operation_name} en {duration:.4f}s",
                extra={**self.metadata, "duration": duration}
            )
        else:
            logger.error(
                f"Error en: {self.operation_name} después de {duration:.4f}s",
                extra={
                    **self.metadata,
                    "duration": duration,
                    "error_type": exc_type.__name__,
                    "error": str(exc_val)
                }
            )
        
        return False  # No suprimir la excepción

def get_logger(name: Optional[str] = None) -> logger: # type: ignore
    """
    Obtiene un logger configurado para el módulo especificado.
    
    Esta función es un alias conveniente que retorna un logger
    con binding al nombre del módulo proporcionado.
    
    Args:
        name: Nombre del módulo (generalmente __name__)
    
    Returns:
        logger: Instancia de Loguru con contexto del módulo
    
    Example:
        >>> from app.utils.logger import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Mensaje de log")
    """
    # Use setup_logger to ensure handlers are configured lazily.
    return setup_logger(name)

def warn(self, message):
    """Alias para warning"""
    return self.warning(message)