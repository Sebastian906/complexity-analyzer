"""
Tests de Integración - Celery Workers

Verifica que el sistema de análisis asíncrono con Celery
funcione correctamente.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch

from app.infrastructure.tasks import (
    submit_analysis,
    submit_batch,
    get_task_status,
    is_celery_available,
)
from app.core.config import settings

@pytest.mark.integration
class TestCeleryAvailability:
    """Tests de disponibilidad de Celery"""
    
    def test_is_celery_available_respects_config(self, monkeypatch):
        """Test que respeta CELERY_ENABLED en settings"""
        # Simular Celery deshabilitado
        monkeypatch.setattr(settings, "CELERY_ENABLED", False)
        
        # Importar módulo de nuevo para que vea el nuevo valor
        from importlib import reload
        from app.infrastructure import tasks
        reload(tasks)
        
        available = tasks.is_celery_available()
        assert available is False
    
    def test_celery_available_when_configured(self):
        """Test disponibilidad cuando está configurado"""
        if not settings.CELERY_ENABLED:
            pytest.skip("Celery no habilitado en configuración")
        
        available = is_celery_available()
        
        # Si está habilitado, debe ser True o False según el worker
        assert isinstance(available, bool)

@pytest.mark.integration
class TestSubmitAnalysis:
    """Tests de submit_analysis (análisis individual)"""
    
    def test_submit_analysis_returns_none_when_celery_disabled(self, monkeypatch):
        """Test que retorna None cuando Celery no está disponible"""
        # Mock para que is_celery_available retorne False
        with patch('app.infrastructure.tasks.is_celery_available', return_value=False):
            request_data = {
                "code": "algorithm test(n) begin x <- 1 end",
                "analyze_complexity": True,
            }
            
            task_id = submit_analysis(request_data)
            
            assert task_id is None
    
    @pytest.mark.skipif(
        not settings.CELERY_ENABLED,
        reason="Celery no habilitado"
    )
    def test_submit_analysis_returns_task_id(self):
        """Test que retorna task_id cuando Celery está disponible"""
        if not is_celery_available():
            pytest.skip("Celery worker no está corriendo")
        
        request_data = {
            "code": "algorithm test(n) begin x <- 1 end",
            "analyze_complexity": True,
            "analyze_patterns": False,
            "analyze_structures": False,
            "generate_visualizations": False,
        }
        
        task_id = submit_analysis(request_data)
        
        # Debe retornar un task_id (string)
        assert task_id is not None
        assert isinstance(task_id, str)
        assert len(task_id) > 0
    
    @pytest.mark.skipif(
        not settings.CELERY_ENABLED,
        reason="Celery no habilitado"
    )
    def test_submit_analysis_task_can_be_queried(self):
        """Test que la tarea enviada puede consultarse"""
        if not is_celery_available():
            pytest.skip("Celery worker no disponible")
        
        request_data = {
            "code": """
algorithm bubbleSort(A[1..n])
begin
    for i ← 1 to n - 1 do
    begin
        for j ← 1 to n - i do
        begin
            if A[j] > A[j + 1] then
            begin
                swap(A[j], A[j + 1])
            end
        end
    end
