"""
Contract Tests - API Response Schema Contracts

Verifica que cada endpoint de la API respete su contrato (schema) de respuesta.
No se prueba la lógica de negocio, sino que la ESTRUCTURA del JSON de respuesta
cumple exactamente con lo definido en los schemas Pydantic.

Objetivo:
    - Garantizar que los tipos de datos en las respuestas sean los correctos.
    - Verificar presencia de campos obligatorios.
    - Verificar que enums contengan valores válidos.
    - Detectar regresiones de contrato cuando se modifiquen schemas.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from app.main import app


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def client():
    """Cliente compartido por módulo para evitar recrear conexiones."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def bubble_sort_code():
    return """algorithm bubbleSort(A[1..n])
begin
    for i ← 1 to n - 1 do
    begin
        for j ← 1 to n - i do
        begin
            if (A[j] > A[j + 1]) then
            begin
                temp ← A[j]
                A[j] ← A[j + 1]
                A[j + 1] ← temp
            end
        end
    end
end"""


@pytest.fixture(scope="module")
def fibonacci_code():
    return """algorithm fibonacci(n)
begin
    if (n <= 1) then
    begin
        return n
    end
    return fibonacci(n - 1) + fibonacci(n - 2)
end"""


@pytest.fixture(scope="module")
def simple_code():
    return """algorithm simple(n)
begin
    x ← 1
end"""


# ─── Helper de validación ────────────────────────────────────────────────────

def assert_field_types(data: dict, schema: dict):
    """
    Verifica que cada campo en *schema* exista en *data* y sea del tipo esperado.

    schema ejemplo: {"success": bool, "algorithm_name": str, "complexity": dict}
    """
    for field, expected_type in schema.items():
        assert field in data, f"Campo faltante en respuesta: '{field}'"
        if expected_type is not None and data[field] is not None:
            assert isinstance(data[field], expected_type), (
                f"Campo '{field}': esperado {expected_type.__name__}, "
                f"recibido {type(data[field]).__name__} (valor={data[field]!r})"
            )


# ═══════════════════════════════════════════════════════════════════════════════
#  CONTRACT: Health
# ═══════════════════════════════════════════════════════════════════════════════

class TestHealthContract:
    """Contrato del endpoint GET /api/v1/health"""

    def test_health_response_contract(self, client):
        """El health check debe devolver los campos obligatorios con tipos correctos."""
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200

        data = resp.json()
        assert_field_types(data, {
            "success": bool,
            "status": str,
            "version": str,
            "environment": str,
            "features": dict,
        })

    def test_health_features_contract(self, client):
        """El sub-objeto 'features' debe tener las claves de módulos."""
        resp = client.get("/api/v1/health")
        features = resp.json()["features"]

        expected_keys = {"parser", "analyzer", "patterns", "visualization"}
        assert expected_keys.issubset(features.keys()), (
            f"Faltan claves de features: {expected_keys - features.keys()}"
        )
        for key in expected_keys:
            assert isinstance(features[key], bool), f"features.{key} debe ser bool"

    def test_health_status_valid_values(self, client):
        """El campo 'status' debe ser un valor conocido."""
        resp = client.get("/api/v1/health")
        assert resp.json()["status"] in ("healthy", "degraded", "unhealthy")


# ═══════════════════════════════════════════════════════════════════════════════
#  CONTRACT: Root
# ═══════════════════════════════════════════════════════════════════════════════

