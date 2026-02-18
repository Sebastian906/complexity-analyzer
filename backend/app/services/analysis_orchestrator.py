"""
Analysis Orchestrator - Orquestación de Análisis Completo

Coordina todos los módulos de análisis (Parser, Analyzer, Patterns, Structures, Visualization)
para proporcionar un análisis completo de algoritmos en un solo flujo.
"""
from __future__ import annotations
import time
from datetime import datetime
from typing import Optional
from uuid import uuid4
import asyncio

from app.core.parser import PseudocodeParser, ProgramNode
from app.core.analyzer import AnalyzerEngine
from app.core.patterns import PatternDetector
from app.core.data_structures import StructureIdentifier
from app.core.visualization import (
    generate_recursion_tree,
    generate_execution_flow,
    render_diagram,
    RenderFormat,
)
from app.core.exceptions import (
    ParserException,
    AnalyzerException,
    TimeoutException,
)
from app.core.config import settings
from app.schemas import (
    # Request Schemas
    CompleteAnalysisRequest,
    
    # Result Schemas
    CompleteAnalysisResult,
    LineByLineAnalysis,
    LineExecution,
    VisualizationResult,
    StructureDetectionResult,
    StructureMatch,
    StructureUsage,
    PatternDetectionResult,
    
    # Algorithm Schemas
    AlgorithmInfo,
    AlgorithmParameter,
    
    # Complexity Schemas
    ComplexityAnalysis,
    SpaceComplexityAnalysis,
    RecurrenceEquation,
    ComplexityClass,
    
    # Pattern Schemas
    PatternMatch,
    ScoredPattern,
    PatternIndicator,
    
    # Common Schemas
    AnalysisMetadata,
    TimingMetadata,
    ConfidenceLevelEnum,
)
from app.utils.logger import setup_logger

from app.profiling import get_performance_monitor

# Import TYPE_CHECKING: solo para anotaciones, no genera importación circular
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.infrastructure.agents.coordinator_agent import CoordinatorAgent

logger = setup_logger(__name__)