end
""",
            "analyze_complexity": True,
            "analyze_patterns": True,
            "analyze_structures": False,
            "generate_visualizations": False,
        }
        
        task_id = submit_analysis(request_data)
        assert task_id is not None
        
        # Consultar estado inmediatamente (PENDING)
        status = get_task_status(task_id)
        
        assert "task_id" in status
        assert status["task_id"] == task_id
        assert "status" in status
        # Puede estar PENDING, STARTED, o SUCCESS si el worker es muy rápido
        assert status["status"] in ["PENDING", "STARTED", "SUCCESS"]

@pytest.mark.integration
class TestSubmitBatch:
    """Tests de submit_batch (análisis múltiple)"""
    
    def test_submit_batch_returns_none_when_celery_disabled(self):
        """Test que retorna None cuando Celery no está disponible"""
        with patch('app.infrastructure.tasks.is_celery_available', return_value=False):
            batch_data = [
                {"code": "algorithm test1(n) begin x <- 1 end", "name": "test1"},
                {"code": "algorithm test2(n) begin x <- 2 end", "name": "test2"},
            ]
            
            task_id = submit_batch(batch_data)
            
            assert task_id is None
    
    @pytest.mark.skipif(
        not settings.CELERY_ENABLED,
        reason="Celery no habilitado"
    )
    def test_submit_batch_returns_task_id(self):
        """Test que retorna task_id para batch"""
        if not is_celery_available():
            pytest.skip("Celery worker no disponible")
        
        batch_data = [
            {
                "code": "algorithm test1(n) begin x <- 1 end",
                "name": "test1",
                "options": {"analyze_complexity": True}
            },
            {
                "code": "algorithm test2(n) begin for i <- 1 to n do x <- x + 1 end end",
                "name": "test2",
                "options": {"analyze_complexity": True}
            },
        ]
        
        task_id = submit_batch(batch_data)
        
        assert task_id is not None
        assert isinstance(task_id, str)

@pytest.mark.integration
class TestGetTaskStatus:
    """Tests de get_task_status"""
    
    def test_get_task_status_when_celery_disabled(self):
        """Test estado cuando Celery no está disponible"""
        with patch('app.infrastructure.tasks.is_celery_available', return_value=False):
            status = get_task_status("fake-task-id")
            
            assert status["status"] == "unavailable"
            assert "error" in status
    
    @pytest.mark.skipif(
        not settings.CELERY_ENABLED,
        reason="Celery no habilitado"
    )
    def test_get_task_status_nonexistent_task(self):
        """Test estado de tarea inexistente"""
        if not is_celery_available():
            pytest.skip("Celery worker no disponible")
        
        status = get_task_status("nonexistent-task-id")
        
        # Debe retornar PENDING (estado por defecto para tareas desconocidas)
        assert status["status"] == "PENDING"
    
    @pytest.mark.skipif(
        not settings.CELERY_ENABLED,
        reason="Celery no habilitado"
    )
    def test_get_task_status_tracks_completion(self):
        """Test que el estado cambia a SUCCESS cuando completa"""
        if not is_celery_available():
            pytest.skip("Celery worker no disponible")
        
        # Enviar tarea simple
        request_data = {
            "code": "algorithm simple(n) begin x <- 1 end",
            "analyze_complexity": True,
            "analyze_patterns": False,
            "analyze_structures": False,
            "generate_visualizations": False,
        }
        
        task_id = submit_analysis(request_data)
        assert task_id is not None
        
        # Polling hasta que complete (máximo 30 segundos)
        max_wait = 30
        start = time.time()
        
        while time.time() - start < max_wait:
            status = get_task_status(task_id)
            
            if status["status"] == "SUCCESS":
                # Debe tener resultado
                assert "result" in status
                break
            elif status["status"] == "FAILURE":
                # Si falló, mostrar error
                pytest.fail(f"Task failed: {status.get('error')}")
            
            time.sleep(1)
        else:
            # Timeout
            final_status = get_task_status(task_id)
            pytest.fail(
                f"Task did not complete in {max_wait}s. "
                f"Final status: {final_status['status']}"
            )

@pytest.mark.integration
class TestCeleryEndpoints:
    """Tests de endpoints async de la API"""
    
    @pytest.fixture
    def client(self):
        """Cliente de prueba para FastAPI"""
        from fastapi.testclient import TestClient
        from app.main import app
        return TestClient(app)
    
    def test_async_endpoint_returns_202(self, client):
        """Test que endpoint async retorna 202 Accepted"""
        if not is_celery_available():
            pytest.skip("Celery no disponible")
        
        response = client.post(
            "/api/v1/analysis/async",
            json={
                "code": "algorithm test(n) begin x <- 1 end",
                "analyze_complexity": True,
            }
        )
        
        if response.status_code == 503:
            pytest.skip("Celery worker no disponible (503)")
        
        assert response.status_code == 202
        data = response.json()
        
        assert "task_id" in data
        assert "status" in data
        assert data["status"] == "submitted"
        assert "poll_url" in data
    
    def test_task_endpoint_returns_status(self, client):
        """Test que endpoint de tarea retorna estado"""
        if not is_celery_available():
            pytest.skip("Celery no disponible")
        
        # Primero enviar una tarea
        submit_response = client.post(
            "/api/v1/analysis/async",
            json={
                "code": "algorithm test(n) begin x <- 1 end",
                "analyze_complexity": True,
            }
        )
        
        if submit_response.status_code == 503:
            pytest.skip("Celery worker no disponible")
        
        task_id = submit_response.json()["task_id"]
        
        # Consultar estado
        status_response = client.get(f"/api/v1/analysis/task/{task_id}")
        
        assert status_response.status_code == 200
        data = status_response.json()
        
        assert "task_id" in data
        assert "status" in data
    
    def test_batch_async_endpoint(self, client):
        """Test endpoint de batch async"""
        if not is_celery_available():
            pytest.skip("Celery no disponible")
        
        response = client.post(
            "/api/v1/analysis/batch-async",
            json={
                "algorithms": [
                    {
                        "code": "algorithm test1(n) begin x <- 1 end",
                        "name": "test1"
                    },
                    {
                        "code": "algorithm test2(n) begin x <- 2 end",
                        "name": "test2"
                    },
                ]
            }
        )
        
        if response.status_code == 503:
            pytest.skip("Celery worker no disponible")
        
        assert response.status_code == 202
        data = response.json()
        
        assert "task_id" in data
        assert "message" in data

@pytest.mark.integration
class TestCeleryPerformance:
    """Tests de rendimiento con Celery"""
    
    @pytest.mark.skipif(
        not settings.CELERY_ENABLED,
        reason="Celery no habilitado"
    )
    @pytest.mark.slow
    def test_async_handles_long_analysis(self):
        """Test que análisis largo no bloquea el worker"""
        if not is_celery_available():
            pytest.skip("Celery worker no disponible")
        
        # Código complejo que toma tiempo
        complex_code = """
