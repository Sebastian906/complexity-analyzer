"""
LLMRouter — Routing inteligente entre LLMs con circuit breaker y retry.

Flujo de decisión:
    1. ¿Está el primario disponible? (circuit breaker CLOSED o HALF_OPEN)
    2. Llamar al primario con timeout y retry (tenacity)
    3. Evaluar respuesta — si score < min_acceptable_score → intentar fallback
    4. Si fallback también falla → propagar excepción

Integración con el sistema existente:
    - Los adaptadores (Claude, Gemini, Ollama) NO cambian
    - LLMFactory.create_router() es el punto de entrada recomendado
    - LLMValidationStep usará el router cuando se implemente

Métricas expuestas:
    - router.get_circuit_breaker_metrics() → para Prometheus
    - RoutedResponse.evaluation.to_dict() → para logging estructurado
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Optional

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.infrastructure.llm.base_llm import BaseLLM, LLMResponse
from app.infrastructure.llm.llm_circuit_breaker import CircuitBreaker, CircuitBreakerMetrics
from app.infrastructure.llm.llm_evaluator import EvaluationResult, LLMEvaluator
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

@dataclass
class RoutedResponse:
    """
    Respuesta del router con metadata de routing.

    Incluye qué LLM se usó, si se activó el fallback y
    el score de calidad de la respuesta.
    """
    response: LLMResponse
    llm_used: str
    evaluation: EvaluationResult
    fallback_used: bool = False
    attempts: int = 1

    def to_dict(self) -> dict:
        return {
            "llm_used":     self.llm_used,
            "fallback_used": self.fallback_used,
            "attempts":     self.attempts,
            "evaluation":   self.evaluation.to_dict(),
            "tokens_used":  self.response.tokens_used,
        }

class LLMRouter:
    """
    Router inteligente que selecciona el LLM óptimo por llamada.

    Se usa en lugar de llamar directamente a un adaptador LLM.
    Encapsula circuit breaker, evaluación de calidad y retry.

    Args:
        primary:               LLM principal (normalmente Ollama).
        fallback:              LLM de respaldo (normalmente Claude o Gemini).
        min_acceptable_score:  Score mínimo para aceptar respuesta del primario
                               sin intentar el fallback.
        timeout_seconds:       Timeout por llamada individual (sin contar retries).
        max_retries:           Número de reintentos ante fallos de red/timeout.

    Example:
        >>> router = LLMFactory.create_router()
        >>> routed = await router.route(
        ...     prompt="Analiza esta complejidad...",
        ...     required_fields=["big_o", "omega", "reasoning"],
        ... )
        >>> print(routed.llm_used)
        >>> print(routed.evaluation.score)
    """

    def __init__(
        self,
        primary: BaseLLM,
        fallback: Optional[BaseLLM] = None,
        min_acceptable_score: float = 0.6,
        timeout_seconds: float = 30.0,
        max_retries: int = 3,
    ) -> None:
        self._primary = primary
        self._fallback = fallback
        self._evaluator = LLMEvaluator()
        self._min_score = min_acceptable_score
        self._timeout = timeout_seconds
        self._max_retries = max_retries

        # Un CircuitBreaker por adaptador
        self._breakers: dict[str, CircuitBreaker] = {
            self._llm_name(primary): CircuitBreaker(
                name=self._llm_name(primary),
                failure_threshold=5,
                recovery_timeout=60.0,
            ),
        }
        if fallback:
            self._breakers[self._llm_name(fallback)] = CircuitBreaker(
                name=self._llm_name(fallback),
                failure_threshold=5,
                recovery_timeout=120.0,
            )

    #  Punto de entrada principal                                         
    async def route(
        self,
        prompt: str,
        required_fields: list[str] = None,
        system_prompt: Optional[str] = None,
    ) -> RoutedResponse:
        """
        Enruta la llamada al mejor LLM disponible.

        Args:
            prompt:          Prompt a enviar al LLM.
            required_fields: Campos JSON que deben estar en la respuesta.
                             Vacío = solo validar latencia y JSON.
            system_prompt:   System prompt opcional.

        Returns:
            RoutedResponse con la respuesta y metadata de routing.

        Raises:
            RuntimeError: Si todos los LLMs fallan o tienen circuit breakers abiertos.
        """
        required_fields = required_fields or []
        primary_name = self._llm_name(self._primary)
        primary_cb = self._breakers[primary_name]

        # ── Intentar primario ────────────────────────────────────────────
        if not primary_cb.is_open:
            try:
                response, latency, attempts = await self._call_with_retry(
                    self._primary, prompt, system_prompt
                )
                primary_cb.record_success()

                evaluation = self._evaluator.evaluate(
                    response.content, required_fields, latency
                )

                if evaluation.score >= self._min_score:
                    logger.debug(
                        f"LLMRouter: {primary_name} aceptado "
                        f"(score={evaluation.score:.2f})"
                    )
                    return RoutedResponse(
                        response=response,
                        llm_used=primary_name,
                        evaluation=evaluation,
                        fallback_used=False,
                        attempts=attempts,
                    )

                logger.info(
                    f"LLMRouter: {primary_name} score bajo ({evaluation.score:.2f}), "
                    f"razones: {evaluation.reasons} — intentando fallback"
                )

            except Exception as exc:
                primary_cb.record_failure()
                logger.warning(
                    f"LLMRouter: {primary_name} falló ({type(exc).__name__}: {exc}), "
                    f"circuit breaker: {primary_cb.state.value}"
                )
        else:
            logger.info(
                f"LLMRouter: circuit breaker abierto para {primary_name} "
                f"— usando fallback directamente"
            )

        # ── Intentar fallback ────────────────────────────────────────────
        if self._fallback:
            fallback_name = self._llm_name(self._fallback)
            fallback_cb = self._breakers.get(fallback_name)

            if fallback_cb and not fallback_cb.is_open:
                try:
                    response, latency, attempts = await self._call_with_retry(
                        self._fallback, prompt, system_prompt
                    )
                    fallback_cb.record_success()

                    evaluation = self._evaluator.evaluate(
                        response.content, required_fields, latency
                    )

                    logger.info(
                        f"LLMRouter: fallback {fallback_name} usado "
                        f"(score={evaluation.score:.2f})"
                    )
                    return RoutedResponse(
                        response=response,
                        llm_used=fallback_name,
                        evaluation=evaluation,
                        fallback_used=True,
                        attempts=attempts,
                    )

                except Exception as exc:
                    if fallback_cb:
                        fallback_cb.record_failure()
                    logger.error(
                        f"LLMRouter: fallback {fallback_name} también falló — {exc}"
                    )

        raise RuntimeError(
            f"Todos los LLMs fallaron o tienen circuit breakers abiertos. "
            f"Estados: {self._format_breaker_states()}"
        )

    async def route_json(
        self,
        prompt: str,
        required_fields: list[str] = None,
        system_prompt: Optional[str] = None,
    ) -> dict:
        """
        Versión conveniente que retorna el JSON parseado directamente.

        Llama a route() y parsea el contenido de la respuesta.
        """
        import json

        routed = await self.route(prompt, required_fields, system_prompt)
        content = routed.response.content.strip()

        # Limpiar markdown code fences si están presentes
        for fence in ("```json", "```"):
            if content.startswith(fence):
                content = content[len(fence):]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        return json.loads(content)

    #  Métricas                                                           
    def get_circuit_breaker_metrics(self) -> list[CircuitBreakerMetrics]:
        """
        Retorna el estado de todos los circuit breakers.

        Usar para exponer a Prometheus o para logging de health check.
        """
        return [cb.get_metrics() for cb in self._breakers.values()]

    def get_status(self) -> dict:
        """Resumen del estado del router para el endpoint /health."""
        return {
            "primary":  self._llm_name(self._primary),
            "fallback": self._llm_name(self._fallback) if self._fallback else None,
            "circuit_breakers": [
                m.to_dict() for m in self.get_circuit_breaker_metrics()
            ],
        }

    #  Helpers privados                                                   
    async def _call_with_retry(
        self,
        llm: BaseLLM,
        prompt: str,
        system_prompt: Optional[str],
    ) -> tuple[LLMResponse, float, int]:
        """
        Llama al LLM con timeout y retry exponencial.

        Retorna (response, latency_ms, attempts).
        """
        attempts = 0

        @retry(
            stop=stop_after_attempt(self._max_retries),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            retry=retry_if_exception_type((TimeoutError, ConnectionError, OSError)),
            reraise=True,
        )
        async def _attempt() -> tuple[LLMResponse, float]:
            nonlocal attempts
            attempts += 1
            start = time.perf_counter()
            response = await asyncio.wait_for(
                llm.generate(prompt, system_prompt=system_prompt),
                timeout=self._timeout,
            )
            latency = (time.perf_counter() - start) * 1000
            return response, latency

        response, latency = await _attempt()
        return response, latency, attempts

    @staticmethod
    def _llm_name(llm: Optional[BaseLLM]) -> str:
        """Nombre corto del adaptador para logs y métricas."""
        if llm is None:
            return "none"
        return type(llm).__name__.replace("Adapter", "").lower()

    def _format_breaker_states(self) -> str:
        return ", ".join(
            f"{name}={cb.state.value}"
            for name, cb in self._breakers.items()
        )