class TestRootContract:
    """Contrato del endpoint GET /"""

    def test_root_response_contract(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert_field_types(data, {
            "name": str,
            "version": str,
            "status": str,
        })
        assert "api" in data


# ═══════════════════════════════════════════════════════════════════════════════
#  CONTRACT: Complete Analysis
# ═══════════════════════════════════════════════════════════════════════════════

class TestAnalysisCompleteContract:
    """Contrato de POST /api/v1/analysis/analyze-complete"""

    def test_complete_analysis_response_contract(self, client, bubble_sort_code):
        """La respuesta de análisis completo debe contener los campos del schema."""
        resp = client.post(
            "/api/v1/analysis/analyze-complete",
            json={"code": bubble_sort_code},
        )
        assert resp.status_code == 200

        data = resp.json()
        # Campos obligatorios de CompleteAnalysisResult
        assert_field_types(data, {
            "success": bool,
            "algorithm_name": str,
            "complexity": dict,
        })

    def test_complexity_subschema(self, client, bubble_sort_code):
        """El objeto 'complexity' debe tener big_o, omega, theta."""
        resp = client.post(
            "/api/v1/analysis/analyze-complete",
            json={"code": bubble_sort_code},
        )
        complexity = resp.json()["complexity"]
        assert_field_types(complexity, {
            "big_o": str,
            "omega": str,
        })
        # theta puede ser None para algoritmos sin cota ajustada
        assert "theta" in complexity

    def test_big_o_format(self, client, bubble_sort_code):
        """big_o debe seguir notación O(...)."""
        resp = client.post(
            "/api/v1/analysis/analyze-complete",
            json={"code": bubble_sort_code},
        )
        big_o = resp.json()["complexity"]["big_o"]
        assert big_o.startswith("O(") or big_o.startswith("Θ("), (
            f"big_o no tiene formato esperado: {big_o}"
        )

    def test_line_by_line_contract(self, client, bubble_sort_code):
        """Si se pide line_by_line, debe ser lista o dict con estructura válida."""
        resp = client.post(
            "/api/v1/analysis/analyze-complete",
            json={
                "code": bubble_sort_code,
                "options": {"analyze_line_by_line": True},
            },
        )
        data = resp.json()
        if "line_by_line" in data and data["line_by_line"] is not None:
            lbl = data["line_by_line"]
            # Puede ser dict con 'lines' o directamente una lista
            if isinstance(lbl, dict):
                assert "lines" in lbl or "total_lines" in lbl
            elif isinstance(lbl, list):
                assert len(lbl) > 0

    def test_space_complexity_contract(self, client, bubble_sort_code):
        """space_complexity debe contener campos de espacio si está presente."""
        resp = client.post(
            "/api/v1/analysis/analyze-complete",
            json={
                "code": bubble_sort_code,
                "options": {"analyze_spatial": True},
            },
        )
        data = resp.json()
        if "space_complexity" in data and data["space_complexity"] is not None:
            space = data["space_complexity"]
            assert isinstance(space, dict)
            assert "total" in space or "input_space" in space


# ═══════════════════════════════════════════════════════════════════════════════
#  CONTRACT: Quick Analysis
# ═══════════════════════════════════════════════════════════════════════════════

class TestQuickAnalysisContract:
    """Contrato de POST /api/v1/analysis/quick"""

    def test_quick_analysis_response_contract(self, client, simple_code):
        resp = client.post("/api/v1/analysis/quick", params={"code": simple_code})
        assert resp.status_code == 200

        data = resp.json()
        assert_field_types(data, {
            "success": bool,
            "big_o": dict,
        })
        # big_o es un dict con la estructura del BigOAnalyzer
        big_o = data["big_o"]
        assert "complexity" in big_o, "big_o debe contener 'complexity'"
        assert "notation" in big_o, "big_o debe contener 'notation'"
        assert "explanation" in big_o, "big_o debe contener 'explanation'"
        assert "confidence" in big_o, "big_o debe contener 'confidence'"
        assert isinstance(big_o["complexity"], str)
        assert isinstance(big_o["confidence"], (int, float))


# ═══════════════════════════════════════════════════════════════════════════════
#  CONTRACT: Pattern Detection
# ═══════════════════════════════════════════════════════════════════════════════

class TestPatternDetectionContract:
    """Contrato de POST /api/v1/patterns/detect"""

    def test_pattern_detection_response_contract(self, client, bubble_sort_code):
        resp = client.post(
            "/api/v1/patterns/detect",
            json={"code": bubble_sort_code},
        )
        assert resp.status_code == 200

        data = resp.json()
        assert_field_types(data, {
            "patterns_found": list,
            "pattern_count": int,
        })

    def test_pattern_match_subschema(self, client, bubble_sort_code):
        """Cada patrón encontrado debe tener los campos requeridos."""
        resp = client.post(
            "/api/v1/patterns/detect",
            json={"code": bubble_sort_code},
        )
        patterns = resp.json()["patterns_found"]
        assert len(patterns) > 0

        for p in patterns:
            assert_field_types(p, {
                "pattern_type": str,
                "pattern_name": str,
                "confidence": (int, float),
                "confidence_level": str,
            })
            assert 0.0 <= p["confidence"] <= 1.0, (
                f"confidence fuera de rango: {p['confidence']}"
            )

    def test_pattern_confidence_level_enum(self, client, bubble_sort_code):
        """confidence_level debe ser un valor conocido del enum."""
        resp = client.post(
            "/api/v1/patterns/detect",
            json={"code": bubble_sort_code},
        )
        valid_levels = {"high", "medium", "low", "very_low", "very_high"}
        for p in resp.json()["patterns_found"]:
            assert p["confidence_level"] in valid_levels, (
                f"confidence_level inválido: {p['confidence_level']}"
            )

    def test_available_patterns_contract(self, client):
        """GET /api/v1/patterns/available debe listar con campos correctos."""
        resp = client.get("/api/v1/patterns/available")
        assert resp.status_code == 200
        data = resp.json()
        assert_field_types(data, {"success": bool, "data": list, "total": int})

        for item in data["data"]:
            assert "type" in item
            assert "name" in item


# ═══════════════════════════════════════════════════════════════════════════════
#  CONTRACT: Structure Detection
# ═══════════════════════════════════════════════════════════════════════════════

class TestStructureDetectionContract:
    """Contrato de POST /api/v1/structures/detect"""

    def test_structure_detection_response_contract(self, client, bubble_sort_code):
        resp = client.post(
            "/api/v1/structures/detect",
            json={"code": bubble_sort_code},
        )
        assert resp.status_code == 200

        data = resp.json()
        assert_field_types(data, {
            "structures_found": list,
            "summary": str,
        })

    def test_structure_match_subschema(self, client, bubble_sort_code):
        """Cada estructura encontrada debe tener campos requeridos."""
        resp = client.post(
            "/api/v1/structures/detect",
            json={"code": bubble_sort_code},
        )
        structures = resp.json()["structures_found"]
        assert len(structures) > 0

        for s in structures:
            assert_field_types(s, {
                "structure_type": str,
                "structure_name": str,
                "confidence": (int, float),
                "confidence_level": str,
            })

    def test_available_structures_contract(self, client):
        resp = client.get("/api/v1/structures/available")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)


