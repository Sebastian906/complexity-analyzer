import json
from typing import Dict, Any, Optional
from anthropic import AsyncAnthropic

from app.infrastructure.llm.base_llm import BaseLLM, LLMResponse
from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

class ClaudeAdapter(BaseLLM):
    """Adapter para Claude (Anthropic)"""

    def __init__(self):
        super().__init__(
            api_key=settings.ANTHROPIC_API_KEY,
            model=settings.CLAUDE_MODEL,
            max_tokens=settings.CLAUDE_MAX_TOKENS,
            temperature=settings.CLAUDE_TEMPERATURE,
        )
        self.client = AsyncAnthropic(api_key=self.api_key)

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Generar respuesta con Claude"""
        try:
            messages = [{"role": "user", "content": prompt}]

            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt if system_prompt else "",
                messages=messages,
                **kwargs
            )

            content = response.content[0].text

            return LLMResponse(
                content=content,
                model=response.model,
                tokens_used=response.usage.input_tokens + response.usage.output_tokens,
                finish_reason=response.stop_reason,
                metadata={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                }
            )

        except Exception as e:
            logger.error(f"Error en Claude: {e}")
            raise

    async def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generar respuesta JSON con Claude"""
        response = await self.generate(prompt, system_prompt, **kwargs)

        # Parsear JSON
        content = response.content.strip()

        # Remover markdown code blocks si existen
        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "").strip()
        elif content.startswith("```"):
            content = content.replace("```", "").strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Error parseando JSON de Claude: {e}")
            logger.debug(f"Contenido: {content}")
            raise