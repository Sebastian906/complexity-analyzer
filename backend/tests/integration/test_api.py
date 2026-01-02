"""
Tests de Integración de la API

Tests que verifican el funcionamiento completo de los endpoints.
NOTA: Los endpoints de health y algorithms están pendientes de implementación.
      Solo se prueban los endpoints actualmente disponibles.
"""

import pytest
from fastapi import status


class TestAnalysisEndpoints:
    """Tests de endpoints de análisis"""
    
    def test_analyze_basic(self, client, simple_algorithm):
        """Test: Endpoint de análisis básico"""
        response = client.post(
            "/api/v1/analysis/analyze",
            json={
                "code": simple_algorithm,
                "analyze_temporal": True,
                "analyze_spatial": True
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "success" in data
        assert "algorithm_name" in data
        assert "message" in data
    
    def test_analyze_placeholder_message(self, client, simple_algorithm):
        """Test: Endpoint de análisis retorna mensaje de placeholder"""
        response = client.post(
            "/api/v1/analysis/analyze",
            json={
                "code": simple_algorithm,
                "analyze_temporal": True,
                "analyze_spatial": True
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Por ahora debe retornar un placeholder
        assert data["success"] is False
        assert "MÓDULO 2" in data["message"]
    
    def test_analyze_with_only_temporal(self, client, simple_algorithm):
        """Test: Análisis solo temporal"""
        response = client.post(
            "/api/v1/analysis/analyze",
            json={
                "code": simple_algorithm,
                "analyze_temporal": True,
                "analyze_spatial": False
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_analyze_with_only_spatial(self, client, simple_algorithm):
        """Test: Análisis solo espacial"""
        response = client.post(
            "/api/v1/analysis/analyze",
            json={
                "code": simple_algorithm,
                "analyze_temporal": False,
                "analyze_spatial": True
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_analyze_response_structure(self, client, simple_algorithm):
        """Test: Estructura de la respuesta de análisis"""
        response = client.post(
            "/api/v1/analysis/analyze",
            json={
                "code": simple_algorithm,
                "analyze_temporal": True,
                "analyze_spatial": True
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Verificar campos esperados
        assert "success" in data
        assert "algorithm_name" in data
        assert "big_o" in data
        assert "omega" in data
        assert "theta" in data
        assert "message" in data
    
    def test_analyze_missing_code(self, client):
        """Test: Error al no enviar código"""
        response = client.post(
            "/api/v1/analysis/analyze",
            json={
                "analyze_temporal": True,
                "analyze_spatial": True
            }
        )
        
        # Pydantic debe rechazar la request
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    
    def test_analyze_empty_body(self, client):
        """Test: Error al enviar body vacío"""
        response = client.post("/api/v1/analysis/analyze")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


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
        
        assert "/api/v1/analysis/analyze" in schema["paths"]
    
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
        response = client.get("/api/v1/analysis/analyze")
        
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    
    def test_422_validation_error(self, client):
        """Test: Error de validación de datos"""
        # POST sin body
        response = client.post("/api/v1/analysis/analyze")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        data = response.json()
        
        # La API usa formato personalizado con 'error' en lugar de 'detail'
        assert "error" in data or "detail" in data


class TestCORS:
    """Tests de CORS"""
    
    def test_cors_preflight_analysis(self, client):
        """Test: Preflight CORS en endpoint de análisis"""
        response = client.options(
            "/api/v1/analysis/analyze",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST"
            }
        )
        
        # CORS middleware debe responder
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT]


class TestRootEndpoint:
    """Tests del endpoint raíz"""
    
    def test_root_endpoint(self, client):
        """Test: Endpoint raíz accesible"""
        response = client.get("/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "message" in data or "name" in data or "status" in data


# Tests pendientes para cuando se implementen los módulos
class TestPendingEndpoints:
    """
    Tests marcados como skip para endpoints pendientes de implementación.
    Estos tests se activarán cuando se implementen los módulos correspondientes.
    """
    
    @pytest.mark.skip(reason="Endpoint /health no implementado - Módulo pendiente")
    def test_health_check(self, client):
        """Test: Health check básico"""
        response = client.get("/api/v1/health/")
        assert response.status_code == status.HTTP_200_OK
    
    @pytest.mark.skip(reason="Endpoint /algorithms/parse no implementado - Módulo pendiente")
    def test_parse_algorithm(self, client, simple_algorithm):
        """Test: Parsear algoritmo"""
        response = client.post(
            "/api/v1/algorithms/parse",
            json={"code": simple_algorithm, "validate": True}
        )
        assert response.status_code == status.HTTP_200_OK
    
    @pytest.mark.skip(reason="Endpoint /algorithms/examples no implementado - Módulo pendiente")
    def test_get_examples(self, client):
        """Test: Obtener ejemplos"""
        response = client.get("/api/v1/algorithms/examples")
        assert response.status_code == status.HTTP_200_OK
    
    @pytest.mark.skip(reason="Endpoint /algorithms/validate no implementado - Módulo pendiente")
    def test_validate_code(self, client, simple_algorithm):
        """Test: Validar código"""
        response = client.post(
            "/api/v1/algorithms/validate",
            json={"code": simple_algorithm}
        )
        assert response.status_code == status.HTTP_200_OK