# ═══════════════════════════════════════════════════════════════════════════════
#  CONTRACT: Validation
# ═══════════════════════════════════════════════════════════════════════════════

class TestValidationContract:
    """Contrato de POST /api/v1/validation/validate"""

    def test_validation_response_contract(self, client, bubble_sort_code):
        resp = client.post(
            "/api/v1/validation/validate",
            json={"code": bubble_sort_code, "level": "syntax"},
        )
        assert resp.status_code == 200

        data = resp.json()
        assert_field_types(data, {
            "success": bool,
            "is_valid": bool,
            "errors": list,
            "warnings": list,
            "error_count": int,
            "warning_count": int,
            "summary": str,
        })

    def test_validation_error_item_schema(self, client):
        """Cada error debe tener severity, message."""
        resp = client.post(
            "/api/v1/validation/validate",
            json={"code": "algorithm bad(\nbegin\nend", "level": "syntax"},
        )
        data = resp.json()
        assert data["is_valid"] is False
        assert len(data["errors"]) > 0

        for err in data["errors"]:
            assert "severity" in err
            assert "message" in err
            assert err["severity"] in ("error", "warning", "info", "hint")

    def test_validation_syntax_sub_object(self, client, bubble_sort_code):
        """El campo 'syntax' debe tener is_valid."""
        resp = client.post(
            "/api/v1/validation/validate",
            json={"code": bubble_sort_code, "level": "syntax"},
        )
        data = resp.json()
        assert "syntax" in data
        assert isinstance(data["syntax"], dict)
        assert "is_valid" in data["syntax"]


# ═══════════════════════════════════════════════════════════════════════════════
#  CONTRACT: Export
# ═══════════════════════════════════════════════════════════════════════════════

class TestExportContract:
    """Contrato de endpoints de exportación."""

    def test_export_formats_contract(self, client):
        """GET /api/v1/export/formats debe listar formatos."""
        resp = client.get("/api/v1/export/formats")
        assert resp.status_code == 200
        data = resp.json()
        assert_field_types(data, {
            "success": bool,
            "formats": list,
            "templates": list,
        })

    def test_export_result_contract(self, client, bubble_sort_code):
        """POST /api/v1/export/export con JSON debe devolver ExportResult."""
        resp = client.post(
            "/api/v1/export/export",
            json={
                "code": bubble_sort_code,
                "algorithm_name": "BubbleSort Contract",
                "options": {
                    "format": "json",
                    "template": "minimal",
                    "sections": ["algorithm_info", "complexity"],
                },
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert_field_types(data, {
            "success": bool,
            "format": str,
            "filename": str,
        })


# ═══════════════════════════════════════════════════════════════════════════════
#  CONTRACT: Visualization
# ═══════════════════════════════════════════════════════════════════════════════

class TestVisualizationContract:
    """Contrato de endpoints de visualización."""

    def test_visualization_formats_contract(self, client):
        """GET /api/v1/visualizations/formats debe listar formatos."""
        resp = client.get("/api/v1/visualizations/formats")
        assert resp.status_code == 200
        data = resp.json()
        assert "formats" in data
        assert isinstance(data["formats"], list)
        assert len(data["formats"]) > 0

        for fmt in data["formats"]:
            assert_field_types(fmt, {
                "format": str,
                "name": str,
                "description": str,
            })

    def test_visualization_layouts_contract(self, client):
        """GET /api/v1/visualizations/layouts debe listar layouts."""
        resp = client.get("/api/v1/visualizations/layouts")
        assert resp.status_code == 200
        data = resp.json()
        assert "layouts" in data
        for layout in data["layouts"]:
            assert "type" in layout
            assert "name" in layout

    def test_recursion_tree_response_contract(self, client, fibonacci_code):
        """POST recursion-tree debe retornar VisualizationResult."""
        resp = client.post(
            "/api/v1/visualizations/recursion-tree",
            json={"code": fibonacci_code, "max_depth": 3},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert_field_types(data, {
            "type": str,
            "format": str,
        })
        # Debe tener contenido o error
        assert "content" in data or "error" in data
