"""
Tests de Integración - API REST Endpoints

Verifica que todos los endpoints de la API funcionen correctamente
con integración completa del sistema.

Endpoints testeados:
- POST /api/v1/algorithms - Crear algoritmo
- GET /api/v1/algorithms/{id} - Obtener algoritmo
- PUT /api/v1/algorithms/{id} - Actualizar algoritmo
- DELETE /api/v1/algorithms/{id} - Eliminar algoritmo
- GET /api/v1/algorithms - Listar algoritmos
- POST /api/v1/analysis/analyze-complete - Análisis completo
- POST /api/v1/patterns/detect - Detectar patrones
- POST /api/v1/structures/detect - Detectar estructuras
- POST /api/v1/export - Exportar resultados
- POST /api/v1/validation/validate - Validar código
"""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path

from app.main import app
from app.schemas import (
    AlgorithmCategory,
    ExportFormat,
    ValidationLevel,
)

# FIXTURES
@pytest.fixture
def client():
    """Cliente de test para FastAPI"""
    return TestClient(app)

@pytest.fixture
def bubble_sort_payload():
    """Payload de Bubble Sort"""
    return {
        "code": """algorithm bubbleSort(A[n])
begin
    for i ← 1 to n-1 do
        for j ← 1 to n-i do
            if A[j] > A[j+1] then
                temp ← A[j]
                A[j] ← A[j+1]
                A[j+1] ← temp
            end
        end
    end
end""",
        "name": "Bubble Sort",
        "category": "sorting",
        "tags": ["sorting", "quadratic"]
    }

@pytest.fixture
def fibonacci_payload():
    """Payload de Fibonacci"""
    return {
        "code": """algorithm fibonacci(n)
begin
    if n <= 1 then
        return n
    end
    return fibonacci(n - 1) + fibonacci(n - 2)
end""",
        "name": "Fibonacci",
        "category": "recursion",
        "tags": ["recursive", "exponential"]
    }

@pytest.fixture
def binary_search_payload():
    """Payload de búsqueda binaria"""
    return {
        "code": """algorithm binarySearch(A[n], target, low, high)
begin
    if low > high then
        return -1
    end
    
    mid ← floor((low + high) / 2)
    
    if A[mid] = target then
        return mid
    end
    
    if A[mid] > target then
        return binarySearch(A, target, low, mid - 1)
    else
        return binarySearch(A, target, mid + 1, high)
    end
end""",
        "name": "Binary Search",
        "category": "searching",
        "tags": ["search", "divide-conquer"]
    }

