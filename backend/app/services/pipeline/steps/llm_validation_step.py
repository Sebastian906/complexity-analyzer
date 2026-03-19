"""
LLMValidationStep — Paso opcional del pipeline para validación cruzada con LLM.

Se registra DESPUÉS de ComplexityStep y ANTES de SummarizeStep.
Solo corre si está habilitado en DynamicConfig.

Flujo:
    1. Toma ctx.complexity (resultado del análisis estático)
    2. Construye prompt con el código y la complejidad calculada
    3. Llama al LLMRouter (que maneja circuit breaker + fallback + retry)
    4. Si el LLM confirma → actualiza ctx con metadata de validación
    5. Si el LLM discrepa → agrega warning (no bloquea el pipeline)
    6. Si el LLM falla → agrega warning y continúa (degradación elegante)

Decisión de diseño:
    El LLM NO sobreescribe el resultado del análisis estático.
    El análisis estático es determinista y reproducible.
    El LLM agrega contexto (reasoning, warnings) pero no cambia Big O.
    Si en el futuro queremos que el LLM corrija, ese es un cambio explícito.

Activar en runtime (sin redeploy):
    # Editar config/runtime_flags.yaml:
    #   llm_validation_enabled: true
    #   pipeline_steps_enabled:
    #     llm_validation: true

    # O desde Redis:
    #   redis-cli SET runtime_flags '{"llm_validation_enabled":true,"pipeline_steps_enabled":{"llm_validation":true}}'

Registrar en el pipeline:
    from app.services.pipeline.steps.llm_validation_step import LLMValidationStep
    from app.infrastructure.llm.llm_factory import LLMFactory

    router = LLMFactory.create_router()
    pipeline.register_step(LLMValidationStep(router), position=4)
    # position=4 → después de StructureStep, antes de SummarizeStep
"""

from __future__ import annotations

import json
from typing import Optional

from app.services.dynamic_config import DynamicConfig
from app.services.pipeline.context import PipelineContext
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# Campos JSON que el LLM debe retornar para que la respuesta sea válida
_REQUIRED_FIELDS = ["big_o", "omega", "matches_our_analysis", "reasoning"]

# Prompt base — reutiliza la estructura de config/llm/claude_prompts.yaml
_VALIDATION_PROMPT_TEMPLATE = """\
Eres un experto en análisis de algoritmos. Analiza el siguiente pseudocódigo
y determina su complejidad temporal.

PSEUDOCÓDIGO:
{algorithm_code}

NUESTRO ANÁLISIS (análisis estático automático):
  Mejor caso (Ω): {omega}
  Peor caso (O): {big_o}
  Caso promedio (Θ): {theta}

INSTRUCCIONES:
1. Analiza el algoritmo línea por línea.
2. Determina la complejidad en notación Big O, Omega y Theta.
3. Indica si coincide con nuestro análisis.
4. Si hay diferencia, explica por qué.

Responde SOLO en formato JSON sin markdown:
{{
    "big_o": "...",
    "omega": "...",
    "theta": "...",
    "matches_our_analysis": true,
    "errors": [],
    "warnings": [],
    "reasoning": "..."
}}"""

