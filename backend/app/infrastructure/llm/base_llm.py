from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

@dataclass
class LLMResponse:
    """Respuesta de un LLM"""
    content: str
    model: str
    tokens_used: int
    finish_reason: str
    metadata: Dict[str, Any]

class BaseLLM(ABC):
    """Interface base para LLMs"""

    def __init__(
        self,
        api_key: str,
        model: str,
        max_tokens: int = 4000,
        temperature: float = 0.0
    ):
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Generar respuesta"""
        pass

    @abstractmethod
    async def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generar respuesta en formato JSON"""
        pass

    async def generate_with_fallback(
        self,
        prompt: str,
        fallback_llm: Optional['BaseLLM'] = None, 
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Intenta generate_json con este LLM; si falla usa fallback_llm.
        Aplica timeout desde settings si está disponible.
        """
        import asyncio
        try:
            from app.core.config import settings
            timeout = getattr(settings, 'LLM_TIMEOUT', 30)
        except Exception:
            timeout = 30

        try:
            return await asyncio.wait_for(
                self.generate_json(prompt, system_prompt, **kwargs),
                timeout=timeout
            )
        except Exception as primary_error:
            if fallback_llm is not None:
                try:
                    return await asyncio.wait_for(
                        fallback_llm.generate_json(prompt, system_prompt, **kwargs),
                        timeout=timeout
                    )
                except Exception:
                    pass
            raise primary_error