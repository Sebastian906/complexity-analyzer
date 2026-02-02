"""
Tests de Integración - LLMs

Prueba la integración con Claude y Gemini.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from app.infrastructure.llm import (
    ClaudeAdapter,
    GeminiAdapter,
    LLMFactory,
    LLMResponse,
)
from app.core.config import settings

@pytest.mark.integration
@pytest.mark.llm
class TestLLMIntegration:
    """Tests de integración con LLMs"""
    
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
            # Handle rate limiting and API errors gracefully
            error_str = str(e)
            if "429" in error_str or "rate" in error_str.lower():
                pytest.skip("Claude API rate limited - skipping test")
            if "401" in error_str or "authentication" in error_str.lower():
                pytest.skip("Claude API authentication failed - skipping test")
            raise  # Re-raise other exceptions
        
        assert isinstance(response, LLMResponse)
        assert response.content is not None
        assert len(response.content) > 0
        assert response.tokens_used > 0
    
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
            # Handle rate limiting (429) and quota errors gracefully
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                pytest.skip("Gemini API quota exceeded - skipping test")
            raise  # Re-raise other exceptions
        
        assert isinstance(response, LLMResponse)
        assert response.content is not None
        assert len(response.content) > 0
        assert response.tokens_used > 0
    
    @pytest.mark.asyncio
    async def test_claude_generate_json_mocked(self):
        """Test generación JSON con Claude (mocked)"""
        with patch.object(ClaudeAdapter, 'generate') as mock_generate:
            # Configurar mock
            mock_generate.return_value = LLMResponse(
                content='{"result": "success", "value": 42}',
                model="claude-3-sonnet",
                tokens_used=50,
                finish_reason="end_turn",
                metadata={}
            )
            
            claude = ClaudeAdapter()
            result = await claude.generate_json(
                prompt="Genera un JSON con result=success y value=42"
            )
            
            assert result["result"] == "success"
            assert result["value"] == 42
    
    @pytest.mark.asyncio
    async def test_llm_factory_create_claude(self):
        """Test factory para Claude"""
        llm = LLMFactory.create("claude")
        
        assert isinstance(llm, ClaudeAdapter)
        assert llm.model == settings.CLAUDE_MODEL
    
    @pytest.mark.asyncio
    async def test_llm_factory_create_gemini(self):
        """Test factory para Gemini"""
        llm = LLMFactory.create("gemini")
        
        assert isinstance(llm, GeminiAdapter)
        assert llm.model == settings.GEMINI_MODEL
    
    @pytest.mark.asyncio
    async def test_llm_factory_create_primary(self):
        """Test factory para LLM primario"""
        llm = LLMFactory.create_primary()
        
        assert llm is not None
        # Debe ser el tipo configurado como primario
        if settings.PRIMARY_LLM == "claude":
            assert isinstance(llm, ClaudeAdapter)
        else:
            assert isinstance(llm, GeminiAdapter)
    
    @pytest.mark.asyncio
    async def test_llm_error_handling(self):
        """Test manejo de errores en LLMs"""
        with patch.object(ClaudeAdapter, 'generate', side_effect=Exception("API Error")):
            claude = ClaudeAdapter()
            
            with pytest.raises(Exception) as exc_info:
                await claude.generate("test prompt")
            
            assert "API Error" in str(exc_info.value)