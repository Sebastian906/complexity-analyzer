"""
AnalysisPipeline — Motor del pipeline de análisis.

Responsabilidades:
- Iterar los pasos en orden
- Llamar should_run() antes de cada paso
- Medir y registrar el tiempo de cada paso en ctx.step_times
- Capturar excepciones no manejadas (última línea de defensa)
- Detener el pipeline si ctx.has_critical_error es True

Lo que NO hace:
- No conoce la lógica de ningún paso
- No sabe qué módulos del core usa cada paso
- No construye el resultado final (eso es el orchestrator)
"""

from __future__ import annotations

import time
from typing import Sequence

from app.services.pipeline.context import PipelineContext
from app.services.pipeline.step import PipelineStep
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class AnalysisPipeline:
    """
    Motor del pipeline declarativo.

    Se construye con una lista ordenada de pasos y se ejecuta
    con un PipelineContext. Cada paso puede ser agregado,
    removido o reemplazado sin modificar el orchestrator.

    Example:
        >>> pipeline = AnalysisPipeline([
        ...     ParseStep(parser),
        ...     ComplexityStep(engine, request),
        ...     PatternStep(detector, request),
        ...     StructureStep(identifier, request),
        ...     SummarizeStep(),
        ... ])
        >>> ctx = await pipeline.run(PipelineContext(request=request))
    """

    def __init__(self, steps: Sequence[PipelineStep]) -> None:
        self._steps: list[PipelineStep] = list(steps)
        logger.debug(
            f"Pipeline creado con {len(self._steps)} pasos: "
            f"{[s.name for s in self._steps]}"
        )

    async def run(self, ctx: PipelineContext) -> PipelineContext:
        """
        Ejecuta el pipeline completo.

        Itera los pasos en orden. Si un paso falla con excepción
        no capturada, agrega el error al contexto y continúa
        (excepto si ctx.has_critical_error después del fallo).

        Args:
            ctx: Contexto inicial del pipeline.

        Returns:
            PipelineContext con todos los resultados acumulados.
        """
        logger.info(
            f"Pipeline iniciado — {len(self._steps)} pasos, "
            f"algoritmo: {ctx.algorithm_name!r}"
        )

        for step in self._steps:
            # Verificar si hay un error crítico antes de cada paso
            # (ParseStep falla → todos los demás no tienen AST)
            if ctx.has_critical_error:
                logger.warning(
                    f"Pipeline interrumpido antes de '{step.name}' "
                    f"por error crítico: {ctx.errors[-1]!r}"
                )
                break

            # El paso decide si debe correr
            if not step.should_run(ctx):
                logger.debug(f"Paso omitido: '{step.name}'")
                continue

            # Ejecutar con medición de tiempo
            start = time.perf_counter()
            try:
                ctx = await step.execute(ctx)
            except Exception as exc:
                # Última línea de defensa — el paso debería haber capturado esto
                logger.error(
                    f"Excepción no capturada en paso '{step.name}': {exc}",
                    exc_info=True,
                )
                ctx.errors.append(f"Error inesperado en '{step.name}': {exc}")
            finally:
                elapsed = time.perf_counter() - start
                ctx.step_times[step.name] = elapsed
                logger.debug(f"Paso '{step.name}' completado en {elapsed*1000:.1f}ms")

        total = sum(ctx.step_times.values())
        logger.info(
            f"Pipeline completado en {total*1000:.1f}ms — "
            f"errores: {len(ctx.errors)}, warnings: {len(ctx.warnings)}"
        )

        return ctx

    def register_step(
        self,
        step: PipelineStep,
        position: int = -1,
    ) -> None:
        """
        Agrega un paso al pipeline en tiempo de ejecución.

        Args:
            step:     Paso a agregar (debe implementar PipelineStep).
            position: Índice de inserción. -1 = al final.
                        0 = antes del primer paso.
                        Útil para insertar LLMValidationStep antes de Summarize.

        Example:
            >>> pipeline.register_step(LLMValidationStep(router), position=4)
        """
        if not isinstance(step, PipelineStep):
            raise TypeError(
                f"{step!r} no implementa el protocolo PipelineStep. "
                f"Debe tener: name, should_run(), execute()."
            )

        if position == -1:
            self._steps.append(step)
        else:
            self._steps.insert(position, step)

        logger.debug(
            f"Paso '{step.name}' registrado en posición "
            f"{position if position != -1 else len(self._steps) - 1}"
        )

    def remove_step(self, name: str) -> bool:
        """
        Elimina un paso por nombre.

        Args:
            name: Nombre del paso a eliminar.

        Returns:
            True si se encontró y eliminó, False si no existía.
        """
        for i, step in enumerate(self._steps):
            if step.name == name:
                self._steps.pop(i)
                logger.debug(f"Paso '{name}' eliminado del pipeline")
                return True
        return False

    @property
    def step_names(self) -> list[str]:
        """Lista de nombres de pasos en orden de ejecución."""
        return [s.name for s in self._steps]

    def __repr__(self) -> str:
        return f"<AnalysisPipeline steps={self.step_names}>"