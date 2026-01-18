"""
Unit Tests - Schemas Functionality

Tests unitarios para verificar que los schemas de Pydantic están
funcionales y correctamente integrados con el sistema.

Estructura de tests:
    1. Common Schemas (BaseResponse, Metadata, etc.)
    2. Algorithm Schemas
    3. Analysis Request Schemas
    4. Analysis Result Schemas
    5. Complexity Schemas
    6. Pattern Schemas
    7. Validation Schemas
    8. Export Schemas
    9. Integration with Services
"""

import pytest
from datetime import datetime
from typing import Dict, Any

# Common Schemas
from app.schemas.common import (
    BaseResponse,
    ErrorDetail,
    ErrorResponse,
    StatusEnum,
    ConfidenceLevelEnum,
    TimingMetadata,
    SourceLocation,
    validate_complexity_notation,
    validate_algorithm_name,
)

# Algorithm Schemas
from app.schemas.algorithm import (
    AlgorithmCategory,
    AlgorithmComplexityClass,
    LanguageType,
    AlgorithmParameter,
    AlgorithmCreate,
    AlgorithmUpdate,
    AlgorithmInfo,
    Algorithm,
    AlgorithmMetadata,
    AlgorithmSearchCriteria,
    AlgorithmResponse,
    AlgorithmListResponse,
)

# Analysis Request Schemas
from app.schemas.analysis_request import (
    AnalysisType,
    RecurrenceMethod,
    ComplexityAnalysisOptions,
    PatternDetectionOptions,
    CompleteAnalysisRequest,
)

# Analysis Result Schemas
from app.schemas.analysis_result import (
    LineExecution,
    LineByLineAnalysis,
    VisualizationResult,
    StructureMatch,
    CompleteAnalysisResult,
)

# Complexity Schemas
from app.schemas.complexity import (
    ComplexityClass,
    RecurrenceType,
    SolutionMethod,
    ComplexityAnalysis,
    SpaceComplexityAnalysis,
    RecurrenceEquation,
)

# Pattern Schemas
from app.schemas.pattern import (
    PatternType,
    PatternIndicator,
    PatternMatch,
    ScoredPattern,
    PatternDetectionResult,
)

# Validation Schemas
from app.schemas.validation import (
    ValidationLevel,
    IssueSeverity,
    IssueCategory,
    ValidationIssue,
    ValidationRequest,
    ValidationResult,
)

# Export Schemas
from app.schemas.export import (
    ExportFormat,
    ExportSection,
    ExportTemplate,
    ExportOptions,
    ExportRequest,
    ExportResult,
)