class LLMValidationStep:
    """
    Paso de validación cruzada con LLM.

    Paso opcional — solo se registra en el pipeline cuando
    llm_validation_enabled=true en DynamicConfig.

    Args:
        router: LLMRouter configurado con primario y fallback.
                Crear con LLMFactory.create_router().
    """

    name = "llm_validation"

    def __init__(self, router) -> None:
        self._router = router

    def should_run(self, ctx: PipelineContext) -> bool:
        """
        Corre si:
        1. El parse fue exitoso (hay AST y código)
        2. Hay resultado de complejidad que validar
        3. La flag está habilitada en DynamicConfig
        """
        if not ctx.parse_succeeded:
            return False
        if ctx.complexity is None:
            return False
        if not DynamicConfig.get("llm_validation_enabled", False):
            return False
        if not DynamicConfig.is_step_enabled("llm_validation"):
            return False
        return True

    async def execute(self, ctx: PipelineContext) -> PipelineContext:
        """
        Valida el resultado de complejidad con el LLM router.

        En caso de fallo, agrega warning y retorna ctx sin modificar
        los campos de complejidad (degradación elegante).
        """
        try:
            prompt = self._build_prompt(ctx)
            routed = await self._router.route(
                prompt=prompt,
                required_fields=_REQUIRED_FIELDS,
                system_prompt=(
                    "Eres un experto en análisis de complejidad algorítmica. "
                    "Responde SOLO con JSON válido."
                ),
            )

            self._process_response(ctx, routed)

        except Exception as exc:
            logger.warning(
                f"LLMValidationStep: fallo no crítico — {type(exc).__name__}: {exc}"
            )
            ctx.warnings.append(
                f"Validación LLM no disponible ({type(exc).__name__}) — "
                f"usando solo análisis estático"
            )

        return ctx

    def _build_prompt(self, ctx: PipelineContext) -> str:
        """Construye el prompt con el código y la complejidad calculada."""
        complexity = ctx.complexity
        return _VALIDATION_PROMPT_TEMPLATE.format(
            algorithm_code=ctx.request.code,
            big_o=complexity.big_o if complexity else "Desconocido",
            omega=complexity.omega if complexity else "Desconocido",
            theta=complexity.theta if complexity else "No calculado",
        )

    def _process_response(self, ctx: PipelineContext, routed) -> None:
        """
        Procesa la respuesta del router y actualiza el contexto.

        No sobreescribe Big O/Omega/Theta — solo agrega metadata
        de validación al contexto.
        """
        content = routed.response.content.strip()

        try:
            # Limpiar markdown fences si el LLM los incluyó
            for fence in ("```json", "```"):
                if content.startswith(fence):
                    content = content[len(fence):]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            llm_result = json.loads(content)

        except json.JSONDecodeError:
            ctx.warnings.append(
                f"LLM retornó respuesta no parseable "
                f"(score={routed.evaluation.score:.2f})"
            )
            return

        matches = llm_result.get("matches_our_analysis", True)
        llm_big_o = llm_result.get("big_o")
        reasoning = llm_result.get("reasoning", "")
        llm_errors = llm_result.get("errors", [])
        llm_warnings = llm_result.get("warnings", [])

        # Log del resultado
        logger.info(
            f"LLMValidationStep: llm={routed.llm_used} "
            f"matches={matches} "
            f"score={routed.evaluation.score:.2f} "
            f"llm_big_o={llm_big_o}"
        )

        # Si el LLM discrepa, agregar warning informativo
        if not matches and llm_big_o and llm_big_o != ctx.complexity.big_o:
            ctx.warnings.append(
                f"Discrepancia de validación LLM: "
                f"análisis estático={ctx.complexity.big_o}, "
                f"LLM={llm_big_o} ({routed.llm_used}). "
                f"Razón: {reasoning[:200]}"
            )

        # Propagar warnings del LLM
        for w in llm_warnings:
            ctx.warnings.append(f"LLM warning: {w}")

        # Los errores del LLM son informativos (no detienen el pipeline)
        for e in llm_errors:
            ctx.warnings.append(f"LLM error: {e}")

        # Guardar metadata de validación en el contexto
        # (el orchestrator puede incluirlo en config_snapshot al persistir)
        if not hasattr(ctx, "_llm_validation_metadata"):
            ctx.__dict__["_llm_validation_metadata"] = {}

        ctx.__dict__["_llm_validation_metadata"] = {
            "llm_used":     routed.llm_used,
            "matches":      matches,
            "llm_big_o":    llm_big_o,
            "score":        routed.evaluation.score,
            "fallback_used": routed.fallback_used,
            "reasoning":    reasoning[:500],
        }