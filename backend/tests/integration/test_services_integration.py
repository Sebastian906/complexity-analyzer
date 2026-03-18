"""
Tests de Integración - Servicios del Módulo 5

Verifica la integración entre servicios y otros módulos:
- AlgorithmService → Parser (validación sintáctica)
- AnalysisOrchestrator → Pipeline completo
- ValidationService → Parser + SemanticAnalyzer
- ExportService → Generación real de archivos
- CacheService → Optimización de análisis

Incluye fixtures reutilizables para casos comunes.
"""

import pytest
import asyncio
from pathlib import Path
from datetime import datetime

from app.services import (
    AlgorithmService,
    AnalysisOrchestrator,
    ValidationService,
    ExportService,
    CacheService,
    get_cache_service,
    generate_cache_key,
    CacheKey,
)

from app.schemas import (
    AlgorithmCreate,
    AlgorithmCategory,
    CompleteAnalysisRequest,
    ValidationRequest,
    ValidationLevel,
    ExportRequest,
    ExportFormat,
    ExportOptions,
)

from app.core.exceptions import (
    ParserException,
    ValidationException,
)

import json


def _normalize_cached_analysis(cached):
    """Normaliza el valor retornado por el cache para los objetos de análisis.

    Puede ser:
    - None
    - Un Pydantic model (con atributos)
    - Un dict (si el backend retornó dict)
    - Un str (si el backend serializó a JSON o a str)

    Retorna: dict o el objeto original (si no puede parsearse)
    """
    if cached is None:
        return None
    # Si es string, intentar deserializar JSON
    if isinstance(cached, str):
        try:
            parsed = json.loads(cached)
            return parsed
        except Exception:
            return cached
    # Si es dict, devolver tal cual
    if isinstance(cached, dict):
        return cached
    # Si es objeto con atributos, devolver tal cual
    return cached

# FIXTURES
@pytest.fixture
def bubble_sort_code():
    """Código de Bubble Sort CORRECTO según gramática"""
    return """
algorithm bubbleSort(A)
begin
    n ← length(A)
    for i ← 1 to n - 1 do
    begin
        for j ← 1 to n - i do
        begin
            if A[j] > A[j + 1] then
            begin
                temp ← A[j]
                A[j] ← A[j + 1]
                A[j + 1] ← temp
            end
        end
    end
end
"""

@pytest.fixture
def fibonacci_code():
    """Código de Fibonacci recursivo CORRECTO"""
    return """
algorithm fibonacci(n)
begin
    if n <= 1 then
    begin
        res ← n
    end
    else
    begin
        res ← fibonacci(n - 1) + fibonacci(n - 2)
    end
end
"""

@pytest.fixture
def binary_search_code():
    """Código de búsqueda binaria CORRECTO"""
    return """
algorithm binarySearch(A, target, low, high)
begin
    if low > high then
    begin
        idx ← -1
    end
    else
    begin
        mid ← floor((low + high) / 2)
        if A[mid] = target then
        begin
            idx ← mid
        end
        else
        begin
            if A[mid] > target then
            begin
                idx ← binarySearch(A, target, low, mid - 1)
            end
            else
            begin
                idx ← binarySearch(A, target, mid + 1, high)
            end
        end
    end
end
"""

@pytest.fixture
def invalid_code():
    """Código con errores sintácticos (falta end)"""
    return """
algorithm invalid(n)
begin
    for i ← 1 to n do
    begin
        x ← i + 1
"""

@pytest.fixture
def algorithm_service():
    """Servicio de algoritmos sin MongoDB"""
    return AlgorithmService(use_mongodb=False)

@pytest.fixture
def analysis_orchestrator():
    """Orquestador de análisis"""
    return AnalysisOrchestrator()

@pytest.fixture
def validation_service():
    """Servicio de validación"""
    return ValidationService()

@pytest.fixture
def export_service():
    """Servicio de exportación"""
    return ExportService()

@pytest.fixture
def cache_service():
    """Servicio de caché"""
    return get_cache_service()

