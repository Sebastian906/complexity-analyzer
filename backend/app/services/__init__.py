"""
Services Module - Capa de Servicios de Aplicación

Proporciona servicios de alto nivel que orquestan operaciones complejas
combinando múltiples módulos del dominio.

Servicios disponibles:
    - AlgorithmService: Gestión completa de algoritmos
    - AnalysisOrchestrator: Orquestación de análisis completo
    - ValidationService: Validación de código y resultados
    - ExportService: Exportación de resultados en múltiples formatos
    - CacheService: Gestión de caché para optimizar rendimiento

Example:
    >>> from app.services import AnalysisOrchestrator
    >>> orchestrator = AnalysisOrchestrator()
    >>> result = await orchestrator.analyze_complete(code)
"""

from app.services.algorithm_service import (
    AlgorithmService,
    AlgorithmCreate,
    AlgorithmUpdate,
    AlgorithmSearchCriteria,
    AlgorithmCategory,
)
from app.services.analysis_orchestrator import (
    AnalysisOrchestrator,
    CompleteAnalysisRequest,
    CompleteAnalysisResult,
)
from app.services.validation_service import (
    ValidationService,
    ValidationRequest,
    ValidationResult,
    ValidationLevel,
    ValidationIssue,
    IssueSeverity,
)
from app.services.export_service import (
    ExportService,
    ExportRequest,
    ExportResult,
    ExportFormat,
    ExportOptions,
)
from app.services.cache_service import (
    CacheService,
    CacheKey,
    get_cache_service,
    generate_cache_key,
)

__all__ = [
    # Algorithm Service
    "AlgorithmService",
    "AlgorithmCreate",
    "AlgorithmUpdate",
    "AlgorithmSearchCriteria",
    "AlgorithmCategory",
    
    # Analysis Orchestrator
    "AnalysisOrchestrator",
    "CompleteAnalysisRequest",
    "CompleteAnalysisResult",
    
    # Validation Service
    "ValidationService",
    "ValidationRequest",
    "ValidationResult",
    "ValidationLevel",
    "ValidationIssue",
    "IssueSeverity",
    
    # Export Service
    "ExportService",
    "ExportRequest",
    "ExportResult",
    "ExportFormat",
    "ExportOptions",
    
    # Cache Service
    "CacheService",
    "CacheKey",
    "get_cache_service",
    "generate_cache_key",
]