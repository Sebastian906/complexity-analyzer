"""
Infrastructure Module - Sistema de Infraestructura del Analizador

Este módulo proporciona toda la infraestructura necesaria para el funcionamiento
del analizador de complejidades algorítmicas:

- Agentes: Sistema multiagente con LangGraph para análisis distribuido
- Bases de Datos: Clientes y repositorios para MongoDB, PostgreSQL
- Caché: Sistema de caché con Redis para optimización
- LLMs: Adaptadores para Claude (Anthropic) y Gemini (Google)
- Exportadores: Generación de reportes en múltiples formatos
- Modelos: Esquemas de datos para persistencia

Arquitectura:
    - Patrón Repository para acceso a datos
    - Factory Pattern para creación de clientes
    - Adapter Pattern para integración de LLMs
    - Strategy Pattern para exportadores

Ejemplo de uso:
    >>> # Usar sistema multiagente
    >>> from app.infrastructure import CoordinatorAgent
    >>> coordinator = CoordinatorAgent(use_llm=True)
    >>> result = await coordinator.execute_pipeline(algorithm_code)
    
    >>> # Exportar resultados
    >>> from app.infrastructure import export_analysis, ExportFormat
    >>> export_result = export_analysis(
    ...     algorithm=algo,
    ...     analysis=analysis_result,
    ...     format=ExportFormat.PDF
    ... )
    
    >>> # Acceso a bases de datos
    >>> from app.infrastructure import get_mongodb_client
    >>> mongo = get_mongodb_client()
    >>> await mongo.connect()
"""

# AGENTES - Sistema Multiagente con LangGraph
from app.infrastructure.agents import (
    # Clases base
    BaseAgent,
    AgentState,
    
    # Agentes especializados
    ParserAgent,
    ComplexityAgent,
    PatternAgent,
    ValidationAgent,
    
    # Coordinación
    CoordinatorAgent,
    AgentGraphOrchestrator,
)

# BASES DE DATOS - Clientes y Gestión de Conexiones
from app.infrastructure.database import (
    # MongoDB
    MongoDBClient,
    get_mongodb_client,
    
    # PostgreSQL
    PostgreSQLClient,
    get_postgresql_client,
    
    # Gestión de conexiones
    DatabaseConnectionManager,
    get_connection_manager,
    init_databases,
    close_databases,
    check_database_health,
    
    # Factory y Backends
    DatabaseFactory,
    RepositoryFactory,
    DatabaseBackend,
    get_default_client,
    get_default_repository_factory,
    MultiBackendManager,
    get_multi_backend_manager,
)

# MODELOS - Esquemas de Datos
from app.infrastructure.database.models.mongo import (
    Algorithm,
    AnalysisResult,
    PatternDetection,
)

from app.infrastructure.database.models.postgres import (
    Base,
    TimestampMixin,
    User,
    Session,
    SessionToken,
    RefreshToken,
    AuditLog,
    AuditEventType,
    AuditSeverity,
    SecurityAudit,
    PerformanceLog,
)

# REPOSITORIOS - Acceso a Datos
from app.infrastructure.database.repositories import (
    # Base
    BaseRepository,
    
    # MongoDB Repositories
    AlgorithmRepository,
    AnalysisRepository,
    
    # PostgreSQL Repositories
    UserRepository,
    MetricsRepository,
    
    # Redis Repository
    CacheRepository,
    cached,
)

# CACHÉ - Sistema de Caché con Redis
from app.infrastructure.cache import (
    # Cliente Redis
    RedisCache,
    get_redis_client,
    
    # Gestión de claves
    CachePrefix,
    CacheTTL,
    
    # Builders de claves
    build_analysis_key,
    build_complexity_key,
    build_recurrence_key,
    build_pattern_key,
    build_pattern_score_key,
    build_structure_key,
    build_llm_key,
    build_llm_validation_key,
    build_tree_key,
    build_graph_key,
    build_diagram_key,
    build_algorithm_key,
    build_algorithm_list_key,
    build_algorithm_search_key,
    build_user_key,
    build_user_session_key,
    build_user_permissions_key,
    build_metrics_key,
    build_stats_key,
    build_temp_key,
    build_lock_key,
    
    # Helpers
    hash_content,
    build_composite_key,
    parse_key,
    get_key_prefix,
)