@pytest.fixture
def temp_output_dir(tmp_path):
    """Directorio temporal para exports"""
    output_dir = tmp_path / "exports"
    output_dir.mkdir()
    return output_dir

# TESTS: AlgorithmService → Parser Integration
class TestAlgorithmServiceIntegration:
    """Tests de integración de AlgorithmService con Parser"""
    
    @pytest.mark.asyncio
    async def test_create_algorithm_validates_syntax(
        self,
        algorithm_service,
        bubble_sort_code
    ):
        """Crear algoritmo debe validar sintaxis con Parser"""
        request = AlgorithmCreate(
            code=bubble_sort_code,
            name="Bubble Sort",
            category=AlgorithmCategory.SORTING,
            tags=["sorting", "quadratic"]
        )
        
        result = await algorithm_service.create(request)
        
        assert result is not None
        assert result.algorithm.name == "Bubble Sort"
        assert result.algorithm.category == AlgorithmCategory.SORTING
        assert "sorting" in result.algorithm.tags
        assert result.algorithm.info is not None
        assert result.algorithm.info.name == "bubbleSort"
    
    @pytest.mark.asyncio
    async def test_create_algorithm_rejects_invalid_syntax(
        self,
        algorithm_service,
        invalid_code
    ):
        """Crear algoritmo debe rechazar sintaxis inválida"""
        request = AlgorithmCreate(
            code=invalid_code,
            name="Invalid",
            category=AlgorithmCategory.OTHER
        )
        
        with pytest.raises(ValidationException):
            await algorithm_service.create(request)
    
    @pytest.mark.asyncio
    async def test_update_algorithm_revalidates_syntax(
        self,
        algorithm_service,
        bubble_sort_code,
        fibonacci_code
    ):
        """Actualizar código debe revalidar sintaxis"""
        create_req = AlgorithmCreate(
            code=bubble_sort_code,
            name="Test",
            category=AlgorithmCategory.SORTING
        )
        created = await algorithm_service.create(create_req)
        
        from app.schemas import AlgorithmUpdate
        update_req = AlgorithmUpdate(code=fibonacci_code)
        
        updated = await algorithm_service.update(created.algorithm.id, update_req)
        
        assert updated is not None
        assert updated.algorithm.code == fibonacci_code
        assert updated.algorithm.info.name == "fibonacci"

