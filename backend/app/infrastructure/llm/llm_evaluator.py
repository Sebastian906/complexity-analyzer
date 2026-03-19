"""
LLMEvaluator — Evalúa calidad de respuesta LLM sin hacer otra llamada.

El score resultante permite al LLMRouter decidir si acepta la respuesta
del LLM primario o intenta el fallback.

Criterios de evaluación:
    1. JSON válido cuando se espera JSON (35% del score)
    2. Campos requeridos presentes (40% del score)
    3. Latencia aceptable (25% del score)
    4. Ajuste opcional por confianza que reporta el propio LLM

Diseño:
    - Sin estado (todos los métodos son pure functions equivalentes)
    - Sin dependencias externas
    - Extensible: agregar criterios sin cambiar la interfaz
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Optional

@dataclass
class EvaluationResult:
    """Resultado de la evaluación de una respuesta LLM."""
    score: float                     # 0.0 a 1.0 — score final
    is_valid_json: bool
    has_required_fields: bool
    latency_ms: float
    confidence_indicator: Optional[float]  # Si el LLM reporta confianza propia
    reasons: list[str] = field(default_factory=list)

    @property
    def is_acceptable(self) -> bool:
        """True si el score supera 0.6 (umbral por defecto del router)."""
        return self.score >= 0.6

    def to_dict(self) -> dict:
        return {
            "score":               round(self.score, 3),
            "is_valid_json":       self.is_valid_json,
            "has_required_fields": self.has_required_fields,
            "latency_ms":          round(self.latency_ms, 1),
            "confidence":          self.confidence_indicator,
            "reasons":             self.reasons,
        }

class LLMEvaluator:
    """
    Evalúa la calidad de respuestas de LLMs.

    Usado por LLMRouter para decidir si aceptar la respuesta
    del primario o intentar el fallback.

    Example:
        >>> evaluator = LLMEvaluator()
        >>> result = evaluator.evaluate(
        ...     response_content='{"big_o": "O(n^2)", "omega": "Omega(n)"}',
        ...     required_fields=["big_o", "omega"],
        ...     latency_ms=450.0,
        ... )
        >>> print(result.score)  # 0.95
        >>> print(result.is_acceptable)  # True
    """

    def evaluate(
        self,
        response_content: str,
        required_fields: list[str],
        latency_ms: float,
        max_acceptable_latency_ms: float = 10_000.0,
    ) -> EvaluationResult:
        """
        Evalúa una respuesta y retorna un score entre 0.0 y 1.0.

        Args:
            response_content:          Texto de la respuesta del LLM.
            required_fields:           Campos que deben estar presentes
                                       (vacío = solo evaluar latencia y JSON).
            latency_ms:                Tiempo de respuesta en milisegundos.
            max_acceptable_latency_ms: Latencia máxima tolerable.

        Returns:
            EvaluationResult con score y detalles.
        """
        score = 0.0
        reasons: list[str] = []

        # Criterio 1: JSON válido (35%) 
        is_json = False
        parsed: Optional[dict[str, Any]] = None

        try:
            parsed = json.loads(response_content.strip())
            is_json = True
            score += 0.35
        except (json.JSONDecodeError, ValueError):
            reasons.append("respuesta no es JSON válido")

        # Criterio 2: Campos requeridos (40%)
        has_fields = False

        if required_fields:
            if parsed is not None:
                found = [f for f in required_fields if f in parsed]
                ratio = len(found) / len(required_fields)
                has_fields = ratio == 1.0
                score += 0.40 * ratio
                if ratio < 1.0:
                    missing = [f for f in required_fields if f not in parsed]
                    reasons.append(f"campos faltantes: {missing}")
            else:
                reasons.append("no se pueden verificar campos — respuesta no es JSON")
        else:
            # Sin campos requeridos: este criterio se cumple automáticamente
            has_fields = True
            score += 0.40

        # Criterio 3: Latencia (25%) 
        latency_score = max(0.0, 1.0 - (latency_ms / max_acceptable_latency_ms))
        score += 0.25 * latency_score

        if latency_ms > max_acceptable_latency_ms * 0.8:
            reasons.append(f"latencia alta: {latency_ms:.0f}ms")

        # Confianza reportada por el LLM (0-20%)
        confidence_indicator: Optional[float] = None

        if parsed and "confidence" in parsed:
            try:
                conf = float(parsed["confidence"])
                if 0.0 <= conf <= 1.0:
                    confidence_indicator = conf
                    # No más del 20% de influencia
                    score = score * 0.80 + conf * 0.20
            except (TypeError, ValueError):
                pass

        return EvaluationResult(
            score=min(1.0, max(0.0, score)),
            is_valid_json=is_json,
            has_required_fields=has_fields,
            latency_ms=latency_ms,
            confidence_indicator=confidence_indicator,
            reasons=reasons,
        )

    def evaluate_best(
        self,
        responses: list[tuple[str, str, float]],
        required_fields: list[str],
    ) -> tuple[int, list[EvaluationResult]]:
        """
        Evalúa múltiples respuestas y retorna el índice del mejor.

        Args:
            responses:       Lista de (llm_name, content, latency_ms).
            required_fields: Campos requeridos para todas las respuestas.

        Returns:
            (índice_del_mejor, lista_de_evaluaciones)

        Example:
            >>> best_idx, evals = evaluator.evaluate_best(
            ...     [("ollama", '{"big_o":"O(n)"}', 200),
            ...      ("claude", '{"big_o":"O(n)","omega":"Omega(1)"}', 800)],
            ...     required_fields=["big_o", "omega"]
            ... )
        """
        evaluations = [
            self.evaluate(content, required_fields, latency)
            for _, content, latency in responses
        ]

        best_idx = max(range(len(evaluations)), key=lambda i: evaluations[i].score)
        return best_idx, evaluations