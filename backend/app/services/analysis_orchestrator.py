"""
Analysis Orchestrator - Orquestación de Análisis Completo

Coordina todos los módulos de análisis (Parser, Analyzer, Patterns, Structures, Visualization)
para proporcionar un análisis completo de algoritmos en un solo flujo.
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from app.core.analyzer import AnalyzerEngine
from app.core.config import settings
from app.core.data_structures import StructureIdentifier
from app.core.parser import PseudocodeParser
from app.core.patterns import PatternDetector
from app.profiling import get_performance_monitor
from app.schemas import (
    AnalysisMetadata,
    CompleteAnalysisRequest,
    CompleteAnalysisResult,
    TimingMetadata,
)
from app.services.cache_service import CacheKey, generate_cache_key, get_cache_service
from app.services.pipeline import AnalysisPipeline, PipelineContext
from app.services.pipeline.steps import (
    ComplexityStep,
    ParseStep,
    PatternStep,
    StructureStep,
    SummarizeStep,
)
from app.utils.logger import setup_logger
from app.services.dynamic_config import DynamicConfig

if TYPE_CHECKING:
    pass

logger = setup_logger(__name__)

class AnalysisOrchestrator:
    """
    Orquestador de análisis completo.

    Construye el pipeline inyectando dependencias y convierte
    el PipelineContext resultante al schema CompleteAnalysisResult.

    La interfaz pública (analyze_complete) es idéntica a la versión
    anterior — ningún endpoint ni test necesita cambiar.

    Example:
        >>> orchestrator = AnalysisOrchestrator()
        >>> result = await orchestrator.analyze_complete(
        ...     CompleteAnalysisRequest(code="algorithm test(n)...")
        ... )
    """

    def __init__(
        self,
        parser: Optional[PseudocodeParser] = None,
        analyzer_engine: Optional[AnalyzerEngine] = None,
        pattern_detector: Optional[PatternDetector] = None,
        structure_identifier: Optional[StructureIdentifier] = None,
    ) -> None:
        self._parser = parser or PseudocodeParser()
        self._engine = analyzer_engine or AnalyzerEngine()
        self._detector = pattern_detector or PatternDetector()
        self._identifier = structure_identifier or StructureIdentifier()

        self._profiling = settings.APP_ENV in ("development", "staging")
        self._monitor = get_performance_monitor() if self._profiling else None

        logger.info("AnalysisOrchestrator inicializado con pipeline formal")

    #  Punto de entrada público                                           
    async def analyze_complete(
        self,
        request: CompleteAnalysisRequest,
    ) -> CompleteAnalysisResult:
        """
        Ejecuta análisis completo de un algoritmo.

        Verifica cache antes de construir el pipeline. Si hay hit,
        retorna directamente. Si no, ejecuta el pipeline y cachea
        el resultado si fue exitoso.
        """
        logger.info(f"Análisis completo solicitado — code length: {len(request.code)}")

        # Feature flag: sistema multiagente
        if settings.ENABLE_MULTIAGENT_SYSTEM:
            try:
                from app.infrastructure.agents.coordinator_agent import CoordinatorAgent

                logger.info("Delegando al sistema multiagente (LangGraph)")
                coordinator = CoordinatorAgent(use_llm=True)
                agent_result = await coordinator.execute_pipeline(request.code)
                return self._map_agent_result(agent_result, request)
            except Exception as exc:
                logger.error(f"Sistema multiagente falló: {exc}. Usando pipeline directo.")

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

        if request.use_cache:
            cached = await cache.get(cache_key)
            if cached is not None:
                logger.info("Cache HIT para análisis completo")
                return cached

        # Ejecutar pipeline con profiling opcional
        if self._profiling and self._monitor:
            with self._monitor.monitor("analyze_complete", module="orchestrator") as m:
                result = await self._run_pipeline(request)
                if m and m.execution_time_ms > 2000:
                    logger.warning(
                        f"Análisis lento: {m.execution_time_ms/1000:.2f}s, "
                        f"memoria: {m.memory_delta_mb:.2f}MB"
                    )
        else:
            result = await self._run_pipeline(request)

        if result.success and request.use_cache:
            await cache.set(cache_key, result, ttl=settings.CACHE_TTL_ANALYSIS)

        return result

    #  Pipeline                                                           
    async def _run_pipeline(
        self,
        request: CompleteAnalysisRequest,
    ) -> CompleteAnalysisResult:
        """Construye y ejecuta el pipeline, retorna el resultado final."""

        # Construir pipeline con los pasos base
        # Cada paso recibe la request para leer sus opciones específicas
        pipeline = AnalysisPipeline([
            ParseStep(self._parser),
            ComplexityStep(self._engine, request),
            PatternStep(self._detector, request),
            StructureStep(self._identifier, request),
            SummarizeStep(),
        ])

        # Si la visualización está habilitada, agregar el paso opcional
        # (implementado en el Paso 3 de la hoja de ruta)
        # if request.generate_visualizations:
        #     from app.services.pipeline.steps.visualization_step import VisualizationStep
        #     pipeline.register_step(VisualizationStep(request), position=-1)

        if DynamicConfig.get("llm_validation_enabled", False):
            from app.services.pipeline.steps.llm_validation_step import LLMValidationStep
            from app.infrastructure.llm.llm_factory import LLMFactory
            pipeline.register_step(LLMValidationStep(LLMFactory.create_router()), position=4)

        ctx = PipelineContext(request=request)
        ctx = await pipeline.run(ctx)

        return self._build_result(ctx)

    #  Construcción del resultado final                                   
    def _build_result(self, ctx: PipelineContext) -> CompleteAnalysisResult:
        """
        Construye el schema CompleteAnalysisResult desde el contexto final.

        Es el único lugar donde el orchestrator sabe sobre los schemas
        de respuesta. Todo lo demás está en los pasos y transformers.
        """
        # If complexity analysis did not run but no explicit errors, add a warning
        if not ctx.errors and ctx.complexity is None:
            logger.warning(
                f"complexity es None sin errores para '{ctx.algorithm_name}' "
                f"— posible fallo silencioso"
            )
            ctx.errors.append("Análisis de complejidad no completado")

        # Consider the analysis successful if there are no errors OR
        # if complexity was produced (tolerate non-critical step errors).
        success_flag = len(ctx.errors) == 0 or (ctx.complexity is not None)

        # Enrich timing metadata
        timing = TimingMetadata(started_at=ctx.started_at)
        timing.completed_at = datetime.utcnow()

        return CompleteAnalysisResult(
            success=success_flag,
            message=(
                "Análisis completado exitosamente"
                if not ctx.errors
                else "Análisis completado con errores"
            ),
            algorithm_name=ctx.algorithm_name,
            algorithm_info=ctx.algorithm_info,
            complexity=ctx.complexity,
            space_complexity=ctx.space_complexity,
            recurrence_temporal=ctx.recurrence_temporal,
            recurrence_spatial=ctx.recurrence_spatial,
            line_by_line=ctx.line_by_line,
            patterns=ctx.patterns,
            structures=ctx.structures,
            visualizations=ctx.visualizations,
            metadata=AnalysisMetadata(
                timing=timing,
                resources=None,
                errors=list(ctx.errors),
                version="1.0.0",
                environment=settings.APP_ENV,
            ),
            summary=ctx.summary,
            recommendations=ctx.recommendations,
        )

    #  Compatibilidad multiagente                                         
    def _map_agent_result(
        self,
        agent_result: dict,
        request: CompleteAnalysisRequest,
    ) -> CompleteAnalysisResult:
        """Convierte el resultado del CoordinatorAgent al schema de la API."""
        from app.services.transformers import ComplexityTransformer
        from app.schemas.analysis_result import (
            PatternDetectionResult,
            StructureDetectionResult,
        )
        from app.schemas.algorithm import AlgorithmInfo
        from app.schemas.complexity import ComplexityAnalysis

        errors = [
            e.get("error", str(e)) if isinstance(e, dict) else str(e)
            for e in agent_result.get("errors", [])
        ]

        raw_c = agent_result.get("complexity") or {}
        complexity = None
        if raw_c.get("big_o"):
            complexity = ComplexityAnalysis(
                big_o=raw_c.get("big_o", "O(?)"),
                omega=raw_c.get("omega", "Ω(?)"),
                theta=raw_c.get("theta"),
                big_o_class=ComplexityTransformer.notation_to_class(raw_c.get("big_o", "")),
                omega_class=ComplexityTransformer.notation_to_class(raw_c.get("omega", "")),
                theta_class=ComplexityTransformer.notation_to_class(raw_c.get("theta", "")),
                explanation="Complejidad validada por sistema multiagente",
                reasoning=["Análisis realizado por ComplexityAgent"],
                has_tight_bound=raw_c.get("theta") is not None,
            )

        raw_p = agent_result.get("patterns") or {}
        patterns = None
        if raw_p.get("primary_pattern"):
            patterns = PatternDetectionResult(
                patterns_found=[], scored_patterns=[], primary_pattern=None,
                confident_patterns=[], summary=raw_p.get("summary", ""),
                pattern_count=0, metadata={"source": "multiagent"},
            )

        raw_s = agent_result.get("structures") or {}
        structures = None
        if raw_s.get("primary_structure"):
            structures = StructureDetectionResult(
                structures_found=[], primary_structure=None,
                primary_usage=None, summary=raw_s.get("summary", ""),
            )

        algorithm_name = agent_result.get("algorithm_name") or "unknown"
        algorithm_info = AlgorithmInfo(
            name=algorithm_name, parameters=[], has_recursion=False,
            has_loops=False, max_nesting_depth=0, total_lines=0, total_statements=0,
        )

        from app.services.summarizer import Summarizer
        summary = Summarizer.generate_summary(algorithm_name, complexity, None, patterns, structures)
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
            visualizations=[],
            metadata=AnalysisMetadata(
                timing=TimingMetadata(started_at=datetime.utcnow()),
                resources=None,
                version="1.0.0",
                environment=settings.APP_ENV,
            ),
            summary=summary,
            recommendations=recommendations,
        )