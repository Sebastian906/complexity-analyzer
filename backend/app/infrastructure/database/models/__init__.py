"""
Database Models Package - Esquemas de Datos para Persistencia

Este paquete contiene todos los modelos de datos utilizados en el sistema:

MongoDB Models:
    - Algorithm: Almacenamiento de algoritmos y su código
    - AnalysisResult: Resultados de análisis de complejidad
    - PatternDetection: Patrones y técnicas detectadas

PostgreSQL Models:
    - User: Gestión de usuarios del sistema
    - Session: Sesiones y autenticación
    - AuditLog: Registros de auditoría
    - SecurityAudit: Eventos de seguridad
    - PerformanceLog: Métricas de rendimiento

Arquitectura:
    - MongoDB: Documentos flexibles para datos de algoritmos y análisis
    - PostgreSQL: Tablas relacionales para usuarios y métricas
    - Mixins: Funcionalidad compartida (timestamps, etc.)

Ejemplo de uso:
    >>> # MongoDB - Crear algoritmo
    >>> from app.infrastructure.database.models import Algorithm
    >>> algorithm = Algorithm(
    ...     name="quicksort",
    ...     code="algorithm quicksort...",
    ...     category="sorting"
    ... )
    >>> await algorithm.insert()
    
    >>> # PostgreSQL - Crear usuario
    >>> from app.infrastructure.database.models import User
    >>> user = User(
    ...     email="user@example.com",
    ...     username="testuser",
    ...     hashed_password="..."
    ... )
"""

# MONGODB MODELS - Documentos para Análisis de Algoritmos
from app.infrastructure.database.models.mongo import (
    # Modelo de Algoritmo
    Algorithm,
    
    # Modelo de Resultados de Análisis
    AnalysisResult,
    
    # Modelo de Detección de Patrones
    PatternDetection,
)

# POSTGRESQL MODELS - Modelos Relacionales
from app.infrastructure.database.models.postgres import (
    # Base y Mixins
    Base,
    TimestampMixin,
    
    # Usuarios y Autenticación
    User,
    
    # Sesiones
    Session,
    SessionToken,
    RefreshToken,
    
    # Auditoría y Logs
    AuditLog,
    AuditEventType,
    AuditSeverity,
    SecurityAudit,
    PerformanceLog,
)

# EXPORTS - API Pública del Módulo
__all__ = [
    # MONGODB MODELS
    "Algorithm",
    "AnalysisResult",
    "PatternDetection",
    
    # POSTGRESQL MODELS - Base
    "Base",
    "TimestampMixin",
    
    # POSTGRESQL MODELS - Usuarios
    "User",
    
    # POSTGRESQL MODELS - Sesiones
    "Session",
    "SessionToken",
    "RefreshToken",
    
    # POSTGRESQL MODELS - Auditoría
    "AuditLog",
    "AuditEventType",
    "AuditSeverity",
    "SecurityAudit",
    "PerformanceLog",
]

# METADATA Y DOCUMENTACIÓN
# Mapeo de modelos por backend
MODELS_BY_BACKEND = {
    "mongodb": [
        Algorithm,
        AnalysisResult,
        PatternDetection,
    ],
    "postgresql": [
        User,
        Session,
        SessionToken,
        RefreshToken,
        AuditLog,
        SecurityAudit,
        PerformanceLog,
    ],
}

# Categorías de modelos
MODELS_BY_CATEGORY = {
    "algorithms": [Algorithm, AnalysisResult, PatternDetection],
    "users": [User, Session, SessionToken, RefreshToken],
    "audit": [AuditLog, SecurityAudit, PerformanceLog],
}

# UTILIDADES
def get_models_info():
    """
    Obtiene información sobre todos los modelos disponibles.
    
    Returns:
        dict: Diccionario con información de modelos
        
    Example:
        >>> from app.infrastructure.database.models import get_models_info
        >>> info = get_models_info()
        >>> print(info['mongodb']['count'])  # 3
    """
    return {
        "mongodb": {
            "models": [m.__name__ for m in MODELS_BY_BACKEND["mongodb"]],
            "count": len(MODELS_BY_BACKEND["mongodb"]),
            "collections": [
                "algorithms",
                "analysis_results",
                "pattern_detections",
            ],
        },
        "postgresql": {
            "models": [m.__name__ for m in MODELS_BY_BACKEND["postgresql"]],
            "count": len(MODELS_BY_BACKEND["postgresql"]),
            "tables": [
                "users",
                "sessions",
                "session_tokens",
                "refresh_tokens",
                "audit_logs",
                "security_audits",
                "performance_logs",
            ],
        },
        "total_models": sum(len(models) for models in MODELS_BY_BACKEND.values()),
    }

