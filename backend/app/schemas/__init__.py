"""
Schemas Package - Pydantic DTOs

Este paquete contiene todos los schemas Pydantic (DTOs - Data Transfer Objects)
utilizados en la API REST y en la lógica de negocio.

Estructura:
    - common.py: Schemas base y reutilizables
    - algorithm.py: Schemas de algoritmos
    - analysis_request.py: Requests de análisis
    - analysis_result.py: Resultados de análisis
    - complexity.py: Schemas de complejidad
    - pattern.py: Schemas de patrones
    - validation.py: Schemas de validación
    - export.py: Schemas de exportación

Uso:
    from app.schemas import (
        CompleteAnalysisRequest,
        CompleteAnalysisResult,
        Algorithm,
        PatternDetectionResult
    )
"""

# Common Schemas
from app.schemas.common import (
    # Base
    BaseResponse,
    ErrorDetail,
    ErrorResponse,
    
    # Enums
    StatusEnum,
    ConfidenceLevelEnum,
    ComplexityNotationEnum,
    
    # Pagination
    PaginationParams,
    PaginatedResponse,
    
    # Metadata
    TimingMetadata,
    ResourceMetadata,
    AnalysisMetadata,
    
    # Source Location
    SourceLocation,
    CodeSnippet,
    
    # Statistics
    Statistics,
    
    # Helpers
    create_success_response,
    create_error_response,
)

# Algorithm Schemas
from app.schemas.algorithm import (
    # Enums
    AlgorithmCategory,
    AlgorithmComplexityClass,
    LanguageType,
    AlgorithmSortBy,
    
    # Base
    AlgorithmParameter,
    AlgorithmBase,
    AlgorithmCreate,
    AlgorithmUpdate,
    
    # Response
    AlgorithmInfo,
    Algorithm,
    AlgorithmMetadata,
    
    # Search
    AlgorithmSearchCriteria,
    AlgorithmListRequest,
    
    # Response wrappers
    AlgorithmResponse,
    AlgorithmListResponse,
)

# Analysis Request Schemas
from app.schemas.analysis_request import (
    # Enums
    AnalysisType,
    RecurrenceMethod,
    VisualizationType,
    
    # Base
    AnalysisRequest,
    
    # Options
    ComplexityAnalysisOptions,
    PatternDetectionOptions,
    StructureDetectionOptions,
    VisualizationOptions,
    
    # Specific Requests
    ComplexityAnalysisRequest,
    PatternDetectionRequest,
    StructureDetectionRequest,
    VisualizationRequest,
    
    # Complete
    CompleteAnalysisRequest,
    
    # Batch
    BatchAnalysisItem,
    BatchAnalysisRequest,
    
    # Quick
    QuickAnalysisRequest,
)

# Analysis Result Schemas
from app.schemas.analysis_result import (
    # Line by Line
    LineExecution,
    LineByLineAnalysis,
    
    # Visualization
    VisualizationResult,
    
    # Structures
    StructureMatch,
    StructureUsage,
    StructureDetectionResult,
    
    # Results
    CompleteAnalysisResult,
    BatchAnalysisItemResult,
    BatchAnalysisResult,
    QuickAnalysisResult,
)

# Complexity Schemas
from app.schemas.complexity import (
    # Enums
    ComplexityClass,
    RecurrenceType,
    SolutionMethod,
    
    # Basic
    Complexity,
    
    # Analysis
    ComplexityAnalysis,
    SpaceComplexityAnalysis,
    
    # Recurrence
    RecurrenceEquation,
    RecurrenceSolution,
    
    # Tight Bounds
    TightBoundResult,
    
    # Comparison
    ComplexityComparison,
    
    # Summary
    ComplexitySummary,
)

# Pattern Schemas
from app.schemas.pattern import (
    # Enums
    PatternType,
    
    # Indicator
    PatternIndicator,
    
    # Match
    PatternMatch,
    ScoredPattern,
    
    # Result
    PatternDetectionResult,
    
    # Statistics
    PatternStatistics,
    
    # Comparison
    PatternComparison,
    
    # Recommendation
    PatternRecommendation,
)