# 1. COMMON SCHEMAS TESTS
class TestCommonSchemas:
    """Tests para schemas comunes y base."""
    
    def test_base_response_creation(self):
        """Test creación de BaseResponse."""
        response = BaseResponse(
            success=True,
            message="Test message"
        )
        
        assert response.success is True
        assert response.message == "Test message"
        assert isinstance(response.timestamp, datetime)
    
    def test_error_response_creation(self):
        """Test creación de ErrorResponse."""
        error = ErrorResponse(
            message="Error occurred",
            error=ErrorDetail(
                type="ValidationError",
                message="Invalid input",
                code="VAL_001"
            )
        )
        
        assert error.success is False
        assert error.error.type == "ValidationError"
        assert error.error.code == "VAL_001"
    
    def test_timing_metadata(self):
        """Test TimingMetadata con cálculo automático de duración."""
        started = datetime.utcnow()
        
        timing = TimingMetadata(
            started_at=started,
            completed_at=datetime.utcnow(),
            duration_ms=100.5
        )
        
        assert timing.started_at == started
        assert timing.duration_ms == 100.5
    
    def test_source_location_str(self):
        """Test representación string de SourceLocation."""
        location = SourceLocation(line=5, column=10)
        assert str(location) == "5:10"
        
        location_range = SourceLocation(
            line=5, column=10,
            end_line=7, end_column=15
        )
        assert str(location_range) == "5:10-7:15"
    
    def test_validate_complexity_notation_valid(self):
        """Test validación de notaciones de complejidad válidas."""
        valid_notations = [
            "O(n)",
            "O(n²)",
            "Ω(log n)",
            "Θ(n log n)",
            "o(n³)",
            "ω(1)"
        ]
        
        for notation in valid_notations:
            result = validate_complexity_notation(notation)
            assert result == notation
    
    def test_validate_complexity_notation_invalid(self):
        """Test validación de notaciones inválidas."""
        invalid_notations = [
            "On",
            "O(n",
            "n²",
            "Big O(n)"
        ]
        
        for notation in invalid_notations:
            with pytest.raises(ValueError):
                validate_complexity_notation(notation)
    
    def test_validate_algorithm_name_valid(self):
        """Test validación de nombres de algoritmo válidos."""
        valid_names = [
            "Bubble Sort",
            "QuickSort",
            "Merge Sort v2",
            "A*"
        ]
        
        for name in valid_names:
            result = validate_algorithm_name(name)
            assert result == name.strip()
    
    def test_validate_algorithm_name_invalid(self):
        """Test validación de nombres inválidos."""
        with pytest.raises(ValueError):
            validate_algorithm_name("")
        
        with pytest.raises(ValueError):
            validate_algorithm_name("   ")
        
        with pytest.raises(ValueError):
            validate_algorithm_name("x" * 101)

# 2. ALGORITHM SCHEMAS TESTS
class TestAlgorithmSchemas:
    """Tests para schemas de algoritmos."""
    
    def test_algorithm_parameter_creation(self):
        """Test creación de AlgorithmParameter."""
        param = AlgorithmParameter(
            name="A",
            type="A[n]",
            is_array=True,
            dimensions=["n"],
            is_object=False
        )
        
        assert param.name == "A"
        assert param.is_array is True
        assert param.dimensions == ["n"]
    
    def test_algorithm_create_validation(self):
        """Test validación de AlgorithmCreate."""
        algo = AlgorithmCreate(
            name="Test Algorithm",
            description="Test description",
            category=AlgorithmCategory.SORTING,
            tags=["test", "sorting"],
            language=LanguageType.PSEUDOCODE,
            code="algorithm test(n)\nbegin\n  x <- 1\nend"
        )
        
        assert algo.name == "Test Algorithm"
        assert algo.category == AlgorithmCategory.SORTING
        assert "test" in algo.tags
        assert len(algo.code) > 0
    
    def test_algorithm_tags_normalization(self):
        """Test normalización automática de tags."""
        algo = AlgorithmCreate(
            name="Test",
            code="test",
            tags=["Sorting", "QUADRATIC", "  simple  ", "Sorting"]
        )
        
        # Tags deben estar en minúsculas y sin duplicados
        assert "sorting" in algo.tags
        assert "quadratic" in algo.tags
        assert "simple" in algo.tags
        assert algo.tags.count("sorting") == 1
    
    def test_algorithm_info_creation(self):
        """Test creación de AlgorithmInfo."""
        info = AlgorithmInfo(
            name="bubbleSort",
            parameters=[
                AlgorithmParameter(name="A", is_array=True, dimensions=["n"])
            ],
            has_recursion=False,
            has_loops=True,
            max_nesting_depth=2,
            total_lines=10,
            total_statements=5
        )
        
        assert info.name == "bubbleSort"
        assert info.has_loops is True
        assert info.max_nesting_depth == 2
        assert len(info.parameters) == 1
    
    def test_algorithm_search_criteria(self):
        """Test creación de criterios de búsqueda."""
        criteria = AlgorithmSearchCriteria(
            query="sort",
            category=AlgorithmCategory.SORTING,
            tags=["quadratic"],
            complexity_class=AlgorithmComplexityClass.QUADRATIC,
            analyzed_only=True
        )
        
        assert criteria.query == "sort"
        assert criteria.category == AlgorithmCategory.SORTING
        assert criteria.analyzed_only is True
    
    def test_algorithm_response_structure(self):
        """Test estructura de AlgorithmResponse."""
        algo = Algorithm(
            id="test_123",
            name="Test",
            code="test",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            analyzed=False,
            analysis_count=0
        )
        
        response = AlgorithmResponse(
            success=True,
            message="Success",
            algorithm=algo
        )
        
        assert response.success is True
        assert response.algorithm.id == "test_123"

