"""
Ollama Adapter - Integración con modelos LLM locales

Ollama es completamente gratuito y open source (MIT).
Descarga y sirve modelos localmente. No requiere API key.
La API REST corre en http://localhost:11434 por defecto.

Instalación de Ollama:
    # Linux/Mac
    curl -fsSL https://ollama.com/install.sh | sh

    # Descargar modelo recomendado para este proyecto
    ollama pull deepseek-coder:6.7b   # 4GB RAM, muy bueno para código
    ollama pull codellama:13b          # 8GB RAM, más capacidad
    ollama pull phi3:mini              # 2GB RAM, muy rápido pero básico

Cuándo usar cada modelo:
    - deepseek-coder:6.7b  → Recomendado. Balance costo/calidad para análisis
    - codellama:13b         → Mejor razonamiento, requiere más recursos
    - phi3:mini             → Máxima velocidad, análisis básico

Arquitectura de uso:
    Ollama (primario, gratuito, local)
        → falla → Gemini (fallback externo)
        → falla → Claude (fallback final)
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

import httpx

from app.infrastructure.llm.base_llm import BaseLLM, LLMResponse

logger = logging.getLogger(__name__)

class OllamaAdapter(BaseLLM):
    """
    Adapter para modelos servidos por Ollama.

    Compatible con la misma interfaz que ClaudeAdapter y GeminiAdapter.
    El resto del sistema (ValidationAgent, CoordinatorAgent, LLMFactory)
    no necesita saber que está hablando con Ollama.

    Args:
        base_url: URL del servidor Ollama (default: http://localhost:11434)
        model: Nombre del modelo (default: deepseek-coder:6.7b)
        max_tokens: Tokens máximos en la respuesta
        temperature: Temperatura de generación (0.0 = determinista)
        timeout: Segundos de timeout para la llamada HTTP
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        timeout: Optional[float] = None,
    ) -> None:
        # Importar settings aquí para permitir override en tests
        from app.core.config import settings

        resolved_base_url = base_url or getattr(
            settings, "OLLAMA_BASE_URL", "http://localhost:11434"
        )
        resolved_model = model or getattr(
            settings, "OLLAMA_MODEL", "deepseek-coder:6.7b"
        )
        resolved_max_tokens = max_tokens or getattr(
            settings, "OLLAMA_MAX_TOKENS", 4000
        )
        resolved_temperature = (
            temperature
            if temperature is not None
            else getattr(settings, "OLLAMA_TEMPERATURE", 0.0)
        )
        resolved_timeout = timeout or getattr(settings, "OLLAMA_TIMEOUT", 60.0)

        # BaseLLM no usa api_key para Ollama — pasamos string vacío
        super().__init__(
            api_key="",
            model=resolved_model,
            max_tokens=resolved_max_tokens,
            temperature=resolved_temperature,
        )

        self.base_url = resolved_base_url.rstrip("/")
        self.timeout = resolved_timeout

        # Cliente HTTP async reutilizable
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            headers={"Content-Type": "application/json"},
        )

        logger.info(
            f"OllamaAdapter inicializado: "
            f"model={self.model}, url={self.base_url}"
        )

    # Métodos de BaseLLM 
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Genera una respuesta de texto usando Ollama.

        Usa el endpoint /api/generate (no streaming).
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": self.max_tokens,
                "temperature": self.temperature,
            },
        }

        if system_prompt:
            payload["system"] = system_prompt

        # Merge de opciones extra si el caller las pasa
        if "options" in kwargs:
            payload["options"].update(kwargs.pop("options"))

        try:
            response = await self._client.post(
                f"{self.base_url}/api/generate",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        except httpx.ConnectError:
            raise ConnectionError(
                f"Ollama no está disponible en {self.base_url}. "
                f"¿Está corriendo 'ollama serve'?"
            )
        except httpx.TimeoutException:
            raise TimeoutError(
                f"Ollama no respondió en {self.timeout}s. "
                f"El modelo '{self.model}' puede necesitar más tiempo."
            )
        except httpx.HTTPStatusError as e:
            raise RuntimeError(
                f"Ollama retornó HTTP {e.response.status_code}: "
                f"{e.response.text[:200]}"
            )

        content = data.get("response", "")
        eval_count = data.get("eval_count", 0)
        prompt_eval_count = data.get("prompt_eval_count", 0)

        return LLMResponse(
            content=content,
            model=data.get("model", self.model),
            tokens_used=eval_count + prompt_eval_count,
            finish_reason="stop" if data.get("done") else "length",
            metadata={
                "eval_count": eval_count,
                "prompt_eval_count": prompt_eval_count,
                "total_duration_ns": data.get("total_duration"),
                "load_duration_ns": data.get("load_duration"),
                "eval_duration_ns": data.get("eval_duration"),
            },
        )

    async def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Genera respuesta y la parsea como JSON.

        Añade instrucción explícita al prompt para que el modelo
        responda solo con JSON válido, sin markdown ni texto extra.
        """
        json_system = (
            "Responde ÚNICAMENTE con JSON válido. "
            "Sin explicaciones, sin markdown, sin bloques de código. "
            "Solo el objeto JSON directamente."
        )

        # Combinar system prompts
        if system_prompt:
            combined_system = f"{system_prompt}\n\n{json_system}"
        else:
            combined_system = json_system

        # Añadir hint al final del prompt
        enhanced_prompt = (
            f"{prompt}\n\n"
            "Responde solo con JSON. Ejemplo de formato: {{\"key\": \"value\"}}"
        )

        response = await self.generate(
            enhanced_prompt,
            system_prompt=combined_system,
            **kwargs,
        )

        content = response.content.strip()

        # Limpiar posibles markdown code fences que el modelo genere
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.warning(
                f"OllamaAdapter: JSON inválido recibido de '{self.model}'. "
                f"Error: {e}. Contenido: {content[:200]}"
            )
            # Intentar extraer JSON del contenido si está embebido
            extracted = self._extract_json(content)
            if extracted:
                return extracted
            raise

    # Utilidades 
    @staticmethod
    def _extract_json(text: str) -> Optional[Dict[str, Any]]:
        """
        Intenta extraer JSON de texto que puede contener texto extra.

        Busca el primer '{' y el último '}' para extraer el JSON.
        """
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                pass
        return None

    async def check_availability(self) -> bool:
        """
        Verifica si Ollama está disponible y el modelo está descargado.

        Útil para el health check del sistema.

        Returns:
            True si Ollama responde y el modelo está disponible
        """
        try:
            response = await self._client.get(
                f"{self.base_url}/api/tags",
                timeout=5.0,
            )
            if response.status_code != 200:
                return False

            data = response.json()
            models = [m.get("name", "") for m in data.get("models", [])]

            # Verificar si el modelo está disponible (puede tener tag :latest)
            model_base = self.model.split(":")[0]
            available = any(
                m == self.model or m.startswith(f"{model_base}:")
                for m in models
            )

            if not available:
                logger.warning(
                    f"Ollama está activo pero el modelo '{self.model}' "
                    f"no está descargado. "
                    f"Ejecuta: ollama pull {self.model}"
                )

            return available

        except Exception:
            return False

    async def list_models(self) -> list[str]:
        """Lista los modelos disponibles en el servidor Ollama."""
        try:
            response = await self._client.get(
                f"{self.base_url}/api/tags",
                timeout=5.0,
            )
            data = response.json()
            return [m.get("name", "") for m in data.get("models", [])]
        except Exception as e:
            logger.warning(f"No se pudo listar modelos Ollama: {e}")
            return []

    async def __aenter__(self) -> "OllamaAdapter":
        return self

    async def __aexit__(self, *exc_info: Any) -> None:
        await self._client.aclose()