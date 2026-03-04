"""
Smoke Tests - Verificación Rápida del Sistema

Los smoke tests son pruebas superficiales y rápidas que verifican que los
componentes principales del sistema están operativos. No validan lógica
en profundidad; solo confirman que "no hay humo" (es decir, nada está roto
catastróficamente).

Objetivo:
    - Validar que la aplicación arranca sin errores.
    - Verificar que cada endpoint responde con status code esperado.
    - Comprobar que los módulos principales se importan correctamente.
    - Asegurar que el parser acepta pseudocódigo básico.
    - Verificar que el analyzer produce algún resultado.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


# ═══════════════════════════════════════════════════════════════════════════════
#  SMOKE: Aplicación & Módulos
# ═══════════════════════════════════════════════════════════════════════════════

class TestAppSmoke:
    """Verifica que la aplicación y módulos principales arrancan."""

    def test_app_starts(self, client):
        """La aplicación FastAPI debe iniciar sin errores."""
        assert client is not None

    def test_root_responds(self, client):
        """GET / debe responder."""
        resp = client.get("/")
        assert resp.status_code == 200

    def test_health_responds(self, client):
        """GET /api/v1/health debe responder."""
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200

    def test_openapi_schema_available(self, client):
        """OpenAPI schema debe estar disponible en modo debug."""
        resp = client.get("/openapi.json")
        # En producción puede devolver 404, en dev 200
        assert resp.status_code in (200, 404)
        if resp.status_code == 200:
            schema = resp.json()
            assert "paths" in schema
            assert "info" in schema


class TestModulesSmoke:
    """Verifica que los módulos principales se importan sin error."""

    def test_import_parser(self):
        from app.core.parser import PseudocodeParser, parse_pseudocode
        assert PseudocodeParser is not None
        assert callable(parse_pseudocode)

    def test_import_analyzer(self):
        from app.core.analyzer import AnalyzerEngine, AnalysisResult
        assert AnalyzerEngine is not None
        assert AnalysisResult is not None

    def test_import_patterns(self):
        from app.core.patterns import PatternDetector, PatternType
        assert PatternDetector is not None
        assert PatternType is not None

    def test_import_data_structures(self):
        from app.core.data_structures import StructureIdentifier, StructureType
        assert StructureIdentifier is not None
        assert StructureType is not None

    def test_import_visualization(self):
        from app.core.visualization import (
            TreeBuilder, RecursionTreeGenerator,
            GraphGenerator, DiagramRenderer,
        )
        assert TreeBuilder is not None
        assert RecursionTreeGenerator is not None

    def test_import_services(self):
        from app.services import (
            AlgorithmService, AnalysisOrchestrator,
            ValidationService, ExportService,
        )
        assert AlgorithmService is not None
        assert AnalysisOrchestrator is not None

    def test_import_schemas(self):
        from app.schemas import (
            CompleteAnalysisResult, AlgorithmCreate,
            PatternDetectionResult, ExportRequest,
        )
        assert CompleteAnalysisResult is not None

    def test_import_config(self):
        from app.core.config import settings
        assert settings is not None
        assert settings.APP_NAME is not None

    def test_import_exceptions(self):
        from app.core.exceptions import (
            ComplexityAnalyzerException, ParserException,
            LLMException, DatabaseException,
        )
        assert ComplexityAnalyzerException is not None

    def test_import_profiling(self):
        from app.profiling import (
            enable_profiling, disable_profiling,
            get_performance_monitor,
        )
        assert callable(enable_profiling)
        assert callable(disable_profiling)


# ═══════════════════════════════════════════════════════════════════════════════
#  SMOKE: Endpoints — cada uno debe responder (sin 500)
# ═══════════════════════════════════════════════════════════════════════════════

SIMPLE_CODE = """algorithm test(n)
begin
    x ← 1
end"""

LOOP_CODE = """algorithm loop(n)
begin
    for i ← 1 to n do
    begin
        x ← i
    end
end"""

RECURSIVE_CODE = """algorithm factorial(n)
begin
    if (n <= 1) then
    begin
        return 1
    end
    return n * factorial(n - 1)