# TESTS: Root y Health Check
class TestRootEndpoints:
    """Tests de endpoints básicos"""
    
    def test_root_endpoint(self, client):
        """GET / debe retornar información de la API"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "status" in data
        assert data["status"] == "running"
    
    def test_health_check(self, client):
        """GET /api/v1/health debe retornar estado del sistema"""
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "ok"]

# TESTS: Algorithms Endpoints (CRUD)
class TestAlgorithmsEndpoints:
    """Tests de endpoints de algoritmos"""
    
    def test_create_algorithm(self, client, bubble_sort_payload):
        """POST /api/v1/algorithms debe crear algoritmo"""
        response = client.post("/api/v1/algorithms", json=bubble_sort_payload)
        
        assert response.status_code == 201 or response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "id" in data["data"]
        assert data["data"]["name"] == "Bubble Sort"
        assert data["data"]["category"] == "sorting"
        
        # Guardar ID para tests posteriores
        return data["data"]["id"]
    
    def test_create_algorithm_validates_syntax(self, client):
        """POST /api/v1/algorithms debe validar sintaxis"""
        invalid_payload = {
            "code": "algorithm invalid(n)\nbegin\n  x ← \nend",
            "name": "Invalid",
            "category": "other"
        }
        
        response = client.post("/api/v1/algorithms", json=invalid_payload)
        
        # Debe rechazar con 400 Bad Request
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "error" in data
    
    def test_get_algorithm(self, client, bubble_sort_payload):
        """GET /api/v1/algorithms/{id} debe retornar algoritmo"""
        # Crear algoritmo primero
        create_response = client.post("/api/v1/algorithms", json=bubble_sort_payload)
        algorithm_id = create_response.json()["data"]["id"]
        
        # Obtener algoritmo
        response = client.get(f"/api/v1/algorithms/{algorithm_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == algorithm_id
        assert data["data"]["name"] == "Bubble Sort"
    
    def test_get_nonexistent_algorithm(self, client):
        """GET /api/v1/algorithms/{id} debe retornar 404 si no existe"""
        response = client.get("/api/v1/algorithms/nonexistent-id-123")
        
        assert response.status_code == 404
    
    def test_update_algorithm(self, client, bubble_sort_payload, fibonacci_payload):
        """PUT /api/v1/algorithms/{id} debe actualizar algoritmo"""
        # Crear algoritmo
        create_response = client.post("/api/v1/algorithms", json=bubble_sort_payload)
        algorithm_id = create_response.json()["data"]["id"]
        
        # Actualizar con código diferente
        update_payload = {
            "code": fibonacci_payload["code"],
            "name": "Fibonacci Updated",
            "tags": ["recursive", "exponential", "updated"]
        }
        
        response = client.put(
            f"/api/v1/algorithms/{algorithm_id}",
            json=update_payload
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "Fibonacci Updated"
        assert "updated" in data["data"]["tags"]
    
    def test_delete_algorithm(self, client, bubble_sort_payload):
        """DELETE /api/v1/algorithms/{id} debe eliminar algoritmo"""
        # Crear algoritmo
        create_response = client.post("/api/v1/algorithms", json=bubble_sort_payload)
        algorithm_id = create_response.json()["data"]["id"]
        
        # Eliminar
        response = client.delete(f"/api/v1/algorithms/{algorithm_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # Verificar que ya no existe
        get_response = client.get(f"/api/v1/algorithms/{algorithm_id}")
        assert get_response.status_code == 404
    
    def test_list_algorithms(self, client, bubble_sort_payload, fibonacci_payload):
        """GET /api/v1/algorithms debe listar algoritmos"""
        # Crear varios algoritmos
        client.post("/api/v1/algorithms", json=bubble_sort_payload)
        client.post("/api/v1/algorithms", json=fibonacci_payload)
        
        # Listar
        response = client.get("/api/v1/algorithms")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)
        assert len(data["data"]) >= 2
    
    def test_search_algorithms_by_category(
        self,
        client,
        bubble_sort_payload,
        fibonacci_payload
    ):
        """GET /api/v1/algorithms?category=sorting debe filtrar"""
        # Crear algoritmos
        client.post("/api/v1/algorithms", json=bubble_sort_payload)
        client.post("/api/v1/algorithms", json=fibonacci_payload)
        
        # Buscar solo sorting
        response = client.get("/api/v1/algorithms?category=sorting")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # Verificar que solo hay sorting
        for algo in data["data"]:
            assert algo["category"] == "sorting"

# TESTS: Analysis Endpoints
class TestAnalysisEndpoints:
    """Tests de endpoints de análisis"""
    
    def test_analyze_complete(self, client, bubble_sort_payload):
        """POST /api/v1/analysis/analyze-complete debe analizar completamente"""
        payload = {
            "code": bubble_sort_payload["code"],
            "analyze_complexity": True,
            "analyze_patterns": True,
            "analyze_structures": True,
            "generate_visualizations": True
        }
        
        response = client.post("/api/v1/analysis/analyze-complete", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "algorithm_name" in data["data"]
        assert data["data"]["algorithm_name"] == "bubbleSort"
        
        # Verificar resultados de complejidad
        assert "big_o" in data["data"]
        assert data["data"]["big_o"] == "O(n^2)"
        
        # Verificar patrones
        if "patterns" in data["data"]:
            assert isinstance(data["data"]["patterns"], dict)
        
        # Verificar estructuras
        if "structures" in data["data"]:
            assert isinstance(data["data"]["structures"], dict)
    
    def test_analyze_quick(self, client, fibonacci_payload):
        """POST /api/v1/analysis/quick debe hacer análisis rápido"""
        payload = {
            "code": fibonacci_payload["code"]
        }
        
        response = client.post("/api/v1/analysis/quick", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "big_o" in data["data"]
        # Fibonacci es exponencial
        assert "2^n" in data["data"]["big_o"] or "exponential" in data["data"]["big_o"].lower()
    
    def test_analyze_line_by_line(self, client, binary_search_payload):
        """POST /api/v1/analysis/line-by-line debe analizar línea por línea"""
        payload = {
            "code": binary_search_payload["code"]
        }
        
        response = client.post("/api/v1/analysis/line-by-line", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "lines" in data["data"]
        assert isinstance(data["data"]["lines"], list)
        assert len(data["data"]["lines"]) > 0

# TESTS: Patterns Endpoints
class TestPatternsEndpoints:
    """Tests de endpoints de detección de patrones"""
    
    def test_detect_patterns(self, client, bubble_sort_payload):
        """POST /api/v1/patterns/detect debe detectar patrones"""
        payload = {
            "code": bubble_sort_payload["code"],
            "min_confidence": 0.3
        }
        
        response = client.post("/api/v1/patterns/detect", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "patterns_found" in data["data"]
        assert len(data["data"]["patterns_found"]) > 0
        
        # Debe detectar fuerza bruta por loops anidados
        pattern_names = [p["pattern_name"] for p in data["data"]["patterns_found"]]
        assert any("brute" in name.lower() or "fuerza" in name.lower() 
                  for name in pattern_names)
    
    def test_detect_specific_pattern(self, client, fibonacci_payload):
        """POST /api/v1/patterns/detect-specific debe detectar patrón específico"""
        payload = {
            "code": fibonacci_payload["code"],
            "pattern_type": "recursive"
        }
        
        response = client.post("/api/v1/patterns/detect-specific", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # Fibonacci es recursivo
        if data["data"]:
            assert data["data"]["pattern_type"] == "recursive"
            assert data["data"]["confidence"] >= 0.5
    
    def test_list_available_patterns(self, client):
        """GET /api/v1/patterns/available debe listar patrones"""
        response = client.get("/api/v1/patterns/available")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert len(data["data"]) > 0
        
        # Verificar que incluye patrones conocidos
        pattern_types = [p["type"] for p in data["data"]]
        assert "recursive" in pattern_types
        assert "divide_and_conquer" in pattern_types

# TESTS: Structures Endpoints
class TestStructuresEndpoints:
    """Tests de endpoints de detección de estructuras"""
    
    def test_detect_structures(self, client, bubble_sort_payload):
        """POST /api/v1/structures/detect debe detectar estructuras"""
        payload = {
            "code": bubble_sort_payload["code"],
            "min_confidence": 0.3
        }
        
        response = client.post("/api/v1/structures/detect", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "structures_found" in data["data"]
        assert len(data["data"]["structures_found"]) > 0
        
        # Debe detectar array
        structure_names = [s["structure_name"] for s in data["data"]["structures_found"]]
        assert any("array" in name.lower() or "lista" in name.lower() 
                  for name in structure_names)
    
    def test_list_available_structures(self, client):
        """GET /api/v1/structures/available debe listar estructuras"""
        response = client.get("/api/v1/structures/available")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert len(data["data"]) > 0

# TESTS: Validation Endpoints
class TestValidationEndpoints:
    """Tests de endpoints de validación"""
    
    def test_validate_code_syntax_only(self, client, bubble_sort_payload):
        """POST /api/v1/validation/validate con level=syntax"""
        payload = {
            "code": bubble_sort_payload["code"],
            "level": "syntax"
        }
        
        response = client.post("/api/v1/validation/validate", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["is_valid"] is True
        assert data["data"]["syntax_valid"] is True
    
    def test_validate_code_complete(self, client, fibonacci_payload):
        """POST /api/v1/validation/validate con level=complete"""
        payload = {
            "code": fibonacci_payload["code"],
            "level": "complete"
        }
        
        response = client.post("/api/v1/validation/validate", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["is_valid"] is True
        assert data["data"]["syntax_valid"] is True
        assert data["data"]["semantic_valid"] is True
    
    def test_validate_invalid_code(self, client):
        """POST /api/v1/validation/validate debe detectar errores"""
        payload = {
            "code": "algorithm invalid(n)\nbegin\n  x ← \nend",
            "level": "syntax"
        }
        
        response = client.post("/api/v1/validation/validate", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["is_valid"] is False
        assert len(data["data"]["errors"]) > 0

# TESTS: Export Endpoints
class TestExportEndpoints:
    """Tests de endpoints de exportación"""
    
    def test_export_to_json(self, client, bubble_sort_payload):
        """POST /api/v1/export debe exportar a JSON"""
        # Primero analizar
        analysis_payload = {
            "code": bubble_sort_payload["code"],
            "analyze_complexity": True
        }
        analysis_response = client.post(
            "/api/v1/analysis/analyze-complete",
            json=analysis_payload
        )
        analysis_data = analysis_response.json()["data"]
        
        # Exportar
        export_payload = {
            "data": analysis_data,
            "format": "json",
            "include_visualizations": False
        }
        
        response = client.post("/api/v1/export", json=export_payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "output_path" in data["data"] or "content" in data["data"]
    
    def test_export_to_markdown(self, client, fibonacci_payload):
        """POST /api/v1/export debe exportar a Markdown"""
        # Analizar
        analysis_payload = {
            "code": fibonacci_payload["code"],
            "analyze_complexity": True
        }
        analysis_response = client.post(
            "/api/v1/analysis/analyze-complete",
            json=analysis_payload
        )
        analysis_data = analysis_response.json()["data"]
        
        # Exportar
        export_payload = {
            "data": analysis_data,
            "format": "markdown"
        }
        
        response = client.post("/api/v1/export", json=export_payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

# TESTS: Visualizations Endpoints
class TestVisualizationsEndpoints:
    """Tests de endpoints de visualización"""
    
    def test_generate_recursion_tree(self, client, fibonacci_payload):
        """POST /api/v1/visualizations/recursion-tree debe generar árbol"""
        payload = {
            "code": fibonacci_payload["code"],
            "start_value": 5,
            "max_depth": 6
        }
        
        response = client.post(
            "/api/v1/visualizations/recursion-tree",
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "tree" in data["data"] or "svg" in data["data"]
    
    def test_generate_execution_flow(self, client, binary_search_payload):
        """POST /api/v1/visualizations/execution-flow debe generar flujo"""
        payload = {
            "code": binary_search_payload["code"]
        }
        
        response = client.post(
            "/api/v1/visualizations/execution-flow",
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

# TESTS: Error Handling
class TestErrorHandling:
    """Tests de manejo de errores"""
    
    def test_invalid_json_payload(self, client):
        """Endpoint debe rechazar JSON inválido"""
        response = client.post(
            "/api/v1/algorithms",
            data="invalid json{",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    def test_missing_required_fields(self, client):
        """Endpoint debe rechazar campos faltantes"""
        payload = {
            "code": "algorithm test(n)\nbegin\nend"
            # Falta 'name' que es requerido
        }
        
        response = client.post("/api/v1/algorithms", json=payload)
        
        assert response.status_code == 422
    
    def test_invalid_enum_value(self, client):
        """Endpoint debe rechazar valores enum inválidos"""
        payload = {
            "code": "algorithm test(n)\nbegin\nend",
            "name": "Test",
            "category": "invalid_category"  # Categoría no válida
        }
        
        response = client.post("/api/v1/algorithms", json=payload)
        
        # Puede ser 422 (validation error) o 400 (bad request)
        assert response.status_code in [400, 422]

# CONFIGURACIÓN PYTEST
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])