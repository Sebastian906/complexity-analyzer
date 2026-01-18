"""
Analysis Orchestrator - Orquestación de Análisis Completo

Coordina todos los módulos de análisis (Parser, Analyzer, Patterns, Structures, Visualization)
para proporcionar un análisis completo de algoritmos en un solo flujo.
"""

import time
from datetime import datetime
from typing import Optional
from uuid import uuid4

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
            try:
                ast = self.parser.parse(request.code, validate=True)
                algorithm_info = self._extract_algorithm_info(ast, request.code)
            except ParserException as e:
                logger.error(f"Error en parsing: {e}")
                errors.append(f"Error de parsing: {e}")
                # Retornar resultado parcial
                return self._create_result(
                    started_at=started_at,
                    start_time=start_time,
                    algorithm_name="unknown",
                    algorithm_info=AlgorithmInfo(
                        name="unknown",
                        parameters=[],
                        has_recursion=False,
                        has_loops=False,
                        max_nesting_depth=0,
                        total_lines=0,
                        total_statements=0
                    ),
                    errors=errors,
                    warnings=warnings,
                )

            # PASO 2: ANÁLISIS DE COMPLEJIDAD
            if request.analyze_complexity and ast:
                logger.info("Paso 2: Análisis de complejidad")
                try:
                    analysis_result = self.analyzer_engine.analyze(
                        ast,
                        analyze_line_by_line=request.complexity_options.analyze_line_by_line,
                        analyze_space=request.complexity_options.analyze_spatial,
                        analyze_recurrence=request.complexity_options.analyze_recurrence,
                        analyze_tight_bounds=request.complexity_options.calculate_tight_bounds,
                    )

                    # Convertir a schemas
                    complexity_result = self._build_complexity_analysis(analysis_result)
                    
                    if analysis_result.space_analysis:
                        space_result = self._build_space_complexity(analysis_result.space_analysis)
                    
                    if analysis_result.temporal_recurrence:
                        recurrence_temporal = self._build_recurrence_equation(
                            analysis_result.temporal_recurrence
                        )
                    
                    if analysis_result.line_by_line:
                        line_by_line_result = self._build_line_by_line(
                            analysis_result.line_by_line,
                            analysis_result.big_o
                        )

                except AnalyzerException as e:
                    logger.warning(f"Error en análisis de complejidad: {e}")
                    warnings.append(f"Análisis de complejidad parcial: {e}")

            # PASO 3: DETECCIÓN DE PATRONES
            if request.analyze_patterns and ast:
                logger.info("Paso 3: Detección de patrones")
                try:
                    patterns_result = self._detect_patterns(ast, request)
                except Exception as e:
                    logger.warning(f"Error en detección de patrones: {e}")
                    warnings.append(f"Detección de patrones fallida: {e}")

            # PASO 4: DETECCIÓN DE ESTRUCTURAS
            if request.analyze_structures and ast:
                logger.info("Paso 4: Detección de estructuras")
                try:
                    structures_result = self._detect_structures(ast, request)
                except Exception as e:
                    logger.warning(f"Error en detección de estructuras: {e}")
                    warnings.append(f"Detección de estructuras fallida: {e}")

            # PASO 5: GENERACIÓN DE VISUALIZACIONES
            if request.generate_visualizations and ast:
                logger.info("Paso 5: Generación de visualizaciones")
                try:
                    visualizations = await self._generate_visualizations(
                        ast,
                        request,
                        complexity_result
                    )
                except Exception as e:
                    logger.warning(f"Error en visualizaciones: {e}")
                    warnings.append(f"Visualizaciones parciales: {e}")

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

    # Helper Methods - Extracción de Información
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
                code=line.code,
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

        # Convertir a schemas
        patterns_found = [
            PatternMatch(
                pattern_type=p.pattern.pattern_type,
                pattern_name=p.pattern.pattern_name,
                confidence=p.pattern.confidence,
                confidence_level=ConfidenceLevelEnum(p.pattern.confidence_level.value),
                indicators_found=[
                    PatternIndicator(
                        name=ind.name,
                        description=ind.description,
                        found=ind.found,
                        weight=ind.weight,
                        evidence=ind.evidence,
                        location=ind.location,
                    )
                    for ind in p.pattern.indicators_found
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
                    for ind in p.pattern.indicators_missing
                ],
                reasoning=p.pattern.reasoning,
                typical_complexity=p.pattern.typical_complexity,
                metadata=p.pattern.metadata,
            )
            for p in result.patterns_found
        ]

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
                raw_score=sp.raw_score,
                adjusted_score=sp.adjusted_score,
                final_score=sp.final_score,
                confidence_bonus=sp.confidence_bonus,
                missing_penalty=sp.missing_penalty,
                conflict_penalty=sp.conflict_penalty,
                conflicts=sp.conflicts,
                rank=sp.rank,
            )
            for sp in result.scored_patterns
        ]

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
                raw_score=sp.raw_score,
                adjusted_score=sp.adjusted_score,
                final_score=sp.final_score,
                confidence_bonus=sp.confidence_bonus,
                missing_penalty=sp.missing_penalty,
                conflict_penalty=sp.conflict_penalty,
                conflicts=sp.conflicts,
                rank=sp.rank,
            )

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
                raw_score=sp.raw_score,
                adjusted_score=sp.adjusted_score,
                final_score=sp.final_score,
                confidence_bonus=sp.confidence_bonus,
                missing_penalty=sp.missing_penalty,
                conflict_penalty=sp.conflict_penalty,
                conflicts=sp.conflicts,
                rank=sp.rank,
            )
            for sp in result.confident_patterns
        ]

        return PatternDetectionResult(
            patterns_found=patterns_found,
            scored_patterns=scored_patterns,
            primary_pattern=primary_pattern,
            confident_patterns=confident_patterns,
            summary=result.summary,
            pattern_count=result.pattern_count,
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
        if request.visualization_options.generate_recursion_tree:
            if complexity and complexity.has_tight_bound:  # Simplificado
                try:
                    tree_result = generate_recursion_tree(
                        ast,
                        start_value=request.visualization_options.recursion_tree_start_value,
                        max_depth=request.visualization_options.recursion_tree_depth
                    )

                    render_format = RenderFormat(request.visualization_options.visualization_format)
                    rendered = render_diagram(tree_result, format=render_format)

                    content = rendered.content
                    if isinstance(content, bytes):
                        content = content.decode('utf-8')

                    visualizations.append(
                        VisualizationResult(
                            type="recursion_tree",
                            format=request.visualization_options.visualization_format,
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
        if request.visualization_options.generate_execution_flow:
            try:
                flow_result = generate_execution_flow(ast)
                render_format = RenderFormat(request.visualization_options.visualization_format)
                rendered = render_diagram(flow_result, format=render_format)

                content = rendered.content
                if isinstance(content, bytes):
                    content = content.decode('utf-8')

                visualizations.append(
                    VisualizationResult(
                        type="execution_flow",
                        format=request.visualization_options.visualization_format,
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
        completed_at = datetime.utcnow()
        duration = time.time() - start_time

        # Metadata
        metadata = AnalysisMetadata(
            timing=TimingMetadata(
                started_at=started_at,
                completed_at=completed_at,
                duration_ms=duration * 1000,
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
            success=len(errors or []) == 0,
            message="Análisis completado" if not errors else "Análisis con errores",
            timestamp=completed_at,
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