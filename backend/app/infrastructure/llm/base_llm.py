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