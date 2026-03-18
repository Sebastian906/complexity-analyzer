"""
Analysis Orchestrator - Orquestación de Análisis Completo

Coordina todos los módulos de análisis (Parser, Analyzer, Patterns, Structures, Visualization)
para proporcionar un análisis completo de algoritmos en un solo flujo.
"""
from __future__ import annotations
import asyncio
import time
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from app.core.analyzer import AnalyzerEngine
from app.core.config import settings
from app.core.data_structures import StructureIdentifier
from app.core.exceptions import AnalyzerException, ParserException, TimeoutException
from app.core.parser import PseudocodeParser, ProgramNode
from app.core.patterns import PatternDetector
from app.core.visualization import (
    RenderFormat,
    generate_execution_flow,
    generate_recursion_tree,
)
from app.core.visualization.diagram_renderer import render_diagram_async
from app.profiling import get_performance_monitor
from app.schemas import (
    AlgorithmInfo,
    AlgorithmParameter,
    AnalysisMetadata,
    CompleteAnalysisRequest,
    CompleteAnalysisResult,
    TimingMetadata,
    VisualizationResult,
)
from app.schemas.analysis_result import (
    LineByLineAnalysis,
    PatternDetectionResult,
    StructureDetectionResult,
)
from app.schemas.complexity import ComplexityAnalysis, SpaceComplexityAnalysis
from app.schemas.pattern import ScoredPattern
from app.services.cache_service import CacheKey, generate_cache_key, get_cache_service
from app.services.summarizer import Summarizer
from app.services.transformers import (
    ComplexityTransformer,
    PatternMapper,
    StructureTransformer,
)
from app.utils.logger import setup_logger

if TYPE_CHECKING:
    from app.infrastructure.agents.coordinator_agent import CoordinatorAgent

logger = setup_logger(__name__)

