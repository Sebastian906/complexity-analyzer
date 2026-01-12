from typing import Literal

from app.infrastructure.llm.base_llm import BaseLLM
from app.infrastructure.llm.claude_adapter import ClaudeAdapter
from app.infrastructure.llm.gemini_adapter import GeminiAdapter
from app.core.config import settings

LLMType = Literal["claude", "gemini"]

class LLMFactory:
    """Factory para crear instancias de LLMs"""

    @staticmethod
    def create(llm_type: LLMType = None) -> BaseLLM:
        """
        Crear instancia de LLM.

        Args:
            llm_type: Tipo de LLM ("claude" o "gemini")
                     Si es None, usa PRIMARY_LLM de settings

        Returns:
            BaseLLM: Instancia del LLM correspondiente
        """
        if llm_type is None:
            llm_type = settings.PRIMARY_LLM

        if llm_type == "claude":
            return ClaudeAdapter()
        elif llm_type == "gemini":
            return GeminiAdapter()
        else:
            raise ValueError(f"LLM type no soportado: {llm_type}")

    @staticmethod
    def create_primary() -> BaseLLM:
        """Crear LLM primario"""
        return LLMFactory.create(settings.PRIMARY_LLM)

    @staticmethod
    def create_fallback() -> BaseLLM:
        """Crear LLM de fallback"""
        return LLMFactory.create(settings.FALLBACK_LLM)