class AnalysisOrchestrator:
    """
    Orquestador de análisis completo refactorizado.

    Utiliza schemas de Pydantic para DTOs y respuestas.

    Example:
        >>> orchestrator = AnalysisOrchestrator()
        >>> request = CompleteAnalysisRequest(
        ...     code="algorithm test(n)\\nbegin\\n  for i <- 1 to n do\\n    x <- x + 1\\nend",
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
    ):
        """Inicializa el orquestador."""
        self.parser = parser or PseudocodeParser()
        self.analyzer_engine = analyzer_engine or AnalyzerEngine()
        self.pattern_detector = pattern_detector or PatternDetector()
        self.structure_identifier = structure_identifier or StructureIdentifier()

        # ========== PROFILING INIT ==========
        # Obtener monitor de performance
        self.profiling_enabled = settings.APP_ENV in ["development", "staging"]
        if self.profiling_enabled:
            self.monitor = get_performance_monitor()
            logger.info("AnalysisOrchestrator con profiling habilitado")
        else:
            self.monitor = None
        # ====================================

        logger.info("AnalysisOrchestrator inicializado")

    async def analyze_complete(
        self,
        request: CompleteAnalysisRequest
    ) -> CompleteAnalysisResult:
        """
        Ejecuta análisis completo de un algoritmo.

        Args:
            request: Configuración del análisis (CompleteAnalysisRequest schema)

        Returns:
            CompleteAnalysisResult: Resultado completo usando schemas
        """
        logger.info("Iniciando análisis completo")

        # FEATURE FLAG: Sistema multiagente
        if settings.ENABLE_MULTIAGENT_SYSTEM:
            try:
                # Lazy import para evitar circular imports
                from app.infrastructure.agents.coordinator_agent import CoordinatorAgent
                logger.info('Delegado al sistema multiagente (LangGraph)')
                coordinator = CoordinatorAgent(use_llm=True)
                agent_result = await coordinator.execute_pipeline(request.code)
                return self._map_agent_result(agent_result, request)
            except Exception as e:
                logger.error(f'Error en sistemas multiagente: {e}. Usando análisis directo.')
                # Fallback automático al análisis directo si el pipeline falla

        # PROFILING: Monitorear análisis completo
        if self.profiling_enabled and self.monitor:
            with self.monitor.monitor("analyze_complete", module="orchestrator") as metrics:
                result = await self._execute_analysis(request)
                
                # Log métricas si la operación fue lenta (execution_time_ms > 2000ms = 2s)
                if metrics and metrics.execution_time_ms > 2000:
                    logger.warning(
                        f"Análisis completo lento: {metrics.execution_time_ms/1000:.2f}s, "
                        f"memoria: {metrics.memory_delta_mb:.2f}MB"
                    )
                
                return result
        else:
            return await self._execute_analysis(request)

    async def _execute_analysis(
        self,
        request: CompleteAnalysisRequest
    ) -> CompleteAnalysisResult:
        """
        Ejecuta el análisis completo (lógica separada para profiling).
        """
        started_at = datetime.utcnow()
        start_time = time.time()

        # Variables para almacenar resultados
        ast: Optional[ProgramNode] = None
        algorithm_info: Optional[AlgorithmInfo] = None
        complexity_result: Optional[ComplexityAnalysis] = None
        space_result: Optional[SpaceComplexityAnalysis] = None
        recurrence_temporal: Optional[RecurrenceEquation] = None
        recurrence_spatial: Optional[RecurrenceEquation] = None
        line_by_line_result: Optional[LineByLineAnalysis] = None
        patterns_result: Optional[PatternDetectionResult] = None
        structures_result: Optional[StructureDetectionResult] = None
        visualizations: list[VisualizationResult] = []
        
        errors = []
        warnings = []

        try:
            # PASO 1: PARSING
            logger.info("Paso 1: Parsing")
            
            # ========== PROFILING: Parsing ==========
            if self.profiling_enabled and self.monitor:
                with self.monitor.monitor("parse_code", module="parser"):
                    ast, algorithm_info = await self._parse_code(request, errors)
            else:
                ast, algorithm_info = await self._parse_code(request, errors)

            # Si parsing falla, retornar early
            if not ast:
                return self._create_result(
                    started_at=started_at,
                    start_time=start_time,
                    algorithm_name=algorithm_info.name if algorithm_info else "unknown",
                    algorithm_info=algorithm_info,
                    errors=errors,
                    warnings=warnings,
                )

            # ========== PASOS 2-4: ANÁLISIS PARALELO ==========
            # Estos pasos son independientes y pueden ejecutarse concurrentemente
            logger.info("Ejecutando análisis paralelo: complejidad, patrones, estructuras")

            # Crear tareas para cada análisis
            tasks = []
            task_names = []

            # Tarea 1: Análisis de complejidad
            if request.analyze_complexity:
                async def analyze_complexity_task():
                    if self.profiling_enabled and self.monitor:
                        with self.monitor.monitor("complexity_analysis", module="analyzer"):
                            return await self._analyze_complexity(ast, request, errors, warnings)
                    else:
                        return await self._analyze_complexity(ast, request, errors, warnings)

                tasks.append(analyze_complexity_task())
                task_names.append("complexity")
            else:
                tasks.append(self._return_none())
                task_names.append("complexity")

            # Tarea 2: Detección de patrones
            if request.analyze_patterns:
                async def detect_patterns_task():
                    if self.profiling_enabled and self.monitor:
                        with self.monitor.monitor("pattern_detection", module="patterns"):
                            return await self._detect_patterns_safe(ast, request, warnings)
                    else:
                        return await self._detect_patterns_safe(ast, request, warnings)

                tasks.append(detect_patterns_task())
                task_names.append("patterns")
            else:
                tasks.append(self._return_none())
                task_names.append("patterns")

            # Tarea 3: Detección de estructuras
            if request.analyze_structures:
                async def detect_structures_task():
                    if self.profiling_enabled and self.monitor:
                        with self.monitor.monitor("structure_detection", module="structures"):
                            return await self._detect_structures_safe(ast, request, warnings)
                    else:
                        return await self._detect_structures_safe(ast, request, warnings)

                tasks.append(detect_structures_task())
                task_names.append("structures")
            else:
                tasks.append(self._return_none())
                task_names.append("structures")

            # EJECUTAR EN PARALELO
            parallel_start = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            parallel_time = time.time() - parallel_start

            logger.info(f"Análisis paralelo completado en {parallel_time:.3f}s")

            # Extraer resultados
            complexity_result = results[0] if not isinstance(results[0], Exception) else None
            patterns_result = results[1] if not isinstance(results[1], Exception) else None
            structures_result = results[2] if not isinstance(results[2], Exception) else None

            # Log errores si los hubo
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Error en {task_names[i]}: {result}")
                    warnings.append(f"{task_names[i]} falló: {str(result)}")

            # ========== PASO 5: VISUALIZACIONES (OPCIONAL) ==========
            if request.generate_visualizations and ast:
                logger.info("Paso 5: Generación de visualizaciones")

                if self.profiling_enabled and self.monitor:
                    with self.monitor.monitor("generate_visualizations", module="visualization"):
                        visualizations = await self._generate_visualizations(
                            ast, request, complexity_result
                        )
                else:
                    visualizations = await self._generate_visualizations(
                        ast, request, complexity_result
                    )

            # CONSTRUIR RESULTADO FINAL
            return self._create_result(
                started_at=started_at,
                start_time=start_time,
                algorithm_name=algorithm_info.name if algorithm_info else "unknown",
                algorithm_info=algorithm_info,
                complexity=complexity_result,
                space_complexity=space_result,
                recurrence_temporal=recurrence_temporal,
                recurrence_spatial=recurrence_spatial,
                line_by_line=line_by_line_result,
                patterns=patterns_result,
                structures=structures_result,
                visualizations=visualizations,
                errors=errors,
                warnings=warnings,
            )

        except TimeoutException as e:
            logger.error(f"Timeout en análisis: {e}")
            errors.append(f"Timeout: {e}")
            return self._create_result(
                started_at=started_at,
                start_time=start_time,
                algorithm_name=algorithm_info.name if algorithm_info else "unknown",
                algorithm_info=algorithm_info,
                errors=errors,
                warnings=warnings,
            )

        except Exception as e:
            logger.error(f"Error inesperado: {e}", exc_info=True)
            errors.append(f"Error inesperado: {e}")
            return self._create_result(
                started_at=started_at,
                start_time=start_time,
                algorithm_name=algorithm_info.name if algorithm_info else "unknown",
                algorithm_info=algorithm_info,
                errors=errors,
                warnings=warnings,
            )
        
    async def _return_none(self):
        """Helper para retornar None de forma async"""
        return None

    # Helper Methods - Extracción de Información
    async def _parse_code(
        self,
        request: CompleteAnalysisRequest,
        errors: list
    ) -> tuple[Optional[ProgramNode], Optional[AlgorithmInfo]]:
        """Parsea el código y extrae información."""
        try:
            ast = self.parser.parse(request.code, validate=True)
            algorithm_info = self._extract_algorithm_info(ast, request.code)
            return ast, algorithm_info
        except ParserException as e:
            logger.error(f"Error en parsing: {e}")
            errors.append(f"Error de parsing: {e}")

            # CREAR PLACEHOLDER EN LUGAR DE RETORNAR
            algorithm_info = AlgorithmInfo(
                name="unknown",
                parameters=[],
                has_recursion=False,
                has_loops=False,
                max_nesting_depth=0,
                total_lines=len(request.code.splitlines()),
                total_statements=0
            )
            return None, algorithm_info

    async def _analyze_complexity(
        self,
        ast: ProgramNode,
        request: CompleteAnalysisRequest,
        errors: list,
        warnings: list
    ) -> Optional[ComplexityAnalysis]:
        """Analiza complejidad del algoritmo."""
        try:
            analysis_result = self.analyzer_engine.analyze(
                ast,
                analyze_line_by_line=request.complexity_options.analyze_line_by_line,
                analyze_space=request.complexity_options.analyze_spatial,
                analyze_recurrence=request.complexity_options.analyze_recurrence,
                analyze_tight_bounds=request.complexity_options.calculate_tight_bounds,
            )

            # AGREGAR VALIDACIÓN
            if analysis_result is None:
                logger.error("AnalyzerEngine retornó None")
                errors.append("Analyzer retornó resultado nulo")
                return None
            else:
                # Convertir a schemas
                return self._build_complexity_analysis(analysis_result)

        except AnalyzerException as e:
            # CAMBIO CRÍTICO: Agregar a errors en vez de solo warnings
            logger.error(f"Error en análisis de complejidad: {e}")
            errors.append(f"Error en análisis de complejidad: {e}")
            # También mantener warning para info adicional
            warnings.append(f"Análisis de complejidad parcial: {e}")
            return None

        except Exception as e:
            # NUEVO: Capturar cualquier otro error
            logger.error(f"Error inesperado en analyzer: {e}", exc_info=True)
            errors.append(f"Error en análisis: {e}")
            return None

    async def _detect_patterns_safe(
        self,
        ast: ProgramNode,
        request: CompleteAnalysisRequest,
        warnings: list
    ) -> Optional[PatternDetectionResult]:
        """Detecta patrones con manejo de errores."""
        try:
            return self._detect_patterns(ast, request)
        except Exception as e:
            logger.warning(f"Error en detección de patrones: {e}")
            warnings.append(f"Detección de patrones fallida: {e}")
            return None

    async def _detect_structures_safe(
        self,
        ast: ProgramNode,
        request: CompleteAnalysisRequest,
        warnings: list
    ) -> Optional[StructureDetectionResult]:
        """Detecta estructuras con manejo de errores."""
        try:
            return self._detect_structures(ast, request)
        except Exception as e:
            logger.warning(f"Error en detección de estructuras: {e}")
            warnings.append(f"Detección de estructuras fallida: {e}")
            return None

    def _extract_algorithm_info(self, ast: ProgramNode, code: str) -> AlgorithmInfo:
        """Extrae información del algoritmo desde el AST."""
        parameters = []
        if ast.algorithm and ast.algorithm.parameters:
            for param in ast.algorithm.parameters:
                parameters.append(
                    AlgorithmParameter(
                        name=param.name,
                        type=getattr(param, 'type', None),
                        is_array=getattr(param, 'is_array', False),
                        dimensions=getattr(param, 'dimensions', []),
                        is_object=getattr(param, 'is_object', False),
                        object_type=getattr(param, 'object_type', None),
                        description=None,
                    )
                )

        return AlgorithmInfo(
            name=ast.algorithm.name if ast.algorithm else "unknown",
            parameters=parameters,
            has_recursion=False,  # Detectar del análisis
            has_loops=True,  # Detectar del análisis
            max_nesting_depth=0,  # Calcular
            total_lines=len(code.splitlines()),
            total_statements=0,  # Contar del AST
        )

    # Helper Methods - Construcción de Schemas
    def _build_complexity_analysis(self, analysis_result) -> ComplexityAnalysis:
        """Construye ComplexityAnalysis desde resultado del analyzer."""
        return ComplexityAnalysis(
            big_o=analysis_result.big_o,
            omega=analysis_result.omega,
            theta=analysis_result.theta,
            big_o_class=self._get_complexity_class(analysis_result.big_o),
            omega_class=self._get_complexity_class(analysis_result.omega),
            theta_class=self._get_complexity_class(analysis_result.theta) if analysis_result.theta else None,
            explanation=f"Complejidad temporal del algoritmo",
            reasoning=[
                "Análisis basado en estructura del código",
                f"Complejidad dominante: {analysis_result.big_o}"
            ],
            has_tight_bound=analysis_result.theta is not None,
        )

    def _build_space_complexity(self, space_analysis) -> SpaceComplexityAnalysis:
        """Construye SpaceComplexityAnalysis."""
        return SpaceComplexityAnalysis(
            total=space_analysis.space_complexity,
            input_space=space_analysis.input_space,
            auxiliary_space=space_analysis.auxiliary_space,
            recursion_space=space_analysis.recursion_space,
            explanation=f"Espacio total: {space_analysis.space_complexity}",
            breakdown={
                "input": space_analysis.input_space,
                "auxiliary": space_analysis.auxiliary_space,
                "recursion": space_analysis.recursion_space,
            }
        )

    def _build_recurrence_equation(self, recurrence) -> Optional[RecurrenceEquation]:
        """Construye RecurrenceEquation."""
        if not recurrence or not recurrence.recurrence_equation:
            return None

        eq = recurrence.recurrence_equation
        return RecurrenceEquation(
            equation=eq.equation,
            base_case=eq.base_case,
            recursion_pattern=eq.recursion_pattern,
            a=None,  # Extraer si disponible
            b=None,
            f_n=None,
            explanation=f"Ecuación de recurrencia",
        )

    def _build_line_by_line(self, line_by_line, dominant_complexity: str) -> LineByLineAnalysis:
        """Construye LineByLineAnalysis."""
        lines = [
            LineExecution(
                line_number=line.line_number,
                code=getattr(line, 'code', getattr(line, 'statement', '')),  
                execution_count=line.execution_count,
                statement_type=line.statement_type,
                complexity_contribution=line.complexity_contribution,
                explanation=line.explanation,
                location=None,
            )
            for line in line_by_line.lines
        ]

        return LineByLineAnalysis(
            lines=lines,
            dominant_complexity=dominant_complexity,
            total_lines=len(lines),
            summary=f"Análisis línea por línea completo",
        )

    def _detect_patterns(
        self,
        ast: ProgramNode,
        request: CompleteAnalysisRequest
    ) -> PatternDetectionResult:
        """Detecta patrones y convierte a schema."""
        result = self.pattern_detector.detect(
            ast,
            min_confidence=request.pattern_options.min_confidence
        )

        # MAPEAR atributos del core al schema
        # result del core tiene: all_patterns, primary_pattern, confident_patterns
        # schema de API necesita: patterns_found, scored_patterns, primary_pattern

        # Verificar estructura ANTES de intentar convertir
        if not hasattr(result, 'all_patterns'):
            logger.error("PatternDetector retornó objeto sin estructura esperada")
            return PatternDetectionResult(
                patterns_found=[],
                scored_patterns=[],
                primary_pattern=None,
                confident_patterns=[],
                summary="Error en detección de patrones",
                pattern_count=0,
                metadata={}
            )

        # Convertir ScoredPattern del core a PatternMatch del schema
        patterns_found = []
        for scored in result.all_patterns:  # Usar all_patterns
            pattern_match = PatternMatch(
                pattern_type=scored.pattern.pattern_type,
                pattern_name=scored.pattern.pattern_name,
                confidence=scored.pattern.confidence,
                confidence_level=ConfidenceLevelEnum(scored.pattern.confidence_level.value),
                indicators_found=[
                    PatternIndicator(
                        name=ind.name,
                        description=ind.description,
                        found=ind.found,
                        weight=ind.weight,
                        evidence=ind.evidence,
                        location=ind.location,
                    )
                    for ind in scored.pattern.indicators_found
                ],
                indicators_missing=[
                    PatternIndicator(
                        name=ind.name,
                        description=ind.description,
                        found=ind.found,
                        weight=ind.weight,
                        evidence=ind.evidence,
                        location=ind.location,
                    )
                    for ind in scored.pattern.indicators_missing
                ],
                reasoning=scored.pattern.reasoning,
                typical_complexity=scored.pattern.typical_complexity,
                metadata=scored.pattern.metadata,
            )
            patterns_found.append(pattern_match)

        # Convertir scored_patterns (con scoring)
        scored_patterns = [
            ScoredPattern(
                pattern=PatternMatch(
                    pattern_type=sp.pattern.pattern_type,
                    pattern_name=sp.pattern.pattern_name,
                    confidence=sp.pattern.confidence,
                    confidence_level=ConfidenceLevelEnum(sp.pattern.confidence_level.value),
                    indicators_found=[
                        PatternIndicator(
                            name=ind.name,
                            description=ind.description,
                            found=ind.found,
                            weight=ind.weight,
                            evidence=ind.evidence,
                            location=ind.location,
                        )
                        for ind in sp.pattern.indicators_found
                    ],
                    indicators_missing=[
                        PatternIndicator(
                            name=ind.name,
                            description=ind.description,
                            found=ind.found,
                            weight=ind.weight,
                            evidence=ind.evidence,
                            location=ind.location,
                        )
                        for ind in sp.pattern.indicators_missing
                    ],
                    reasoning=sp.pattern.reasoning,
                    typical_complexity=sp.pattern.typical_complexity,
                    metadata=sp.pattern.metadata,
                ),
                raw_score=getattr(sp, 'raw_score', sp.pattern.confidence),
                adjusted_score=getattr(sp, 'adjusted_score', sp.final_score),
                final_score=getattr(sp, 'final_score', sp.pattern.confidence),
                confidence_bonus=getattr(sp, 'confidence_bonus', 0.0),
                missing_penalty=getattr(sp, 'missing_penalty', 0.0),
                conflict_penalty=getattr(sp, 'conflict_penalty', 0.0),
                conflicts=getattr(sp, 'conflicts', []),
                rank=getattr(sp, 'rank', 0),
            )
            for sp in result.all_patterns  # Usar all_patterns
        ]

        # Convertir primary_pattern
        primary_pattern = None
        if result.primary_pattern:
            sp = result.primary_pattern
            primary_pattern = ScoredPattern(
                pattern=PatternMatch(
                    pattern_type=sp.pattern.pattern_type,
                    pattern_name=sp.pattern.pattern_name,
                    confidence=sp.pattern.confidence,
                    confidence_level=ConfidenceLevelEnum(sp.pattern.confidence_level.value),
                    indicators_found=[
                        PatternIndicator(
                            name=ind.name,
                            description=ind.description,
                            found=ind.found,
                            weight=ind.weight,
                            evidence=ind.evidence,
                            location=ind.location,
                        )
                        for ind in sp.pattern.indicators_found
                    ],
                    indicators_missing=[
                        PatternIndicator(
                            name=ind.name,
                            description=ind.description,
                            found=ind.found,
                            weight=ind.weight,
                            evidence=ind.evidence,
                            location=ind.location,
                        )
                        for ind in sp.pattern.indicators_missing
                    ],
                    reasoning=sp.pattern.reasoning,
                    typical_complexity=sp.pattern.typical_complexity,
                    metadata=sp.pattern.metadata,
                ),
                raw_score=getattr(sp, 'raw_score', sp.pattern.confidence),
                adjusted_score=getattr(sp, 'adjusted_score', sp.final_score),
                final_score=getattr(sp, 'final_score', sp.pattern.confidence),
                confidence_bonus=getattr(sp, 'confidence_bonus', 0.0),
                missing_penalty=getattr(sp, 'missing_penalty', 0.0),
                conflict_penalty=getattr(sp, 'conflict_penalty', 0.0),
                conflicts=getattr(sp, 'conflicts', []),
                rank=getattr(sp, 'rank', 0),
            )

        # Convertir confident_patterns
        confident_patterns = [
            ScoredPattern(
                pattern=PatternMatch(
                    pattern_type=sp.pattern.pattern_type,
                    pattern_name=sp.pattern.pattern_name,
                    confidence=sp.pattern.confidence,
                    confidence_level=ConfidenceLevelEnum(sp.pattern.confidence_level.value),
                    indicators_found=[
                        PatternIndicator(
                            name=ind.name,
                            description=ind.description,
                            found=ind.found,
                            weight=ind.weight,
                            evidence=ind.evidence,
                            location=ind.location,
                        )
                        for ind in sp.pattern.indicators_found
                    ],
                    indicators_missing=[
                        PatternIndicator(
                            name=ind.name,
                            description=ind.description,
                            found=ind.found,
                            weight=ind.weight,
                            evidence=ind.evidence,
                            location=ind.location,
                        )
                        for ind in sp.pattern.indicators_missing
                    ],
                    reasoning=sp.pattern.reasoning,
                    typical_complexity=sp.pattern.typical_complexity,
                    metadata=sp.pattern.metadata,
                ),
                raw_score=getattr(sp, 'raw_score', sp.pattern.confidence),
                adjusted_score=getattr(sp, 'adjusted_score', sp.final_score),
                final_score=getattr(sp, 'final_score', sp.pattern.confidence),
                confidence_bonus=getattr(sp, 'confidence_bonus', 0.0),
                missing_penalty=getattr(sp, 'missing_penalty', 0.0),
                conflict_penalty=getattr(sp, 'conflict_penalty', 0.0),
                conflicts=getattr(sp, 'conflicts', []),
                rank=getattr(sp, 'rank', 0),
            )
            for sp in result.confident_patterns
        ]

        return PatternDetectionResult(
            patterns_found=patterns_found,  # Usar patterns_found
            scored_patterns=scored_patterns,
            primary_pattern=primary_pattern,
            confident_patterns=confident_patterns,
            summary=result.summary,
            pattern_count=len(patterns_found),  # Contar patterns_found
            metadata=result.metadata,
        )

    def _detect_structures(
        self,
        ast: ProgramNode,
        request: CompleteAnalysisRequest
    ) -> StructureDetectionResult:
        """Detecta estructuras y convierte a schema."""
        result = self.structure_identifier.identify(
            ast,
            min_confidence=request.structure_options.min_confidence
        )

        structures_found = [
            StructureMatch(
                structure_type=s.structure_type.value,
                structure_name=s.structure_name,
                confidence=s.confidence,
                confidence_level=ConfidenceLevelEnum(s.confidence_level.value),
                variables=s.variables,
                operations=s.operations,
                reasoning=s.reasoning,
            )
            for s in result.structures_found
        ]

        primary_structure = None
        if result.primary_structure:
            s = result.primary_structure
            primary_structure = StructureMatch(
                structure_type=s.structure_type.value,
                structure_name=s.structure_name,
                confidence=s.confidence,
                confidence_level=ConfidenceLevelEnum(s.confidence_level.value),
                variables=s.variables,
                operations=s.operations,
                reasoning=s.reasoning,
            )

        return StructureDetectionResult(
            structures_found=structures_found,
            primary_structure=primary_structure,
            primary_usage=None,  # Implementar si se requiere
            summary=result.summary,
        )

    async def _generate_visualizations(
        self,
        ast: ProgramNode,
        request: CompleteAnalysisRequest,
        complexity: Optional[ComplexityAnalysis]
    ) -> list[VisualizationResult]:
        """Genera visualizaciones."""
        visualizations = []

        # Árbol de recursión
        from app.schemas.analysis_request import VisualizationType
        if VisualizationType.RECURSION_TREE in request.visualization_options.types:
            if complexity and complexity.has_tight_bound:  # Simplificado
                try:
                    tree_result = generate_recursion_tree(
                        ast,
                        start_value=request.visualization_options.start_value,
                        max_depth=request.visualization_options.max_depth
                    )

                    render_format = RenderFormat(request.visualization_options.format)
                    rendered = render_diagram(tree_result, format=render_format)

                    content = rendered.content
                    if isinstance(content, bytes):
                        content = content.decode('utf-8')

                    visualizations.append(
                        VisualizationResult(
                            type="recursion_tree",
                            format=request.visualization_options.format,
                            content=content,
                            file_path=None,
                            statistics={
                                "recursion_type": tree_result.recursion_type.value,
                                "total_calls": tree_result.total_calls,
                                "max_depth": tree_result.max_depth,
                            },
                            metadata={"algorithm_name": ast.algorithm.name if ast.algorithm else "unknown"},
                        )
                    )
                except Exception as e:
                    logger.warning(f"Error en árbol de recursión: {e}")

        # Flujo de ejecución
        if VisualizationType.EXECUTION_FLOW in request.visualization_options.types:
            try:
                flow_result = generate_execution_flow(ast)
                render_format = RenderFormat(request.visualization_options.format)
                rendered = render_diagram(flow_result, format=render_format)

                content = rendered.content
                if isinstance(content, bytes):
                    content = content.decode('utf-8')

                visualizations.append(
                    VisualizationResult(
                        type="execution_flow",
                        format=request.visualization_options.format,
                        content=content,
                        file_path=None,
                        statistics=flow_result.statistics,
                        metadata={"algorithm_name": ast.algorithm.name if ast.algorithm else "unknown"},
                    )
                )
            except Exception as e:
                logger.warning(f"Error en flujo de ejecución: {e}")

        return visualizations

    def _create_result(
        self,
        started_at: datetime,
        start_time: float,
        algorithm_name: str,
        algorithm_info: Optional[AlgorithmInfo],
        complexity: Optional[ComplexityAnalysis] = None,
        space_complexity: Optional[SpaceComplexityAnalysis] = None,
        recurrence_temporal: Optional[RecurrenceEquation] = None,
        recurrence_spatial: Optional[RecurrenceEquation] = None,
        line_by_line: Optional[LineByLineAnalysis] = None,
        patterns: Optional[PatternDetectionResult] = None,
        structures: Optional[StructureDetectionResult] = None,
        visualizations: list[VisualizationResult] = None,
        errors: list[str] = None,
        warnings: list[str] = None,
    ) -> CompleteAnalysisResult:
        """Crea el resultado final usando schemas."""

        # AGREGAR VALIDACIÓN
        if errors is None:
            errors = []
        if warnings is None:
            warnings = []

        # NUEVO: Detectar fallo silencioso
        if not errors and complexity is None:
            logger.warning("No hay errores pero complexity es None - posible fallo silencioso")
            errors.append("Análisis de complejidad no completado")

        # Metadata
        metadata = AnalysisMetadata(
            timing=TimingMetadata(
                started_at=started_at,
                # completed_at=completed_at,
                # duration_ms=duration * 1000,
            ),
            resources=None,
            version="1.0.0",
            environment="production",
        )

        # Resumen
        summary = self._generate_summary(
            algorithm_name,
            complexity,
            space_complexity,
            patterns,
            structures
        )

        # Recomendaciones
        recommendations = self._generate_recommendations(complexity, patterns)

        return CompleteAnalysisResult(
            success=len(errors) == 0,
            message="Análisis completado" if not errors else "Análisis con errores",
            # timestamp=completed_at,
            algorithm_name=algorithm_name,
            algorithm_info=algorithm_info,
            complexity=complexity,
            space_complexity=space_complexity,
            recurrence_temporal=recurrence_temporal,
            recurrence_spatial=recurrence_spatial,
            line_by_line=line_by_line,
            patterns=patterns,
            structures=structures,
            visualizations=visualizations or [],
            metadata=metadata,
            summary=summary,
            recommendations=recommendations,
        )

    def _generate_summary(
        self,
        algorithm_name: str,
        complexity: Optional[ComplexityAnalysis],
        space_complexity: Optional[SpaceComplexityAnalysis],
        patterns: Optional[PatternDetectionResult],
        structures: Optional[StructureDetectionResult],
    ) -> str:
        """Genera resumen ejecutivo."""
        lines = [f"Algoritmo: {algorithm_name}", ""]

        if complexity:
            lines.append(f"Complejidad temporal: {complexity.big_o}")
            if complexity.theta:
                lines.append(f"Cota ajustada: {complexity.theta}")

        if space_complexity:
            lines.append(f"Complejidad espacial: {space_complexity.total}")

        if patterns and patterns.primary_pattern:
            primary = patterns.primary_pattern
            lines.append(f"Patrón: {primary.pattern.pattern_name} ({primary.final_score:.0%})")

        if structures and structures.primary_structure:
            primary = structures.primary_structure
            lines.append(f"Estructura: {primary.structure_name} ({primary.confidence:.0%})")

        return "\n".join(lines)

    def _generate_recommendations(
        self,
        complexity: Optional[ComplexityAnalysis],
        patterns: Optional[PatternDetectionResult]
    ) -> list[str]:
        """Genera recomendaciones."""
        recommendations = []

        if complexity:
            if complexity.big_o_class in [ComplexityClass.EXPONENTIAL, ComplexityClass.FACTORIAL]:
                recommendations.append("Considerar optimización - complejidad muy alta")
            elif complexity.big_o_class == ComplexityClass.QUADRATIC:
                recommendations.append("Evaluar algoritmos alternativos de menor complejidad")

        return recommendations

    def _get_complexity_class(self, notation: str) -> Optional[ComplexityClass]:
        """Obtiene clase de complejidad desde notación."""
        if not notation:
            return None

        clean = notation.replace("O(", "").replace(")", "").replace("Ω(", "").replace("Θ(", "")

        mapping = {
            "1": ComplexityClass.CONSTANT,
            "log n": ComplexityClass.LOGARITHMIC,
            "n": ComplexityClass.LINEAR,
            "n log n": ComplexityClass.LINEARITHMIC,
            "n²": ComplexityClass.QUADRATIC,
            "n^2": ComplexityClass.QUADRATIC,
            "n³": ComplexityClass.CUBIC,
            "n^3": ComplexityClass.CUBIC,
            "2^n": ComplexityClass.EXPONENTIAL,
            "n!": ComplexityClass.FACTORIAL,
        }

        return mapping.get(clean, ComplexityClass.POLYNOMIAL)
    
    def _map_agent_result(
        self,
        agent_result: dict,
        request: CompleteAnalysisRequest
    ) -> CompleteAnalysisRequest:
        """
        Convierte el dict de CoordinatorAgent al schema CompleteAnalysisResult.

        El pipeline de agentes devuelve con claves:
            success, algorithm_name, complexity, patterns,
            structures, validation, errors
        Este método lo adapta al schema que usan los endpoints de la API
        """
        from datetime import datetime
        started_at = datetime.utcnow()
        start_time = __import__('time').time()
        errors = [e.get('error', str(e)) if isinstance(e, dict) else str(e)
                  for e in agent_result.get('errors', [])]
        warnings = []

        # Complejidad
        complexity_schema = None
        raw_complexity = agent_result.get('complexity') or {}
        if raw_complexity.get('big_o'):
            complexity_schema = ComplexityAnalysis(
                big_o=raw_complexity.get('big_o', 'O(?)'),
                omega=raw_complexity.get('omega', 'Ω(?)'),
                theta=raw_complexity.get('theta'),
                big_o_class=self._get_complexity_class(raw_complexity.get('big_o', '')),
                omega_class=self._get_complexity_class(raw_complexity.get('omega', '')),
                theta_class=self._get_complexity_class(raw_complexity.get('theta', '')),
                explanation='Complejidad validada por sistema multiagente',
                reasoning=[
                    'Analisís realizado por ComplexityAgent',
                    f"Validación LLM: {raw_complexity.get('llm_validation', {}).get('big_o', 'N/A')}"
                ],
                has_tight_bound=raw_complexity.get('theta') is not None,
            )

        # Patrones
        patterns_schema = None
        raw_patterns = agent_result.get('patterns') or {}
        if raw_patterns.get('primary_pattern'):
            # Reutilizar _detect_patterns si tenemos el AST disponible,
            # o construir un PatternDetectionResult mínimo desde el dict.
            from app.schemas import PatternDetectionResult as PDR
            patterns_schema = PDR(
                patterns_found=[],
                scored_patterns=[],
                primary_pattern=None,
                confident_patterns=[],
                summary=raw_patterns.get('summary', ''),
                pattern_count=len(raw_patterns.get('all_patterns', [])),
                metadata={'source': 'multiagent'},
            )

        # Estructuras
        structures_schema = None
        raw_structures = agent_result.get('structures') or {}
        if raw_structures.get('primary_structure'):
            from app.schemas import StructureDetectionResult as SDR
            structures_schema = SDR(
                structures_found=[],
                primary_structure=None,
                primary_usage=None,
                summary=raw_structures.get('summary', ''),
            )

        algorithm_name = agent_result.get('algorithm_name') or 'unknown'

        return self._create_result(
            started_at=started_at,
            start_time=start_time,
            algorithm_name=algorithm_name,
            algorithm_info=None,   # No disponible desde pipeline de agentes
            complexity=complexity_schema,
            patterns=patterns_schema,
            structures=structures_schema,
            errors=errors,
            warnings=warnings,
        )