# 3. ANALYSIS REQUEST SCHEMAS TESTS
class TestAnalysisRequestSchemas:
    """Tests para schemas de requests de análisis."""
    
    def test_complexity_analysis_options_defaults(self):
        """Test valores por defecto de ComplexityAnalysisOptions."""
        options = ComplexityAnalysisOptions()
        
        assert options.analyze_temporal is True
        assert options.analyze_spatial is True
        assert options.analyze_recurrence is True
        assert options.recurrence_method == RecurrenceMethod.AUTO
        assert options.analyze_line_by_line is True
    
    def test_pattern_detection_options_validation(self):
        """Test validación de PatternDetectionOptions."""
        options = PatternDetectionOptions(
            min_confidence=0.5,
            detect_all=True,
            include_indicators=True
        )
        
        assert options.min_confidence == 0.5
        assert options.detect_all is True
        
        # Test validación de rango
        with pytest.raises(ValueError):
            PatternDetectionOptions(min_confidence=1.5)
    
    def test_complete_analysis_request_creation(self):
        """Test creación de CompleteAnalysisRequest."""
        request = CompleteAnalysisRequest(
            code="algorithm test(n)\nbegin\n  for i <- 1 to n do\n    x <- x + 1\nend",
            language=LanguageType.PSEUDOCODE,
            algorithm_name="Test Algorithm",
            analyze_complexity=True,
            analyze_patterns=True,
            analyze_structures=True,
            generate_visualizations=False
        )
        
        assert len(request.code) > 0
        assert request.analyze_complexity is True
        assert request.analyze_patterns is True
        assert request.generate_visualizations is False
    
    def test_analysis_request_code_validation(self):
        """Test validación de código vacío."""
        with pytest.raises(ValueError):
            CompleteAnalysisRequest(code="   ")