class AnalysisOrchestrator:
    """
    Orquestador de análisis completo.

    Punto de entrada para el análisis de un algoritmo. Solo coordina;
    toda la lógica de dominio vive en los módulos del core y los
    transformers se encargan de la traducción de tipos.

    Example:
        >>> orchestrator = AnalysisOrchestrator()
        >>> request = CompleteAnalysisRequest(
        ...     code="algorithm test(n)\\nbegin\\n  for i <- 1 to n do\\n    x <- x+1\\nend",
        ...     analyze_complexity=True,
        ...     analyze_patterns=True,
        ... )
        >>> result = await orchestrator.analyze_complete(request)
        >>> print(result.summary)
    """

    def __init__(
        self,
        parser: Optional[PseudocodeParser] = None,
        analyzer_engine: Optional[AnalyzerEngine] = None,
        pattern_detector: Optional[PatternDetector] = None,
        structure_identifier: Optional[StructureIdentifier] = None,
    ) -> None:
        self.parser = parser or PseudocodeParser()
        self.analyzer_engine = analyzer_engine or AnalyzerEngine()
        self.pattern_detector = pattern_detector or PatternDetector()
        self.structure_identifier = structure_identifier or StructureIdentifier()

        self.profiling_enabled = settings.APP_ENV in ("development", "staging")
        self.monitor = get_performance_monitor() if self.profiling_enabled else None

        logger.info("AnalysisOrchestrator inicializado")

    #  Punto de entrada público                                           #
    async def analyze_complete(
        self,
        request: CompleteAnalysisRequest,
    ) -> CompleteAnalysisResult:
        """
        Ejecuta análisis completo de un algoritmo.

        Aplica cache antes de ejecutar el pipeline. Si el resultado está
        en cache, lo retorna directamente sin tocar ningún módulo del core.
        """
        logger.info("Iniciando análisis completo")

        # Feature flag: sistema multiagente (LangGraph)
        if settings.ENABLE_MULTIAGENT_SYSTEM:
            try:
                from app.infrastructure.agents.coordinator_agent import CoordinatorAgent

                logger.info("Delegando al sistema multiagente (LangGraph)")
                coordinator = CoordinatorAgent(use_llm=True)
                agent_result = await coordinator.execute_pipeline(request.code)
                return self._map_agent_result(agent_result, request)
            except Exception as exc:
                logger.error(
                    f"Sistema multiagente falló: {exc}. Usando análisis directo."
                )

        # Cache check
        cache = get_cache_service()
        cache_key = generate_cache_key(
            CacheKey.ANALYSIS,
            request.code,
            analyze_complexity=request.analyze_complexity,
            analyze_patterns=request.analyze_patterns,
            analyze_structures=request.analyze_structures,
            generate_visualizations=request.generate_visualizations,
        )

        cached = await cache.get(cache_key)
        if cached is not None:
            logger.info("Cache HIT para análisis completo")
            return cached

        # Ejecutar pipeline
        if self.profiling_enabled and self.monitor:
            with self.monitor.monitor("analyze_complete", module="orchestrator") as metrics:
                result = await self._execute_pipeline(request)
                if metrics and metrics.execution_time_ms > 2000:
                    logger.warning(
                        f"Análisis lento: {metrics.execution_time_ms / 1000:.2f}s, "
                        f"memoria: {metrics.memory_delta_mb:.2f}MB"
                    )
        else:
            result = await self._execute_pipeline(request)

        if result.success:
            await cache.set(cache_key, result, ttl=settings.CACHE_TTL_ANALYSIS)

        return result

    #  Pipeline principal                                                  
    async def _execute_pipeline(
        self,
        request: CompleteAnalysisRequest,
    ) -> CompleteAnalysisResult:
        """Ejecuta el pipeline completo de análisis."""
        started_at = datetime.utcnow()
        start_time = time.time()
        errors: list[str] = []
        warnings: list[str] = []

        # PASO 1: Parse
        ast, algorithm_info = await self._step_parse(request, errors)
        if ast is None:
            return self._build_result(
                started_at, start_time, algorithm_info, errors=errors
            )

        # PASOS 2-4: Análisis paralelo (independientes entre sí)
        complexity, patterns, structures = await self._step_parallel_analysis(
            ast, request, errors, warnings
        )

        # PASO 5: Visualizaciones
        visualizations: list[VisualizationResult] = []
        if request.generate_visualizations:
            visualizations = await self._step_visualizations(
                ast, request, complexity
            )

        return self._build_result(
            started_at,
            start_time,
            algorithm_info,
            complexity=complexity,
            patterns=patterns,
            structures=structures,
            visualizations=visualizations,
            errors=errors,
            warnings=warnings,
        )

    #  Pasos del pipeline                                                  #
    async def _step_parse(
        self,
        request: CompleteAnalysisRequest,
        errors: list[str],
    ) -> tuple[Optional[ProgramNode], Optional[AlgorithmInfo]]:
        """Paso 1: Parsing del código."""
        try:
            ast = self.parser.parse(request.code, validate=True)
            algorithm_info = self._extract_algorithm_info(ast, request.code)
            return ast, algorithm_info
        except ParserException as exc:
            logger.error(f"Error en parsing: {exc}")
            errors.append(f"Error de parsing: {exc}")
            algorithm_info = AlgorithmInfo(
                name="unknown",
                parameters=[],
                has_recursion=False,
                has_loops=False,
                max_nesting_depth=0,
                total_lines=len(request.code.splitlines()),
                total_statements=0,
            )
            return None, algorithm_info

    async def _step_parallel_analysis(
        self,
        ast: ProgramNode,
        request: CompleteAnalysisRequest,
        errors: list[str],
        warnings: list[str],
    ) -> tuple[
        Optional[ComplexityAnalysis],
        Optional[PatternDetectionResult],
        Optional[StructureDetectionResult],
    ]:
        """
        Pasos 2-4 en paralelo: complejidad, patrones y estructuras.

        Los tres módulos son independientes — no comparten estado entre sí
        y todos reciben el mismo AST de lectura. asyncio.gather() los ejecuta
        concurrentemente dentro del event loop.
        """
        async def run_complexity() -> Optional[ComplexityAnalysis]:
            if not request.analyze_complexity:
                return None
            try:
                core_result = self.analyzer_engine.analyze(
                    ast,
                    analyze_line_by_line=request.complexity_options.analyze_line_by_line,
                    analyze_space=request.complexity_options.analyze_spatial,
                    analyze_recurrence=request.complexity_options.analyze_recurrence,
                    analyze_tight_bounds=request.complexity_options.calculate_tight_bounds,
                    source_code=request.code,
                )
                if core_result is None:
                    errors.append("Analyzer retornó resultado nulo")
                    return None
                return ComplexityTransformer.to_schema(core_result)
            except AnalyzerException as exc:
                logger.error(f"Error en análisis de complejidad: {exc}")
                errors.append(f"Error en análisis de complejidad: {exc}")
                return None
            except Exception as exc:
                logger.error(f"Error inesperado en analyzer: {exc}", exc_info=True)
                errors.append(f"Error en análisis: {exc}")
                return None

        async def run_patterns() -> Optional[PatternDetectionResult]:
            if not request.analyze_patterns:
                return None
            try:
                core_result = self.pattern_detector.detect(
                    ast,
                    min_confidence=request.pattern_options.min_confidence,
                )
                return PatternMapper.result_to_schema(core_result)
            except Exception as exc:
                logger.warning(f"Error en detección de patrones: {exc}")
                warnings.append(f"Detección de patrones fallida: {exc}")
                return None

        async def run_structures() -> Optional[StructureDetectionResult]:
            if not request.analyze_structures:
                return None
            try:
                core_result = self.structure_identifier.identify(
                    ast,
                    min_confidence=request.structure_options.min_confidence,
                )
                return StructureTransformer.to_schema(core_result)
            except Exception as exc:
                logger.warning(f"Error en detección de estructuras: {exc}")
                warnings.append(f"Detección de estructuras fallida: {exc}")
                return None

        results = await asyncio.gather(
            run_complexity(),
            run_patterns(),
            run_structures(),
            return_exceptions=True,
        )

        complexity = results[0] if not isinstance(results[0], Exception) else None
        patterns   = results[1] if not isinstance(results[1], Exception) else None
        structures = results[2] if not isinstance(results[2], Exception) else None

        for i, (name, res) in enumerate(
            zip(("complexity", "patterns", "structures"), results)
        ):
            if isinstance(res, Exception):
                logger.error(f"Excepción no capturada en {name}: {res}")
                warnings.append(f"{name} falló con excepción: {res}")

        return complexity, patterns, structures

    async def _step_visualizations(
        self,
        ast: ProgramNode,
        request: CompleteAnalysisRequest,
        complexity: Optional[ComplexityAnalysis],
    ) -> list[VisualizationResult]:
        """Paso 5: Generación de visualizaciones."""
        from app.schemas.analysis_request import VisualizationType

        visualizations: list[VisualizationResult] = []

        if VisualizationType.RECURSION_TREE in request.visualization_options.types:
            if complexity and complexity.has_tight_bound:
                try:
                    tree_result = generate_recursion_tree(
                        ast,
                        start_value=request.visualization_options.start_value,
                        max_depth=request.visualization_options.max_depth,
                    )
                    rendered = await render_diagram_async(
                        tree_result,
                        format=RenderFormat(request.visualization_options.format),
                    )
                    content = rendered.content
                    if isinstance(content, bytes):
                        content = content.decode("utf-8", errors="replace")

                    visualizations.append(
                        VisualizationResult(
                            type="recursion_tree",
                            format=request.visualization_options.format,
                            content=content,
                            file_path=None,
                            statistics={
                                "recursion_type": tree_result.recursion_type.value,
                                "total_calls":    tree_result.total_calls,
                                "max_depth":      tree_result.max_depth,
                            },
                            metadata={
                                "algorithm_name": (
                                    ast.algorithm.name if ast.algorithm else "unknown"
                                )
                            },
                        )
                    )
                except Exception as exc:
                    logger.warning(f"Error generando árbol de recursión: {exc}")

        if VisualizationType.EXECUTION_FLOW in request.visualization_options.types:
            try:
                flow_result = generate_execution_flow(ast)
                rendered = await render_diagram_async(
                    flow_result,
                    format=RenderFormat(request.visualization_options.format),
                )
                content = rendered.content
                if isinstance(content, bytes):
                    content = content.decode("utf-8", errors="replace")

                visualizations.append(
                    VisualizationResult(
                        type="execution_flow",
                        format=request.visualization_options.format,
                        content=content,
                        file_path=None,
                        statistics=flow_result.statistics,
                        metadata={
                            "algorithm_name": (
                                ast.algorithm.name if ast.algorithm else "unknown"
                            )
                        },
                    )
                )
            except Exception as exc:
                logger.warning(f"Error generando flujo de ejecución: {exc}")

        return visualizations

    #  Construcción del resultado final                                    #
    def _build_result(
        self,
        started_at: datetime,
        start_time: float,
        algorithm_info: Optional[AlgorithmInfo],
        complexity: Optional[ComplexityAnalysis] = None,
        patterns: Optional[PatternDetectionResult] = None,
        structures: Optional[StructureDetectionResult] = None,
        visualizations: Optional[list[VisualizationResult]] = None,
        errors: Optional[list[str]] = None,
        warnings: Optional[list[str]] = None,
    ) -> CompleteAnalysisResult:
        """Construye el schema de respuesta final."""
        errors = errors or []
        warnings = warnings or []

        if not errors and complexity is None:
            logger.warning("complexity es None sin errores — posible fallo silencioso")
            errors.append("Análisis de complejidad no completado")

        algorithm_name = algorithm_info.name if algorithm_info else "unknown"

        summary = Summarizer.generate_summary(
            algorithm_name, complexity, None, patterns, structures
        )
        recommendations = Summarizer.generate_recommendations(complexity, patterns)

        return CompleteAnalysisResult(
            success=len(errors) == 0,
            message="Análisis completado" if not errors else "Análisis con errores",
            algorithm_name=algorithm_name,
            algorithm_info=algorithm_info,
            complexity=complexity,
            space_complexity=None,
            recurrence_temporal=None,
            recurrence_spatial=None,
            line_by_line=None,
            patterns=patterns,
            structures=structures,
            visualizations=visualizations or [],
            metadata=AnalysisMetadata(
                timing=TimingMetadata(started_at=started_at),
                resources=None,
                version="1.0.0",
                environment=settings.APP_ENV,
            ),
            summary=summary,
            recommendations=recommendations,
        )

    #  Extracción de información del AST                                   #
    def _extract_algorithm_info(
        self, ast: ProgramNode, code: str
    ) -> AlgorithmInfo:
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

    #  Compatibilidad con sistema multiagente                              #
    def _map_agent_result(
        self,
        agent_result: dict,
        request: CompleteAnalysisRequest,
    ) -> CompleteAnalysisResult:
        """
        Convierte el dict de CoordinatorAgent al schema CompleteAnalysisResult.

        El pipeline de agentes devuelve claves: success, algorithm_name,
        complexity, patterns, structures, validation, errors.
        """
        started_at = datetime.utcnow()
        start_time = time.time()

        errors = [
            e.get("error", str(e)) if isinstance(e, dict) else str(e)
            for e in agent_result.get("errors", [])
        ]

        raw_complexity = agent_result.get("complexity") or {}
        complexity_schema: Optional[ComplexityAnalysis] = None
        if raw_complexity.get("big_o"):
            complexity_schema = ComplexityAnalysis(
                big_o=raw_complexity.get("big_o", "O(?)"),
                omega=raw_complexity.get("omega", "Ω(?)"),
                theta=raw_complexity.get("theta"),
                big_o_class=ComplexityTransformer.notation_to_class(
                    raw_complexity.get("big_o", "")
                ),
                omega_class=ComplexityTransformer.notation_to_class(
                    raw_complexity.get("omega", "")
                ),
                theta_class=ComplexityTransformer.notation_to_class(
                    raw_complexity.get("theta", "")
                ),
                explanation="Complejidad validada por sistema multiagente",
                reasoning=[
                    "Análisis realizado por ComplexityAgent",
                    f"Validación LLM: "
                    f"{raw_complexity.get('llm_validation', {}).get('big_o', 'N/A')}",
                ],
                has_tight_bound=raw_complexity.get("theta") is not None,
            )

        # Patrones y estructuras del agente se construyen mínimos
        # (el agente no produce el detalle completo de indicadores)
        raw_patterns = agent_result.get("patterns") or {}
        patterns_schema: Optional[PatternDetectionResult] = None
        if raw_patterns.get("primary_pattern"):
            from app.schemas.analysis_result import PatternDetectionResult as APDR

            patterns_schema = APDR(
                patterns_found=[],
                scored_patterns=[],
                primary_pattern=None,
                confident_patterns=[],
                summary=raw_patterns.get("summary", ""),
                pattern_count=len(raw_patterns.get("all_patterns", [])),
                metadata={"source": "multiagent"},
            )

        raw_structures = agent_result.get("structures") or {}
        structures_schema: Optional[StructureDetectionResult] = None
        if raw_structures.get("primary_structure"):
            structures_schema = StructureDetectionResult(
                structures_found=[],
                primary_structure=None,
                primary_usage=None,
                summary=raw_structures.get("summary", ""),
            )

        algorithm_name = agent_result.get("algorithm_name") or "unknown"
        algorithm_info = AlgorithmInfo(
            name=algorithm_name,
            parameters=[],
            has_recursion=False,
            has_loops=False,
            max_nesting_depth=0,
            total_lines=0,
            total_statements=0,
        )

        return self._build_result(
            started_at,
            start_time,
            algorithm_info,
            complexity=complexity_schema,
            patterns=patterns_schema,
            structures=structures_schema,
            errors=errors,
        )