# TESTS: AnalysisOrchestrator → Pipeline Completo
class TestAnalysisOrchestratorIntegration:
    """Tests de integración del pipeline completo de análisis"""
    
    @pytest.mark.asyncio
    async def test_complete_pipeline_bubble_sort(
        self,
        analysis_orchestrator,
        bubble_sort_code
    ):
        """Pipeline completo con VALIDACIÓN MEJORADA"""
        request = CompleteAnalysisRequest(
            code=bubble_sort_code,
            analyze_complexity=True,
            analyze_patterns=True,
            analyze_structures=True,
            generate_visualizations=False
        )
        
        result = await analysis_orchestrator.analyze_complete(request)
        
        # CRÍTICO: Verificar éxito PRIMERO
        if not result.success:
            pytest.fail(
                f"Análisis falló:\n"
                f"  Message: {result.message}\n"
                f"  Summary: {result.summary}\n"
                f"  Errors: {result.metadata.get('errors', []) if isinstance(result.metadata, dict) else getattr(result.metadata, 'errors', [])}"
            )

        # Ahora verificar campos
        assert result.algorithm_name == "bubbleSort"
        assert result.complexity is not None, "Complexity no debe ser None"
        assert result.complexity.big_o == "O(n^2)"

        # erificar patterns con mensaje claro
        if result.patterns is None:
            pytest.fail(
                f"Patterns es None. Revisar:\n"
                f"1. Pesos de PatternIndicators (deben ser <= 1.0)\n"
                f"2. Logs de PatternDetector\n"
                f"3. Excepciones capturadas en orchestrator"
            )

        assert len(result.patterns.patterns_found) > 0
        assert result.structures is not None
        assert len(result.structures.structures_found) > 0
        
        # Patrones (CRÍTICO - era None por error de pesos)
        if result.patterns is None:
            # Buscar razón en logs
            pytest.fail(
                "Patterns es None. Revisar:\n"
                "1. Pesos de PatternIndicators (deben ser <= 1.0)\n"
                "2. Logs de PatternDetector\n"
                "3. Excepciones capturadas en orchestrator"
            )
        
        assert len(result.patterns.patterns_found) > 0, \
            "No se detectaron patrones - revisar PatternDetector"
        
        # Estructuras
        assert result.structures is not None
        assert len(result.structures.structures_found) > 0
    
    @pytest.mark.asyncio
    async def test_complete_pipeline_fibonacci(
        self,
        analysis_orchestrator,
        fibonacci_code
    ):
        """Pipeline para recursión con DETECCIÓN MEJORADA"""
        request = CompleteAnalysisRequest(
            code=fibonacci_code,
            analyze_complexity=True,
            analyze_patterns=True,
            analyze_structures=True,
            generate_visualizations=False
        )
        
        result = await analysis_orchestrator.analyze_complete(request)
        
        # Verificar éxito
        if not result.success:
            pytest.fail(f"Análisis falló: {result.message}")
        
        assert result.algorithm_name == "fibonacci"
        
        # Complejidad
        if result.complexity is None:
            pytest.fail("Complexity es None para fibonacci")
        
        # CRÍTICO: Detectar recursión
        recursion_detected = False
        
        if result.patterns and result.patterns.patterns_found:
            pattern_names = [p.pattern_name.lower() for p in result.patterns.patterns_found]
            recursion_detected = any("recurs" in name for name in pattern_names)
            
            if not recursion_detected:
                # Mostrar qué patrones SÍ se detectaron
                detected = ", ".join([p.pattern_name for p in result.patterns.patterns_found])
                pytest.fail(
                    f"PatternDetector NO detectó recursión.\n"
                    f"Patrones detectados: {detected}\n"
                    f"Revisar RecursiveDetector y sus pesos."
                )
        else:
            pytest.fail(
                "result.patterns es None o vacío. "
                "Revisar pesos de PatternIndicators."
            )

        assert recursion_detected, \
            "Fibonacci es recursivo pero PatternDetector no lo detectó"

    @pytest.mark.asyncio
    async def test_validation_detects_semantic_errors(
        self,
        validation_service
    ):
        """Validación semántica MEJORADA"""
        code_with_error = """
algorithm test(n)
begin
    x ← undeclared_var + 1
end
"""
        from app.schemas import ValidationRequest, ValidationLevel
        
        request = ValidationRequest(
            code=code_with_error,
            level=ValidationLevel.SEMANTIC
        )

        result = await validation_service.validate(request)

        # El SemanticAnalyzer CORREGIDO debe detectar esto
        has_undeclared_error = any(
            "undeclared" in error.message.lower() or
            "not declared" in error.message.lower()
            for error in result.errors
        )

        if not has_undeclared_error:
            # Mostrar qué errores SÍ se detectaron
            errors_found = [e.message for e in result.errors]
            warnings_found = [w.message for w in result.warnings]
            
            pytest.fail(
                f"SemanticAnalyzer NO detectó variable no declarada.\n"
                f"Errores encontrados: {errors_found}\n"
                f"Warnings encontrados: {warnings_found}\n"
                f"Revisar SemanticAnalyzer._check_undeclared_variables()"
            )

        assert has_undeclared_error, \
            "Variable 'undeclared_var' debería haber sido detectada como no declarada"