# 4. ANALYSIS RESULT SCHEMAS TESTS
class TestAnalysisResultSchemas:
    """Tests para schemas de resultados de análisis."""
    
    def test_line_execution_creation(self):
        """Test creación de LineExecution."""
        line = LineExecution(
            line_number=5,
            code="for i <- 1 to n do",
            execution_count="n",
            statement_type="for_loop",
            complexity_contribution="O(n)",
            explanation="Loop ejecutado n veces"
        )
        
        assert line.line_number == 5
        assert line.execution_count == "n"
        assert line.statement_type == "for_loop"
    
    def test_line_by_line_analysis_structure(self):
        """Test estructura de LineByLineAnalysis."""
        analysis = LineByLineAnalysis(
            lines=[
                LineExecution(
                    line_number=1,
                    code="x <- 1",
                    execution_count="1",
                    statement_type="assignment",
                    complexity_contribution="O(1)",
                    explanation="Asignación constante"
                )
            ],
            dominant_complexity="O(n)",
            total_lines=5,
            summary="Análisis completado"
        )
        
        assert len(analysis.lines) == 1
        assert analysis.total_lines == 5
        assert analysis.dominant_complexity == "O(n)"
    
    def test_visualization_result_creation(self):
        """Test creación de VisualizationResult."""
        viz = VisualizationResult(
            type="recursion_tree",
            format="svg",
            content="<svg>...</svg>",
            statistics={
                "total_nodes": 15,
                "max_depth": 5
            },
            metadata={
                "algorithm_name": "fibonacci"
            }
        )
        
        assert viz.type == "recursion_tree"
        assert viz.format == "svg"
        assert viz.statistics["total_nodes"] == 15
    
    def test_structure_match_creation(self):
        """Test creación de StructureMatch."""
        structure = StructureMatch(
            structure_type="array",
            structure_name="Array/Lista",
            confidence=0.85,
            confidence_level=ConfidenceLevelEnum.HIGH,
            variables=["A"],
            operations=["Acceso: A[i]"],
            reasoning="Se encontraron indicadores de array"
        )
        
        assert structure.structure_type == "array"
        assert structure.confidence == 0.85
        assert structure.confidence_level == ConfidenceLevelEnum.HIGH
    
    def test_complete_analysis_result_comprehensive(self):
        """Test creación completa de CompleteAnalysisResult."""
        from app.schemas.common import AnalysisMetadata, TimingMetadata
        result = CompleteAnalysisResult(
            success=True,
            message="Análisis completado",
            timestamp=datetime.utcnow(),
            algorithm_name="test",
            algorithm_info=AlgorithmInfo(
                name="test",
                parameters=[],
                has_recursion=False,
                has_loops=True,
                max_nesting_depth=1,
                total_lines=5,
                total_statements=3
            ),
            complexity=ComplexityAnalysis(
                big_o="O(n)",
                omega="Ω(n)",
                theta="Θ(n)",
                explanation="Complejidad lineal",
                reasoning=["Loop simple"],
                has_tight_bound=True
            ),
            metadata=AnalysisMetadata(
                timing=TimingMetadata(
                    started_at=datetime.utcnow(),
                    completed_at=datetime.utcnow(),
                    duration_ms=0.0
                ),
                resources=None,
                version="1.0.0"
            ),
            summary="Test summary",
            recommendations=["Optimizar loops"]
        )
        assert result.success is True
        assert result.algorithm_name == "test"
        assert result.complexity.big_o == "O(n)"
        assert len(result.recommendations) > 0

# 5. COMPLEXITY SCHEMAS TESTS
class TestComplexitySchemas:
    """Tests para schemas de complejidad."""
    
    def test_complexity_analysis_creation(self):
        """Test creación de ComplexityAnalysis."""
        complexity = ComplexityAnalysis(
            big_o="O(n²)",
            omega="Ω(n)",
            theta=None,
            big_o_class=ComplexityClass.QUADRATIC,
            omega_class=ComplexityClass.LINEAR,
            explanation="Complejidad cuadrática",
            reasoning=["Loops anidados"],
            has_tight_bound=False
        )
        
        assert complexity.big_o == "O(n²)"
        assert complexity.big_o_class == ComplexityClass.QUADRATIC
        assert complexity.has_tight_bound is False
    
    def test_space_complexity_analysis(self):
        """Test creación de SpaceComplexityAnalysis."""
        space = SpaceComplexityAnalysis(
            total="O(n)",
            input_space="O(n)",
            auxiliary_space="O(1)",
            recursion_space="O(log n)",
            explanation="Espacio lineal por entrada",
            breakdown={
                "input": "O(n)",
                "aux": "O(1)",
                "recursion": "O(log n)"
            }
        )
        
        assert space.total == "O(n)"
        assert space.auxiliary_space == "O(1)"
        assert "input" in space.breakdown
    
    def test_recurrence_equation_creation(self):
        """Test creación de RecurrenceEquation."""
        recurrence = RecurrenceEquation(
            equation="T(n) = 2T(n/2) + O(n)",
            base_case="T(1) = O(1)",
            recursion_pattern=RecurrenceType.BINARY,
            a=2,
            b=2,
            f_n="O(n)",
            explanation="Divide y vencerás binario"
        )
        
        assert recurrence.equation == "T(n) = 2T(n/2) + O(n)"
        assert recurrence.recursion_pattern == RecurrenceType.BINARY
        assert recurrence.a == 2
        assert recurrence.b == 2