algorithm complexRecursive(n)
begin
    if n <= 1 then
        return 1
    end
    
    result <- 0
    for i <- 1 to n do
    begin
        result <- result + complexRecursive(n - i)
    end
    
    return result
end
"""
        
        request_data = {
            "code": complex_code,
            "analyze_complexity": True,
            "analyze_patterns": True,
            "analyze_structures": True,
            "generate_visualizations": False,
        }
        
        # Enviar
        start = time.time()
        task_id = submit_analysis(request_data)
        submit_time = time.time() - start
        
        # Debe retornar inmediatamente (< 1 segundo)
        assert submit_time < 1.0
        assert task_id is not None
        
        # Esperar resultado
        max_wait = 60
        start_wait = time.time()
        
        while time.time() - start_wait < max_wait:
            status = get_task_status(task_id)
            
            if status["status"] in ["SUCCESS", "FAILURE"]:
                break
            
            time.sleep(2)
        
        # Verificar que completó
        final_status = get_task_status(task_id)
        
        if final_status["status"] == "SUCCESS":
            assert "result" in final_status
        else:
            # Puede fallar por timeout o error, pero no debe colgar
            assert final_status["status"] in ["FAILURE", "PENDING", "STARTED"]

@pytest.mark.integration
class TestCeleryErrorHandling:
    """Tests de manejo de errores en Celery"""
    
    @pytest.mark.skipif(
        not settings.CELERY_ENABLED,
        reason="Celery no habilitado"
    )
    def test_invalid_code_returns_failure(self):
        """Test que código inválido retorna FAILURE"""
        if not is_celery_available():
            pytest.skip("Celery worker no disponible")
        
        request_data = {
            "code": "invalid code here without proper syntax",
            "analyze_complexity": True,
        }
        
        task_id = submit_analysis(request_data)
        assert task_id is not None
        
        # Esperar resultado
        max_wait = 20
        start = time.time()
        
        while time.time() - start < max_wait:
            status = get_task_status(task_id)
            
            if status["status"] == "FAILURE":
                # Debe tener mensaje de error
                assert "error" in status or "traceback" in status
                return
            elif status["status"] == "SUCCESS":
                # No debería tener éxito con código inválido
                pytest.fail("Task succeeded with invalid code")
            
            time.sleep(1)
        
        pytest.fail("Task did not fail as expected")

# Ejecutar tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])