# TESTS: ValidationService → Parser + SemanticAnalyzer
class TestValidationServiceIntegration:
    """Tests de integración de ValidationService"""
    
    @pytest.mark.asyncio
    async def test_syntax_validation_uses_parser(
        self,
        validation_service,
        bubble_sort_code
    ):
        """Validación sintáctica usa Parser correctamente"""
        request = ValidationRequest(
            code=bubble_sort_code,
            level=ValidationLevel.SYNTAX
        )
        
        result = await validation_service.validate(request)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    @pytest.mark.asyncio
    async def test_semantic_validation_integrates_parser_and_analyzer(
        self,
        validation_service,
        bubble_sort_code
    ):
        """Validación semántica usa Parser + SemanticAnalyzer"""
        request = ValidationRequest(
            code=bubble_sort_code,
            level=ValidationLevel.SEMANTIC
        )
        
        result = await validation_service.validate(request)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    @pytest.mark.asyncio
    async def test_validation_detects_semantic_errors(
        self,
        validation_service
    ):
        """
        Validación debe detectar errores semánticos.
        
        NOTA: Este test es permisivo porque el SemanticAnalyzer
        puede no detectar todas las variables no declaradas dependiendo
        de la configuración.
        """
        code_with_error = """
algorithm test(n)
begin
    x ← undeclared_var + 1
end
"""
        request = ValidationRequest(
            code=code_with_error,
            level=ValidationLevel.SEMANTIC
        )
        result = await validation_service.validate(request)
        
        # Verificar que al menos se completó la validación
        assert result is not None
        
        # Si la validación detectó problemas, debe tener errores o warnings
        if not result.is_valid:
            assert len(result.errors) > 0 or len(result.warnings) > 0
        else:
            # Si no detectó el error, fallar el test para visibilidad
            assert False, (
                "SemanticAnalyzer no detectó variable no declarada. "
                "Antes se skipeaba, ahora se fuerza a fallar para visibilidad. "
                "Revisar la lógica de validación semántica."
            )
    
    @pytest.mark.asyncio
    async def test_complete_validation_checks_all_levels(
        self,
        validation_service,
        fibonacci_code
    ):
        """Validación completa ejecuta todos los niveles"""
        request = ValidationRequest(
            code=fibonacci_code,
            level=ValidationLevel.COMPLETE
        )
        
        result = await validation_service.validate(request)
        
        assert result.is_valid is True
        assert len(result.errors) == 0

# TESTS: ExportService → Generación Real de Archivos
class TestExportServiceIntegration:
    """Tests de integración de ExportService con sistema de archivos"""
    
    @pytest.mark.asyncio
    async def test_export_to_json_creates_file(
        self,
        export_service,
        analysis_orchestrator,
        bubble_sort_code,
        temp_output_dir
    ):
        """Exportar JSON debe crear archivo real"""
        analysis_req = CompleteAnalysisRequest(
            code=bubble_sort_code,
            analyze_complexity=True,
            analyze_patterns=False,
            analyze_structures=False,
            generate_visualizations=False
        )
        analysis_result = await analysis_orchestrator.analyze_complete(analysis_req)
        
        if not analysis_result.success:
            pytest.skip(f"Análisis falló, skipping export test: {analysis_result.message}")
        
        data = {
            "algorithm_name": analysis_result.algorithm_name,
            "big_o": analysis_result.complexity.big_o if analysis_result.complexity else "N/A",
            "complexity": analysis_result.complexity.model_dump() if analysis_result.complexity else {}
        }
        
        output_path = temp_output_dir / "bubble_sort.json"
        
        from app.services.export_service import ExportRequest as ServiceExportRequest
        from app.services.export_service import ExportOptions as ServiceExportOptions
        from app.services.export_service import ExportFormat as ServiceExportFormat
        
        export_req = ServiceExportRequest(
            data=data,
            format=ServiceExportFormat.JSON,
            options=ServiceExportOptions(),
            output_path=output_path
        )
        
        export_result = await export_service.export(export_req)
        
        assert export_result.success is True
        assert output_path.exists()
        
        import json
        with open(output_path, 'r') as f:
            saved_data = json.load(f)
        assert "algorithm_name" in saved_data
    
    @pytest.mark.asyncio
    async def test_export_to_markdown_creates_file(
        self,
        export_service,
        analysis_orchestrator,
        fibonacci_code,
        temp_output_dir
    ):
        """Exportar Markdown debe crear archivo legible"""
        analysis_req = CompleteAnalysisRequest(
            code=fibonacci_code,
            analyze_complexity=True,
            analyze_patterns=False,
            analyze_structures=False,
            generate_visualizations=False
        )
        analysis_result = await analysis_orchestrator.analyze_complete(analysis_req)
        
        if not analysis_result.success:
            pytest.skip("Análisis falló, skipping export test")
        
        data = {
            "algorithm_name": analysis_result.algorithm_name,
            "complexity_result": {
                "big_o": analysis_result.complexity.big_o if analysis_result.complexity else "N/A",
            },
            "summary": analysis_result.summary
        }
        
        output_path = temp_output_dir / "fibonacci.md"
        
        from app.services.export_service import ExportRequest as ServiceExportRequest
        from app.services.export_service import ExportOptions as ServiceExportOptions
        from app.services.export_service import ExportFormat as ServiceExportFormat
        
        export_req = ServiceExportRequest(
            data=data,
            format=ServiceExportFormat.MARKDOWN,
            options=ServiceExportOptions(),
            output_path=output_path
        )
        
        export_result = await export_service.export(export_req)
        
        assert export_result.success is True
        assert output_path.exists()
        
        content = output_path.read_text()
        assert "fibonacci" in content.lower()