# 6. PATTERN SCHEMAS TESTS
class TestPatternSchemas:
    """Tests para schemas de patrones."""
    
    def test_pattern_indicator_creation(self):
        """Test creación de PatternIndicator."""
        indicator = PatternIndicator(
            name="nested_loops",
            description="Loops anidados profundos",
            found=True,
            weight=0.4,
            evidence="for i...for j...",
            location="lines 2-5"
        )
        
        assert indicator.name == "nested_loops"
        assert indicator.found is True
        assert indicator.weight == 0.4
    
    def test_pattern_match_creation(self):
        """Test creación de PatternMatch."""
        pattern = PatternMatch(
            pattern_type=PatternType.BRUTE_FORCE,
            pattern_name="Fuerza Bruta",
            confidence=0.85,
            confidence_level=ConfidenceLevelEnum.HIGH,
            indicators_found=[],
            indicators_missing=[],
            reasoning="Se detectaron 3 indicadores clave",
            typical_complexity="O(n²)"
        )
        
        assert pattern.pattern_type == PatternType.BRUTE_FORCE
        assert pattern.confidence == 0.85
        assert pattern.confidence_level == ConfidenceLevelEnum.HIGH
    
    def test_scored_pattern_structure(self):
        """Test estructura de ScoredPattern."""
        base_pattern = PatternMatch(
            pattern_type=PatternType.DIVIDE_AND_CONQUER,
            pattern_name="Divide y Vencerás",
            confidence=0.92,
            confidence_level=ConfidenceLevelEnum.VERY_HIGH,
            indicators_found=[],
            indicators_missing=[],
            reasoning="Patrón claro de D&C"
        )
        
        scored = ScoredPattern(
            pattern=base_pattern,
            raw_score=0.92,
            adjusted_score=1.0,
            final_score=0.95,
            confidence_bonus=0.08,
            missing_penalty=0.0,
            conflict_penalty=0.05,
            conflicts=["brute_force"],
            rank=1
        )
        
        assert scored.final_score == 0.95
        assert scored.rank == 1
        assert "brute_force" in scored.conflicts
    
    def test_pattern_detection_result_properties(self):
        """Test propiedades computadas de PatternDetectionResult."""
        pattern = PatternMatch(
            pattern_type=PatternType.RECURSIVE,
            pattern_name="Recursión",
            confidence=0.88,
            confidence_level=ConfidenceLevelEnum.HIGH,
            indicators_found=[],
            indicators_missing=[],
            reasoning="Detectada recursión"
        )
        
        scored = ScoredPattern(
            pattern=pattern,
            raw_score=0.88,
            adjusted_score=0.88,
            final_score=0.88,
            rank=1
        )
        
        result = PatternDetectionResult(
            patterns_found=[pattern],
            scored_patterns=[scored],
            primary_pattern=scored,
            confident_patterns=[scored],
            summary="Recursión detectada",
            pattern_count=1,
            metadata={}
        )
        
        assert result.has_patterns is True
        assert result.primary_pattern_name == "Recursión"
        assert result.primary_confidence == 0.88

