"""
LLM Factory - Creación de instancias de LLMs
"""

from __future__ import annotations

import logging
from typing import List, Literal, Optional

from app.infrastructure.llm.base_llm import BaseLLM
from app.infrastructure.llm.claude_adapter import ClaudeAdapter
from app.infrastructure.llm.gemini_adapter import GeminiAdapter
from app.infrastructure.llm.ollama_adapter import OllamaAdapter
from app.core.config import settings

logger = logging.getLogger(__name__)

LLMType = Literal["claude", "gemini", "ollama"]

class LLMFactory:
    """Factory para crear instancias de LLMs"""

    @staticmethod
    def create(llm_type: Optional[LLMType] = None) -> BaseLLM:
        """
        Crea instancia de LLM.
 
        Args:
            llm_type: "claude", "gemini" u "ollama".
                     Si es None, usa PRIMARY_LLM de settings.
 
        Returns:
            BaseLLM: Instancia del LLM correspondiente
 
        Raises:
            ValueError: Si llm_type no es un tipo soportado
        """
        if llm_type is None:
            llm_type = settings.PRIMARY_LLM
 
        if llm_type == "claude":
            if not settings.ANTHROPIC_API_KEY:
                raise ValueError(
                    "ANTHROPIC_API_KEY no configurada. "
                    "Añadir a .env para usar Claude."
                )
            return ClaudeAdapter()
 
        elif llm_type == "gemini":
            if not settings.GOOGLE_API_KEY:
                raise ValueError(
                    "GOOGLE_API_KEY no configurada. "
                    "Añadir a .env para usar Gemini."
                )
            return GeminiAdapter()

        elif llm_type == "ollama":
            # Ollama no requiere API key — siempre se puede intentar crear
            return OllamaAdapter()

        else:
            raise ValueError(
                f"LLM type no soportado: '{llm_type}'. "
                f"Valores válidos: 'claude', 'gemini', 'ollama'"
            )
 
    @staticmethod
    def create_primary() -> BaseLLM:
        """Crea LLM primario según settings.PRIMARY_LLM."""
        try:
            return LLMFactory.create(settings.PRIMARY_LLM)
        except Exception as e:
            logger.error(f"No se pudo crear LLM primario '{settings.PRIMARY_LLM}': {e}")
            raise
 
    @staticmethod
    def create_fallback() -> Optional[BaseLLM]:
        """
        Crea LLM de fallback según settings.FALLBACK_LLM.
 
        Retorna None si no está configurado, en lugar de lanzar excepción.
        """
        try:
            return LLMFactory.create(settings.FALLBACK_LLM)
        except Exception as e:
            logger.warning(
                f"LLM fallback '{settings.FALLBACK_LLM}' no disponible: {e}"
            )
            return None
 
    @staticmethod
    def create_validation_chain() -> List[BaseLLM]:
        """
        Crea la cadena completa de LLMs para validación cruzada.
 
        El orden refleja el flujo: primario → fallback → adicionales.
        Solo incluye LLMs que están configurados.
 
        Returns:
            Lista de LLMs en orden de prioridad
 
        Example:
            >>> chain = LLMFactory.create_validation_chain()
            >>> # [OllamaAdapter, GeminiAdapter, ClaudeAdapter]
            >>> for llm in chain:
            ...     result = await llm.generate_json(prompt)
        """
        chain = []
 
        # Primario
        try:
            chain.append(LLMFactory.create_primary())
        except Exception as e:
            logger.warning(f"LLM primario no disponible: {e}")
 
        # Fallback (solo si es diferente del primario)
        if settings.FALLBACK_LLM != settings.PRIMARY_LLM:
            try:
                fallback = LLMFactory.create_fallback()
                if fallback:
                    chain.append(fallback)
            except Exception as e:
                logger.warning(f"LLM fallback no disponible: {e}")

        # Añadir LLMs adicionales para validación cruzada
        # (los que no son primario ni fallback)
        all_types: List[LLMType] = ["ollama", "gemini", "claude"]
        used = {settings.PRIMARY_LLM, settings.FALLBACK_LLM}

        for llm_type in all_types:
            if llm_type not in used:
                try:
                    chain.append(LLMFactory.create(llm_type))
                    used.add(llm_type)
                except Exception:
                    pass  # LLM no configurado, continuar

        if not chain:
            raise RuntimeError(
                "Ningún LLM disponible. "
                "Configura al menos uno: ANTHROPIC_API_KEY, GOOGLE_API_KEY, "
                "o instala Ollama (ollama serve)."
            )

        logger.info(
            f"Cadena de validación: "
            f"{[type(llm).__name__ for llm in chain]}"
        )
        return chain

    @staticmethod
    async def check_availability() -> dict:
        """
        Verifica qué LLMs están disponibles en este momento.

        Útil para el endpoint /health o para diagnóstico.

        Returns:
            Dict con el estado de cada LLM
        """
        status = {}

        # Claude
        if settings.ANTHROPIC_API_KEY:
            status["claude"] = {"configured": True, "model": settings.CLAUDE_MODEL}
        else:
            status["claude"] = {"configured": False}

        # Gemini
        if settings.GOOGLE_API_KEY:
            status["gemini"] = {"configured": True, "model": settings.GEMINI_MODEL}
        else:
            status["gemini"] = {"configured": False}

        # Ollama — verificar conectividad activa
        ollama_model = getattr(settings, "OLLAMA_MODEL", "deepseek-coder:6.7b")
        try:
            ollama = OllamaAdapter()
            available = await ollama.check_availability()
            models = await ollama.list_models() if available else []
            status["ollama"] = {
                "configured": True,
                "model": ollama_model,
                "available": available,
                "models_installed": models,
            }
        except Exception as e:
            status["ollama"] = {
                "configured": False,
                "error": str(e),
            }

        status["primary"] = settings.PRIMARY_LLM
        status["fallback"] = settings.FALLBACK_LLM

        return status