end"""


class TestEndpointsSmoke:
    """Cada endpoint principal debe devolver algo distinto de 500."""

    def test_analysis_complete_responds(self, client):
        resp = client.post(
            "/api/v1/analysis/analyze-complete",
            json={"code": LOOP_CODE},
        )
        assert resp.status_code != 500, f"Endpoint falló: {resp.text[:300]}"

    def test_analysis_quick_responds(self, client):
        resp = client.post(
            "/api/v1/analysis/quick",
            json={"code": SIMPLE_CODE},
        )
        assert resp.status_code != 500

    def test_patterns_detect_responds(self, client):
        resp = client.post(
            "/api/v1/patterns/detect",
            json={"code": LOOP_CODE},
        )
        assert resp.status_code != 500

    def test_patterns_available_responds(self, client):
        resp = client.get("/api/v1/patterns/available")
        assert resp.status_code == 200

    def test_patterns_types_responds(self, client):
        resp = client.get("/api/v1/patterns/types")
        assert resp.status_code == 200

    def test_structures_detect_responds(self, client):
        resp = client.post(
            "/api/v1/structures/detect",
            json={"code": LOOP_CODE},
        )
        assert resp.status_code != 500

    def test_structures_available_responds(self, client):
        resp = client.get("/api/v1/structures/available")
        assert resp.status_code == 200

    def test_structures_types_responds(self, client):
        resp = client.get("/api/v1/structures/types")
        assert resp.status_code == 200

    def test_validation_responds(self, client):
        resp = client.post(
            "/api/v1/validation/validate",
            json={"code": SIMPLE_CODE, "level": "syntax"},
        )
        assert resp.status_code != 500

    def test_validation_quick_responds(self, client):
        resp = client.post(
            "/api/v1/validation/validate/quick",
            json={"code": SIMPLE_CODE},
        )
        assert resp.status_code in (200, 404, 405)

    def test_export_formats_responds(self, client):
        resp = client.get("/api/v1/export/formats")
        assert resp.status_code == 200

    def test_export_responds(self, client):
        resp = client.post(
            "/api/v1/export/export",
            json={
                "code": SIMPLE_CODE,
                "algorithm_name": "Smoke Test",
                "options": {
                    "format": "json",
                    "template": "minimal",
                    "sections": ["algorithm_info"],
                },
            },
        )
        assert resp.status_code != 500

    def test_visualization_formats_responds(self, client):
        resp = client.get("/api/v1/visualizations/formats")
        assert resp.status_code == 200

    def test_visualization_layouts_responds(self, client):
        resp = client.get("/api/v1/visualizations/layouts")
        assert resp.status_code == 200

    def test_visualization_recursion_tree_responds(self, client):
        resp = client.post(
            "/api/v1/visualizations/recursion-tree",
            json={"code": RECURSIVE_CODE, "max_depth": 3},
        )
        assert resp.status_code != 500

    def test_visualization_execution_flow_responds(self, client):
        resp = client.post(
            "/api/v1/visualizations/execution-flow",
            json={"code": LOOP_CODE},
        )
        assert resp.status_code != 500


# ═══════════════════════════════════════════════════════════════════════════════
#  SMOKE: Parser básico
# ═══════════════════════════════════════════════════════════════════════════════

class TestParserSmoke:
    """Verifica que el parser funciona con inputs básicos."""

    def test_parser_creates_instance(self):
        from app.core.parser import PseudocodeParser
        parser = PseudocodeParser()
        assert parser is not None

    def test_parser_parses_simple_code(self):
        from app.core.parser import parse_pseudocode
        ast = parse_pseudocode(SIMPLE_CODE)
        assert ast is not None
        assert ast.algorithm is not None
        assert ast.algorithm.name == "test"

    def test_parser_parses_loop(self):
        from app.core.parser import parse_pseudocode
        ast = parse_pseudocode(LOOP_CODE)
        assert ast is not None
        assert ast.algorithm.name == "loop"

    def test_parser_parses_recursive(self):
        from app.core.parser import parse_pseudocode
        ast = parse_pseudocode(RECURSIVE_CODE)
        assert ast is not None
        assert ast.algorithm.name == "factorial"


# ═══════════════════════════════════════════════════════════════════════════════
#  SMOKE: Analyzer básico
# ═══════════════════════════════════════════════════════════════════════════════

class TestAnalyzerSmoke:
    """Verifica que el analyzer produce resultados sin error."""

    def test_analyzer_produces_result(self):
        from app.core.analyzer import AnalyzerEngine
        from app.core.parser import parse_pseudocode

        ast = parse_pseudocode(LOOP_CODE)
        engine = AnalyzerEngine()
        result = engine.analyze(ast)

        assert result is not None
        assert result.big_o is not None
        assert result.omega is not None
        assert result.algorithm_name == "loop"

    def test_analyzer_analyze_from_code(self):
        from app.core.analyzer import AnalyzerEngine

        engine = AnalyzerEngine()
        result = engine.analyze_from_code(SIMPLE_CODE)
        assert result is not None
        assert result.big_o is not None
