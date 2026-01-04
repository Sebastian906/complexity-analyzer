"""
Recurrence Module - Módulo de Ecuaciones de Recurrencia

Proporciona herramientas completas para construcción y resolución
de ecuaciones de recurrencia T(n) y S(n).

Exports principales:
    - RecurrenceBuilder: Constructor de ecuaciones
    - RecurrenceSolver: Resolvedor con 5 métodos
    - TemporalComplexityAnalyzer: Wrapper para T(n)
    - SpatialComplexityAnalyzer: Wrapper para S(n)
"""

from app.core.analyzer.recurrence.recurrence_builder import (
    RecurrenceBuilder,
    RecurrenceEquation,
    build_recurrence_equations
)

from app.core.analyzer.recurrence.recurrence_solver import (
    RecurrenceSolver,
    RecurrenceForm,
    SolutionMethod,
    RecurrencePattern,
    SolutionResult,
    solve_recurrence
)

from app.core.analyzer.recurrence.temporal_complexity import (
    TemporalComplexityAnalyzer,
    TemporalComplexityResult,
    analyze_temporal_complexity
)

from app.core.analyzer.recurrence.spatial_complexity import (
    SpatialComplexityAnalyzer,
    SpatialComplexityResult,
    analyze_spatial_complexity
)

__all__ = [
    # Builder
    "RecurrenceBuilder",
    "RecurrenceEquation",
    "build_recurrence_equations",
    
    # Solver
    "RecurrenceSolver",
    "RecurrenceForm",
    "SolutionMethod",
    "RecurrencePattern",
    "SolutionResult",
    "solve_recurrence",
    
    # Temporal
    "TemporalComplexityAnalyzer",
    "TemporalComplexityResult",
    "analyze_temporal_complexity",
    
    # Spatial
    "SpatialComplexityAnalyzer",
    "SpatialComplexityResult",
    "analyze_spatial_complexity",
]