# 7. VALIDATION SCHEMAS TESTS
class TestValidationSchemas:
    """Tests para schemas de validación."""
    
    def test_validation_issue_creation(self):
        """Test creación de ValidationIssue."""
        issue = ValidationIssue(
            severity=IssueSeverity.ERROR,
            category=IssueCategory.SYNTAX,
            message="Expected 'end'",
            description="Bloque sin cierre",
            location=SourceLocation(line=5, column=1),
            code_snippet="begin\n  x <- 1\n",
            rule="MISSING_END",
            suggestion="Agregue 'end' al final"
        )
        
        assert issue.severity == IssueSeverity.ERROR
        assert issue.category == IssueCategory.SYNTAX
        assert issue.rule == "MISSING_END"
    
    def test_validation_request_defaults(self):
        """Test valores por defecto de ValidationRequest."""
        request = ValidationRequest(
            code="algorithm test(n)\nbegin\n  x <- 1\nend"
        )
        
        assert request.language == LanguageType.PSEUDOCODE
        assert request.level == ValidationLevel.COMPLETE
        assert request.max_line_length == 100
        assert request.check_naming_conventions is True
    
    def test_validation_result_structure(self):
        """Test estructura de ValidationResult."""
        result = ValidationResult(
            success=True,
            message="Validación completada",
            is_valid=False,
            errors=[
                ValidationIssue(
                    severity=IssueSeverity.ERROR,
                    category=IssueCategory.SYNTAX,
                    message="Missing end",
                    rule="MISSING_END"
                )
            ],
            warnings=[],
            info=[],
            hints=[],
            error_count=1,
            warning_count=0,
            info_count=0,
            hint_count=0,
            lines_analyzed=5,
            statements_analyzed=3,
            summary="1 error encontrado"
        )
        
        assert result.is_valid is False
        assert result.error_count == 1
        assert len(result.errors) == 1

# 8. EXPORT SCHEMAS TESTS
class TestExportSchemas:
    """Tests para schemas de exportación."""
    
    def test_export_options_defaults(self):
        """Test valores por defecto de ExportOptions."""
        options = ExportOptions(format=ExportFormat.JSON)
        
        assert options.format == ExportFormat.JSON
        assert options.template == ExportTemplate.STANDARD
        assert options.include_visualizations is True
        assert options.pretty_print is True
    
    def test_export_request_validation(self):
        """Test validación de ExportRequest."""
        # Debe tener analysis_id O code
        with pytest.raises(ValueError):
            ExportRequest(
                options=ExportOptions(format=ExportFormat.JSON)
            )
    
    def test_export_result_creation(self):
        """Test creación de ExportResult."""
        result = ExportResult(
            success=True,
            message="Exportación exitosa",
            format=ExportFormat.PDF,
            filename="report.pdf",
            file_path="/exports/report.pdf",
            file_size_bytes=245678,
            sections_included=["algorithm_info", "complexity"],
            visualizations_count=2,
            total_pages=8,
            generated_at=datetime.utcnow(),
            generation_time_ms=1234.56
        )
        
        assert result.format == ExportFormat.PDF
        assert result.file_size_bytes == 245678
        assert result.total_pages == 8

# 9. INTEGRATION WITH SERVICES TESTS
class TestSchemasServiceIntegration:
    """Tests de integración de schemas con servicios."""
    
    def test_algorithm_service_create_schema_compatibility(self):
        """Test compatibilidad de schemas con AlgorithmService.create()."""
        from app.schemas.algorithm import AlgorithmCreate
        
        # Schema debe ser compatible con el servicio
        create_request = AlgorithmCreate(
            name="Test Algorithm",
            description="Test",
            category=AlgorithmCategory.SORTING,
            tags=["test"],
            language=LanguageType.PSEUDOCODE,
            code="algorithm test(n)\nbegin\n  x <- 1\nend"
        )
        
        # Verificar que todos los campos requeridos estén presentes
        assert hasattr(create_request, 'name')
        assert hasattr(create_request, 'code')
        assert hasattr(create_request, 'category')
    
    def test_analysis_orchestrator_request_schema_compatibility(self):
        """Test compatibilidad con AnalysisOrchestrator.analyze_complete()."""
        from app.schemas.analysis_request import CompleteAnalysisRequest
        
        request = CompleteAnalysisRequest(
            code="algorithm test(n)\nbegin\n  for i <- 1 to n do\n    x <- x + 1\nend",
            analyze_complexity=True,
            analyze_patterns=True,
            analyze_structures=True,
            generate_visualizations=False
        )
        
        # Verificar que tenga todas las opciones necesarias
        assert hasattr(request, 'code')
        assert hasattr(request, 'complexity_options')
        assert hasattr(request, 'pattern_options')
        assert hasattr(request, 'structure_options')
    
    def test_validation_service_schema_compatibility(self):
        """Test compatibilidad con ValidationService.validate()."""
        from app.schemas.validation import ValidationRequest
        
        request = ValidationRequest(
            code="algorithm test(n)\nbegin\n  x <- 1\nend",
            level=ValidationLevel.COMPLETE
        )
        
        assert hasattr(request, 'code')
        assert hasattr(request, 'level')
        assert request.level == ValidationLevel.COMPLETE
    
    def test_export_service_schema_compatibility(self):
        """Test compatibilidad con ExportService.export()."""
        from app.schemas.export import ExportRequest, ExportOptions
        
        request = ExportRequest(
            analysis_id="test_123",
            options=ExportOptions(
                format=ExportFormat.JSON,
                template=ExportTemplate.STANDARD
            ),
            filename="test_export"
        )
        
        assert hasattr(request, 'options')
        assert request.options.format == ExportFormat.JSON

