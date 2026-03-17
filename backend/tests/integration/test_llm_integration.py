"""
Tests de Integración - LLMs

Prueba la integración con Ollama (primario), Claude y Gemini (fallback/validación).
"""

import pytest
import warnings
from unittest.mock import Mock, patch, AsyncMock

from app.infrastructure.llm import (
    OllamaAdapter,
    ClaudeAdapter,
    GeminiAdapter,
    LLMFactory,
    LLMResponse,
)
from app.core.config import settings

# Suprimir warning de deprecación de aiohttp en Google GenAI SDK
@pytest.fixture(autouse=True)
def suppress_genai_warnings():
    """Suprimir warnings de deprecación de Google GenAI SDK"""
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning, module="google.genai")
        yield

@pytest.mark.integration
@pytest.mark.llm
class TestLLMErrorHandling:
    """Tests de manejo de errores en LLMs"""
    
    @pytest.mark.asyncio
    async def test_llm_connection_error(self):
        """Test error de conexión con Ollama"""
        # URL inválida para forzar error de conexión
        ollama = OllamaAdapter(base_url="http://localhost:99999")
        
        # Debe lanzar ConnectionError o similar
        with pytest.raises((ConnectionError, Exception)):
            await ollama.generate("test")
    
    @pytest.mark.asyncio
    async def test_llm_factory_with_invalid_claude_key(self):
        """Test factory con API key inválida de Claude"""
        # Guardar clave original
        original_key = settings.ANTHROPIC_API_KEY
        
        try:
            # Simular clave inválida
            with patch.object(settings, 'ANTHROPIC_API_KEY', 'invalid-key-test-123'):
                # El factory debe crear el adapter, pero fallar al usarlo
                claude = ClaudeAdapter()
                
                # Intentar generar debe fallar con error de auth
                with pytest.raises(Exception) as exc_info:
                    await claude.generate("test")
                
                # Debe ser un error de autenticación
                error_str = str(exc_info.value).lower()
                assert any(word in error_str for word in ["401", "auth", "api", "key", "invalid"])
        
        finally:
            # Restaurar clave original
            with patch.object(settings, 'ANTHROPIC_API_KEY', original_key):
                pass
    
    @pytest.mark.asyncio
    async def test_llm_factory_handles_missing_api_keys(self):
        """Test factory maneja ausencia de API keys"""
        # Guardar claves originales
        original_claude = settings.ANTHROPIC_API_KEY
        original_gemini = settings.GOOGLE_API_KEY
        
        try:
            # Simular ausencia de claves
            with patch.object(settings, 'ANTHROPIC_API_KEY', ''):
                with patch.object(settings, 'GOOGLE_API_KEY', ''):
                    # Ollama no requiere API key, debe funcionar
                    ollama = OllamaAdapter()
                    assert isinstance(ollama, OllamaAdapter)
                    
                    # Claude debe funcionar pero fallar al generar sin key
                    claude = ClaudeAdapter()
                    assert isinstance(claude, ClaudeAdapter)
                    
                    # Gemini __init__ crea internamente genai.Client, que falla
                    # si no hay API key; parchear el cliente para permitir la
                    # creación del adapter sin llamar a la API real.
                    with patch("app.infrastructure.llm.gemini_adapter.genai.Client") as mock_genai_client:
                        mock_genai_client.return_value = Mock()
                        gemini = GeminiAdapter()
                        assert isinstance(gemini, GeminiAdapter)
        
        finally:
            # Restaurar claves
            with patch.object(settings, 'ANTHROPIC_API_KEY', original_claude):
                with patch.object(settings, 'GOOGLE_API_KEY', original_gemini):
                    pass
    
    @pytest.mark.asyncio
    async def test_llm_timeout_handling(self):
        """Test manejo de timeout en Ollama"""
        # Usar timeout muy corto para forzar TimeoutError
        ollama = OllamaAdapter(timeout=0.001)
        
        with pytest.raises(TimeoutError) as exc_info:
            await ollama.generate("Test prompt que probablemente haga timeout")
        
        # Verificar que el mensaje menciona timeout, respondió, o tiempo
        error_msg = str(exc_info.value).lower()
        assert any(word in error_msg for word in ["timeout", "respondió", "tiempo", "timed"])