# LLMs - Integración con Large Language Models
from app.infrastructure.llm import (
    # Base
    BaseLLM,
    LLMResponse,
    
    # Adaptadores
    ClaudeAdapter,
    GeminiAdapter,
    
    # Factory
    LLMFactory,
    
    # Utilidades
    ResponseParser,
)

# EXPORTADORES - Generación de Reportes
from app.infrastructure.export import (
    # Base
    BaseExporter,
    ExportConfig,
    ExportData,
    ExportFormat,
    ExportResult,
    
    # Exportadores específicos
    JSONExporter,
    MarkdownExporter,
    CSVExporter,
    DOTExporter,
    MermaidExporter,
    SVGExporter,
    HTMLExporter,
    PDFExporter,      # Requiere reportlab
    ExcelExporter,    # Requiere openpyxl
    
    # Funciones helper
    export_to_json,
    export_to_markdown,
    export_to_csv,
    export_to_dot,
    export_to_mermaid,
    export_to_svg,
    export_to_html,
    export_to_pdf,
    export_to_excel,
    
    # Factory y utilidades
    ExporterFactory,
    export_analysis,
    export_to_multiple_formats,
    
    # Flags de disponibilidad
    PDF_AVAILABLE,
    EXCEL_AVAILABLE,
)

# EXPORTS - API Pública del Módulo
__all__ = [
    # AGENTES
    "BaseAgent",
    "AgentState",
    "ParserAgent",
    "ComplexityAgent",
    "PatternAgent",
    "ValidationAgent",
    "CoordinatorAgent",
    "AgentGraphOrchestrator",
    
    # BASES DE DATOS
    # Clientes
    "MongoDBClient",
    "get_mongodb_client",
    "PostgreSQLClient",
    "get_postgresql_client",
    
    # Gestión de conexiones
    "DatabaseConnectionManager",
    "get_connection_manager",
    "init_databases",
    "close_databases",
    "check_database_health",
    
    # Factory
    "DatabaseFactory",
    "RepositoryFactory",
    "DatabaseBackend",
    "get_default_client",
    "get_default_repository_factory",
    "MultiBackendManager",
    "get_multi_backend_manager",
    
    # MODELOS - MongoDB
    "Algorithm",
    "AnalysisResult",
    "PatternDetection",
    
    # MODELOS - PostgreSQL
    "Base",
    "TimestampMixin",
    "User",
    "Session",
    "SessionToken",
    "RefreshToken",
    "AuditLog",
    "AuditEventType",
    "AuditSeverity",
    "SecurityAudit",
    "PerformanceLog",
    
    # REPOSITORIOS
    "BaseRepository",
    "AlgorithmRepository",
    "AnalysisRepository",
    "UserRepository",
    "MetricsRepository",
    "CacheRepository",
    "cached",
    
    # CACHÉ
    "RedisCache",
    "get_redis_client",
    "CachePrefix",
    "CacheTTL",
    
    # Key builders
    "build_analysis_key",
    "build_complexity_key",
    "build_recurrence_key",
    "build_pattern_key",
    "build_pattern_score_key",
    "build_structure_key",
    "build_llm_key",
    "build_llm_validation_key",
    "build_tree_key",
    "build_graph_key",
    "build_diagram_key",
    "build_algorithm_key",
    "build_algorithm_list_key",
    "build_algorithm_search_key",
    "build_user_key",
    "build_user_session_key",
    "build_user_permissions_key",
    "build_metrics_key",
    "build_stats_key",
    "build_temp_key",
    "build_lock_key",
    
    # Helpers
    "hash_content",
    "build_composite_key",
    "parse_key",
    "get_key_prefix",
    
    # LLMs
    "BaseLLM",
    "LLMResponse",
    "ClaudeAdapter",
    "GeminiAdapter",
    "LLMFactory",
    "ResponseParser",
    
    # EXPORTADORES
    # Base
    "BaseExporter",
    "ExportConfig",
    "ExportData",
    "ExportFormat",
    "ExportResult",
    
    # Exportadores
    "JSONExporter",
    "MarkdownExporter",
    "CSVExporter",
    "DOTExporter",
    "MermaidExporter",
    "SVGExporter",
    "HTMLExporter",
    "PDFExporter",
    "ExcelExporter",
    
    # Helpers
    "export_to_json",
    "export_to_markdown",
    "export_to_csv",
    "export_to_dot",
    "export_to_mermaid",
    "export_to_svg",
    "export_to_html",
    "export_to_pdf",
    "export_to_excel",
    
    # Factory
    "ExporterFactory",
    "export_analysis",
    "export_to_multiple_formats",
    
    # Flags
    "PDF_AVAILABLE",
    "EXCEL_AVAILABLE",
]