# 10. SCHEMA SERIALIZATION TESTS
class TestSchemaSerialization:
    """Tests de serialización y deserialización de schemas."""
    
    def test_algorithm_json_serialization(self):
        """Test serialización a JSON de Algorithm."""
        algo = Algorithm(
            id="test_123",
            name="Test",
            code="test code",
            category=AlgorithmCategory.SORTING,
            tags=["test"],
            language=LanguageType.PSEUDOCODE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            analyzed=False,
            analysis_count=0
        )
        
        # Serializar
        json_data = algo.model_dump_json()
        assert isinstance(json_data, str)
        
        # Deserializar
        algo_dict = algo.model_dump()
        algo_reconstructed = Algorithm(**algo_dict)
        assert algo_reconstructed.id == algo.id
    
    def test_complete_analysis_result_serialization(self):
        """Test serialización de CompleteAnalysisResult complejo."""
        from app.schemas.common import AnalysisMetadata, TimingMetadata
        
        result = CompleteAnalysisResult(
            success=True,
            message="Test",
            timestamp=datetime.utcnow(),
            algorithm_name="test",
            algorithm_info=AlgorithmInfo(
                name="test",
                parameters=[],
                has_recursion=False,
                has_loops=False,
                max_nesting_depth=0,
                total_lines=1,
                total_statements=1
            ),
            metadata=AnalysisMetadata(
                timing=TimingMetadata(
                    started_at=datetime.utcnow(),
                    completed_at=datetime.utcnow(),
                    duration_ms=100
                ),
                version="1.0.0"
            ),
            summary="Test summary",
            recommendations=[]
        )
        
        # Debe poder serializarse sin errores
        json_data = result.model_dump_json()
        assert isinstance(json_data, str)
        assert len(json_data) > 0

# FIXTURES
@pytest.fixture
def sample_algorithm_create():
    """Fixture: AlgorithmCreate de ejemplo."""
    return AlgorithmCreate(
        name="Bubble Sort",
        description="Algoritmo de ordenamiento por burbuja",
        category=AlgorithmCategory.SORTING,
        tags=["sorting", "quadratic"],
        language=LanguageType.PSEUDOCODE,
        code="algorithm bubbleSort(A[n])\nbegin\n  for i <- 1 to n-1 do\n    for j <- 1 to n-i do\n      if A[j] > A[j+1] then\n        swap(A[j], A[j+1])\nend"
    )

@pytest.fixture
def sample_complete_analysis_request():
    """Fixture: CompleteAnalysisRequest de ejemplo."""
    return CompleteAnalysisRequest(
        code="algorithm test(n)\nbegin\n  for i <- 1 to n do\n    x <- x + 1\nend",
        analyze_complexity=True,
        analyze_patterns=True,
        analyze_structures=True,
        generate_visualizations=False
    )

@pytest.fixture
def sample_validation_request():
    """Fixture: ValidationRequest de ejemplo."""
    return ValidationRequest(
        code="algorithm test(n)\nbegin\n  x <- 1\nend",
        level=ValidationLevel.COMPLETE
    )

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])