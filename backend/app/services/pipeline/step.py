"""
PipelineStep — Protocolo (interfaz) que todo paso del pipeline debe implementar.

Por qué Protocol y no ABC:
- Protocol es estructural (duck typing): cualquier clase que tenga
    `name`, `should_run()` y `execute()` es un paso válido, sin
    necesidad de importar ni heredar de esta clase.
- Facilita el testing: los mocks no necesitan heredar de nada.
- Facilita plugins externos: código de terceros puede implementar
    pasos sin depender del paquete completo.

Contrato que cada paso debe respetar:
1. should_run() no debe tener side effects — solo leer el contexto.
2. execute() debe SIEMPRE retornar el contexto (modificado o no).
3. execute() NUNCA debe lanzar excepciones no capturadas —
    agregar a ctx.errors o ctx.warnings y retornar.
4. execute() solo modifica los campos del contexto que le pertenecen.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.services.pipeline.context import PipelineContext

@runtime_checkable
class PipelineStep(Protocol):
    """
    Protocolo mínimo para pasos del pipeline.

    runtime_checkable permite usar isinstance(obj, PipelineStep)
    en tests y en el motor para validar que los pasos son correctos.
    """

    name: str
    """Identificador único del paso. Usado en logs y step_times."""

    def should_run(self, ctx: PipelineContext) -> bool:
        """
        Decide si este paso debe ejecutarse dado el estado actual del contexto.

        Ejemplos de decisiones:
        - ComplexityStep: retorna ctx.request.analyze_complexity
        - ParseStep: siempre retorna True
        - LLMValidationStep: retorna settings flag Y ctx.parse_succeeded

        No debe tener side effects.
        """
        ...

    async def execute(self, ctx: PipelineContext) -> PipelineContext:
        """
        Ejecuta la lógica del paso y retorna el contexto modificado.

        Contrato:
        - Siempre retorna ctx (aunque no lo modifique).
        - Captura sus propias excepciones y las agrega a ctx.errors
            o ctx.warnings según gravedad.
        - No llama a pasos anteriores ni posteriores.
        """
        ...