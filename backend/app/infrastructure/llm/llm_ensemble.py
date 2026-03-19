"""
infrastructure/llm/llm_ensemble.py

Sistema de ensemble para validación cruzada entre múltiples LLMs.

Dos estrategias disponibles:
    BEST_SCORE  — retorna la respuesta con mayor score del evaluador
    MAJORITY_VOTE — retorna la respuesta donde más LLMs coinciden en big_o/omega

Cuándo usar cada una:
    - BEST_SCORE:     cuando necesitas la respuesta de mayor calidad individual
                      (latencia = máx de los LLMs paralelos)
    - MAJORITY_VOTE:  cuando necesitas consenso para detectar errores del análisis estático
                      (más robusto pero más costoso)

Integración con LLMRouter:
    El ensemble NO reemplaza al router — lo complementa.
    El router maneja resiliencia (circuit breaker, fallback, retry).
    El ensemble maneja consenso (cuando quieres más de una opinión).

Ejemplo:
    ensemble = LLMEnsemble(
        llms=[ollama_adapter, claude_adapter, gemini_adapter],
        strategy=EnsembleStrategy.MAJORITY_VOTE,
    )
    result = await ensemble.validate(
        prompt=prompt,
        required_fields=["big_o", "omega", "matches_our_analysis"],
    )
    print(result.winning_response)
    print(result.agreement_score)
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from app.infrastructure.llm.base_llm import BaseLLM
from app.infrastructure.llm.llm_evaluator import EvaluationResult, LLMEvaluator
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class EnsembleStrategy(str, Enum):
    BEST_SCORE    = "best_score"
    MAJORITY_VOTE = "majority_vote"

@dataclass
class EnsembleResult:
    """
    Resultado del ensemble.

    winning_response: contenido JSON de la mejor/más votada respuesta.
    agreement_score:  0.0-1.0, qué fracción de LLMs coincidió en big_o.
    consensus_reached: True si agreement_score >= min_agreement.
    per_llm_scores:   score del evaluador por cada LLM.
    strategy_used:    qué estrategia produjo este resultado.
    """
    winning_response: dict
    agreement_score: float
    consensus_reached: bool
    per_llm_scores: dict[str, float] = field(default_factory=dict)
    strategy_used: EnsembleStrategy = EnsembleStrategy.BEST_SCORE
    llms_consulted: list[str] = field(default_factory=list)
    llms_failed: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "winning_response":  self.winning_response,
            "agreement_score":   round(self.agreement_score, 3),
            "consensus_reached": self.consensus_reached,
            "per_llm_scores":    {k: round(v, 3) for k, v in self.per_llm_scores.items()},
            "strategy_used":     self.strategy_used.value,
            "llms_consulted":    self.llms_consulted,
            "llms_failed":       self.llms_failed,
        }

class LLMEnsemble:
    """
    Ensemble de múltiples LLMs con estrategia de selección configurable.

    Llama a todos los LLMs en paralelo y combina sus respuestas.
    Los LLMs que fallan se excluyen silenciosamente del ensemble.

    Args:
        llms:          Lista de adaptadores LLM. Mínimo 2 para tener consenso.
        strategy:      Estrategia de selección (BEST_SCORE o MAJORITY_VOTE).
        timeout:       Timeout por LLM individual en segundos.
        min_agreement: Fracción mínima de LLMs que deben coincidir para
                       considerar que hay consenso (solo MAJORITY_VOTE).
    """

    def __init__(
        self,
        llms: list[BaseLLM],
        strategy: EnsembleStrategy = EnsembleStrategy.BEST_SCORE,
        timeout: float = 30.0,
        min_agreement: float = 0.6,
    ) -> None:
        if len(llms) < 2:
            raise ValueError("El ensemble requiere al menos 2 LLMs")
        self._llms = llms
        self._strategy = strategy
        self._timeout = timeout
        self._min_agreement = min_agreement
        self._evaluator = LLMEvaluator()

    async def validate(
        self,
        prompt: str,
        required_fields: list[str],
        system_prompt: Optional[str] = None,
    ) -> EnsembleResult:
        """
        Llama a todos los LLMs en paralelo y combina sus respuestas.

        Args:
            prompt:          Prompt a enviar a todos los LLMs.
            required_fields: Campos requeridos para evaluación de calidad.
            system_prompt:   System prompt opcional.

        Returns:
            EnsembleResult con la mejor respuesta y métricas de consenso.

        Raises:
            RuntimeError: Si todos los LLMs fallaron.
        """
        # Llamar a todos en paralelo
        raw_responses = await self._call_all(prompt, system_prompt)

        if not raw_responses:
            raise RuntimeError(
                "Todos los LLMs del ensemble fallaron — sin respuestas válidas"
            )

        # Evaluar calidad de cada respuesta
        evaluated = self._evaluate_all(raw_responses, required_fields)

        # Seleccionar ganador según estrategia
        if self._strategy == EnsembleStrategy.MAJORITY_VOTE:
            return self._majority_vote(evaluated, raw_responses)
        else:
            return self._best_score(evaluated, raw_responses)

    #  Estrategias                                                        
    def _best_score(
        self,
        evaluated: list[tuple[str, dict, EvaluationResult]],
        raw: list[tuple[str, str, float]],
    ) -> EnsembleResult:
        """Retorna la respuesta con mayor score del evaluador."""
        best_name, best_parsed, best_eval = max(
            evaluated, key=lambda x: x[2].score
        )

        per_llm = {name: ev.score for name, _, ev in evaluated}

        # Determinar LLMs que fallaron comparando contra la lista original
        all_names = [
            f"{type(llm).__name__.replace('Adapter', '').lower()}_{i}"
            for i, llm in enumerate(self._llms)
        ]
        failed = [n for n in all_names if n not in per_llm]

        # Calcular acuerdo en big_o como métrica informativa
        agreement = self._calculate_agreement(
            [parsed for _, parsed, _ in evaluated], "big_o"
        )

        logger.info(
            f"Ensemble BEST_SCORE: ganador={best_name} "
            f"score={best_eval.score:.2f} acuerdo_big_o={agreement:.2f}"
        )

        return EnsembleResult(
            winning_response=best_parsed,
            agreement_score=agreement,
            consensus_reached=agreement >= self._min_agreement,
            per_llm_scores=per_llm,
            strategy_used=EnsembleStrategy.BEST_SCORE,
            llms_consulted=[name for name, _, _ in evaluated],
            llms_failed=failed,
        )

    def _majority_vote(
        self,
        evaluated: list[tuple[str, dict, EvaluationResult]],
        raw: list[tuple[str, str, float]],
    ) -> EnsembleResult:
        """
        Retorna la respuesta cuyo big_o recibe más votos.

        En caso de empate, desempata por score del evaluador.
        """
        # Contar votos por big_o
        vote_counts: dict[str, int] = {}
        vote_best: dict[str, tuple[str, dict, EvaluationResult]] = {}

        for name, parsed, evaluation in evaluated:
            big_o = parsed.get("big_o", "unknown")
            vote_counts[big_o] = vote_counts.get(big_o, 0) + 1

            # Guardar la mejor respuesta por big_o (mayor score)
            if big_o not in vote_best or evaluation.score > vote_best[big_o][2].score:
                vote_best[big_o] = (name, parsed, evaluation)

        # Ordenar por votos, luego por score
        winning_big_o = max(
            vote_counts,
            key=lambda k: (vote_counts[k], vote_best[k][2].score),
        )

        winner_name, winner_parsed, winner_eval = vote_best[winning_big_o]
        total_votes = sum(vote_counts.values())
        agreement = vote_counts[winning_big_o] / total_votes

        per_llm = {name: ev.score for name, _, ev in evaluated}

        # Determinar LLMs que fallaron comparando contra la lista original
        all_names = [
            f"{type(llm).__name__.replace('Adapter', '').lower()}_{i}"
            for i, llm in enumerate(self._llms)
        ]
        failed = [n for n in all_names if n not in per_llm]

        logger.info(
            f"Ensemble MAJORITY_VOTE: big_o={winning_big_o} "
            f"votos={vote_counts[winning_big_o]}/{total_votes} "
            f"acuerdo={agreement:.2f}"
        )

        return EnsembleResult(
            winning_response=winner_parsed,
            agreement_score=agreement,
            consensus_reached=agreement >= self._min_agreement,
            per_llm_scores=per_llm,
            strategy_used=EnsembleStrategy.MAJORITY_VOTE,
            llms_consulted=[name for name, _, _ in evaluated],
            llms_failed=failed,
        )

    #  Internos                                       
    async def _call_all(
        self,
        prompt: str,
        system_prompt: Optional[str],
    ) -> list[tuple[str, str, float]]:
        """
        Llama a todos los LLMs en paralelo.

        Retorna lista de (llm_name, response_content, latency_ms).
        Los LLMs que fallan se omiten sin propagar excepción.
        """
        import time

        async def _call_one(llm: BaseLLM, idx: int) -> Optional[tuple[str, str, float]]:
            # Incluir índice para distinguir múltiples adaptadores del mismo tipo (ej. MagicMock)
            base = type(llm).__name__.replace("Adapter", "").lower()
            name = f"{base}_{idx}"
            try:
                start = time.perf_counter()
                response = await asyncio.wait_for(
                    llm.generate(prompt, system_prompt=system_prompt),
                    timeout=self._timeout,
                )
                latency = (time.perf_counter() - start) * 1000
                return name, response.content, latency
            except Exception as exc:
                logger.warning(f"Ensemble: {name} falló — {type(exc).__name__}: {exc}")
                return None
 
        results = await asyncio.gather(*[_call_one(llm, idx) for idx, llm in enumerate(self._llms)])
        return [r for r in results if r is not None]

    def _evaluate_all(
        self,
        raw: list[tuple[str, str, float]],
        required_fields: list[str],
    ) -> list[tuple[str, dict, EvaluationResult]]:
        """
        Evalúa y parsea todas las respuestas.

        Retorna lista de (name, parsed_dict, evaluation).
        Las respuestas que no son JSON válido se omiten.
        """
        import json

        results = []
        for name, content, latency in raw:
            evaluation = self._evaluator.evaluate(
                content, required_fields, latency
            )

            # Solo incluir si es JSON parseable
            if evaluation.is_valid_json:
                try:
                    clean = content.strip()
                    for fence in ("```json", "```"):
                        if clean.startswith(fence):
                            clean = clean[len(fence):]
                    if clean.endswith("```"):
                        clean = clean[:-3]
                    parsed = json.loads(clean.strip())
                    results.append((name, parsed, evaluation))
                except json.JSONDecodeError:
                    logger.debug(f"Ensemble: {name} — JSON inválido después de limpiar")

        return results

    @staticmethod
    def _calculate_agreement(responses: list[dict], field: str) -> float:
        """Calcula la fracción de respuestas que coinciden en un campo."""
        if not responses:
            return 0.0
        values = [r.get(field) for r in responses if r.get(field)]
        if not values:
            return 0.0
        most_common = max(set(values), key=values.count)
        return values.count(most_common) / len(values)