# TESTS: CacheService → Optimización de Análisis
class TestCacheServiceIntegration:
    """Tests de integración de CacheService"""
    
    @pytest.mark.asyncio
    async def test_cache_stores_and_retrieves_analysis(
        self,
        cache_service,
        analysis_orchestrator,
        bubble_sort_code
    ):
        """Caché debe almacenar y recuperar análisis"""
        cache_key = generate_cache_key(CacheKey.ANALYSIS, bubble_sort_code)
        
        cached = await cache_service.get(cache_key)
        assert cached is None
        
        request = CompleteAnalysisRequest(
            code=bubble_sort_code,
            analyze_complexity=True,
            analyze_patterns=False,
            analyze_structures=False,
            generate_visualizations=False
        )
        result = await analysis_orchestrator.analyze_complete(request)
        
        if not result.success or result.complexity is None:
            pytest.skip(f"Análisis falló, skipping cache test: {result.message}")
        
        await cache_service.set(
            cache_key,
            result,
            cache_type="analysis"
        )
        
        cached = await cache_service.get(cache_key)
        assert cached is not None
        cached_norm = _normalize_cached_analysis(cached)
        # cached_norm puede ser dict o model
        if isinstance(cached_norm, dict):
            assert cached_norm.get("complexity", {}).get("big_o") == result.complexity.big_o
        else:
            assert getattr(cached_norm, "complexity").big_o == result.complexity.big_o
    
    @pytest.mark.asyncio
    async def test_cache_avoids_redundant_analysis(
        self,
        cache_service,
        analysis_orchestrator,
        fibonacci_code
    ):
        """Caché debe evitar análisis redundantes"""
        cache_key = generate_cache_key(CacheKey.ANALYSIS, fibonacci_code)
        
        request = CompleteAnalysisRequest(
            code=fibonacci_code,
            analyze_complexity=True,
            analyze_patterns=False,
            analyze_structures=False,
            generate_visualizations=False
        )
        result1 = await analysis_orchestrator.analyze_complete(request)
        
        if not result1.success or result1.complexity is None:
            pytest.skip("Análisis falló, skipping cache test")
        
        await cache_service.set(cache_key, result1, cache_type="analysis")
        
        cached_result = await cache_service.get(cache_key)
        
        assert cached_result is not None
        cached_norm = _normalize_cached_analysis(cached_result)
        if isinstance(cached_norm, dict):
            assert cached_norm.get("complexity", {}).get("big_o") == result1.complexity.big_o
        else:
            assert getattr(cached_norm, "complexity").big_o == result1.complexity.big_o
    
    @pytest.mark.asyncio
    async def test_cache_clears_expired_entries(
        self,
        cache_service,
        bubble_sort_code
    ):
        """Caché debe limpiar entradas expiradas"""
        cache_key = generate_cache_key(CacheKey.ANALYSIS, bubble_sort_code)
        
        test_data = {"test": "data"}
        await cache_service.set(cache_key, test_data, ttl=1)
        
        cached = await cache_service.get(cache_key)
        assert cached is not None
        
        await asyncio.sleep(2)
        
        cached_after_expiry = await cache_service.get(cache_key)
        assert cached_after_expiry is None