def get_model_by_name(name: str):
    """
    Obtiene un modelo por su nombre.
    
    Args:
        name: Nombre del modelo (ej: "Algorithm", "User")
        
    Returns:
        Model class o None si no existe
        
    Example:
        >>> from app.infrastructure.database.models import get_model_by_name
        >>> AlgorithmModel = get_model_by_name("Algorithm")
        >>> algorithm = AlgorithmModel(name="test", code="...")
    """
    all_models = {
        model.__name__: model
        for models in MODELS_BY_BACKEND.values()
        for model in models
    }
    return all_models.get(name)

def get_mongodb_models():
    """
    Obtiene lista de modelos MongoDB.
    
    Returns:
        list: Lista de clases de modelos MongoDB
    """
    return MODELS_BY_BACKEND["mongodb"]

def get_postgresql_models():
    """
    Obtiene lista de modelos PostgreSQL.
    
    Returns:
        list: Lista de clases de modelos PostgreSQL
    """
    return MODELS_BY_BACKEND["postgresql"]

def validate_models():
    """
    Valida que todos los modelos estén correctamente definidos.
    
    Returns:
        dict: Resultado de validación por modelo
        
    Example:
        >>> from app.infrastructure.database.models import validate_models
        >>> validation = validate_models()
        >>> if validation['all_valid']:
        ...     print("Todos los modelos son válidos")
    """
    validation_results = {
        "mongodb": {},
        "postgresql": {},
        "errors": [],
    }
    
    # Validar modelos MongoDB
    for model in MODELS_BY_BACKEND["mongodb"]:
        try:
            # Verificar que tenga Settings
            if not hasattr(model, 'Settings'):
                validation_results["errors"].append(
                    f"{model.__name__}: Missing Settings class"
                )
                validation_results["mongodb"][model.__name__] = False
            else:
                validation_results["mongodb"][model.__name__] = True
        except Exception as e:
            validation_results["errors"].append(f"{model.__name__}: {str(e)}")
            validation_results["mongodb"][model.__name__] = False
    
    # Validar modelos PostgreSQL
    for model in MODELS_BY_BACKEND["postgresql"]:
        try:
            # Verificar que herede de Base
            if not hasattr(model, '__tablename__'):
                validation_results["errors"].append(
                    f"{model.__name__}: Missing __tablename__"
                )
                validation_results["postgresql"][model.__name__] = False
            else:
                validation_results["postgresql"][model.__name__] = True
        except Exception as e:
            validation_results["errors"].append(f"{model.__name__}: {str(e)}")
            validation_results["postgresql"][model.__name__] = False
    
    # Determinar si todos son válidos
    validation_results["all_valid"] = len(validation_results["errors"]) == 0
    
    return validation_results

# Agregar utilidades a __all__
__all__.extend([
    "MODELS_BY_BACKEND",
    "MODELS_BY_CATEGORY",
    "get_models_info",
    "get_model_by_name",
    "get_mongodb_models",
    "get_postgresql_models",
    "validate_models",
])

# INFORMACIÓN DEL PAQUETE
__version__ = "1.0.0"
__author__ = "Sebastián Salazar Güiza"

# Esquema de modelos para documentación
MODEL_SCHEMA = {
    "Algorithm": {
        "backend": "mongodb",
        "collection": "algorithms",
        "description": "Algoritmos y su código fuente",
        "fields": ["name", "code", "language", "category", "tags"],
    },
    "AnalysisResult": {
        "backend": "mongodb",
        "collection": "analysis_results",
        "description": "Resultados de análisis de complejidad",
        "fields": ["algorithm", "big_o", "omega", "theta", "space_complexity"],
    },
    "PatternDetection": {
        "backend": "mongodb",
        "collection": "pattern_detections",
        "description": "Patrones y técnicas detectadas",
        "fields": ["algorithm", "primary_pattern", "primary_confidence"],
    },
    "User": {
        "backend": "postgresql",
        "table": "users",
        "description": "Usuarios del sistema",
        "fields": ["email", "username", "hashed_password", "is_active"],
    },
    "Session": {
        "backend": "postgresql",
        "table": "sessions",
        "description": "Sesiones de usuario",
        "fields": ["user_id", "token", "expires_at", "is_active"],
    },
    "AuditLog": {
        "backend": "postgresql",
        "table": "audit_logs",
        "description": "Logs de auditoría del sistema",
        "fields": ["event_type", "severity", "user_id", "resource_type"],
    },
}

__all__.append("MODEL_SCHEMA")