# CONFIGURACIÓN Y VALIDACIÓN
def validate_infrastructure():
    """
    Valida que todos los componentes de infraestructura estén disponibles.
    
    Returns:
        dict: Diccionario con el estado de cada componente
        
    Example:
        >>> from app.infrastructure import validate_infrastructure
        >>> status = validate_infrastructure()
        >>> print(status['mongodb'])  # True/False
    """
    status = {
        "mongodb": False,
        "postgresql": False,
        "redis": False,
        "claude": False,
        "gemini": False,
        "pdf_export": PDF_AVAILABLE,
        "excel_export": EXCEL_AVAILABLE,
    }
    
    # Validar MongoDB
    try:
        from app.core.config import settings
        if settings.MONGODB_URL:
            status["mongodb"] = True
    except Exception:
        pass
    
    # Validar PostgreSQL
    try:
        from app.core.config import settings
        if settings.POSTGRES_HOST:
            status["postgresql"] = True
    except Exception:
        pass
    
    # Validar Redis
    try:
        from app.core.config import settings
        if settings.REDIS_HOST:
            status["redis"] = True
    except Exception:
        pass
    
    # Validar Claude
    try:
        from app.core.config import settings
        if settings.ANTHROPIC_API_KEY:
            status["claude"] = True
    except Exception:
        pass
    
    # Validar Gemini
    try:
        from app.core.config import settings
        if settings.GOOGLE_API_KEY:
            status["gemini"] = True
    except Exception:
        pass
    
    return status

def get_infrastructure_info():
    """
    Obtiene información detallada de la infraestructura.
    
    Returns:
        dict: Información de versiones y configuración
    """
    from app.core.config import settings
    
    return {
        "database": {
            "type": settings.DATABASE_TYPE,
            "mongodb": {
                "configured": bool(settings.MONGODB_URL),
                "database": settings.MONGODB_DB_NAME,
            },
            "postgresql": {
                "configured": bool(settings.POSTGRES_HOST),
                "host": settings.POSTGRES_HOST if settings.POSTGRES_HOST else None,
            },
        },
        "cache": {
            "redis": {
                "configured": bool(settings.REDIS_HOST),
                "host": settings.REDIS_HOST if settings.REDIS_HOST else None,
            },
        },
        "llms": {
            "primary": settings.PRIMARY_LLM,
            "fallback": settings.FALLBACK_LLM,
            "claude": {
                "configured": bool(settings.ANTHROPIC_API_KEY),
                "model": settings.CLAUDE_MODEL,
            },
            "gemini": {
                "configured": bool(settings.GOOGLE_API_KEY),
                "model": settings.GEMINI_MODEL,
            },
        },
        "export": {
            "formats_available": ExporterFactory.get_available_formats(),
            "pdf_available": PDF_AVAILABLE,
            "excel_available": EXCEL_AVAILABLE,
        },
    }

# Agregar funciones a __all__
__all__.extend([
    "validate_infrastructure",
    "get_infrastructure_info",
])