import json
from typing import Dict, Any, Optional
import google.generativeai as genai

from app.infrastructure.llm.base_llm import BaseLLM, LLMResponse
from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

class GeminiAdapter(BaseLLM):
    """Adapter para Google Gemini"""

    def __init__(self):
        super().__init__(
            api_key=settings.GOOGLE_API_KEY,
            model=settings.GEMINI_MODEL,
            max_tokens=settings.GEMINI_MAX_TOKENS,
            temperature=settings.GEMINI_TEMPERATURE,
        )
        genai.configure(api_key=self.api_key)
        self.client = genai.GenerativeModel(self.model)

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Generar respuesta con Gemini"""
        try:
            # Combinar system prompt con prompt si existe
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"

            response = await self.client.generate_content_async(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=self.max_tokens,
                    temperature=self.temperature,
                    **kwargs
                )
            )

            return LLMResponse(
                content=response.text,
                model=self.model,
                tokens_used=response.usage_metadata.total_token_count,
                finish_reason=str(response.candidates[0].finish_reason),
                metadata={
                    "prompt_tokens": response.usage_metadata.prompt_token_count,
                    "completion_tokens": response.usage_metadata.candidates_token_count,
                }
            )

        except Exception as e:
            logger.error(f"Error en Gemini: {e}")
            raise

    async def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generar respuesta JSON con Gemini"""
        response = await self.generate(prompt, system_prompt, **kwargs)

        content = response.content.strip()

        # Remover markdown code blocks
        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "").strip()
        elif content.startswith("```"):
            content = content.replace("```", "").strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Error parseando JSON de Gemini: {e}")
            raise