# Validation Schemas
from app.schemas.validation import (
    # Enums
    ValidationLevel,
    IssueSeverity,
    IssueCategory,
    
    # Issue
    ValidationIssue,
    
    # Request
    ValidationRequest,
    
    # Results
    ValidationResult,
    SyntaxValidationResult,
    SemanticValidationResult,
    StructuralValidationResult,
    
    # Best Practices
    BestPracticeCheck,
    BestPracticesValidationResult,
    
    # Complete
    CompleteValidationResult,
)

# Export Schemas
from app.schemas.export import (
    # Enums
    ExportFormat,
    ExportSection,
    ExportTemplate,
    
    # Options
    ExportOptions,
    
    # Request
    ExportRequest,
    
    # Result
    ExportResult,
    
    # Batch
    BatchExportItem,
    BatchExportRequest,
    BatchExportItemResult,
    BatchExportResult,
    
    # Templates
    ExportTemplateInfo,
    AvailableExportsResponse,
)

# __all__ - Exports públicos
__all__ = [
    # Common
    "BaseResponse",
    "ErrorDetail",
    "ErrorResponse",
    "StatusEnum",
    "ConfidenceLevelEnum",
    "ComplexityNotationEnum",
    "PaginationParams",
    "PaginatedResponse",
    "TimingMetadata",
    "ResourceMetadata",
    "AnalysisMetadata",
    "SourceLocation",
    "CodeSnippet",
    "Statistics",
    "create_success_response",
    "create_error_response",
    
    # Algorithm
    "AlgorithmCategory",
    "AlgorithmComplexityClass",
    "LanguageType",
    "AlgorithmSortBy",
    "AlgorithmParameter",
    "AlgorithmBase",
    "AlgorithmCreate",
    "AlgorithmUpdate",
    "AlgorithmInfo",
    "Algorithm",
    "AlgorithmMetadata",
    "AlgorithmSearchCriteria",
    "AlgorithmListRequest",
    "AlgorithmResponse",
    "AlgorithmListResponse",
    
    # Analysis Request
    "AnalysisType",
    "RecurrenceMethod",
    "VisualizationType",
    "AnalysisRequest",
    "ComplexityAnalysisOptions",
    "PatternDetectionOptions",
    "StructureDetectionOptions",
    "VisualizationOptions",
    "ComplexityAnalysisRequest",
    "PatternDetectionRequest",
    "StructureDetectionRequest",
    "VisualizationRequest",
    "CompleteAnalysisRequest",
    "BatchAnalysisItem",
    "BatchAnalysisRequest",
    "QuickAnalysisRequest",
    
    # Analysis Result
    "LineExecution",
    "LineByLineAnalysis",
    "VisualizationResult",
    "StructureMatch",
    "StructureUsage",
    "StructureDetectionResult",
    "CompleteAnalysisResult",
    "BatchAnalysisItemResult",
    "BatchAnalysisResult",
    "QuickAnalysisResult",
    
    # Complexity
    "ComplexityClass",
    "RecurrenceType",
    "SolutionMethod",
    "Complexity",
    "ComplexityAnalysis",
    "SpaceComplexityAnalysis",
    "RecurrenceEquation",
    "RecurrenceSolution",
    "TightBoundResult",
    "ComplexityComparison",
    "ComplexitySummary",
    
    # Pattern
    "PatternType",
    "PatternIndicator",
    "PatternMatch",
    "ScoredPattern",
    "PatternDetectionResult",
    "PatternStatistics",
    "PatternComparison",
    "PatternRecommendation",
    
    # Validation
    "ValidationLevel",
    "IssueSeverity",
    "IssueCategory",
    "ValidationIssue",
    "ValidationRequest",
    "ValidationResult",
    "SyntaxValidationResult",
    "SemanticValidationResult",
    "StructuralValidationResult",
    "BestPracticeCheck",
    "BestPracticesValidationResult",
    "CompleteValidationResult",
    
    # Export
    "ExportFormat",
    "ExportSection",
    "ExportTemplate",
    "ExportOptions",
    "ExportRequest",
    "ExportResult",
    "BatchExportItem",
    "BatchExportRequest",
    "BatchExportItemResult",
    "BatchExportResult",
    "ExportTemplateInfo",
    "AvailableExportsResponse",
]