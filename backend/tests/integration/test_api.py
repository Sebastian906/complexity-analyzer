"""
Tests de Integración de la API

Tests que verifican el funcionamiento completo de los endpoints.
"""

import pytest
from fastapi import status


class TestAnalysisEndpoints:
    """Tests de endpoints de análisis"""
    
    def test_analyze_complete_basic(self, client, simple_algorithm):
        """Test: Endpoint de análisis completo básico"""
        response = client.post(
            "/api/v1/analysis/analyze-complete",
            json={
                "code": simple_algorithm,
                "options": {
                    "analyze_line_by_line": True,
                    "analyze_spatial": True,
                    "analyze_recurrence": True,
                    "calculate_tight_bounds": True
                }
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["success"] is True
        assert "algorithm_name" in data
        assert "complexity" in data
    
    def test_analyze_complete_success(self, client, simple_algorithm):
        """Test: Endpoint de análisis retorna análisis completo exitoso"""
        response = client.post(
            "/api/v1/analysis/analyze-complete",
            json={
                "code": simple_algorithm,
                "options": {
                    "analyze_line_by_line": True,
                    "analyze_spatial": True,
                    "analyze_recurrence": True,
                    "calculate_tight_bounds": True
                }
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Verificar análisis exitoso
        assert data["success"] is True
        assert "completado" in data["message"].lower() or "exitosamente" in data["message"].lower()
    
    def test_analyze_with_minimal_options(self, client, simple_algorithm):
        """Test: Análisis con opciones mínimas"""
        response = client.post(
            "/api/v1/analysis/analyze-complete",
            json={
                "code": simple_algorithm,
                "options": {
                    "analyze_line_by_line": False,
                    "analyze_spatial": False,
                    "analyze_recurrence": False,
                    "calculate_tight_bounds": False
                }
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
    
    def test_analyze_without_options(self, client, simple_algorithm):
        """Test: Análisis sin especificar opciones (usa defaults)"""
        response = client.post(
            "/api/v1/analysis/analyze-complete",
            json={
                "code": simple_algorithm
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
    
    def test_analyze_response_structure(self, client, simple_algorithm):
        """Test: Estructura de la respuesta de análisis"""
        response = client.post(
            "/api/v1/analysis/analyze-complete",
            json={
                "code": simple_algorithm,
                "options": {
                    "analyze_line_by_line": True,
                    "analyze_spatial": True,
                    "analyze_recurrence": True,
                    "calculate_tight_bounds": True
                }
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Verificar campos principales según CompleteAnalysisResult
        assert "success" in data
        assert "message" in data
        assert "timestamp" in data
        assert "algorithm_name" in data
        assert "algorithm_info" in data
        assert "complexity" in data
        assert "metadata" in data
        assert "summary" in data
        
        # Verificar estructura de complexity
        complexity = data["complexity"]
        assert "big_o" in complexity
        assert "omega" in complexity
        assert "theta" in complexity
        assert "big_o_class" in complexity
        
        # Verificar estructura de space_complexity si está presente
        if data.get("space_complexity"):
            space = data["space_complexity"]
            assert "total" in space
            assert "input_space" in space
            assert "auxiliary_space" in space
    
    def test_analyze_missing_code(self, client):
        """Test: Error al no enviar código"""
        response = client.post(
            "/api/v1/analysis/analyze-complete",
            json={
                "options": {
                    "analyze_line_by_line": True
                }
            }
        )
        
        # Pydantic debe rechazar la request
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_analyze_empty_code(self, client):
        """Test: Error al enviar código vacío"""
        response = client.post(
            "/api/v1/analysis/analyze-complete",
            json={
                "code": ""
            }
        )
        
        # Debe fallar en validación o análisis
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_500_INTERNAL_SERVER_ERROR
        ]
    
    def test_analyze_invalid_code(self, client):
        """Test: Código con errores sintácticos"""
        response = client.post(
            "/api/v1/analysis/analyze-complete",
            json={
                "code": "algorithm invalid(n begin x ← 1 end"
            }
        )
        
        # Debe retornar error del parser
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_500_INTERNAL_SERVER_ERROR
        ]


class TestQuickAnalysisEndpoint:
    """Tests del endpoint de análisis rápido"""
    
    def test_quick_analysis(self, client, simple_algorithm):
        """Test: Análisis rápido básico"""
        import urllib.parse
        encoded_code = urllib.parse.quote(simple_algorithm, safe='')
        response = client.post(
            f"/api/v1/analysis/quick?code={encoded_code}"
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["success"] is True
        assert "big_o" in data
        assert "algorithm_name" in data


class TestLineByLineEndpoint:
    """Tests del endpoint de análisis línea por línea"""
    
    def test_line_by_line_analysis(self, client, simple_algorithm):
        """Test: Análisis línea por línea"""
        import urllib.parse
        encoded_code = urllib.parse.quote(simple_algorithm, safe='')
        response = client.post(
            f"/api/v1/analysis/line-by-line?code={encoded_code}"
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["success"] is True
        assert "lines" in data
        assert "total_lines" in data
        assert isinstance(data["lines"], list)


class TestHealthEndpoint:
    """Tests del endpoint de health"""
    
    def test_health_check(self, client):
        """Test: Health check básico"""
        response = client.get("/api/v1/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["success"] is True
        assert data["status"] == "healthy"
        assert "version" in data
        assert "features" in data
    
    def test_detailed_status(self, client):
        """Test: Estado detallado del sistema"""
        response = client.get("/api/v1/health/status")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "application" in data
        assert "services" in data
        assert "llms" in data


class TestAPIDocumentation:
    """Tests de documentación de la API"""
    
    def test_openapi_schema(self, client):
        """Test: Schema OpenAPI está disponible"""
        response = client.get("/openapi.json")
        
        assert response.status_code == status.HTTP_200_OK
        schema = response.json()
        
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema
    
    def test_openapi_has_analysis_endpoint(self, client):
        """Test: OpenAPI incluye endpoint de análisis"""
        response = client.get("/openapi.json")
        schema = response.json()
        
        assert "/api/v1/analysis/analyze-complete" in schema["paths"]
    
    def test_docs_available(self, client):
        """Test: Documentación Swagger disponible"""
        response = client.get("/docs")
        
        # Swagger retorna HTML
        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers["content-type"]
    
    def test_redoc_available(self, client):
        """Test: Documentación ReDoc disponible"""
        response = client.get("/redoc")
        
        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers["content-type"]


class TestErrorHandling:
    """Tests de manejo de errores"""
    
    def test_404_not_found(self, client):
        """Test: Endpoint no existente"""
        response = client.get("/api/v1/nonexistent")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_405_method_not_allowed(self, client):
        """Test: Método no permitido - GET en endpoint POST"""
        response = client.get("/api/v1/analysis/analyze-complete")
        
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    
    def test_422_validation_error(self, client):
        """Test: Error de validación de datos"""
        # POST sin body
        response = client.post("/api/v1/analysis/analyze-complete")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        
        # FastAPI validation error structure
        assert "detail" in data or "error" in data


class TestCORS:
    """Tests de CORS"""
    
    def test_cors_preflight_analysis(self, client):
        """Test: Preflight CORS en endpoint de análisis"""
        response = client.options(
            "/api/v1/analysis/analyze-complete",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST"
            }
        )
        
        # CORS middleware debe responder
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_204_NO_CONTENT
        ]


class TestRootEndpoint:
    """Tests del endpoint raíz"""
    
    def test_root_endpoint(self, client):
        """Test: Endpoint raíz accesible"""
        response = client.get("/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "name" in data or "status" in data
        assert data.get("status") == "running" or data.get("name") is not None


class TestComplexAlgorithms:
    """Tests con algoritmos más complejos"""
    
    def test_bubble_sort_analysis(self, client, bubble_sort_code):
        """Test: Análisis de bubble sort"""
        response = client.post(
            "/api/v1/analysis/analyze-complete",
            json={
                "code": bubble_sort_code,
                "options": {
                    "analyze_line_by_line": True,
                    "analyze_spatial": True
                }
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["success"] is True
        # Bubble sort debe ser O(n²)
        assert "n²" in data["complexity"]["big_o"] or "n^2" in data["complexity"]["big_o"]
    
    def test_fibonacci_analysis(self, client, fibonacci_code):
        """Test: Análisis de fibonacci recursivo"""
        response = client.post(
            "/api/v1/analysis/analyze-complete",
            json={
                "code": fibonacci_code,
                "options": {
                    "analyze_recurrence": True
                }
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["success"] is True
        assert data["algorithm_info"]["has_recursion"] is True


# Marcar todos los tests de esta suite como integración
pytestmark = pytest.mark.integration