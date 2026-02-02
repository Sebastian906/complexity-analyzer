import json
from typing import Dict, Any, Optional
from google import genai
from google.genai import types

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
        self.client = genai.Client(api_key=self.api_key)

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

            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=self.max_tokens,
                    temperature=self.temperature,
                    **kwargs
                )
            )

            return LLMResponse(
                content=response.text,
                model=self.model,
                tokens_used=response.usage_metadata.total_token_count if response.usage_metadata else 0,
                finish_reason=str(response.candidates[0].finish_reason) if response.candidates else "unknown",
                metadata={
                    "prompt_tokens": response.usage_metadata.prompt_token_count if response.usage_metadata else 0,
                    "completion_tokens": response.usage_metadata.candidates_token_count if response.usage_metadata else 0,
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