# TESTS: Integración Completa End-to-End
class TestEndToEndIntegration:
    """Tests end-to-end que verifican el flujo completo"""
    
    @pytest.mark.asyncio
    async def test_full_workflow_create_analyze_export(
        self,
        algorithm_service,
        analysis_orchestrator,
        validation_service,
        export_service,
        cache_service,
        bubble_sort_code,
        temp_output_dir
    ):
        """Flujo completo: Validar → Crear → Analizar → Cache → Exportar"""
        
        # 1. Validar código
        val_request = ValidationRequest(
            code=bubble_sort_code,
            level=ValidationLevel.COMPLETE
        )
        val_result = await validation_service.validate(val_request)
        assert val_result.is_valid is True
        
        # 2. Crear algoritmo
        create_request = AlgorithmCreate(
            code=bubble_sort_code,
            name="Bubble Sort Test",
            category=AlgorithmCategory.SORTING
        )
        algorithm = await algorithm_service.create(create_request)
        assert algorithm is not None
        
        # 3. Verificar caché
        cache_key = generate_cache_key(CacheKey.ANALYSIS, bubble_sort_code)
        cached = await cache_service.get(cache_key)
        
        # 4. Analizar (o usar caché)
        if cached is None:
            analysis_request = CompleteAnalysisRequest(
                code=bubble_sort_code,
                analyze_complexity=True,
                analyze_patterns=True,
                analyze_structures=True,
                generate_visualizations=False
            )
            analysis_result = await analysis_orchestrator.analyze_complete(analysis_request)
            
            if not analysis_result.success or analysis_result.complexity is None:
                pytest.skip(f"Análisis falló, skipping end-to-end test: {analysis_result.message}")
            
            await cache_service.set(cache_key, analysis_result, cache_type="analysis")
        else:
            cached_norm = _normalize_cached_analysis(cached)
            if isinstance(cached_norm, dict):
                # reconstruir un objeto mínimo con lo que necesitamos
                class _Minimal:
                    pass
                ana = _Minimal()
                # construir nested minimal complexity object
                comp = type("C", (), {})()
                comp.big_o = cached_norm.get("complexity", {}).get("big_o")
                ana.complexity = comp
                ana.algorithm_name = cached_norm.get("algorithm_name") if isinstance(cached_norm.get("algorithm_name"), str) else getattr(cached_norm, "algorithm_name", None)
                ana.patterns = None
                analysis_result = ana
            else:
                analysis_result = cached_norm
        
        assert analysis_result.complexity.big_o == "O(n^2)"
        
        # 5. Exportar resultados
        data = {
            "algorithm_name": analysis_result.algorithm_name,
            "big_o": analysis_result.complexity.big_o,
            "patterns": [p.pattern_name for p in analysis_result.patterns.patterns_found] if analysis_result.patterns else []
        }
        
        export_path = temp_output_dir / "bubble_sort_complete.json"
        
        from app.services.export_service import ExportRequest as ServiceExportRequest
        from app.services.export_service import ExportOptions as ServiceExportOptions
        from app.services.export_service import ExportFormat as ServiceExportFormat
        
        export_request = ServiceExportRequest(
            data=data,
            format=ServiceExportFormat.JSON,
            options=ServiceExportOptions(),
            output_path=export_path
        )
        export_result = await export_service.export(export_request)
        
        assert export_result.success is True
        assert export_path.exists()
        
        import json
        with open(export_path, 'r') as f:
            saved_data = json.load(f)
        assert "algorithm_name" in saved_data
        assert saved_data["big_o"] == "O(n^2)"

# CONFIGURACIÓN PYTEST
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])