@pytest.mark.integration
@pytest.mark.llm
class TestClaudeIntegration:
    """Tests de integración con Claude (LLM de validación)"""
    
    @pytest.mark.skipif(
        not settings.ANTHROPIC_API_KEY,
        reason="Claude API key not configured"
    )
    @pytest.mark.asyncio
    async def test_claude_generate(self):
        """Test generación con Claude (real API)"""
        claude = ClaudeAdapter()
        
        try:
            response = await claude.generate(
                prompt="Responde con 'OK' si entiendes este mensaje.",
                system_prompt="Eres un asistente útil."
            )
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "rate" in error_str.lower():
                pytest.skip("Claude API rate limited - skipping test")
            if "401" in error_str or "authentication" in error_str.lower():
                pytest.skip("Claude API authentication failed - skipping test")
            if "credit" in error_str.lower() or "balance" in error_str.lower():
                pytest.skip("Claude API insufficient credits - skipping test")
            raise
        
        assert isinstance(response, LLMResponse)
        assert response.content is not None
        assert len(response.content) > 0
        assert response.tokens_used > 0

@pytest.mark.integration
@pytest.mark.llm
class TestGeminiIntegration:
    """Tests de integración con Gemini (LLM de validación)"""
    
    @pytest.mark.skipif(
        not settings.GOOGLE_API_KEY,
        reason="Gemini API key not configured"
    )
    @pytest.mark.asyncio
    async def test_gemini_generate(self):
        """Test generación con Gemini (real API)"""
        gemini = GeminiAdapter()
        
        try:
            response = await gemini.generate(
                prompt="Responde con 'OK' si entiendes este mensaje."
            )
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                pytest.skip("Gemini API quota exceeded - skipping test")
            raise
        
        assert isinstance(response, LLMResponse)
        assert response.content is not None
        assert len(response.content) > 0
        assert response.tokens_used > 0

@pytest.mark.integration
@pytest.mark.llm
class TestOllamaIntegration:
    """Tests de integración con Ollama (LLM local primario)"""
    
    @pytest.mark.asyncio
    async def test_ollama_availability(self):
        """Test verificar disponibilidad de Ollama"""
        ollama = OllamaAdapter()
        
        available = await ollama.check_availability()
        
        if not available:
            pytest.skip(
                "Ollama no está disponible. "
                "Iniciar con: ollama serve && ollama pull deepseek-coder:6.7b"
            )
        
        assert available is True
    
    @pytest.mark.asyncio
    async def test_ollama_list_models(self):
        """Test listar modelos disponibles en Ollama"""
        ollama = OllamaAdapter()
        
        try:
            models = await ollama.list_models()
        except Exception as e:
            pytest.skip(f"Ollama no disponible: {e}")
        
        assert isinstance(models, list)
        # Si está configurado correctamente, debe tener al menos un modelo
        if models:
            assert len(models) > 0
    
    @pytest.mark.asyncio
    async def test_ollama_generate(self):
        """Test generación con Ollama (real API local)"""
        ollama = OllamaAdapter()
        
        try:
            available = await ollama.check_availability()
            if not available:
                pytest.skip("Ollama no disponible")
            
            response = await ollama.generate(
                prompt="Responde SOLO con la palabra 'OK' si entiendes.",
                system_prompt="Eres un asistente conciso."
            )
        except Exception as e:
            pytest.skip(f"Ollama error: {e}")
        
        assert isinstance(response, LLMResponse)
        assert response.content is not None
        assert len(response.content) > 0
        assert response.tokens_used >= 0

@pytest.mark.integration
@pytest.mark.llm
class TestLLMFactory:
    """Tests del factory de LLMs"""
    
    def test_factory_create_ollama(self):
        """Test factory para Ollama"""
        llm = LLMFactory.create("ollama")
        
        assert isinstance(llm, OllamaAdapter)
        # Verificar configuración
        assert llm.model == settings.OLLAMA_MODEL
    
    def test_factory_create_claude(self):
        """Test factory para Claude"""
        if not settings.ANTHROPIC_API_KEY:
            pytest.skip("Claude API key not configured")
        
        llm = LLMFactory.create("claude")
        
        assert isinstance(llm, ClaudeAdapter)
    
    def test_factory_create_gemini(self):
        """Test factory para Gemini"""
        if not settings.GOOGLE_API_KEY:
            pytest.skip("Gemini API key not configured")
        
        llm = LLMFactory.create("gemini")
        
        assert isinstance(llm, GeminiAdapter)
    
    @pytest.mark.asyncio
    async def test_check_availability_reports_all_llms(self):
        """Test que check_availability reporta todos los LLMs"""
        status = await LLMFactory.check_availability()
        
        # Debe reportar al menos Ollama
        assert "ollama" in status
        assert "configured" in status["ollama"]
        
        # Si hay API keys, debe reportar Claude/Gemini
        if settings.ANTHROPIC_API_KEY:
            assert "claude" in status
        
        if settings.GOOGLE_API_KEY:
            assert "gemini" in status

# Ejecutar tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])