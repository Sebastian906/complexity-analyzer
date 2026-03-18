"""
ParseStep

Convierte el código fuente en un AST y extrae información básica
del algoritmo. Es el único paso que puede causar una parada total
del pipeline (si falla, ctx.has_critical_error es True).
"""

from __future__ import annotations

from app.core.exceptions import ParserException
from app.core.parser import PseudocodeParser
from app.schemas.algorithm import AlgorithmInfo, AlgorithmParameter
from app.services.pipeline.context import PipelineContext
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class ParseStep:
    """
    Paso de parsing: código fuente → AST + AlgorithmInfo.

    Siempre se ejecuta (should_run retorna True).
    Si el parse falla, agrega a ctx.errors y retorna sin AST,
    lo que causa que has_critical_error sea True y el pipeline
    se detenga antes del siguiente paso.
    """

    name = "parse"

    def __init__(self, parser: PseudocodeParser = None) -> None:
        self._parser = parser or PseudocodeParser()

    def should_run(self, ctx: PipelineContext) -> bool:
        return True

    async def execute(self, ctx: PipelineContext) -> PipelineContext:
        try:
            ctx.ast = self._parser.parse(ctx.request.code, validate=True)
            ctx.algorithm_info = self._extract_algorithm_info(
                ctx.ast, ctx.request.code
            )
            logger.debug(
                f"ParseStep: algoritmo '{ctx.algorithm_name}' parseado correctamente"
            )
        except ParserException as exc:
            logger.error(f"ParseStep: error de parsing — {exc}")
            ctx.errors.append(f"Error de parsing: {exc}")
            ctx.algorithm_info = AlgorithmInfo(
                name="unknown",
                parameters=[],
                has_recursion=False,
                has_loops=False,
                max_nesting_depth=0,
                total_lines=len(ctx.request.code.splitlines()),
                total_statements=0,
            )
        except Exception as exc:
            logger.error(f"ParseStep: error inesperado — {exc}", exc_info=True)
            ctx.errors.append(f"Error inesperado en parsing: {exc}")

        return ctx

    def _extract_algorithm_info(self, ast, code: str) -> AlgorithmInfo:
        """Extrae metadatos del algoritmo desde el AST."""
        parameters: list[AlgorithmParameter] = []

        if ast.algorithm and ast.algorithm.parameters:
            for param in ast.algorithm.parameters:
                parameters.append(
                    AlgorithmParameter(
                        name=param.name,
                        type=getattr(param, "type", None),
                        is_array=getattr(param, "is_array", False),
                        dimensions=getattr(param, "dimensions", []),
                        is_object=getattr(param, "is_object", False),
                        object_type=getattr(param, "object_type", None),
                        description=None,
                    )
                )

        return AlgorithmInfo(
            name=ast.algorithm.name if ast.algorithm else "unknown",
            parameters=parameters,
            has_recursion=False,
            has_loops=True,
            max_nesting_depth=0,
            total_lines=len(code.splitlines()),
            total_statements=0,
        )